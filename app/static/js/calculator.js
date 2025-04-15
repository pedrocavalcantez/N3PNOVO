// Store selected foods data
let selectedFoods = new Map();

// Add a new food item input
function addFoodItem() {
  const foodsList = document.getElementById("foodsList");
  const foodItem = document.createElement("div");
  foodItem.className = "food-item mb-3";
  foodItem.innerHTML = `
    <div class="input-group">
      <input type="text" class="form-control food-code" placeholder="Código do alimento" onkeyup="searchFood(this)">
      <input type="number" class="form-control food-min" placeholder="Min (g)" style="max-width: 100px;" min="0" step="1">
      <input type="number" class="form-control food-max" placeholder="Max (g)" style="max-width: 100px;" min="0" step="1">
      <button type="button" class="btn" style="background-color: #FF7F6B; color: white;" onclick="removeFoodItem(this)">
        <i class="fas fa-times"></i>
      </button>
      <div class="search-results d-none position-absolute w-100 bg-white border rounded-3 shadow-sm" style="z-index: 1000; top: 100%"></div>
    </div>
    <small class="text-muted">Deixe min/max vazios para sem limites</small>
  `;
  foodsList.appendChild(foodItem);

  // Animate the new item
  foodItem.style.opacity = "0";
  foodItem.style.transform = "translateY(-10px)";
  setTimeout(() => {
    foodItem.style.transition = "all 0.3s ease-out";
    foodItem.style.opacity = "1";
    foodItem.style.transform = "translateY(0)";
  }, 10);
}

// Remove a food item with animation
function removeFoodItem(button) {
  const foodItem = button.closest(".food-item");
  const input = foodItem.querySelector(".food-code");
  selectedFoods.delete(input.value);

  // Animate removal
  foodItem.style.transition = "all 0.3s ease-out";
  foodItem.style.opacity = "0";
  foodItem.style.transform = "translateY(-10px)";
  setTimeout(() => foodItem.remove(), 300);
}

// Search for foods with improved feedback
async function searchFood(input) {
  const resultsDiv = input.parentElement.querySelector(".search-results");
  const query = input.value.trim();

  if (query.length < 2) {
    resultsDiv.classList.add("d-none");
    return;
  }

  // Show loading state
  resultsDiv.innerHTML =
    '<div class="p-2 text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Buscando...</div>';
  resultsDiv.classList.remove("d-none");

  try {
    const response = await fetch(
      `/api/search_food?query=${encodeURIComponent(query)}`
    );
    const data = await response.json();

    resultsDiv.innerHTML = "";
    if (data.length > 0) {
      data.forEach((food) => {
        const div = document.createElement("div");
        div.className = "search-result";
        div.textContent = `${food.food_code}`;
        div.onclick = () => selectFood(input, food);
        resultsDiv.appendChild(div);
      });
    } else {
      resultsDiv.innerHTML =
        '<div class="p-2 text-muted">Nenhum alimento encontrado</div>';
    }
  } catch (error) {
    console.error("Error searching foods:", error);
    resultsDiv.innerHTML =
      '<div class="p-2 text-danger">Erro ao buscar alimentos</div>';
  }
}

// Select a food from search results with feedback
function selectFood(input, food) {
  input.value = food.food_code;
  const foodItem = input.closest(".food-item");
  const minInput = foodItem.querySelector(".food-min");
  const maxInput = foodItem.querySelector(".food-max");

  selectedFoods.set(food.food_code, {
    code: food.food_code,
    description: food.food_code,
    quantity: food.qtd,
    min: minInput.value ? parseFloat(minInput.value) : null,
    max: maxInput.value ? parseFloat(maxInput.value) : null,
  });

  // Hide results with animation
  const resultsDiv = input.parentElement.querySelector(".search-results");
  resultsDiv.style.transition = "all 0.2s ease-out";
  resultsDiv.style.opacity = "0";
  setTimeout(() => {
    resultsDiv.classList.add("d-none");
    resultsDiv.style.opacity = "1";
  }, 200);

  // Visual feedback
  input.style.transition = "all 0.2s ease-out";
  input.style.backgroundColor = "rgba(180, 217, 87, 0.1)";
  setTimeout(() => {
    input.style.backgroundColor = "";
  }, 500);
}

// Update tolerance value display with animation
function updateToleranceValue(value) {
  const valueSpan = document.getElementById("toleranceValue");
  valueSpan.style.transform = "scale(1.2)";
  valueSpan.textContent = `${value}%`;
  setTimeout(() => {
    valueSpan.style.transition = "transform 0.2s ease-out";
    valueSpan.style.transform = "scale(1)";
  }, 50);
}

