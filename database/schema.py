from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    transactions = relationship("Transaction", back_populates="user")
    budgets = relationship("Budget", back_populates="user")


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'income' or 'expense'
    transactions = relationship('Transaction', back_populates='category')

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="transactions")
    category_id = Column(Integer, ForeignKey('categories.id'))
    type = Column(String, nullable=False)  # 'income' or 'expense'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text)

    category = relationship('Category', back_populates='transactions')

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="budgets")
    year = Column(Integer)
    month = Column(Integer)
    amount = Column(Float)

    category = relationship("Category")

# Create SQLite DB and tables
if __name__ == '__main__':
    engine = create_engine('sqlite:///database/finsight.db')
    Base.metadata.create_all(engine)
    print("Database and tables created successfully.")
