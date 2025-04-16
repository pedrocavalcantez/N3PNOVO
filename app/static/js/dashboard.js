// Dashboard JavaScript functionality

// Constants
const MEAL_TYPES = [
  "cafe_da_manha",
  "lanche_manha",
  "almoco",
  "lanche_tarde",
  "janta",
  "ceia",
];

const NUTRIENT_TYPES = {
  calories: { label: "Calorias", unit: "" },
  proteins: { label: "Proteínas", unit: "g" },
  carbs: { label: "Carboidratos", unit: "g" },
  fats: { label: "Gorduras", unit: "g" },
};

// Mode Detection
function isGuestMode() {
  return !document.querySelector(".progress-wrapper");
}

// API Helpers
async function makeDietApiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    // Handle non-200 responses
    if (!response.ok) {
      throw new Error(data.error || `HTTP error! status: ${response.status}`);
    }

    // Handle search endpoints differently as they return arrays
    if (url.includes("/api/search_food")) {
      return data;
    }

    // For other endpoints, check success property
    if (data.success === false) {
      throw new Error(data.error || "Unknown error occurred");
    }

    return data;
  } catch (error) {
    console.error("API Call Error:", error);
    throw error;
  }
}

function handleApiError(error, customMessage) {
  console.error("Error:", error);
  alert(customMessage + ": " + error.message);
}

// UI Helpers
function closeModal(modalId) {
  const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
  if (modal) {
    modal.hide();
  }
}

// Row Management Helpers
function getFoodRowData(row) {
  return {
    food_code: row.querySelector(".food-code").value,
    quantity: row.querySelector(".quantity").value,
    calories: row.querySelector(".calories").textContent,
    proteins: row.querySelector(".proteins").textContent,
    carbs: row.querySelector(".carbs").textContent,
    fats: row.querySelector(".fats").textContent,
  };
}

function clearAllTables() {
  document.querySelectorAll('tbody[id$="-foods"]').forEach((tbody) => {
    tbody.innerHTML = "";
  });
}

// Nutritional Value Helpers
function getNutritionalValues(row) {
  return {
    calories: parseFloat(row.querySelector(".calories").textContent) || 0,
    proteins: parseFloat(row.querySelector(".proteins").textContent) || 0,
    carbs: parseFloat(row.querySelector(".carbs").textContent) || 0,
    fats: parseFloat(row.querySelector(".fats").textContent) || 0,
  };
}

function setNutritionalValues(row, values, includeUnits = false) {
  if (!row) {
    console.warn("Attempted to set nutritional values on null/undefined row");
    return;
  }

  // Skip if this is a header row
  if (row.closest("thead")) {
    return;
  }

  // Check if this is a total row (has strong tags)
  const isTotal = row.querySelector("strong") !== null;

  let elements;
  if (isTotal) {
    // For total rows, look for strong tags in cells
    const cells = Array.from(row.cells);
    elements = {
      calories: cells[2]?.querySelector("strong"),
      proteins: cells[3]?.querySelector("strong"),
      carbs: cells[4]?.querySelector("strong"),
      fats: cells[5]?.querySelector("strong"),
    };
  } else {
    // For regular rows, look for class names
    elements = {
      calories: row.querySelector(".calories"),
      proteins: row.querySelector(".proteins"),
      carbs: row.querySelector(".carbs"),
      fats: row.querySelector(".fats"),
    };
  }

  // Check if all required elements exist
  const missingElements = Object.entries(elements)
    .filter(([_, element]) => !element)
    .map(([name]) => name);

  if (missingElements.length > 0) {
    console.warn(
      `Missing nutritional elements in ${isTotal ? "total" : ""} row (${
        row.id || "no id"
      }):`,
      missingElements.join(", "),
      "\nRow HTML:",
      row.innerHTML
    );
    return;
  }

  // Validate values
  const validValues = {
    calories: parseFloat(values.calories) || 0,
    proteins: parseFloat(values.proteins) || 0,
    carbs: parseFloat(values.carbs) || 0,
    fats: parseFloat(values.fats) || 0,
  };

  // Set the values with proper formatting
  elements.calories.textContent =
    validValues.calories.toFixed(1) + (includeUnits ? "" : "");
  elements.proteins.textContent =
    validValues.proteins.toFixed(1) + (includeUnits ? "g" : "");
  elements.carbs.textContent =
    validValues.carbs.toFixed(1) + (includeUnits ? "g" : "");
  elements.fats.textContent =
    validValues.fats.toFixed(1) + (includeUnits ? "g" : "");
}

