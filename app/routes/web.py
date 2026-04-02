import io

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from sqlalchemy import func, or_

from ..extensions import db
from ..forms import (
    TRANSACTION_TYPES,
    validate_expense_form,
    validate_named_entity_form,
    validate_sale_form,
    validate_transaction_form,
)
from ..models import Employee, Expense, ExpenseType, ProductType, Sale, Transaction
from ..services.dashboard import get_dashboard_totals
from ..services.exports import transactions_to_csv, transactions_to_excel
from ..services.reports import build_report_payload
from ..utils import default_date, delete_uploaded_file, save_uploaded_file, serve_uploaded_file


web = Blueprint("web", __name__)


def _apply_transaction_filters():
    query = Transaction.query
    search = (request.args.get("search") or "").strip()
    tx_type = (request.args.get("type") or "").strip().lower()
    start_date = (request.args.get("start_date") or "").strip()
    end_date = (request.args.get("end_date") or "").strip()

    if search:
        like = f"%{search}%"
        query = query.filter(or_(Transaction.category.ilike(like), Transaction.note.ilike(like)))
    if tx_type in TRANSACTION_TYPES:
        query = query.filter(Transaction.type == tx_type)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    return query.order_by(Transaction.date.desc(), Transaction.id.desc())


def _apply_expense_filters():
    query = Expense.query.outerjoin(Expense.employee).outerjoin(Expense.expense_type)
    search = (request.args.get("search") or "").strip()
    mode = (request.args.get("mode") or "").strip()
    start_date = (request.args.get("start_date") or "").strip()
    end_date = (request.args.get("end_date") or "").strip()

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Expense.note.ilike(like),
                Employee.name.ilike(like),
                ExpenseType.name.ilike(like),
            )
        )
    if mode == "salary":
        query = query.filter(Expense.is_salary.is_(True))
    elif mode == "expense":
        query = query.filter(Expense.is_salary.is_(False))
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    return query.order_by(Expense.date.desc(), Expense.id.desc())


def _apply_sale_filters():
    query = Sale.query.join(Sale.product_type)
    search = (request.args.get("search") or "").strip()
    start_date = (request.args.get("start_date") or "").strip()
    end_date = (request.args.get("end_date") or "").strip()

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(Sale.note.ilike(like), Sale.sold_to.ilike(like), ProductType.name.ilike(like))
        )
    if start_date:
        query = query.filter(Sale.date >= start_date)
    if end_date:
        query = query.filter(Sale.date <= end_date)

    return query.order_by(Sale.date.desc(), Sale.id.desc())


def _handle_receipt_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    return save_uploaded_file(file_storage)


@web.app_template_filter("currency")
def currency_filter(value):
    return f"₱{float(value or 0):,.2f}"


@web.route("/")
def dashboard():
    recent_transactions = Transaction.query.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(5).all()
    recent_expenses = Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).limit(5).all()
    recent_sales = Sale.query.order_by(Sale.date.desc(), Sale.id.desc()).limit(5).all()
    return render_template(
        "dashboard.html",
        totals=get_dashboard_totals(),
        recent_transactions=recent_transactions,
        recent_expenses=recent_expenses,
        recent_sales=recent_sales,
    )


@web.route("/transactions")
def transactions():
    items = _apply_transaction_filters().all()
    return render_template("transactions.html", transactions=items, filters=request.args, transaction_types=sorted(TRANSACTION_TYPES))


@web.route("/transactions/new", methods=["GET", "POST"])
def create_transaction():
    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_transaction_form(request.form)
        if not errors:
            try:
                receipt_filename = _handle_receipt_upload(request.files.get("receipt"))
                transaction = Transaction(receipt_filename=receipt_filename, **cleaned)
                db.session.add(transaction)
                db.session.commit()
                flash("Transaction created successfully.", "success")
                return redirect(url_for("web.transactions"))
            except ValueError as exc:
                errors["receipt"] = str(exc)
    return render_template(
        "transaction_form.html",
        action="Create",
        transaction=None,
        errors=errors,
        form_data=request.form,
        default_date=default_date(),
        transaction_types=sorted(TRANSACTION_TYPES),
    )


