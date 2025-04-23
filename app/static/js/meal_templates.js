// Global variables
let currentTemplateId = null;
let mealTypes = {};

// Initialize the page
document.addEventListener("DOMContentLoaded", async function () {
  // Load meal types from backend
  try {
    const response = await fetch("/api/constants");
    const data = await response.json();
    if (data.success) {
      mealTypes = data.meal_types;
    }
  } catch (error) {
    console.error("Erro ao carregar constantes:", error);
  }

  loadTemplates();
  setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
  // Clear form when modal is closed
  document
    .getElementById("addTemplateModal")
    .addEventListener("hidden.bs.modal", function () {
      clearForm();
    });
}

// Load all templates
async function loadTemplates() {
  try {
    const response = await fetch("/api/meal_templates");
    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error || "Erro ao carregar templates");
    }

    const tbody = document.getElementById("templatesTable");
    tbody.innerHTML = "";

    data.templates.forEach((template) => {
      const row = createTemplateRow(template);
      tbody.appendChild(row);
    });
  } catch (error) {
    console.error("Erro ao carregar templates:", error);
    alert("Erro ao carregar templates: " + error.message);
  }
}

// Create a template row for the table
function createTemplateRow(template) {
  const row = document.createElement("tr");
  const foodsList = template.meals_data
    .map((food) => `${food.food_code} (${food.quantity}g)`)
    .join(", ");

  row.innerHTML = `
        <td>${template.name}</td>
        <td>${template.description || ""}</td>
        <td>${mealTypes[template.meal_type] || template.meal_type}</td>
        <td>${foodsList}</td>
        <td>
            <button class="btn btn-sm btn-primary me-1" onclick="editTemplate(${
              template.id
            })">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-danger" onclick="deleteTemplate(${
              template.id
            })">
                <i class="fas fa-trash"></i>
            </button>
        </td>
    `;

  return row;
}

// Add a new food row to the form
function addFoodRow() {
  const container = document.getElementById("foodsContainer");
  const template = document.getElementById("foodRowTemplate");
  const clone = template.content.cloneNode(true);

  // Setup food search functionality
  const foodCodeInput = clone.querySelector(".food-code");
  foodCodeInput.addEventListener("input", function () {
    Food.searchFood(this);
  });

  container.appendChild(clone);
}

// Remove a food row from the form
function removeFoodRow(button) {
  const row = button.closest(".food-row");
  row.remove();
}

// Clear the form
function clearForm() {
  document.getElementById("templateForm").reset();
  document.getElementById("foodsContainer").innerHTML = "";
  currentTemplateId = null;
}

// Edit a template
async function editTemplate(templateId) {
  try {
    const response = await fetch(`/api/meal_templates/${templateId}`);
    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error || "Erro ao carregar template");
    }

    const template = data.template;
    currentTemplateId = templateId;

    // Fill form with template data
    document.getElementById("templateId").value = templateId;
    document.getElementById("templateName").value = template.name;
    document.getElementById("templateDescription").value =
      template.description || "";
    document.getElementById("mealType").value = template.meal_type;

    // Clear and add food rows
    const container = document.getElementById("foodsContainer");
    container.innerHTML = "";

    template.meals_data.forEach((food) => {
      addFoodRow();
      const lastRow = container.lastElementChild;
      lastRow.querySelector(".food-code").value = food.food_code;
      lastRow.querySelector(".quantity").value = food.quantity;
    });

    // Show modal
    const modal = new bootstrap.Modal(
      document.getElementById("addTemplateModal")
    );
    modal.show();
  } catch (error) {
    console.error("Erro ao editar template:", error);
    alert("Erro ao editar template: " + error.message);
  }
}

// Delete a template
async function deleteTemplate(templateId) {
  if (!confirm("Tem certeza que deseja excluir este template?")) {
    return;
  }

  try {
    const response = await fetch(`/api/meal_templates/${templateId}`, {
      method: "DELETE",
    });
    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error || "Erro ao excluir template");
    }

    loadTemplates();
  } catch (error) {
    console.error("Erro ao excluir template:", error);
    alert("Erro ao excluir template: " + error.message);
  }
}

// Save template
async function saveTemplate() {
  const form = document.getElementById("templateForm");
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }

  const foods = [];
  document.querySelectorAll(".food-row").forEach((row) => {
    const foodCode = row.querySelector(".food-code").value;
    const quantity = parseFloat(row.querySelector(".quantity").value);

    if (foodCode && !isNaN(quantity)) {
      foods.push({
        food_code: foodCode,
        quantity: quantity,
      });
    }
  });

  if (foods.length === 0) {
    alert("Adicione pelo menos um alimento ao template");
    return;
  }

  const templateData = {
    name: document.getElementById("templateName").value,
    description: document.getElementById("templateDescription").value,
    meal_type: document.getElementById("mealType").value,
    meals_data: foods,
  };

  try {
    const url = currentTemplateId
      ? `/api/meal_templates/${currentTemplateId}`
      : "/api/meal_templates";

    const response = await fetch(url, {
      method: currentTemplateId ? "PUT" : "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(templateData),
    });

    const data = await response.json();

    if (!data.success) {
      throw new Error(data.error || "Erro ao salvar template");
    }

    // Close modal and reload templates
    const modal = bootstrap.Modal.getInstance(
      document.getElementById("addTemplateModal")
    );
    modal.hide();
    loadTemplates();
  } catch (error) {
    console.error("Erro ao salvar template:", error);
    alert("Erro ao salvar template: " + error.message);
  }
}
