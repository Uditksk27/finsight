from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.schema import Category, Base

engine = create_engine("sqlite:///database/finsight.db")
Session = sessionmaker(bind=engine)
session = Session()

default_categories = {
    "Salary": "income",
    "Freelance": "income",
    "Food": "expense",
    "Travel": "expense",
    "Shopping": "expense",
    "Entertainment": "expense",
    "Health": "expense",
    "Utilities": "expense",
    "Groceries": "expense",
    "Bills": "expense",
    "Other": "expense"
}

for cat, cat_type in default_categories.items():
    exists = session.query(Category).filter_by(name=cat).first()
    if not exists:
        session.add(Category(name=cat, type=cat_type))

session.commit()
print("✅ Default categories added.")
