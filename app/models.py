from datetime import datetime

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Transaction(TimestampMixin, db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    category = db.Column(db.String(120), nullable=False, index=True)
    note = db.Column(db.Text, nullable=True)
    receipt_filename = db.Column(db.String(255), nullable=True)


class Employee(TimestampMixin, db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    expenses = db.relationship("Expense", back_populates="employee")


class ExpenseType(TimestampMixin, db.Model):
    __tablename__ = "expense_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    expenses = db.relationship("Expense", back_populates="expense_type")


class Expense(TimestampMixin, db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    note = db.Column(db.Text, nullable=True)
    receipt_filename = db.Column(db.String(255), nullable=True)
    is_salary = db.Column(db.Boolean, nullable=False, default=False)
    include_in_balance = db.Column(db.Boolean, nullable=False, default=True)
    expense_type_id = db.Column(db.Integer, db.ForeignKey("expense_types.id"), nullable=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)

    expense_type = db.relationship("ExpenseType", back_populates="expenses")
    employee = db.relationship("Employee", back_populates="expenses")


class ProductType(TimestampMixin, db.Model):
    __tablename__ = "product_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    sales = db.relationship("Sale", back_populates="product_type")


class Sale(TimestampMixin, db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=True)
    note = db.Column(db.Text, nullable=True)
    receipt_filename = db.Column(db.String(255), nullable=True)
    product_type_id = db.Column(db.Integer, db.ForeignKey("product_types.id"), nullable=False)

    product_type = db.relationship("ProductType", back_populates="sales")
