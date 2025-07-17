from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.schema import Base, Category, Transaction
import datetime

# Set up DB connection
engine = create_engine('sqlite:///database/finsight.db')
Session = sessionmaker(bind=engine)
session = Session()

# Sample categories
categories = [
    Category(name="Salary", type="income"),
    Category(name="Freelance", type="income"),
    Category(name="Food", type="expense"),
    Category(name="Rent", type="expense"),
    Category(name="Entertainment", type="expense")
]

# Insert categories only if empty
if not session.query(Category).first():
    session.add_all(categories)
    session.commit()
    print("✅ Categories inserted.")

# Sample transactions
transactions = [
    Transaction(amount=50000, category_id=1, type="income", notes="Monthly salary"),
    Transaction(amount=7000, category_id=2, type="income", notes="Freelance gig"),
    Transaction(amount=1200, category_id=3, type="expense", notes="Zomato order"),
    Transaction(amount=15000, category_id=4, type="expense", notes="Flat rent"),
    Transaction(amount=900, category_id=5, type="expense", notes="Movie night")
]

# Insert transactions only if empty
if not session.query(Transaction).first():
    session.add_all(transactions)
    session.commit()
    print("✅ Transactions inserted.")

session.close()
