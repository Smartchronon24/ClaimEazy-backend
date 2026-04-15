class DataModel:
    def __init__(self):
        print("Model Initialized")

        self._customer_info = {
            "cust_001": {
                'name': "Bejoy",
                "phone": 2351572112,
                'age': 32,
                'location': "chennai"
            },
            "cust_002": {
                'name': "Amar",
                "phone": 8351083712,
                'age': 45,
                'location': "pune"
            },
            "cust_003": {
                'name': "Sandhanam",
                "phone": 676702831,
                'age': 29,
                'location': "bangalore"
            },
            "cust_004": {
                'name': "Agent Lawrence",
                "phone": 1259826791,
                'age': 38,
                'location': "mumbai"
            },
            "cust_005": {
                'name': "Agent Tina",
                "phone": 2356931328,
                'age': 26,
                'location': "hyderabad"
            },
            "cust_006": {
                'name': "Vikram",
                'phone' : 7492100905,
                'age': 48,
                'location': "Chennai"
            },
            "cust_007" : {
                'name': "Rolex",
                'phone' : 6677633212,
                'age': 37,
                'location': "Mumbai"
            }
        }

        self._claim_details = {
            "C2001": {
                'policy_id': "P1001",
                'claim_date': "2025-02-10",
                'incident_type': "hospitalization",
                'claim_amt': 11000,
                'status': "Approved",
                'Cust_id': ""
            },
            "C2002": {
                'policy_id': "P1002",
                'claim_date': "2025-02-18",
                'incident_type': "surgery",
                'claim_amt': 23400,
                'status': "Pending",
                'Cust_id': ""
            },
            "C2003": {
                'policy_id': "P1003",
                'claim_date': "2025-03-01",
                'incident_type': "accident",
                'claim_amt': 18000,
                'status': "Rejected",
                'Cust_id': ""
            },
            "C2004": {
                'policy_id': "P1004",
                'claim_date': "2025-03-05",
                'incident_type': "fire damage",
                'claim_amt': 55000,
                'status': "Approved",
                'Cust_id': ""
            },
            "C2005": {
                'policy_id': "P1005",
                'claim_date': "2025-03-08",
                'incident_type': "checkup",
                'claim_amt': 9500,
                'status': "Pending",
                'Cust_id': ""
            },
            "C2006": {
                'policy_id': "P1001",
                'claim_date': "2025-03-15",
                'incident_type': "treatment",
                'claim_amt': 6000,
                'status': "Approved",
                'Cust_id': ""
            },
            "C2007": {
                'policy_id': "P1002",
                'claim_date': "2025-03-20",
                'incident_type': "diagnostics",
                'claim_amt': 8000,
                'status': "Rejected",
                'Cust_id': ""
            },
            "C2008": {
                'policy_id': "P1003",
                'claim_date': "2025-03-22",
                'incident_type': "vehicle repair",
                'claim_amt': 12000,
                'status': "Approved",
                'Cust_id': ""
            },
            "C2009": {
                'policy_id': "P1004",
                'claim_date': "2025-03-25",
                'incident_type': "property damage",
                'claim_amt': 30000,
                'status': "Pending",
                'Cust_id': ""
            },
            "C2010": {
                'policy_id': "P1005",
                'claim_date': "2025-03-27",
                'incident_type': "lab tests",
                'claim_amt': 4000,
                'status': "Approved",
                'Cust_id': ""
            },
            "C2011": {
                'policy_id': "P1003",
                'claim_date': "2025-03-28",
                'incident_type': "accident",
                'claim_amt': 7000,
                'status': "Pending",
                'Cust_id': ""
            },
            "C2012": {
                'policy_id': "P1002",
                'claim_date': "2025-03-29",
                'incident_type': "emergency care",
                'claim_amt': 15000,
                'status': "Approved",
                'Cust_id': ""
            },
            "C2013": {
                'policy_id': "P1001",
                'claim_date': "2025-02-10",
                'incident_type': "hospitalization",
                'claim_amt': 11000,
                'status': "Approved",
                'Cust_id': ""
            }
        }
        
        self._policy_details = {
            "P1001": {
                "policy_type": "Health Insurance",
                "premium_amount": 12000,
                "coverage_amount": 200000,
                "start_date": "2024-01-01",
                "end_date": "2026-01-01"
            },
            "P1002": {
                "policy_type": "Surgical Cover",
                "premium_amount": 15000,
                "coverage_amount": 300000,
                "start_date": "2024-06-15",
                "end_date": "2026-06-15"
            },
            "P1003": {
                "policy_type": "Accident Insurance",
                "premium_amount": 10000,
                "coverage_amount": 250000,
                "start_date": "2025-01-01",
                "end_date": "2027-01-01"
            },
            "P1004": {
                "policy_type": "Property Insurance",
                "premium_amount": 20000,
                "coverage_amount": 500000,
                "start_date": "2023-09-01",
                "end_date": "2026-09-01"
            },
            "P1005": {
                "policy_type": "General Health",
                "premium_amount": 8000,
                "coverage_amount": 150000,
                "start_date": "2025-03-01",
                "end_date": "2027-03-01"
            }
        }
        
        
        self._payment_details = {
            "PAY001": {
                "policy_id": "P1001",
                "payment_amount": 12000,
                "payment_date": "2025-01-01",
                "payment_mode": "UPI",
                "payment_status": "Completed"
            },
            "PAY002": {
                "policy_id": "P1002",
                "payment_amount": 15000,
                "payment_date": "2025-02-10",
                "payment_mode": "Credit Card",
                "payment_status": "Completed"
            },
            "PAY003": {
                "policy_id": "P1003",
                "payment_amount": 10000,
                "payment_date": "2025-03-05",
                "payment_mode": "Net Banking",
                "payment_status": "Completed"
            },
            "PAY004": {
                "policy_id": "P1004",
                "payment_amount": 20000,
                "payment_date": "2025-03-10",
                "payment_mode": "Debit Card",
                "payment_status": "Pending"
            },
            "PAY005": {
                "policy_id": "P1005",
                "payment_amount": 8000,
                "payment_date": "2025-03-20",
                "payment_mode": "UPI",
                "payment_status": "Completed"
            }
        }

        self._user_details = {
            "USR001": {"username": "Bejoy", "password": "1234", "role_id": 1, "status": "ACTIVE"},
            "USR002": {"username": "Amar", "password": "1234", "role_id": 1, "status": "ACTIVE"},
            "USR003": {"username": "Sandhanam", "password": "1234", "role_id": 1, "status": "ACTIVE"},
            "USR004": {"username": "Vikram", "password": "1234", "role_id": 1, "status": "ACTIVE"},
            "USR005": {"username": "Rolex", "password": "1234", "role_id": 1, "status": "ACTIVE"},
            "USR006": {"username": "Agent Lawrence", "password": "1234", "role_id": 2, "status": "ACTIVE"},
            "USR007": {"username": "Agent Tina", "password": "1234", "role_id": 2, "status": "ACTIVE"},
            "USR008": {"username": "Parthipan", "password": "1234", "role_id": 3, "status": "ACTIVE"},
            "USR009": {"username": "Dilli", "password": "1234", "role_id": 4, "status": "ACTIVE"},
            "USR010": {"username": "Adaikalam", "password": "1234", "role_id": 4, "status": "ACTIVE"}
        }

        self._role_details = {
            1: {
                "role_name": "CLIENT",
                "description": "Can Create claims and update claims that they created"
            },
            2: {
                "role_name": "APPROVER",
                "description": "Can approve or reject claims"
            },
            3: {
                "role_name": "ADMIN",
                "description": "Full system access"
            },
            4: {
                "role_name": "ETL",
                "description": "Can update and post Insights on Existing data"
            }
        }

    # expose safely
    @property
    def customer_info(self):
        return self._customer_info

    @property
    def claim_details(self):
        return self._claim_details
    
    @property
    def policy_details(self):
        return self._policy_details

    @property
    def payment_details(self):
        return self._payment_details
    
    @property
    def user_details(self):
        return self._user_details
    
    @property
    def role_details(self):
        return self._role_details