// Calculate portions with improved feedback
async function calculatePortions() {
  if (selectedFoods.size === 0) {
    showAlert("Por favor, selecione pelo menos um alimento.", "warning");
    return;
  }

  const targets = {
    calories: parseFloat(document.getElementById("targetCalories").value) || 0,
    proteins: parseFloat(document.getElementById("targetProteins").value) || 0,
    carbs: parseFloat(document.getElementById("targetCarbs").value) || 0,
    fats: parseFloat(document.getElementById("targetFats").value) || 0,
  };

  const tolerance =
    parseFloat(document.getElementById("tolerance").value) / 100;

  if (Object.values(targets).every((v) => v === 0)) {
    showAlert(
      "Por favor, defina pelo menos um valor desejado (calorias, proteínas, carboidratos ou gorduras).",
      "warning"
    );
    return;
  }

  // Update boundaries for all foods
  document.querySelectorAll(".food-item").forEach((item) => {
    const code = item.querySelector(".food-code").value;
    const minInput = item.querySelector(".food-min");
    const maxInput = item.querySelector(".food-max");

    if (selectedFoods.has(code)) {
      const food = selectedFoods.get(code);
      food.min = minInput.value ? parseFloat(minInput.value) : null;
      food.max = maxInput.value ? parseFloat(maxInput.value) : null;
      selectedFoods.set(code, food);
    }
  });

  // Show loading state
  const submitBtn = document.querySelector('button[type="submit"]');
  const originalContent = submitBtn.innerHTML;
  submitBtn.innerHTML =
    '<i class="fas fa-spinner fa-spin me-2"></i>Calculando...';
  submitBtn.disabled = true;

  try {
    const response = await fetch("/api/calculate_portions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        targets: targets,
        tolerance: tolerance,
        foods: Array.from(selectedFoods.values()).map((food) => ({
          code: food.code,
          min: food.min,
          max: food.max,
        })),
      }),
    });

    const data = await response.json();
    if (data.success) {
      displayResults(data.portions);
      showAlert("Cálculo realizado com sucesso!", "success");
    } else {
      showAlert(data.error || "Erro ao calcular porções.", "danger");
    }
  } catch (error) {
    console.error("Error calculating portions:", error);
    showAlert(
      "Erro ao calcular porções. Por favor, tente novamente.",
      "danger"
    );
  } finally {
    submitBtn.innerHTML = originalContent;
    submitBtn.disabled = false;
  }
}

// Display calculation results with animation
function displayResults(portions) {
  const resultsDiv = document.getElementById("results");
  const resultsBody = document.getElementById("resultsBody");

  // Clear previous results
  resultsBody.innerHTML = "";
  let totals = {
    calories: 0,
    proteins: 0,
    carbs: 0,
    fats: 0,
  };

  // Add new results with animation
  portions.forEach((portion, index) => {
    const food = selectedFoods.get(portion.food_code);
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${food.code}</td>
      <td>${portion.quantity.toFixed(1)}g</td>
      <td>${portion.calories.toFixed(1)}</td>
      <td>${portion.proteins.toFixed(1)}</td>
      <td>${portion.carbs.toFixed(1)}</td>
      <td>${portion.fats.toFixed(1)}</td>
    `;

    // Animate row entry
    row.style.opacity = "0";
    row.style.transform = "translateY(-10px)";
    setTimeout(() => {
      row.style.transition = "all 0.3s ease-out";
      row.style.opacity = "1";
      row.style.transform = "translateY(0)";
    }, index * 100);

    resultsBody.appendChild(row);

    // Add to totals
    totals.calories += portion.calories;
    totals.proteins += portion.proteins;
    totals.carbs += portion.carbs;
    totals.fats += portion.fats;
  });

  // Update totals with animation
  animateValue("totalCalories", totals.calories);
  animateValue("totalProteins", totals.proteins);
  animateValue("totalCarbs", totals.carbs);
  animateValue("totalFats", totals.fats);

  // Calculate and update ratios
  const userWeight = parseFloat(document.getElementById("userWeight").value);
  if (userWeight > 0) {
    animateValue("ratioCalories", totals.calories / userWeight);
    animateValue("ratioProteins", totals.proteins / userWeight);
    animateValue("ratioCarbs", totals.carbs / userWeight);
    animateValue("ratioFats", totals.fats / userWeight);
  }

  // Show results section with animation
  resultsDiv.style.opacity = "0";
  resultsDiv.classList.remove("d-none");
  setTimeout(() => {
    resultsDiv.style.transition = "opacity 0.5s ease-out";
    resultsDiv.style.opacity = "1";
  }, 100);
}

// Animate number value change
function animateValue(elementId, value) {
  const element = document.getElementById(elementId);
  const start = parseFloat(element.textContent);
  const duration = 500;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    const current = start + (value - start) * progress;
    element.textContent = current.toFixed(2);

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}

// Show alert message
function showAlert(message, type) {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  // Insert alert at the top of the form
  const form = document.getElementById("calculatorForm");
  form.parentNode.insertBefore(alertDiv, form);

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    alertDiv.classList.remove("show");
    setTimeout(() => alertDiv.remove(), 150);
  }, 5000);
}

// Form submission handler
document
  .getElementById("calculatorForm")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    calculatePortions();
  });

// Close search results when clicking outside
document.addEventListener("click", function (e) {
  if (!e.target.classList.contains("food-code")) {
    document.querySelectorAll(".search-results").forEach((div) => {
      div.style.transition = "opacity 0.2s ease-out";
      div.style.opacity = "0";
      setTimeout(() => {
        div.classList.add("d-none");
        div.style.opacity = "1";
      }, 200);
    });
  }
});

// Import user goals with animation
function importUserGoals() {
  const fields = [
    { id: "targetCalories", goal: "userCaloriesGoal" },
    { id: "targetProteins", goal: "userProteinsGoal" },
    { id: "targetCarbs", goal: "userCarbsGoal" },
    { id: "targetFats", goal: "userFatsGoal" },
  ];

  fields.forEach(({ id, goal }) => {
    const input = document.getElementById(id);
    const value = parseFloat(document.getElementById(goal).value) || 0;

    // Animate input
    input.style.transition = "all 0.3s ease-out";
    input.style.backgroundColor = "rgba(180, 217, 87, 0.1)";
    input.value = value;

    setTimeout(() => {
      input.style.backgroundColor = "";
    }, 500);
  });

  showAlert("Metas importadas com sucesso!", "success");
}
