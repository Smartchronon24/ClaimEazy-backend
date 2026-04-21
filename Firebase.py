import ViewModel
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import pandas as pd
import time
import KEYS.KEYS as KEYS


class InsightGeneratorLogic(ViewModel.DataViewModel): 
    def __init__(self):
        super().__init__()
        print("Insight Generator initialized")

    def compute_claims_insights(self):
        df = self.get_df("claims_info")

        # 🔹 Total claims
        total = len(df)

        # 🔹 Count by status
        by_status = df["status"].value_counts().to_dict()

        # Ensure all keys exist (important for UI consistency)
        for key in ["Approved", "Pending", "Rejected"]:
            by_status.setdefault(key, 0)

        # 🔹 Total claimed amount (ONLY approved)
        approved_df = df[df["status"] == "Approved"]

        total_claimed_amt = approved_df["claim_amount"].sum()

        # Handle None / NaN
        total_claimed_amt = int(total_claimed_amt) if total_claimed_amt else 0

        return {
            "total": int(total),
            "by_status": by_status,
            "totalclaimed_amt": total_claimed_amt
        }
    
    def compute_payment_insights(self):
        df = self.get_df("payment_info")

        # 🔹 by_status count
        by_status = df["payment_status"].value_counts().to_dict()

        for key in ["Completed", "Pending", "Failed"]:
            by_status.setdefault(key, 0)

        # 🔹 payment_mode count
        payment_mode = df["payment_mode"].value_counts().to_dict()

        for key in ["UPI", "NetBanking", "Credit Card", "Debit Card", "Crypto", "Cash"]:
            payment_mode.setdefault(key, 0)

        # 🔹 total revenue (COMPLETED only)
        completed_df = df[df["payment_status"] == "Completed"]
        total_revenue = completed_df["payment_amount"].sum()

        # 🔹 pending amount
        pending_df = df[df["payment_status"] == "Pending"]
        pending_amount = pending_df["payment_amount"].sum()

        return {
            "total_revenue": int(total_revenue) if total_revenue else 0,
            "pending": int(pending_amount) if pending_amount else 0,
            "by_status": by_status,
            "payment_mode": payment_mode
        }

    def compute_policy_insights(self):
        df = self.get_df("policy_info")

        now = datetime.now()

        df["start_date"] = pd.to_datetime(df["start_date"])
        df["end_date"] = pd.to_datetime(df["end_date"])

        # 🔹 Active
        active_df = df[
            (df["start_date"] <= now) &
            (df["end_date"] >= now)
        ]

        # 🔹 Expired
        expired_df = df[df["end_date"] < now]

        # 🔹 Upcoming (NEW 🔥)
        upcoming_df = df[df["start_date"] > now]

        return {
            "active": int(len(active_df)),
            "expired": int(len(expired_df)),
            "upcoming": int(len(upcoming_df))
        }

    def compute_user_insights(self):
        users_df = self.get_df("user_accounts").reset_index()
        roles_df = self.get_df("roles").reset_index()

        # 🔹 Merge to get role_name
        merged_df = users_df.merge(
            roles_df,
            on="role_id",
            how="left"
        )

        # 🔹 Total users
        total = len(merged_df)

        # 🔹 Count by role_name
        by_role = merged_df["role_name"].value_counts().to_dict()

        # Ensure all roles exist
        for role in ["CLIENT", "ADMIN", "ETL", "APPROVER"]:
            by_role.setdefault(role, 0)

        return {
            "total": int(total),
            "by_role": by_role
        }

    def compute_customer_insights(self):
        df = self.get_df("customer_info")

        # 🔹 AGE GROUPING
        def get_age_group(age):
            if age is None:
                return None
            age = int(age)

            if 18 <= age < 30:
                return "18-30"
            elif 30 <= age < 40:
                return "30-40"
            elif 40 <= age < 50:
                return "40-50"
            elif 50 <= age < 60:
                return "50-60"
            elif age >= 60:
                return "60+"
            return None

        df["age_group"] = df["age"].apply(get_age_group)

        age_group_counts = df["age_group"].value_counts().to_dict()

        # ensure all buckets exist
        for key in ["18-30", "30-40", "40-50", "50-60", "60+"]:
            age_group_counts.setdefault(key, 0)

        # 🔹 ADDRESS GROUPING
        df["address"] = df["address"].astype(str).str.strip().str.upper()

        address_counts = df["address"].value_counts().to_dict()

        # ensure all states exist (your predefined list)
        states = [
            "ANDHRA PRADESH","ARUNACHAL PRADESH","ASSAM","BIHAR","CHHATTISGARH",
            "GOA","GUJARAT","HARYANA","HIMACHAL PRADESH","JHARKHAND",
            "KARNATAKA","KERALA","MADHYA PRADESH","MAHARASHTRA","MANIPUR",
            "MEGHALAYA","MIZORAM","NAGALAND","ODISHA","PUNJAB",
            "RAJASTHAN","SIKKIM","TAMIL NADU","TELANGANA","TRIPURA",
            "UTTAR PRADESH","UTTARAKHAND","WEST BENGAL"
        ]

        for state in states:
            address_counts.setdefault(state, 0)

        return {
            "age_group": age_group_counts,
            "address": address_counts
        }