function resetNutritionalValues(row) {
  setNutritionalValues(row, {
    calories: 0,
    proteins: 0,
    carbs: 0,
    fats: 0,
  });
}

// Update Totals Helpers
function updateTotalsDisplay(totals) {
  if (isGuestMode()) {
    // Guest mode - update the simple summary boxes
    document.getElementById("total-calories").textContent =
      totals.calories.toFixed(1);
    document.getElementById("total-proteins").textContent =
      totals.proteins.toFixed(1);
    document.getElementById("total-carbs").textContent =
      totals.carbs.toFixed(1);
    document.getElementById("total-fats").textContent = totals.fats.toFixed(1);
  } else {
    // Regular mode - update the nutrient boxes and progress bar
    updateNutrientBoxes(totals);
    updateProgressBar(totals.calories);
  }
}

// Helper function to create and setup a food row
function setupFoodRow(food = null, mealType = null) {
  // Clone the template
  const template = document.getElementById("food-row-template");
  const row = template.content.cloneNode(true).querySelector("tr");

  // Set row ID if food exists
  if (food && food.id) {
    row.id = `food-${food.id}`;
  }

  // Get elements
  const foodCodeInput = row.querySelector(".food-code");
  const quantityInput = row.querySelector(".quantity");
  const caloriesCell = row.querySelector(".calories");
  const proteinsCell = row.querySelector(".proteins");
  const carbsCell = row.querySelector(".carbs");
  const fatsCell = row.querySelector(".fats");
  const saveButton = row.querySelector(".save-food");
  const deleteButton = row.querySelector(".btn-danger");

  // Set values if food data exists
  if (food) {
    foodCodeInput.value = food.food_code || "";
    quantityInput.value = food.quantity || "";
    caloriesCell.textContent = food.calories || "0";
    proteinsCell.textContent = food.proteins || "0";
    carbsCell.textContent = food.carbs || "0";
    fatsCell.textContent = food.fats || "0";
  }

  // Set up event listeners
  foodCodeInput.addEventListener("input", () => searchFood(foodCodeInput));
  quantityInput.addEventListener("input", () => updateNutrition(quantityInput));

  // Setup save button
  if (saveButton) {
    if (document.querySelector(".progress-wrapper")) {
      // Logged-in mode
      saveButton.onclick = () => saveFood(saveButton, mealType);
    } else {
      // Guest mode
      saveButton.onclick = () => saveGuestFood(saveButton);
    }
  }

  // Setup delete button
  if (deleteButton) {
    deleteButton.onclick = () => {
      if (food && food.id) {
        deleteFood(food.id);
      } else {
        row.remove();
        updateDailyTotals();
      }
    };
  }

  return row;
}