@web.route("/transactions/<int:transaction_id>")
def transaction_detail(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    return render_template("transaction_detail.html", transaction=transaction)


@web.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_transaction_form(request.form)
        if not errors:
            try:
                new_receipt = request.files.get("receipt")
                if new_receipt and new_receipt.filename:
                    old_receipt = transaction.receipt_filename
                    transaction.receipt_filename = _handle_receipt_upload(new_receipt)
                    delete_uploaded_file(old_receipt)
                transaction.date = cleaned["date"]
                transaction.type = cleaned["type"]
                transaction.amount = cleaned["amount"]
                transaction.category = cleaned["category"]
                transaction.note = cleaned["note"]
                db.session.commit()
                flash("Transaction updated successfully.", "success")
                return redirect(url_for("web.transaction_detail", transaction_id=transaction.id))
            except ValueError as exc:
                errors["receipt"] = str(exc)
    return render_template(
        "transaction_form.html",
        action="Edit",
        transaction=transaction,
        errors=errors,
        form_data=request.form,
        default_date=default_date(),
        transaction_types=sorted(TRANSACTION_TYPES),
    )


@web.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    delete_uploaded_file(transaction.receipt_filename)
    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted.", "success")
    return redirect(url_for("web.transactions"))


@web.route("/expenses")
def expenses():
    items = _apply_expense_filters().all()
    expense_types = ExpenseType.query.order_by(ExpenseType.name.asc()).all()
    employees = Employee.query.order_by(Employee.name.asc()).all()
    return render_template(
        "expenses.html",
        expenses=items,
        filters=request.args,
        expense_types=expense_types,
        employees=employees,
    )


@web.route("/expenses/new", methods=["GET", "POST"])
def create_expense():
    errors = {}
    expense_types = ExpenseType.query.order_by(ExpenseType.name.asc()).all()
    employees = Employee.query.order_by(Employee.name.asc()).all()
    if request.method == "POST":
        cleaned, errors = validate_expense_form(request.form)
        if not errors:
            try:
                expense = Expense(
                    date=cleaned["date"],
                    amount=cleaned["amount"],
                    note=cleaned["note"],
                    receipt_filename=_handle_receipt_upload(request.files.get("receipt")),
                    is_salary=cleaned["is_salary"],
                    include_in_balance=cleaned["include_in_balance"],
                    unit_type=cleaned["unit_type"],
                    unit_quantity=cleaned["unit_quantity"],
                    employee=cleaned["employee"],
                    expense_type=cleaned["expense_type"],
                )
                db.session.add(expense)
                db.session.commit()
                flash("Expense created successfully.", "success")
                return redirect(url_for("web.expenses"))
            except ValueError as exc:
                errors["receipt"] = str(exc)
    return render_template(
        "expense_form.html",
        action="Create",
        expense=None,
        errors=errors,
        form_data=request.form,
        default_date=default_date(),
        expense_types=expense_types,
        employees=employees,
    )


@web.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    errors = {}
    expense_types = ExpenseType.query.order_by(ExpenseType.name.asc()).all()
    employees = Employee.query.order_by(Employee.name.asc()).all()
    if request.method == "POST":
        cleaned, errors = validate_expense_form(request.form)
        if not errors:
            try:
                new_receipt = request.files.get("receipt")
                if new_receipt and new_receipt.filename:
                    old_receipt = expense.receipt_filename
                    expense.receipt_filename = _handle_receipt_upload(new_receipt)
                    delete_uploaded_file(old_receipt)
                expense.date = cleaned["date"]
                expense.amount = cleaned["amount"]
                expense.note = cleaned["note"]
                expense.is_salary = cleaned["is_salary"]
                expense.include_in_balance = cleaned["include_in_balance"]
                expense.unit_type = cleaned["unit_type"]
                expense.unit_quantity = cleaned["unit_quantity"]
                expense.employee = cleaned["employee"]
                expense.expense_type = cleaned["expense_type"]
                db.session.commit()
                flash("Expense updated successfully.", "success")
                return redirect(url_for("web.expenses"))
            except ValueError as exc:
                errors["receipt"] = str(exc)
    return render_template(
        "expense_form.html",
        action="Edit",
        expense=expense,
        errors=errors,
        form_data=request.form,
        default_date=default_date(),
        expense_types=expense_types,
        employees=employees,
    )


@web.route("/expenses/<int:expense_id>/delete", methods=["POST"])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    delete_uploaded_file(expense.receipt_filename)
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "success")
    return redirect(url_for("web.expenses"))


