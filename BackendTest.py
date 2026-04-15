from DataModel import DataModel
from ViewModel import DataViewModel, Input_Handler

model = DataModel()
vm = DataViewModel(model)
handler = Input_Handler()


while True:
    choice = input("\nCRUD? (C/R/U/D/SYNC/EXIT): ").upper().strip()

    # CREATE
    if choice == "C":
        sub = input("Create (1:Customer, 2:Claim): ")

        if sub == "1":
            data = handler.input_customer()   # no cust_id anymore
            cust_id = vm.generate_customer_id()

            vm.add_customer(cust_id, data)

            print(f"Customer Added with ID: {cust_id} 🔥")

        elif sub == "2":
            data = handler.input_claim()
            claim_id = vm.generate_claim_id()

            vm.add_claim(claim_id, data)

            print(f"Claim Added with ID: {claim_id} 🔥")
            print("Claim Added 🔥")

    # READ
    elif choice == "R":
        sub = input("Read (1:Customer, 2:Claim): ")

        if sub == "1":
            cust_id = input("Enter Cust ID: ")
            try:
                print(vm.get_customer(cust_id))
            except:
                print("Invalid Customer ID")

        elif sub == "2":
            claim_id = input("Enter Claim ID: ")
            try:
                print(vm.get_claim(claim_id))
            except:
                print("Invalid Claim ID")

    # UPDATE
    elif choice == "U":
        sub = input("Update (1:Customer, 2:Claim): ")

        if sub == "1":
            cust_id = input("Enter Cust ID to update: ")
            try:
                vm.get_customer(cust_id)
                new_data = handler.input_customer()
                vm.update_customer(cust_id, new_data)
                print("Customer Updated ✅")
            except:
                print("Customer not found")

        elif sub == "2":
            claim_id = input("Enter Claim ID to update: ")
            try:
                vm.get_claim(claim_id)
                new_data = handler.input_claim()
                vm.update_claim(claim_id, new_data)
                print("Claim Updated ✅")
            except:
                print("Claim not found")

    # DELETE
    elif choice == "D":
        sub = input("Delete (1:Customer, 2:Claim): ")

        if sub == "1":
            cust_id = input("Enter Cust ID to delete: ")
            vm.remove_customer(cust_id)
            print("Customer Deleted 🗑️")

        elif sub == "2":
            claim_id = input("Enter Claim ID to delete: ")
            vm.remove_claim(claim_id)
            print("Claim Deleted 🗑️")

    #SYNC
    elif choice == "SYNC":
        vm.sync_customers_from_model(model)
        vm.sync_claims_from_model(model)
        vm.sync_policies_from_model(model)
        vm.sync_payments_from_model(model)
        print("Full DataModel synced with DB ✅🔥")

    # EXIT
    elif choice == "EXIT":
        print("Exited!")
        break

    else:
        print("Invalid option")