// Function to convert row back to editable form
function editFoodRow(button) {
  const row = button.closest("tr");
  const cells = row.cells;

  // Extrai os valores originais
  const foodCode = cells[0].textContent.trim();
  const quantity = parseFloat(cells[1].textContent);
  const calories = parseFloat(cells[2].textContent);
  const proteins = parseFloat(cells[3].textContent);
  const carbs = parseFloat(cells[4].textContent);
  const fats = parseFloat(cells[5].textContent);

  // Transforma em campos editáveis
  cells[0].innerHTML = `
    <div class="input-group">
      <input type="text" class="form-control food-code" value="${foodCode}" onkeyup="searchFood(this)">
      <div class="search-results d-none position-absolute w-100 bg-white border rounded-bottom shadow-sm" style="z-index: 1000; top: 100%"></div>
    </div>
  `;
  cells[1].innerHTML = `
    <input type="number" class="form-control quantity" value="${quantity}" step="1" min="0" style="width: 80px" oninput="updateNutrition(this)">
  `;

  // Coloca spans vazios com classes corretas para serem atualizados
  cells[2].innerHTML = `<span class="calories">${calories.toFixed(1)}</span>`;
  cells[3].innerHTML = `<span class="proteins">${proteins.toFixed(1)}g</span>`;
  cells[4].innerHTML = `<span class="carbs">${carbs.toFixed(1)}g</span>`;
  cells[5].innerHTML = `<span class="fats">${fats.toFixed(1)}g</span>`;

  // Botões de ação
  const actionButtons = cells[6].querySelector(".action-buttons");
  const foodId = row.id.replace("food-", "");
  actionButtons.innerHTML = `
    <button class="btn btn-success save-food" onclick="saveFood(this, '${getMealType(
      row
    )}')" title="Salvar">
      <i class="fas fa-check"></i>
    </button>
    <button class="btn btn-danger" onclick="deleteFood(${foodId})" title="Remover">
      <i class="fas fa-trash"></i>
    </button>
  `;
}
// Helper function to get meal type from row
function getMealType(row) {
  const tbody = row.closest("tbody");
  return tbody.id.replace("-foods", "");
}

// Update createFoodRow to include edit button
function createFoodRow(food) {
  if (!food || !food.id) {
    // For new rows, use the existing setup with input fields
    return setupFoodRow(food);
  }

  // For loaded foods, create a static row
  const row = document.createElement("tr");
  row.id = `food-${food.id}`;

  // Create cells with static text
  row.innerHTML = `
    <td>${food.food_code}</td>
    <td>${parseFloat(food.quantity).toFixed(1)}g</td>
    <td class="calories">${parseFloat(food.calories).toFixed(1)}</td>
    <td class="proteins">${parseFloat(food.proteins).toFixed(1)}g</td>
    <td class="carbs">${parseFloat(food.carbs).toFixed(1)}g</td>
    <td class="fats">${parseFloat(food.fats).toFixed(1)}g</td>
    <td>
      <div class="action-buttons">
        <button class="btn btn-primary btn-sm" onclick="editFoodRow(this)" title="Editar">
          <i class="fas fa-edit"></i>
        </button>
        <button class="btn btn-danger" onclick="deleteFood(${
          food.id
        })" title="Remover">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </td>
  `;

  return row;
}

function collectMealsData() {
  const mealsData = {};

  MEAL_TYPES.forEach((mealType) => {
    mealsData[mealType] = Array.from(
      document.querySelectorAll(
        `#${mealType}-foods tr:not(.table-secondary):not(.template-row)`
      )
    )
      .filter((row) => {
        // Skip rows that are being edited (have input fields but no values)
        const foodCodeInput = row.querySelector(".food-code");
        const quantityInput = row.querySelector(".quantity");

        if (foodCodeInput && quantityInput) {
          // This is a new row being edited
          return (
            foodCodeInput.value &&
            foodCodeInput.value.trim() !== "" &&
            quantityInput.value &&
            quantityInput.value.trim() !== ""
          );
        } else {
          // This is an existing saved food row
          const cells = row.cells;
          if (cells.length >= 6) {
            const foodId = row.id?.replace("food-", "");
            return foodId && foodId !== "";
          }
          return false;
        }
      })
      .map((row) => {
        const foodCodeInput = row.querySelector(".food-code");
        const quantityInput = row.querySelector(".quantity");

        if (foodCodeInput && quantityInput) {
          // New row being edited
          return {
            food_code: foodCodeInput.value,
            quantity: quantityInput.value,
            calories:
              parseFloat(row.querySelector(".calories").textContent) || 0,
            proteins:
              parseFloat(row.querySelector(".proteins").textContent) || 0,
            carbs: parseFloat(row.querySelector(".carbs").textContent) || 0,
            fats: parseFloat(row.querySelector(".fats").textContent) || 0,
          };
        } else {
          // Existing saved food row
          const cells = row.cells;
          // Extract quantity value, removing the 'g' suffix if present
          const quantityText = cells[1].textContent.trim();
          const quantity = parseFloat(quantityText.replace("g", "")) || 0;

          return {
            id: row.id?.replace("food-", ""),
            food_code: cells[0].textContent.trim(),
            quantity: quantity,
            calories: parseFloat(cells[2].textContent) || 0,
            proteins: parseFloat(cells[3].textContent) || 0,
            carbs: parseFloat(cells[4].textContent) || 0,
            fats: parseFloat(cells[5].textContent) || 0,
          };
        }
      });
  });

  return mealsData;
}

