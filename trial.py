# try_me.py (optional quick test)
from db.queries import add_transaction, list_transactions, get_transaction, update_transaction, delete_transaction, monthly_income_expense, category_breakdown

# Add a couple transactions
tx1 = add_transaction(type_="income",  category="Salary",    amount_dollars="2500.00", date_iso="2025-10-01", notes="Paycheck")
tx2 = add_transaction(type_="expense", category="Rent",      amount_dollars="1700.00", date_iso="2025-10-01", notes="October rent")
tx3 = add_transaction(type_="expense", category="Groceries", amount_dollars="120.45",  date_iso="2025-10-02")

print("Inserted IDs:", tx1, tx2, tx3)

# Read back
print("One tx:", get_transaction(tx2))
print("All recent:", list_transactions(limit=5))

# Update
update_transaction(tx3, notes="Trader Joe's + Costco")

# Analytics
print("Oct totals:", monthly_income_expense(user_id=1, year=2025, month=10))
print("Breakdown:", category_breakdown(1, "2025-10-01", "2025-10-31"))

# Delete one (try commenting this out if you want to keep data)
# delete_transaction(tx2)