class FireBaseTools(InsightGeneratorLogic):

    def __init__(self):
        super().__init__()
        print("FirebaseTools Initialized")

        cred = credentials.Certificate("ClaimEazy/KEYS/Firebase_admin_KEY.json")

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': KEYS.DATABASEURL
            })

        print("Firebase-Admin Initialized")

    # 🔥 atomic counter
    def update_counter(self, path, delta):
        ref = db.reference(path)

        def updater(current):
            return (current or 0) + delta

        ref.transaction(updater)


    # ==================
    # CLAIM
    # ================== 

    # 🔥 CREATE
    def handle_claim_create(self, status, claim_amount):
        self.update_counter("admin_insights/claims/total", +1)
        self.update_counter(f"admin_insights/claims/by_status/{status}", +1)

        if status == "APPROVED":
            self.update_counter("admin_insights/claims/totalclaimed_amt", claim_amount)

    # 🔥 DELETE
    def handle_claim_delete(self, status, claim_amount):
        self.update_counter("admin_insights/claims/total", -1)
        self.update_counter(f"admin_insights/claims/by_status/{status}", -1)

        if status == "APPROVED":
            self.update_counter("admin_insights/claims/totalclaimed_amt", -claim_amount)

    # 🔥 UPDATE (safe fallback)
    def handle_claim_update(self):
        self.push_claims_insights()

    # 🔥 FULL recompute
    def push_claims_insights(self):
        data = self.compute_claims_insights()

        db.reference().update({
            "admin_insights/claims": data
        })

    # ==================
    # PAYMENT
    # ==================

    def handle_payment_create(self, status, amount, mode):
        # 🔹 status count
        self.update_counter(f"admin_insights/payments/by_status/{status}", +1)

        # 🔹 mode count
        self.update_counter(f"admin_insights/payments/payment_mode/{mode}", +1)

        # 🔹 revenue
        if status == "Completed":
            self.update_counter("admin_insights/payments/total_revenue", amount)

        # 🔹 pending amount
        if status == "Pending":
            self.update_counter("admin_insights/payments/pending", amount)
    
    def handle_payment_delete(self, status, amount, mode):
        # 🛡️ Normalize inputs (VERY important)
        status = (status or "").strip()
        mode = (mode or "").strip()
        amount = float(amount or 0)

        # 🔹 status count
        self.update_counter(f"admin_insights/payments/by_status/{status}", -1)

        # 🔹 mode count
        self.update_counter(f"admin_insights/payments/payment_mode/{mode}", -1)

        # 🔹 revenue rollback
        if status.lower() == "completed":
            self.update_counter("admin_insights/payments/total_revenue", -amount)

        # 🔹 pending rollback
        elif status.lower() == "pending":
            self.update_counter("admin_insights/payments/pending", -amount)
    
    def push_payment_insights(self):
        data = self.compute_payment_insights()

        db.reference().update({
            "admin_insights/payments": data
        })


    # ==================
    # POLICY
    # ==================

    def push_policy_insights(self):
        try:
            data = self.compute_policy_insights()

            db.reference().update({
                "admin_insights/policies": data
            })

            print("POLICY PUSH SUCCESS ✅")

        except Exception as e:
            print("POLICY PUSH ERROR ❌", e)

    
    # ==================
    # USER
    # ==================

    def push_user_insights(self):
        data = self.compute_user_insights()

        db.reference().update({
            "admin_insights/users": data
        })

    def handle_user_create(self, role_name):
        self.update_counter("admin_insights/users/total", +1)
        self.update_counter(f"admin_insights/users/by_role/{role_name}", +1)

    def handle_user_delete(self, role_name):
        self.update_counter("admin_insights/users/total", -1)
        self.update_counter(f"admin_insights/users/by_role/{role_name}", -1)


    # ==================
    # CUSTOMER
    # ================== 

    def push_customer_insights(self):
        data = self.compute_customer_insights()

        db.reference().update({
            "admin_insights/customers": data
        })