// Diet name suggestions
function showDietSuggestions(input) {
  const value = input.value.toLowerCase().trim();
  const suggestionsDiv = document.getElementById("dietSuggestions");
  const savedDiets = Array.from(
    document.querySelectorAll("#loadDietModal .list-group-item button.btn-link")
  ).map((btn) => ({
    id: btn.getAttribute("onclick").match(/loadDiet\((\d+)\)/)[1],
    name: btn.textContent.trim(),
  }));

  // Clear previous suggestions
  suggestionsDiv.innerHTML = "";

  if (!value) {
    suggestionsDiv.classList.add("d-none");
    return;
  }

  // Filter matching diets
  const matches = savedDiets.filter((diet) =>
    diet.name.toLowerCase().includes(value)
  );

  // Add matching suggestions
  matches.forEach((diet) => {
    const div = document.createElement("div");
    div.className = "diet-suggestion-item";
    div.textContent = diet.name;
    div.dataset.id = diet.id;
    div.onclick = () => selectDietSuggestion(diet.name, diet.id);
    suggestionsDiv.appendChild(div);
  });

  // Show suggestions if we have any matches
  suggestionsDiv.classList.toggle("d-none", matches.length === 0);
}

function selectDietSuggestion(name, id) {
  const input = document.getElementById("dietName");
  input.value = name;
  input.dataset.selectedId = id || "";
  document.getElementById("dietSuggestions").classList.add("d-none");
}

function getDietInfo() {
  const dietNameInput = document.getElementById("dietName");
  const dietName = dietNameInput.value.trim();
  return {
    dietName,
    existingDietId: dietNameInput.dataset.selectedId || null,
  };
}

// Update addNewRow to use the helper function
function addNewRow(mealType) {
  const content = document.getElementById(`${mealType}-content`);
  const btn = document
    .querySelector(`#${mealType}-content`)
    .closest(".card")
    .querySelector(".expand-btn i");

  // Ensure the section is expanded
  if (content.style.display === "none") {
    content.style.display = "block";
    btn.classList.remove("fa-chevron-down");
    btn.classList.add("fa-chevron-up");
    content.style.opacity = "1";
    content.style.transform = "translateY(0)";
  }

  const tbody = document.getElementById(`${mealType}-foods`);
  const row = setupFoodRow(null, mealType);

  // Find the total row (table-secondary class)
  const totalRow = tbody.querySelector(".table-secondary");

  if (totalRow) {
    // Insert the new row before the total row
    tbody.insertBefore(row, totalRow);
  } else {
    // If no total row found, just append to the end
    tbody.appendChild(row);
  }
}

// Search for food items
async function searchFood(input) {
  const searchResults = input.nextElementSibling;
  const query = input.value.trim();

  if (query.length < 2) {
    searchResults.classList.add("d-none");
    return;
  }

  try {
    searchResults.innerHTML = "<div class='p-2'>Buscando...</div>";
    searchResults.classList.remove("d-none");

    const data = await makeDietApiCall(
      `/api/search_food?query=${encodeURIComponent(query)}`
    );
    searchResults.innerHTML = "";

    if (!Array.isArray(data)) {
      throw new Error("Formato de resposta inválido");
    }

    if (data.length === 0) {
      searchResults.innerHTML =
        "<div class='p-2 text-muted'>Nenhum alimento encontrado</div>";
      return;
    }

    data.forEach((food) => {
      const div = document.createElement("div");
      div.className = "p-2 border-bottom";
      div.style.cursor = "pointer";
      div.textContent = `${food.food_code}`;
      div.onclick = () => selectFood(input, food);
      searchResults.appendChild(div);
    });
  } catch (error) {
    console.error("Search Error:", error);
    searchResults.innerHTML =
      "<div class='p-2 text-danger'>Erro ao buscar alimentos: " +
      (error.message || "Erro desconhecido") +
      "</div>";
  }
}

