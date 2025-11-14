window.NUTRIENT_TYPES = {
  calories: { label: "Calorias", unit: "" },
  proteins: { label: "Proteínas", unit: "g" },
  carbs: { label: "Carboidratos", unit: "g" },
  fats: { label: "Gorduras", unit: "g" },
};

window.isGuestMode = function () {
  return !document.querySelector(".progress-wrapper");
};
window.clearAllTables = function () {
  Object.keys(MEAL_TYPES || {}).forEach((mealType) => {
    const tbody = document.querySelector(`#${mealType}-foods`);
    if (tbody) {
      // Remove all rows except the totals row (table-secondary)
      const rows = tbody.querySelectorAll("tr:not(.table-secondary)");
      rows.forEach((row) => row.remove());
    }
  });
};
window.closeModal = function (modalId) {
  const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
  if (modal) {
    modal.hide();
  }
};
