import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import KEYS.KEYS as KEYS

class DataViewModel:
    def __init__(self, model=None):
        print("DataViewModel Initialized")

        self.engine = create_engine(
            KEYS.MYSQLENGINE
        )
        print("connected to MYSQL-DB")


    def generate_customer_id(self):
        df = self.get_df("customer_info")

        if df.empty:
            return "cust_001"

        ids = df.index.astype(str)

        last_id = (
            pd.Series(ids)
            .str.replace("cust_", "", regex=False)
            .astype(int)
            .max()
        )

        return f"cust_{last_id + 1:03d}"

    def generate_claim_id(self):
        df = self.get_df("claims_info")

        if df.empty:
            return "C2001"

        ids = df.index.astype(str)

        last_id = (
            pd.Series(ids)
            .str.replace("C", "", regex=False)
            .astype(int)
            .max()
        )

        return f"C{last_id + 1}"

    def generate_policy_id(self):
        df = self.get_df("policy_info")

        if df.empty:
            return "P1001"

        ids = df.index.astype(str)

        last_id = (
            pd.Series(ids)
            .str.replace("P", "", regex=False)
            .astype(int)
            .max()
        )

        return f"P{last_id + 1:03d}"


    def generate_payment_id(self):
        df = self.get_df("payment_info")

        if df.empty:
            return "PAY001"

        ids = df.index.astype(str)

        last_id = (
            pd.Series(ids)
            .str.replace("PAY", "", regex=False)
            .astype(int)
            .max()
        )

        return f"PAY{last_id + 1:03d}"


    def generate_user_id(self):
        df = self.get_df("user_accounts")

        if df.empty:
            return "USR001"

        ids = df.index.astype(str)

        last_id = (
            pd.Series(ids)
            .str.replace("USR", "", regex=False)
            .astype(int)
            .max()
        )

        return f"USR{last_id + 1:03d}"


    TABLE_CONFIG = {
        "customer_info": {
            "pk": "customer_id",
            "columns": ["name", "phone", "age", "address", "email"]
        },
        "claims_info": {
            "pk": "claim_id",
            "columns": ["policy_id", "claim_date", "hospital_id", "claim_amount", "status", "customer_id"]
        },
        "policy_info": {
            "pk": "policy_id",
            "columns": ["policy_type", "premium", "coverage_amount", "start_date", "end_date"]
        },
        "payment_info": {
            "pk": "Payment_ID",
            "columns": ["policy_id", "payment_amount", "payment_date", "payment_mode", "payment_status"]
        },
        "user_accounts": {
            "pk": "user_id",
            "columns": ["username", "password", "role_id", "status", "customer_id"]
        },
        "roles": {
            "pk": "role_id",
            "columns": ["role_name", "description"]
        }
    }


    # =========================
    # INTERNAL HELPERS
    # =========================


    def _process_special_fields(self, data):
        processed = {}

        for key, val in data.items():
            if key == "claims" and isinstance(val, list):
                processed[key] = ",".join(val)

            elif key == "payment_date" and isinstance(val, str):
                try:
                    dt = datetime.strptime(val, "%a, %d %b %Y %H:%M:%S %Z")
                    processed[key] = dt.strftime("%Y-%m-%d")
                except:
                    processed[key] = val  # fallback (not ideal)

            else:
                processed[key] = val

        return processed

    def _postprocess_df(self, df):
        """Convert DB fields back to usable format"""
        if "claims" in df.columns:
            df["claims"] = df["claims"].apply(
                lambda x: x.split(",") if isinstance(x, str) and x else []
            )
        return df


    def get_user_with_role(self, user_id):
        query = """
            SELECT u.user_id, u.customer_id, r.role_name
            FROM user_accounts u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
        """

        df = pd.read_sql(query, self.engine, params=(user_id,))

        if df.empty:
            raise Exception("User not found")

        user = df.iloc[0]

        return {
            "user_id": user["user_id"],
            "customer_id": user["customer_id"],
            "role": user["role_name"]
        }
    
    def get_role_name(self, role_id):
        role = self.get_one("roles", role_id)
        return role["role_name"]

    # =========================
    # CREATE
    # =========================
    def insert(self, table, record_id, data):
        config = self.TABLE_CONFIG[table]
        pk = config["pk"]
        cols = config["columns"]

        query = text(f"""
            INSERT INTO {table}
            ({pk}, {", ".join(cols)})
            VALUES (:{pk}, {", ".join([f":{c}" for c in cols])})
        """)

        data = self._process_special_fields(data)

        params = {pk: record_id}

        for col in cols:
            val = data.get(col) if data else None

            # default for user status
            if table == "user_accounts" and col == "status":
                val = val if val is not None else "ACTIVE"

            params[col] = val

        print("INSERT DEBUG →", params)

        with self.engine.connect() as conn:
            conn.execute(query, params)
            conn.commit()

    # =========================
    # READ (ALL → DataFrame)
    # =========================
    def get_df(self, table):
        config = self.TABLE_CONFIG[table]
        pk = config["pk"]

        df = pd.read_sql(f"SELECT * FROM {table}", self.engine)
        df = self._postprocess_df(df)

        df = df.where(pd.notnull(df), None)   # 🔥 FIX

        df.set_index(pk, inplace=True)
        return df

    # =========================
    # READ (SINGLE)
    # =========================
    def get_one(self, table, record_id):
        config = self.TABLE_CONFIG[table]
        pk = config["pk"]

        df = pd.read_sql(
            f"SELECT * FROM {table} WHERE {pk} = %s",
            self.engine,
            params=(record_id,)
        )

        if df.empty:
            raise Exception(f"{table} record not found")

        df = self._postprocess_df(df)
        return df.iloc[0]

    # =========================
    # UPDATE
    # =========================
    def update(self, table, record_id, data):
        config = self.TABLE_CONFIG[table]
        pk = config["pk"]
        cols = config["columns"]

        # 🔥 STEP 1: Fix date formats
        for key in data:
            if "date" in key and data[key]:
                try:
                    # Convert "Tue, 08 Apr 2025 00:00:00 GMT"
                    parsed_date = datetime.strptime(
                        data[key], "%a, %d %b %Y %H:%M:%S GMT"
                    )
                    data[key] = parsed_date.strftime("%Y-%m-%d")
                except:
                    pass  # already correct format

        # 🔥 STEP 2: Normal processing
        data = self._process_special_fields(data)

        set_clause = ", ".join([f"{col}=:{col}" for col in cols])

        query = text(f"""
            UPDATE {table}
            SET {set_clause}
            WHERE {pk}=:id
        """)

        params = {"id": record_id}

        for col in cols:
            params[col] = data.get(col)

        with self.engine.connect() as conn:
            result = conn.execute(query, params)
            conn.commit()

            # 🔥 DEBUG PRINT (!VERY IMPORTANT)
            print("UPDATE DEBUG →", record_id, params)

            if result.rowcount == 0:
                raise Exception(f"{table} record not found")

    # =========================
    # DELETE
    # =========================
    
    def delete(self, table, record_id):
        config = self.TABLE_CONFIG[table]
        pk = config["pk"]

        with self.engine.begin() as conn:

            # =========================
            # 🔥 SPECIAL CASE: USER
            # =========================
            if table == "user_accounts":

                # Step 1: Fetch customer_id
                result = conn.execute(
                    text(f"SELECT customer_id FROM {table} WHERE {pk} = :id"),
                    {"id": record_id}
                ).fetchone()

                # ❌ If user not found → THROW ERROR
                if not result:
                    raise Exception(f"{table} record not found")

                customer_id = result[0]

                # Step 2: Delete user
                user_delete = conn.execute(
                    text(f"DELETE FROM {table} WHERE {pk} = :id"),
                    {"id": record_id}
                )

                # Step 3: Delete customer (if exists)
                if customer_id:
                    conn.execute(
                        text("DELETE FROM customer_info WHERE customer_id = :cid"),
                        {"cid": customer_id}
                    )

                print("DELETE DEBUG (USER) →", record_id, customer_id)

            # =========================
            # 🔥 GENERIC DELETE
            # =========================
            else:
                result = conn.execute(
                    text(f"DELETE FROM {table} WHERE {pk} = :id"),
                    {"id": record_id}
                )

                # ❌ If nothing deleted → THROW ERROR
                if result.rowcount == 0:
                    raise Exception(f"{table} record not found")

                print("DELETE DEBUG →", table, record_id)


    # =========================
    # CSV EXPORT
    # =========================
    def export_csv(self):
        self.get_df("customer_info").to_csv("customer_info.csv")
        self.get_df("claims_info").to_csv("claims_info.csv")
        self.get_df("policy_info").to_csv("policy_info.csv")
        self.get_df("payment_info").to_csv("payment_info.csv")
        self.get_df("user_accounts").to_csv("user_accounts.csv")
        self.get_df("roles").to_csv("roles_info.csv")
        print("CSV Exported ✅")

    # =========================
    # SYNC
    # =========================
    def sync_customers_from_model(self, model):
        db_df = self.get_df("customer_info")

        for customer_id, data in model.customer_info.items():
            if customer_id in db_df.index:
                self.update("customer_info", customer_id, data)
                print(f"{customer_id} updated 🔄")
            else:
                self.insert("customer_info", customer_id, data)
                print(f"{customer_id} inserted ➕")

    def sync_claims_from_model(self, model):
        db_df = self.get_df("claims_info")

        for claim_id, data in model.claim_details.items():
            if claim_id in db_df.index:
                self.update("claims_info", claim_id, data)
            else:
                self.insert("claims_info", claim_id, data)

    def sync_policies_from_model(self, model):
        db_df = self.get_df("policy_info")

        for policy_id, data in model.policy_details.items():
            if policy_id in db_df.index:
                self.update("policy_info", policy_id, data)
            else:
                self.insert("policy_info", policy_id, data)

    
    def sync_payments_from_model(self, model):
        db_df = self.get_df("payment_info")

        for payment_id, data in model.payment_details.items():
            if payment_id in db_df.index:
                self.update("payment_info", payment_id, data)
            else:
                self.insert("payment_info", payment_id, data)

    def sync_user_from_model(self, model):
        db_df = self.get_df("user_accounts")

        for user_id, data in model.user_details.items():
            if user_id in db_df.index:
                self.update("user_accounts", user_id, data)
            else:
                self.insert("user_accounts", user_id, data)
    
    def sync_role_from_model(self, model):
        db_df = self.get_df("roles")

        for role_id, data in model.role_details.items():
            if role_id in db_df.index:
                self.update("roles", role_id, data)
            else:
                self.insert("roles", role_id, data)


    # =========================
    # RBAC
    # =========================
    def get_user_role(self, user_id):
        query = """
            SELECT r.role_name
            FROM user_accounts u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
        """
        df = pd.read_sql(query, self.engine, params=(user_id,))

        if df.empty:
            raise Exception("User not found")

        return df.iloc[0]["role_name"]

    
    def authenticate_user(self, identifier, password):
        query = """
            SELECT u.user_id, u.password, u.customer_id, r.role_name
            FROM user_accounts u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.customer_id = %s OR u.user_id = %s
        """

        df = pd.read_sql(query, self.engine, params=(identifier, identifier))

        if df.empty:
            raise Exception("User not found")

        user = df.iloc[0]

        # 🔥 Password check
        if user["password"] != password:
            raise Exception("Invalid password")

        return {
            "user_id": user["user_id"],
            "role": user["role_name"],
            "customer_id": user["customer_id"]  # can be None for admin/etl
        }


    def get_user_context(self, identifier):
        query = """
            SELECT u.user_id, u.customer_id, r.role_name
            FROM user_accounts u
            LEFT JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s OR u.customer_id = %s
        """

        df = pd.read_sql(query, self.engine, params=(identifier, identifier))

        if df.empty:
            raise Exception("User not found")

        user = df.iloc[0]

        user_id = user["user_id"]
        customer_id = user["customer_id"]
        role = user["role_name"]

        # 🔥 CASE 1: Input was user_id → return customer_id or role
        if identifier == user_id:
            if pd.notnull(customer_id):
                return {
                    "type": "client",
                    "user_id": user_id,
                    "customer_id": customer_id
                }
            else:
                return {
                    "type": "staff",
                    "user_id": user_id,
                    "role": role
                }

        # 🔥 CASE 2: Input was customer_id → return user_id
        elif identifier == customer_id:
            return {
                "type": "reverse_lookup",
                "customer_id": customer_id,
                "user_id": user_id,
                "role": role
            }

        # fallback (shouldn't hit ideally)
        else:
            raise Exception("Invalid identifier")

    # =========================
    # Claims Helpers
    # =========================

    def get_unassigned_claims(self):
        query = text("""
            SELECT * FROM claims_info
            WHERE customer_id IS NULL
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    
    def assign_claim(self, claim_id, customer_id):
        query = text("""
            UPDATE claims_info
            SET customer_id = :customer_id
            WHERE claim_id = :claim_id
            AND customer_id IS NULL
        """)

        with self.engine.begin() as conn:
            result = conn.execute(query, {
                "claim_id": claim_id,
                "customer_id": customer_id
            })

            if result.rowcount == 0:
                raise Exception("Claim not found or already assigned")


    def deassign_claim(self, claim_id):
        query = text("""
            UPDATE claims_info
            SET customer_id = NULL
            WHERE claim_id = :claim_id
            AND customer_id IS NOT NULL
        """)

        with self.engine.begin() as conn:
            result = conn.execute(query, {"claim_id": claim_id})

            if result.rowcount == 0:
                raise Exception("Claim not found or already unassigned")


    def get_claims_by_customer(self, customer_id):
        query = text("""
            SELECT claim_id FROM claims_info
            WHERE customer_id = :customer_id
        """)

        with self.engine.connect() as conn:
            result = conn.execute(query, {"customer_id": customer_id})
            return [row[0] for row in result]







# =====================
# ⬇️⬇️BACKENDTEST⬇️⬇️
# =====================


class Input_Handler:
    def __init__():
        print("Input Handler Initialized")

    def input_customer(self):
        name = input("Name: ")
        phone = int(input("Phone: "))
        age = int(input("Age: "))
        address = input("address: ")
        email = input("Email: ")
        claims = input("Claims (comma separated): ").split(",")

        return {
            "name": name,
            "phone": phone,
            "age": age,
            "address": address,
            "email": email,
            "claims": claims if claims != [''] else []
        }


    def input_claim(self):
        policy_id = input("Policy ID: ")
        claim_date = input("Claim Date (YYYY-MM-DD): ")
        hospital_id = input("Hospital ID: ")
        claim_amount = int(input("Claim Amount: "))
        status = input("Status: ")

        return {
            "policy_id": policy_id,
            "claim_date": claim_date,
            "hospital_id": hospital_id,
            "claim_amount": claim_amount,
            "status": status
        }
    
