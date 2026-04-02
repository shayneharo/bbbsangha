import io

from ..utils import build_csv

try:
    from openpyxl import Workbook
except ModuleNotFoundError:
    Workbook = None


def transactions_to_csv(transactions):
    rows = [
        [
            transaction.id,
            transaction.date.isoformat(),
            transaction.type,
            f"{transaction.amount:.2f}",
            transaction.category,
            transaction.note or "",
            transaction.receipt_filename or "",
        ]
        for transaction in transactions
    ]
    return build_csv(
        rows,
        ["ID", "Date", "Type", "Amount", "Category", "Note", "Receipt Filename"],
    )


def transactions_to_excel(transactions):
    if Workbook is None:
        raise RuntimeError("Excel export requires the 'openpyxl' package to be installed.")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Transactions"
    sheet.append(["ID", "Date", "Type", "Amount", "Category", "Note", "Receipt Filename"])

    for transaction in transactions:
        sheet.append(
            [
                transaction.id,
                transaction.date.isoformat(),
                transaction.type,
                float(transaction.amount),
                transaction.category,
                transaction.note or "",
                transaction.receipt_filename or "",
            ]
        )

    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)
    return output.getvalue()
