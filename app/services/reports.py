from ..models import Expense, Sale, Transaction
from ..utils import get_period_dates


def build_report_payload(period, start_str=None, end_str=None):
    start_date, end_date = get_period_dates(period, start_str, end_str)

    transactions = (
        Transaction.query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .all()
    )
    expenses = (
        Expense.query.filter(Expense.date >= start_date, Expense.date <= end_date)
        .order_by(Expense.date.desc(), Expense.id.desc())
        .all()
    )
    sales = (
        Sale.query.filter(Sale.date >= start_date, Sale.date <= end_date)
        .order_by(Sale.date.desc(), Sale.id.desc())
        .all()
    )

    totals = {
        "received": sum(item.amount for item in transactions if item.type == "received"),
        "sent": sum(item.amount for item in transactions if item.type == "sent"),
        "deposited": sum(item.amount for item in transactions if item.type == "deposited"),
        "expenses": sum(item.amount for item in expenses),
        "sales": sum(item.amount for item in sales),
    }
    totals["balance_change"] = totals["received"] + totals["sales"] - totals["sent"] - totals["deposited"] - totals["expenses"]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "transactions": transactions,
        "expenses": expenses,
        "sales": sales,
        "totals": totals,
    }