// Select food from search results
function selectFood(input, food) {
  input.value = food.food_code;
  input.nextElementSibling.classList.add("d-none");
  const row = input.closest("tr");
  const quantityInput = row.querySelector(".quantity");
  quantityInput.value = food.qtd;
  quantityInput.dispatchEvent(new Event("input")); // Trigger nutrition update
  quantityInput.focus();
}

// Update nutrition values based on quantity
async function updateNutrition(input) {
  const row = input.closest("tr");
  const code = row.querySelector(".food-code").value;
  const quantity = parseFloat(input.value) || 0;

  if (code && quantity >= 0) {
    try {
      const data = await makeDietApiCall(
        `/api/food_nutrition/${encodeURIComponent(code)}?quantity=${quantity}`
      );
      setNutritionalValues(row, {
        calories: data.calories,
        proteins: data.proteins,
        carbs: data.carbs,
        fats: data.fats,
      });
      row.querySelector(".save-food").style.display =
        quantity > 0 ? "inline-block" : "none";
    } catch (error) {
      handleApiError(error, "Erro ao atualizar valores nutricionais");
      resetNutritionalValues(row);
      row.querySelector(".save-food").style.display = "none";
    }
  } else {
    resetNutritionalValues(row);
    row.querySelector(".save-food").style.display = "none";
  }
}

// Save food entry
async function saveFood(button, mealType) {
  const row = button.closest("tr");
  const foodCodeInput = row.querySelector(".food-code");
  const quantityInput = row.querySelector(".quantity");
  const code = foodCodeInput.value;
  const quantity = parseFloat(quantityInput.value);

  try {
    const data = await makeDietApiCall("/api/add_food", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        food_code: code,
        quantity: quantity,
        meal_type: mealType,
      }),
    });

    // Update the row with the returned data
    setNutritionalValues(row, data.food);
    row.id = `food-${data.food.id}`;

    // Convert input fields to static td cells
    const foodCodeCell = foodCodeInput.closest("td");
    const quantityCell = quantityInput.closest("td");

    // Replace food code input with static text
    foodCodeCell.innerHTML = code;

    // Replace quantity input with static text
    quantityCell.innerHTML = `${quantity.toFixed(1)}g`;

    // Update action buttons to include edit and delete
    const actionButtons = row.querySelector(".action-buttons");
    actionButtons.innerHTML = `
      <button class="btn btn-primary btn-sm" onclick="editFoodRow(this)" title="Editar">
        <i class="fas fa-edit"></i>
      </button>
      <button class="btn btn-danger" onclick="deleteFood(${data.food.id})" title="Remover">
        <i class="fas fa-trash"></i>
      </button>
    `;

    updateDailyTotals();
  } catch (error) {
    handleApiError(error, "Erro ao salvar alimento");
    button.style.display = "inline-block";
  }
}

// Delete food entry
async function deleteFood(foodId) {
  try {
    const data = await makeDietApiCall(`/api/delete_food/${foodId}`, {
      method: "DELETE",
    });

    const row = document.getElementById(`food-${foodId}`);
    if (row) {
      const tbody = row.closest("tbody");
      const mealType = tbody.id.replace("-foods", "");
      row.remove();
      updateMealTotals(mealType);
      updateDailyTotals();
    }
  } catch (error) {
    handleApiError(error, "Erro ao remover alimento");
  }
}