def policy_sync_job():
    fb = FireBaseTools()   # ✅ only once

    while True:
        try:
            fb.push_policy_insights()
        except Exception as e:
            print("POLICY SYNC ERROR →", e)

        time.sleep(120)










# ==================
# ⬇️INITIAL-SETUP⬇️
# ==================



def push_some_stats(claim, pay):
    ref = db.reference()
    ref.update({
    "Insights/claims": claim,
    "Insights/payments": pay,
    "Insights/total": claim+pay
    })
    return "Updated!"

def push_all_stats():
    ref = db.reference()
    ref.update({
    "admin_insights": {
        "customers": {
            "age_group":{
                "18-30":12,
                "30-40":20,
                "40-50":26,
                "50-60":18,
                "60+":35
            },
            "address": {
                "ANDHRA PRADESH": 3,
                "ARUNACHAL PRADESH": 1,
                "ASSAM": 2,
                "BIHAR": 4,
                "CHHATTISGARH": 2,
                "GOA": 1,
                "GUJARAT": 3,
                "HARYANA": 2,
                "HIMACHAL PRADESH": 1,
                "JHARKHAND": 2,
                "KARNATAKA": 3,
                "KERALA": 2,
                "MADHYA PRADESH": 3,
                "MAHARASHTRA": 5,
                "MANIPUR": 1,
                "MEGHALAYA": 1,
                "MIZORAM": 0,
                "NAGALAND": 0,
                "ODISHA": 2,
                "PUNJAB": 2,
                "RAJASTHAN": 3,
                "SIKKIM": 0,
                "TAMIL NADU": 6,
                "TELANGANA": 3,
                "TRIPURA": 1,
                "UTTAR PRADESH": 5,
                "UTTARAKHAND": 1,
                "WEST BENGAL": 3
            }
        },
        "claims": {
            "total": 20,
            "by_status": {
                "Approved": 10,
                "Pending": 5,
                "Rejected": 4
            },
            "totalclaimed_amt": 115060
        },
        "payments": {
            "total_revenue": 1000000,
            "pending": 20000,
            "by_status": {
                "Completed":5,
                "Pending":3,
                "Failed":1
            },
            "payment_mode": {
                "UPI":10,
                "NetBanking":5,
                "Credit Card":2,
                "Debit Card":2,
                "Crypto":0,
                "Cash":3
            }
        },
        "policies": {
            "active": 50,
            "expired": 10,
            "upcoming":2
        },
        "users": {
            "total": 100,
            "by_role": {
                "CLIENT": 80,
                "ADMIN": 5,
                "ETL": 2,
                "APPROVER": 2
            }
        }
    },"KEY":""
    })
    print("Updated values")

'''def get_claim_stats():
    ref = db.reference("Insights/claims")
    return ref.get()

print(get_claim_stats())'''

#push_some_stats(13, 17)

#obj = FireBaseTools()
#push_all_stats()