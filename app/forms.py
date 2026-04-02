from decimal import Decimal, InvalidOperation

from .models import Employee, ExpenseType, ProductType
from .utils import parse_date


TRANSACTION_TYPES = {"received", "sent", "deposited"}


def _clean_text(value, max_length=255):
    cleaned = (value or "").strip()
    if len(cleaned) > max_length:
        raise ValueError(f"Must be {max_length} characters or fewer.")
    return cleaned


def _clean_amount(value, field_name="Amount"):
    raw = (value or "").strip()
    try:
        amount = Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a valid number.") from exc
    if amount <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return amount.quantize(Decimal("0.01"))


def validate_transaction_form(form):
    errors = {}
    cleaned = {}

    try:
        cleaned["date"] = parse_date(form.get("date"))
    except ValueError as exc:
        errors["date"] = str(exc)

    tx_type = _clean_text(form.get("type"), 20).lower()
    if tx_type not in TRANSACTION_TYPES:
        errors["type"] = "Select a valid transaction type."
    else:
        cleaned["type"] = tx_type

    try:
        cleaned["amount"] = _clean_amount(form.get("amount"))
    except ValueError as exc:
        errors["amount"] = str(exc)

    category = _clean_text(form.get("category"), 120)
    if not category:
        errors["category"] = "Category is required."
    else:
        cleaned["category"] = category

    note = _clean_text(form.get("note"), 2000)
    cleaned["note"] = note or None

    return cleaned, errors


def validate_expense_form(form):
    errors = {}
    cleaned = {}

    try:
        cleaned["date"] = parse_date(form.get("date"))
    except ValueError as exc:
        errors["date"] = str(exc)

    try:
        cleaned["amount"] = _clean_amount(form.get("amount"))
    except ValueError as exc:
        errors["amount"] = str(exc)

    is_salary = form.get("is_salary") == "true"
    cleaned["is_salary"] = is_salary
    cleaned["include_in_balance"] = form.get("include_in_balance", "true") != "false"

    expense_type_id = (form.get("expense_type_id") or "").strip()
    employee_id = (form.get("employee_id") or "").strip()
    employee = None

    if employee_id:
        employee = Employee.query.get(employee_id)
        if not employee:
            errors["employee_id"] = "Employee not found."

    if is_salary:
        if not employee_id:
            errors["employee_id"] = "Select an employee for salary records."
        else:
            cleaned["employee"] = employee
        cleaned["expense_type"] = None
    else:
        if not expense_type_id:
            errors["expense_type_id"] = "Select an expense type."
        else:
            expense_type = ExpenseType.query.get(expense_type_id)
            if not expense_type:
                errors["expense_type_id"] = "Expense type not found."
            else:
                cleaned["expense_type"] = expense_type
        cleaned["employee"] = employee

    note = _clean_text(form.get("note"), 2000)
    cleaned["note"] = note or None

    return cleaned, errors


def validate_sale_form(form):
    errors = {}
    cleaned = {}

    try:
        cleaned["date"] = parse_date(form.get("date"))
    except ValueError as exc:
        errors["date"] = str(exc)

    try:
        cleaned["amount"] = _clean_amount(form.get("amount"))
    except ValueError as exc:
        errors["amount"] = str(exc)

    product_type_id = (form.get("product_type_id") or "").strip()
    if not product_type_id:
        errors["product_type_id"] = "Select a product type."
    else:
        product_type = ProductType.query.get(product_type_id)
        if not product_type:
            errors["product_type_id"] = "Product type not found."
        else:
            cleaned["product_type"] = product_type

    quantity_raw = (form.get("quantity") or "").strip()
    if quantity_raw:
        try:
            cleaned["quantity"] = _clean_amount(quantity_raw, "Quantity")
        except ValueError as exc:
            errors["quantity"] = str(exc)
    else:
        cleaned["quantity"] = None

    note = _clean_text(form.get("note"), 2000)
    cleaned["note"] = note or None

    return cleaned, errors


def validate_named_entity_form(form, field_name="name"):
    errors = {}
    cleaned = {}

    name = _clean_text(form.get(field_name), 120)
    if not name:
        errors[field_name] = "Name is required."
    else:
        cleaned["name"] = name

    return cleaned, errors
