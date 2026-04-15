from flask import Flask, request, jsonify
from ViewModel import DataViewModel
from Firebase import FireBaseTools
import threading


app = Flask(__name__)
vm = DataViewModel()
ft = FireBaseTools()

@app.route("/")
def welcome_screen():
    return jsonify("Welcome to Insurance Manager")


# =========================
# CUSTOMER APIs
# =========================

@app.route("/customer", methods=["POST"])
def create_customer():
    data = request.json or {}

    customer_id = vm.generate_customer_id()

    # Extract claims list
    claims = data.pop("claims", [])  # remove from payload

    # Insert customer (without claims)
    vm.insert("customer_info", customer_id, data)
    ft.push_customer_insights() #PUSH update into RTDB
    # Assign claims
    for claim_id in claims:
        try:
            vm.assign_claim(claim_id, customer_id)
        except Exception as e:
            print("Assign error:", e)

    return jsonify({
        "customer_id": customer_id,
        "message": "Customer created with claims assigned"
    })


@app.route("/customers", methods=["GET"])
def get_all_customers():
    df = vm.get_df("customer_info")
    return jsonify(df.reset_index().to_dict(orient="records"))


@app.route("/customer/<customer_id>", methods=["GET"])
def get_customer(customer_id):
    try:
        data = vm.get_one("customer_info", customer_id)
        return jsonify(data.to_dict())
    except:
        return jsonify({"error": "Customer not found"}), 404


@app.route("/customer/<customer_id>", methods=["PUT"])
def update_customer(customer_id):
    data = request.json or {}

    new_claims = set(data.pop("claims", []))

    try:
        # 🔥 STEP 1: Get current claims from DB
        df = vm.get_df("claims_info")
        current_claims = set(
            df[df["customer_id"] == customer_id].index.tolist()
        )

        # 🔥 STEP 2: Compute diff
        to_add = new_claims - current_claims
        to_remove = current_claims - new_claims

        # 🔥 STEP 3: Update customer basic info
        vm.update("customer_info", customer_id, data)

        # 🔥 STEP 4: Assign new claims
        for claim_id in to_add:
            vm.assign_claim(claim_id, customer_id)

        # 🔥 STEP 5: Deassign removed claims
        for claim_id in to_remove:
            vm.deassign_claim(claim_id)

        ft.push_customer_insights()
        return jsonify({"message": "Customer updated with claims sync"})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/customer/<customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    vm.delete("customer_info", customer_id)
    ft.push_customer_insights()
    return jsonify({"message": "Customer deleted"})


# =========================
# CLAIM APIs
# =========================