@web.route("/sales")
def sales():
    items = _apply_sale_filters().all()
    product_types = ProductType.query.order_by(ProductType.name.asc()).all()
    return render_template("sales.html", sales=items, filters=request.args, product_types=product_types)


@web.route("/sales/new", methods=["GET", "POST"])
def create_sale():
    errors = {}
    product_types = ProductType.query.order_by(ProductType.name.asc()).all()
    if request.method == "POST":
        cleaned, errors = validate_sale_form(request.form)
        if not errors:
            try:
                sale = Sale(
                    date=cleaned["date"],
                    amount=cleaned["amount"],
                    quantity=cleaned["quantity"],
                    unit_type=cleaned["unit_type"],
                    sold_to=cleaned["sold_to"],
                    note=cleaned["note"],
                    receipt_filename=_handle_receipt_upload(request.files.get("receipt")),
                    include_in_totals=cleaned["include_in_totals"],
                    product_type=cleaned["product_type"],
                )
                db.session.add(sale)
                db.session.commit()
                flash("Sale created successfully.", "success")
                return redirect(url_for("web.sales"))
            except ValueError as exc:
                errors["receipt"] = str(exc)
    return render_template(
        "sale_form.html",
        action="Create",
        sale=None,
        errors=errors,
        form_data=request.form,
        default_date=default_date(),
        product_types=product_types,
    )


@web.route("/sales/<int:sale_id>/edit", methods=["GET", "POST"])
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    errors = {}
    product_types = ProductType.query.order_by(ProductType.name.asc()).all()
    if request.method == "POST":
        cleaned, errors = validate_sale_form(request.form)
        if not errors:
            try:
                new_receipt = request.files.get("receipt")
                if new_receipt and new_receipt.filename:
                    old_receipt = sale.receipt_filename
                    sale.receipt_filename = _handle_receipt_upload(new_receipt)
                    delete_uploaded_file(old_receipt)
                sale.date = cleaned["date"]
                sale.amount = cleaned["amount"]
                sale.quantity = cleaned["quantity"]
                sale.unit_type = cleaned["unit_type"]
                sale.sold_to = cleaned["sold_to"]
                sale.note = cleaned["note"]
                sale.include_in_totals = cleaned["include_in_totals"]
                sale.product_type = cleaned["product_type"]
                db.session.commit()
                flash("Sale updated successfully.", "success")
                return redirect(url_for("web.sales"))
            except ValueError as exc:
                errors["receipt"] = str(exc)
    return render_template(
        "sale_form.html",
        action="Edit",
        sale=sale,
        errors=errors,
        form_data=request.form,
        default_date=default_date(),
        product_types=product_types,
    )


@web.route("/sales/<int:sale_id>/delete", methods=["POST"])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    delete_uploaded_file(sale.receipt_filename)
    db.session.delete(sale)
    db.session.commit()
    flash("Sale deleted.", "success")
    return redirect(url_for("web.sales"))


@web.route("/employees", methods=["GET", "POST"])
def employees():
    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_named_entity_form(request.form)
        if not errors:
            existing = Employee.query.filter(func.lower(Employee.name) == cleaned["name"].lower()).first()
            if existing:
                errors["name"] = "Employee already exists."
            else:
                db.session.add(Employee(name=cleaned["name"]))
                db.session.commit()
                flash("Employee added successfully.", "success")
                return redirect(url_for("web.employees"))
    employees_list = Employee.query.order_by(Employee.name.asc()).all()
    return render_template("employees.html", employees=employees_list, errors=errors)


