from decimal import Decimal

from sqlalchemy import func

from ..extensions import db
from ..models import Expense, Sale, Transaction


def _sum(query):
    return query.scalar() or Decimal("0.00")


def get_dashboard_totals():
    total_received = _sum(
        db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == "received")
    )
    total_sent = _sum(
        db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == "sent")
    )
    total_deposited = _sum(
        db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == "deposited")
    )
    total_expenses = _sum(db.session.query(func.sum(Expense.amount)))
    balance_expenses = _sum(
        db.session.query(func.sum(Expense.amount)).filter(Expense.include_in_balance.is_(True))
    )
    total_sales = _sum(
        db.session.query(func.sum(Sale.amount)).filter(Sale.include_in_totals.is_(True))
    )
    current_balance = (
        total_received + total_sales - total_sent - total_deposited - balance_expenses
    )

    return {
        "total_received": total_received,
        "total_sent": total_sent,
        "total_deposited": total_deposited,
        "total_expenses": total_expenses,
        "balance_expenses": balance_expenses,
        "total_sales": total_sales,
        "current_balance": current_balance,
    }