// Update updateMealTotals to handle row types better
function updateMealTotals(mealType) {
  const tbody = document.getElementById(`${mealType}-foods`);
  if (!tbody) {
    console.warn(`Table body not found for meal type: ${mealType}`);
    return {
      calories: 0,
      proteins: 0,
      carbs: 0,
      fats: 0,
    };
  }

  const totals = {
    calories: 0,
    proteins: 0,
    carbs: 0,
    fats: 0,
  };

  // Get all food rows in this meal (excluding header, footer, and template rows)
  tbody
    .querySelectorAll("tr:not(.table-secondary):not(.template-row)")
    .forEach((row) => {
      // Get values directly from the cells
      const cells = row.cells;
      if (cells.length >= 6) {
        // Make sure we have enough cells
        totals.calories += parseFloat(cells[2].textContent) || 0;
        totals.proteins += parseFloat(cells[3].textContent) || 0;
        totals.carbs += parseFloat(cells[4].textContent) || 0;
        totals.fats += parseFloat(cells[5].textContent) || 0;
      }
    });

  // Update meal totals in the footer
  const tfoot = tbody.closest("table")?.querySelector("tfoot");
  const totalRow = tfoot?.querySelector("tr");

  if (totalRow) {
    const cells = totalRow.cells;
    if (cells.length >= 6) {
      const strongElements = {
        calories: cells[2].querySelector("strong"),
        proteins: cells[3].querySelector("strong"),
        carbs: cells[4].querySelector("strong"),
        fats: cells[5].querySelector("strong"),
      };

      if (strongElements.calories)
        strongElements.calories.textContent = totals.calories.toFixed(1);
      if (strongElements.proteins)
        strongElements.proteins.textContent = totals.proteins.toFixed(1) + "g";
      if (strongElements.carbs)
        strongElements.carbs.textContent = totals.carbs.toFixed(1) + "g";
      if (strongElements.fats)
        strongElements.fats.textContent = totals.fats.toFixed(1) + "g";
    }
  }

  return totals;
}

// Update updateDailyTotals to use helpers
function updateDailyTotals() {
  const totals = {
    calories: 0,
    proteins: 0,
    carbs: 0,
    fats: 0,
  };

  // Calculate totals for each meal type
  MEAL_TYPES.forEach((mealType) => {
    const mealTotals = updateMealTotals(mealType);
    totals.calories += mealTotals.calories;
    totals.proteins += mealTotals.proteins;
    totals.carbs += mealTotals.carbs;
    totals.fats += mealTotals.fats;
  });

  updateTotalsDisplay(totals);
}

// Helper function to update nutrient boxes
function updateNutrientBoxes(totals) {
  const nutrientBoxes = document.querySelectorAll(".nutrient-box");
  nutrientBoxes.forEach((box) => {
    const valueElement = box.querySelector("p");
    if (!valueElement) return;

    for (const [type, info] of Object.entries(NUTRIENT_TYPES)) {
      if (box.textContent.includes(info.label)) {
        valueElement.textContent = `${totals[type].toFixed(1)}${info.unit}`;
        break;
      }
    }
  });
}

// Helper function to update progress bar
function updateProgressBar(totalCalories) {
  const progressWrapper = document.querySelector(".progress-wrapper");
  if (!progressWrapper) return;

  const caloriesDisplay = progressWrapper.querySelector(
    ".d-flex span:last-child"
  );
  const progressBar = progressWrapper.querySelector(".progress-bar");
  if (!caloriesDisplay || !progressBar) return;

  // Extract goal calories once
  const goalCalories =
    parseFloat(caloriesDisplay.textContent.split("/")[1]) || 0;

  // Update calories display
  caloriesDisplay.textContent = `${totalCalories.toFixed(
    1
  )} / ${goalCalories.toFixed(1)} kcal`;

  // Update progress bar
  if (goalCalories > 0) {
    const percentage = Math.min(100, (totalCalories / goalCalories) * 100);
    progressBar.style.width = `${percentage}%`;
  }
}

