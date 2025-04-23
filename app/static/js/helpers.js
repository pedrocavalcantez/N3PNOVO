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
  document.querySelectorAll('tbody[id$="-foods"]').forEach((tbody) => {
    tbody.innerHTML = "";
  });
};
window.closeModal = function (modalId) {
  const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
  if (modal) {
    modal.hide();
  }
};