@app.route("/claim", methods=["POST"])
def create_claim():
    data = request.json or {}

    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id required"}), 400

    try:
        user = vm.get_user_with_role(user_id)
        role = user["role"].lower()

        # ✅ Allow only client + admin
        if role not in ["client", "admin"]:
            return jsonify({"error": "Unauthorized role"}), 403

        customer_id = user.get("customer_id")

        # 🔥 CORE LOGIC SPLIT
        if role == "client":
            if not customer_id:
                return jsonify({"error": "Client not linked to customer profile"}), 400

            data["customer_id"] = customer_id

        elif role == "admin":
            # 👇 Admin → no linking
            data["customer_id"] = None

        # 🔥 Create claim
        claim_id = vm.generate_claim_id()
        vm.insert("claims_info", claim_id, data)

        # 🔥 Optional insights
        status = data.get("status", "PENDING")
        claim_amount = data.get("claim_amount", 0)

        ft.handle_claim_create(status, claim_amount)

        return jsonify({
            "claim_id": claim_id,
            "message": "Claim created"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/claims", methods=["GET"])
def get_all_claims():
    df = vm.get_df("claims_info")
    return jsonify(df.reset_index().to_dict(orient="records"))


@app.route("/claim/<claim_id>", methods=["GET"])
def get_claim(claim_id):
    try:
        data = vm.get_one("claims_info", claim_id)
        return jsonify(data.to_dict())
    except:
        return jsonify({"error": "Claim not found"}), 404


@app.route("/claim/<claim_id>", methods=["PUT"])
def update_claim(claim_id):
    data = request.json or {}
    try:
        vm.update("claims_info", claim_id, data)
    except:
        return jsonify({"error": "Claim not found"}), 404

    # 🔥 Firebase should NEVER break API
    try:
        threading.Thread(target=ft.push_claims_insights).start() 
    except Exception as e:
        print("Firebase error:", e)

    return jsonify({"message": "Claim updated"})


@app.route("/claim/<claim_id>", methods=["DELETE"])
def delete_claim(claim_id):
    try:
        # 🔥 Fetch BEFORE delete
        claim = vm.get_one("claims_info", claim_id)

        status = claim["status"]
        claim_amount = claim["claim_amount"]

        vm.delete("claims_info", claim_id)

        ft.handle_claim_delete(status, claim_amount)

        return jsonify({"message": "Claim deleted"})

    except:
        return jsonify({"error": "Claim not found"}), 404


# 🔥 NEW CLAIM ASSIGNMENT SYSTEM

@app.route("/claims/unassigned", methods=["GET"])
def get_unassigned_claims():
    try:
        data = vm.get_unassigned_claims()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/claims/assign", methods=["PUT"])
def assign_claim():
    data = request.json or {}

    claim_id = data.get("claim_id")
    customer_id = data.get("customer_id")

    if not claim_id or not customer_id:
        return jsonify({"error": "claim_id and customer_id required"}), 400

    try:
        vm.assign_claim(claim_id, customer_id)
        return jsonify({"message": "Claim assigned successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/claims/deassign/<claim_id>", methods=["PUT"])
def deassign_claim(claim_id):
    try:
        vm.deassign_claim(claim_id)
        return jsonify({"message": "Claim deassigned successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# =========================
# POLICY APIs
# =========================

@app.route("/policy", methods=["POST"])
def create_policy():
    data = request.json or {}
    policy_id = vm.generate_policy_id()

    vm.insert("policy_info", policy_id, data)

    ft.push_policy_insights()  # 🔥 recompute

    return jsonify({
        "policy_id": policy_id,
        "message": "Policy created"
    })


@app.route("/policies", methods=["GET"])
def get_all_policies():
    df = vm.get_df("policy_info")
    return jsonify(df.reset_index().to_dict(orient="records"))


@app.route("/policy/<policy_id>", methods=["GET"])
def get_policy(policy_id):
    try:
        data = vm.get_one("policy_info", policy_id)
        return jsonify(data.to_dict())
    except:
        return jsonify({"error": "Policy not found"}), 404


@app.route("/policy/<policy_id>", methods=["PUT"])
def update_policy(policy_id):
    data = request.json or {}
    try:
        vm.update("policy_info", policy_id, data)

        ft.push_policy_insights()  # 🔥 recompute

        return jsonify({"message": "Policy updated"})
    except:
        return jsonify({"error": "Policy not found"}), 404


@app.route("/policy/<policy_id>", methods=["DELETE"])
def delete_policy(policy_id):
    try:
        vm.delete("policy_info", policy_id)

        ft.push_policy_insights()  # 🔥 recompute

        return jsonify({"message": "Policy deleted"})
    except:
        return jsonify({"error": "Policy not found"}), 404


# =========================
# PAYMENT APIs
# =========================

@app.route("/payment", methods=["POST"])
def create_payment():
    data = request.json or {}

    payment_id = vm.generate_payment_id()
    vm.insert("payment_info", payment_id, data)

    # 🔥 extract values
    status = data.get("payment_status", "PENDING")
    amount = int(data.get("payment_amount", 0))
    mode = data.get("payment_mode", "UNKNOWN")

    ft.handle_payment_create(status, amount, mode)

    return jsonify({
        "payment_id": payment_id,
        "message": "Payment created"
    })


@app.route("/payments", methods=["GET"])
def get_all_payments():
    df = vm.get_df("payment_info")
    return jsonify(df.reset_index().to_dict(orient="records"))


@app.route("/payment/<payment_id>", methods=["GET"])
def get_payment(payment_id):
    try:
        data = vm.get_one("payment_info", payment_id)
        return jsonify(data.to_dict())
    except:
        return jsonify({"error": "Payment not found"}), 404


@app.route("/payment/<payment_id>", methods=["PUT"])
def update_payment(payment_id):
    data = request.json or {}
    try:
        vm.update("payment_info", payment_id, data)

        ft.push_payment_insights()  # 🔥 recompute

        return jsonify({"message": "Payment updated"})
    except:
        return jsonify({"error": "Payment not found"}), 404


@app.route("/payment/<payment_id>", methods=["DELETE"])
def delete_payment(payment_id):
    try:
        payment = vm.get_one("payment_info", payment_id)

        status = payment["payment_status"]
        amount = payment["payment_amount"]
        mode = payment["payment_mode"]

        vm.delete("payment_info", payment_id)

        ft.handle_payment_delete(status, amount, mode)

        return jsonify({"message": "Payment deleted"})

    except:
        return jsonify({"error": "Payment not found"}), 404


# =========================
# USER APIs
# =========================

@app.route("/user", methods=["POST"])
def create_user():
    data = request.json or {}

    role_id = data.get("role_id")
    username = data.get("username")
    password = data.get("password")

    if not username or not password or not role_id:
        return jsonify({"error": "username, password, role_id required"}), 400

    user_id = vm.generate_user_id()

    # 🔥 CASE 1: CLIENT
    if role_id == 1:
        required_fields = ["name", "phone", "age", "address", "email"]

        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required for client"}), 400

        # ✅ generate customer_id
        customer_id = vm.generate_customer_id()

        # ✅ insert into customer_info
        vm.insert("customer_info", customer_id, {
            "name": data["name"],
            "phone": data["phone"],
            "age": data["age"],
            "address": data["address"],
            "email": data["email"]
        })

        # ✅ insert into user_accounts WITH customer_id
        vm.insert("user_accounts", user_id, {
            "username": username,
            "password": password,
            "role_id": role_id,
            "status": data.get("status"),
            "customer_id": customer_id   # 🔥 LINK
        })

        role_name = vm.get_role_name(role_id)

        threading.Thread(
            target=ft.handle_user_create,
            args=(role_name,)
        ).start()

        return jsonify({
            "message": "Client user created",
            "user_id": user_id,
            "customer_id": customer_id
        })

    # 🔥 CASE 2: STAFF (etl/admin/approver)
    else:
        vm.insert("user_accounts", user_id, {
            "username": username,
            "password": password,
            "role_id": role_id,
            "status": data.get("status"),
            "customer_id": None
        })

        #role_name = vm.get_role_name(role_id)


        threading.Thread(
            target=ft.push_user_insights
        ).start()

        return jsonify({
            "message": "Staff user created",
            "user_id": user_id
        })

@app.route("/users", methods=["GET"])
def get_all_users():
    df = vm.get_df("user_accounts")
    return jsonify(df.reset_index().to_dict(orient="records"))


@app.route("/user/<user_id>", methods=["GET"])
def get_user(user_id):
    try:
        data = vm.get_one("user_accounts", user_id)
        return jsonify(data.to_dict())
    except:
        return jsonify({"error": "User not found"}), 404



@app.route("/user/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json or {}
    try:
        vm.update("user_accounts", user_id, data)
        threading.Thread(
            target=ft.push_user_insights
        ).start()
        return jsonify({"message": "User updated"})
    except:
        return jsonify({"error": "User not found"}), 404
    




@app.route("/user/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user = vm.get_one("user_accounts", user_id)

        print("USER DEBUG →", user)
        print("INDEX DEBUG →", user.index.tolist())

        # 🔥 SAFE ACCESS for pandas Series
        role_id = int(user.get("role_id"))
        role_name = vm.get_role_name(role_id)

        if role_id is None:
            raise Exception("role_id missing")

        vm.delete("user_accounts", user_id)
        
        ft.handle_user_delete(role_name)

        return jsonify({"message": "User deleted"})

    except Exception as e:
        print("DELETE ERROR →", e)
        return jsonify({"error": "User not found"}), 404

# =========================
# ROLE APIs
# =========================

@app.route("/role", methods=["POST"])
def create_role():
    data = request.json or {}
    role_id = data.get("role_id")

    vm.insert("roles", role_id, data)

    return jsonify({
        "role_id": role_id,
        "message": "Role created"
    })


@app.route("/roles", methods=["GET"])
def get_all_roles():
    df = vm.get_df("roles")
    return jsonify(df.reset_index().to_dict(orient="records"))


@app.route("/role/<int:role_id>", methods=["GET"])
def get_role(role_id):
    try:
        data = vm.get_one("roles", role_id)
        return jsonify(data.to_dict())
    except:
        return jsonify({"error": "Role not found"}), 404


@app.route("/role/<int:role_id>", methods=["PUT"])
def update_role(role_id):
    data = request.json or {}
    try:
        vm.update("roles", role_id, data)
        return jsonify({"message": "Role updated"})
    except:
        return jsonify({"error": "Role not found"}), 404


@app.route("/role/<int:role_id>", methods=["DELETE"])
def delete_role(role_id):
    vm.delete("roles", role_id)
    return jsonify({"message": "Role deleted"})


# =========================
# RBAC / AUTHENTICATION
# =========================
@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}

    identifier = data.get("identifier")   # 🔥 unified input
    password = data.get("password")

    if not identifier or not password:
        return jsonify({"error": "identifier and password required"}), 400

    try:
        user = vm.authenticate_user(identifier, password)

        return jsonify({
            "message": "Login successful",
            "user_id": user["user_id"],
            "role": user["role"],
            "customer_id": user["customer_id"]   # NULL for admin/etl
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 401
    

@app.route("/user/context/<identifier>", methods=["GET"])
def get_user_context(identifier):
    try:
        data = vm.get_user_context(identifier)
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/user/<user_id>/role", methods=["GET"])
def get_user_role(user_id):
    try:
        user = vm.get_user_with_role(user_id)

        return jsonify({
            "role": user["role"].lower
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 404

# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



    