@web.route("/employees/<int:employee_id>/delete", methods=["POST"])
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    if employee.expenses:
        flash("Cannot delete an employee linked to salary records.", "error")
        return redirect(url_for("web.employees"))
    db.session.delete(employee)
    db.session.commit()
    flash("Employee deleted.", "success")
    return redirect(url_for("web.employees"))


@web.route("/settings", methods=["GET", "POST"])
def settings():
    form_kind = request.form.get("kind")
    errors = {"expense_type": {}, "product_type": {}}

    if request.method == "POST":
        cleaned, validation_errors = validate_named_entity_form(request.form)
        if form_kind == "expense_type":
            if validation_errors:
                errors["expense_type"] = validation_errors
            elif ExpenseType.query.filter(func.lower(ExpenseType.name) == cleaned["name"].lower()).first():
                errors["expense_type"]["name"] = "Expense type already exists."
            else:
                db.session.add(ExpenseType(name=cleaned["name"]))
                db.session.commit()
                flash("Expense type added successfully.", "success")
                return redirect(url_for("web.settings"))
        elif form_kind == "product_type":
            if validation_errors:
                errors["product_type"] = validation_errors
            elif ProductType.query.filter(func.lower(ProductType.name) == cleaned["name"].lower()).first():
                errors["product_type"]["name"] = "Product type already exists."
            else:
                db.session.add(ProductType(name=cleaned["name"]))
                db.session.commit()
                flash("Product type added successfully.", "success")
                return redirect(url_for("web.settings"))

    return render_template(
        "settings.html",
        expense_types=ExpenseType.query.order_by(ExpenseType.name.asc()).all(),
        product_types=ProductType.query.order_by(ProductType.name.asc()).all(),
        errors=errors,
    )


@web.route("/settings/expense-types/<int:type_id>/delete", methods=["POST"])
def delete_expense_type(type_id):
    expense_type = ExpenseType.query.get_or_404(type_id)
    if expense_type.expenses:
        flash("Cannot delete an expense type already used by expenses.", "error")
        return redirect(url_for("web.settings"))
    db.session.delete(expense_type)
    db.session.commit()
    flash("Expense type deleted.", "success")
    return redirect(url_for("web.settings"))


@web.route("/settings/product-types/<int:type_id>/delete", methods=["POST"])
def delete_product_type(type_id):
    product_type = ProductType.query.get_or_404(type_id)
    if product_type.sales:
        flash("Cannot delete a product type already used by sales.", "error")
        return redirect(url_for("web.settings"))
    db.session.delete(product_type)
    db.session.commit()
    flash("Product type deleted.", "success")
    return redirect(url_for("web.settings"))


@web.route("/reports")
def reports():
    period = (request.args.get("period") or "monthly").strip()
    start_date = (request.args.get("start_date") or "").strip()
    end_date = (request.args.get("end_date") or "").strip()
    error = None
    payload = None

    try:
        payload = build_report_payload(period, start_date or None, end_date or None)
    except ValueError as exc:
        error = str(exc)
        payload = build_report_payload("monthly")
        period = "monthly"

    return render_template("reports.html", period=period, error=error, payload=payload)


@web.route("/exports/transactions.csv")
def export_transactions_csv():
    transactions = _apply_transaction_filters().all()
    data = transactions_to_csv(transactions)
    return send_file(
        io.BytesIO(data),
        mimetype="text/csv",
        as_attachment=True,
        download_name="transactions.csv",
    )


@web.route("/exports/transactions.xlsx")
def export_transactions_excel():
    if not current_app.config["EXCEL_EXPORT_ENABLED"]:
        flash("Excel export is disabled in this environment.", "error")
        return redirect(url_for("web.transactions"))

    transactions = _apply_transaction_filters().all()
    try:
        data = transactions_to_excel(transactions)
    except RuntimeError as exc:
        flash(str(exc), "error")
        return redirect(url_for("web.transactions"))

    return send_file(
        io.BytesIO(data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="transactions.xlsx",
    )


@web.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return serve_uploaded_file(filename)