// Close search results when clicking outside
document.addEventListener("click", function (event) {
  if (!event.target.classList.contains("food-code")) {
    const results = document.querySelectorAll(".search-results");
    results.forEach((result) => result.classList.add("d-none"));
  }
});

async function loadDiet(dietId) {
  try {
    const data = await makeDietApiCall(`/api/load_diet/${dietId}`);
    clearAllTables();

    // Add foods from the loaded diet
    Object.entries(data.meals_data).forEach(([mealType, foods]) => {
      const tbody = document.querySelector(`#${mealType}-foods`);
      if (tbody) {
        foods.forEach((food) => {
          const row = createFoodRow(food);
          tbody.appendChild(row);
          // Update meal totals after each food is added
          updateMealTotals(mealType);
        });
      }
    });

    closeModal("loadDietModal");
    // Ensure totals are updated after all foods are loaded
    updateDailyTotals();
  } catch (error) {
    alert("Erro ao carregar dieta: " + error.message);
  }
}

async function saveDiet() {
  try {
    const { dietName, existingDietId } = getDietInfo();

    if (!dietName) {
      alert("Por favor, insira um nome para a dieta");
      return;
    }

    // If it's an existing diet, confirm overwrite
    if (
      existingDietId &&
      !confirm(`A dieta "${dietName}" já existe. Deseja sobrescrevê-la?`)
    ) {
      return;
    }

    const mealsData = collectMealsData();
    const url = existingDietId
      ? `/api/save_diet?diet_id=${existingDietId}`
      : "/api/save_diet";

    await makeDietApiCall(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: dietName, meals_data: mealsData }),
    });

    closeModal("saveDietModal");
    alert(
      existingDietId
        ? "Dieta atualizada com sucesso!"
        : "Dieta salva com sucesso!"
    );
    location.reload();
  } catch (error) {
    alert("Erro ao salvar dieta: " + error.message);
  }
}

// Event Listeners
document.addEventListener("DOMContentLoaded", function () {
  // Close search results when clicking outside
  document.addEventListener("click", function (event) {
    if (!event.target.classList.contains("food-code")) {
      const results = document.querySelectorAll(".search-results");
      results.forEach((result) => result.classList.add("d-none"));
    }
  });

  // Update diet name when selecting an existing diet
  const existingDietSelect = document.getElementById("existingDiet");
  if (existingDietSelect) {
    existingDietSelect.addEventListener("change", function () {
      const selectedOption = this.options[this.selectedIndex];
      const dietNameInput = document.getElementById("dietName");
      if (dietNameInput) {
        dietNameInput.value = selectedOption.value ? selectedOption.text : "";
      }
    });
  }

  // Calculate totals from existing rows on page load
  console.log("Calculating initial totals...");
  MEAL_TYPES.forEach((mealType) => {
    console.log(`Calculating totals for ${mealType}...`);
    updateMealTotals(mealType);
  });
  updateDailyTotals();

  // Diet name input handler
  const dietNameInput = document.getElementById("dietName");
  if (dietNameInput) {
    dietNameInput.addEventListener("input", () =>
      showDietSuggestions(dietNameInput)
    );
    dietNameInput.addEventListener("focus", () =>
      showDietSuggestions(dietNameInput)
    );

    // Close suggestions when clicking outside
    document.addEventListener("click", (event) => {
      if (
        !event.target.closest("#dietName") &&
        !event.target.closest("#dietSuggestions")
      ) {
        document.getElementById("dietSuggestions").classList.add("d-none");
      }
    });

    // Handle keyboard navigation
    dietNameInput.addEventListener("keydown", (event) => {
      const suggestions = document.getElementById("dietSuggestions");
      const items = suggestions.querySelectorAll(".diet-suggestion-item");
      const activeItem = suggestions.querySelector(
        ".diet-suggestion-item.active"
      );

      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          if (!suggestions.classList.contains("d-none")) {
            if (!activeItem) {
              items[0]?.classList.add("active");
            } else {
              const nextItem = activeItem.nextElementSibling;
              if (nextItem) {
                activeItem.classList.remove("active");
                nextItem.classList.add("active");
              }
            }
          }
          break;

        case "ArrowUp":
          event.preventDefault();
          if (!suggestions.classList.contains("d-none")) {
            if (activeItem) {
              const prevItem = activeItem.previousElementSibling;
              if (prevItem) {
                activeItem.classList.remove("active");
                prevItem.classList.add("active");
              }
            }
          }
          break;

        case "Enter":
          if (!suggestions.classList.contains("d-none") && activeItem) {
            event.preventDefault();
            selectDietSuggestion(
              activeItem.textContent.replace(" (existente)", ""),
              activeItem.dataset.id
            );
          }
          break;

        case "Escape":
          suggestions.classList.add("d-none");
          break;
      }
    });
  }

  // Initialize meal sections
  MEAL_TYPES.forEach((mealType) => {
    const content = document.getElementById(`${mealType}-content`);
    const btn = document
      .querySelector(`#${mealType}-content`)
      .closest(".card")
      .querySelector(".expand-btn i");
    const tbody = document.getElementById(`${mealType}-foods`);

    // Check if there are any food rows (excluding the total row)
    const hasFood =
      tbody &&
      Array.from(tbody.children).some(
        (row) =>
          !row.classList.contains("table-secondary") &&
          !row.classList.contains("template-row")
      );

    if (hasFood) {
      content.style.display = "block";
      btn.classList.remove("fa-chevron-down");
      btn.classList.add("fa-chevron-up");
      // Animate the content
      content.style.opacity = "1";
      content.style.transform = "translateY(0)";
    }
  });
});

