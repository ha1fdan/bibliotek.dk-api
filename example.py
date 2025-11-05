from bibliotekdk import BibliotekDK, AgencyHelper
import os
from dotenv import load_dotenv
load_dotenv()

agency_id=AgencyHelper().search("Odense Bibliotekerne", limit=1)[0]["agencyId"]

b = BibliotekDK(agency_id)

USER_ID = str(os.getenv("USER_ID"))
PINCODE = str(os.getenv("PINCODE"))
b.login(USER_ID, PINCODE)

user = b.get_user_info()
print("Name:", user["name"])
print("Email:", user["mail"])
print("Rights:", user["rights"])
print("Branches:", [x["name"] for x in user["agencies"][0]["result"]])

print("\n\n")

loans = b.get_loans()
reservations = b.get_reservations()

if not loans:
    print("No loans")
else:
    print("Loans:")
    for l in loans:
        print(f"{l['title']} - due {l['dueDate']}")

if not reservations:
    print("No reservations")
else:
    print("Reservations:")
    for r in reservations:
        print(f"{r['title']} @ {r['pickUpBranch']['agencyName']}")

print("\n\n")

renewed = b.renew_all()
print("Renewal results:")
for r in renewed:
    if r["renewed"]:
        print(f"Loan {r['loanId']} renewed successfully, new due date: {r['dueDate']}")
    else:
        print(f"Loan {r['loanId']} renewal failed: {r['error']}")