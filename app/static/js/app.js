const modal = document.getElementById("detail-modal");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function buildModalContent(row) {
  const receipt = row.dataset.receipt
    ? `<a class="btn btn-secondary" href="${row.dataset.receipt}" target="_blank" rel="noopener">Open receipt</a>`
    : "<p class='muted'>No receipt uploaded.</p>";

  return `
    <div class="list-stack">
      <div class="list-item plain"><strong>Date</strong><span>${escapeHtml(row.dataset.date)}</span></div>
      <div class="list-item plain"><strong>Type</strong><span>${escapeHtml(row.dataset.type)}</span></div>
      <div class="list-item plain"><strong>Category</strong><span>${escapeHtml(row.dataset.category)}</span></div>
      <div class="list-item plain"><strong>Amount</strong><span>${escapeHtml(row.dataset.amount)}</span></div>
    </div>
    <div class="detail-block">
      <span class="detail-label">Note</span>
      <p>${escapeHtml(row.dataset.note)}</p>
    </div>
    <div class="form-actions">
      ${receipt}
      <a class="btn btn-primary" href="${row.dataset.detailUrl}">Open full page</a>
    </div>
  `;
}

document.querySelectorAll(".clickable-row").forEach((row) => {
  row.addEventListener("click", (event) => {
    if (event.target.closest("a, button, form")) {
      return;
    }
    if (!modal) {
      return;
    }
    document.getElementById("modal-title").textContent = row.dataset.modalTitle;
    document.getElementById("modal-body").innerHTML = buildModalContent(row);
    modal.showModal();
  });
});

document.querySelectorAll("[data-close-modal]").forEach((button) => {
  button.addEventListener("click", () => {
    modal?.close();
  });
});

modal?.addEventListener("click", (event) => {
  const card = event.target.closest(".modal-card");
  if (!card) {
    modal.close();
  }
});

function syncExpenseMode() {
  const salaryRadio = document.querySelector('input[name="is_salary"][value="true"]');
  const expenseTypeField = document.querySelector('select[name="expense_type_id"]')?.closest("label");
  const employeeField = document.querySelector('select[name="employee_id"]')?.closest("label");

  if (!salaryRadio || !expenseTypeField || !employeeField) {
    return;
  }

  const salarySelected = salaryRadio.checked;
  expenseTypeField.hidden = salarySelected;
  employeeField.hidden = !salarySelected;
}

document.querySelectorAll('input[name="is_salary"]').forEach((input) => {
  input.addEventListener("change", syncExpenseMode);
});

syncExpenseMode();