// Delete diet
async function deleteDiet(dietId) {
  if (!confirm("Tem certeza que deseja excluir esta dieta?")) {
    return;
  }

  try {
    const data = await makeDietApiCall(`/api/delete_diet/${dietId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });

    // Remove the diet item from the list
    const dietItem = document
      .querySelector(`[onclick="deleteDiet(${dietId})"]`)
      .closest(".list-group-item");
    dietItem.remove();

    // If this was the last diet, close the modal
    const remainingDiets = document.querySelectorAll(".list-group-item");
    if (remainingDiets.length === 0) {
      closeModal("loadDietModal");
    }

    alert("Dieta excluída com sucesso!");
  } catch (error) {
    handleApiError(error, "Erro ao excluir dieta");
  }
}

// Add this function to handle meal section toggling
function toggleMealSection(mealType) {
  const content = document.getElementById(`${mealType}-content`);
  const btn = document
    .querySelector(`#${mealType}-content`)
    .closest(".card")
    .querySelector(".expand-btn i");

  if (content.style.display === "none") {
    content.style.display = "block";
    btn.classList.remove("fa-chevron-down");
    btn.classList.add("fa-chevron-up");
    // Animate the content
    content.style.opacity = "0";
    content.style.transform = "translateY(-10px)";
    setTimeout(() => {
      content.style.transition = "all 0.3s ease";
      content.style.opacity = "1";
      content.style.transform = "translateY(0)";
    }, 10);
  } else {
    content.style.opacity = "0";
    content.style.transform = "translateY(-10px)";
    setTimeout(() => {
      content.style.display = "none";
      btn.classList.remove("fa-chevron-up");
      btn.classList.add("fa-chevron-down");
    }, 300);
  }
}

// Add export to Excel functionality
async function exportToExcel() {
  try {
    // Collect all meal data
    const mealsData = collectMealsData();

    // Get the current date for the filename
    const date = new Date().toISOString().split("T")[0];
    const filename = `dieta_${date}.xlsx`;

    // Make API call to get the Excel file
    const response = await fetch("/api/export_diet", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(mealsData),
    });

    if (!response.ok) {
      throw new Error("Erro ao exportar dieta");
    }

    // Convert response to blob
    const blob = await response.blob();

    // Create download link and trigger download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error("Export Error:", error);
    alert("Erro ao exportar dieta: " + error.message);
  }
}
