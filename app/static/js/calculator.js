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
      <button type="button" class="btn btn-danger" onclick="removeFoodItem(this)">
        <i class="fas fa-times"></i>
      </button>
      <div class="search-results d-none position-absolute w-100 bg-white border rounded-bottom shadow-sm" style="z-index: 1000; top: 100%"></div>
    </div>
    <small class="text-muted">Deixe min/max vazios para sem limites</small>
  `;
  foodsList.appendChild(foodItem);
}

// Remove a food item
function removeFoodItem(button) {
  const foodItem = button.closest(".food-item");
  const input = foodItem.querySelector(".food-code");
  selectedFoods.delete(input.value);
  foodItem.remove();
}

// Search for foods
async function searchFood(input) {
  const resultsDiv = input.parentElement.querySelector(".search-results");
  const query = input.value.trim();

  if (query.length < 2) {
    resultsDiv.classList.add("d-none");
    return;
  }

  try {
    const response = await fetch(
      `/api/search_food?query=${encodeURIComponent(query)}`
    );
    const data = await response.json();

    resultsDiv.innerHTML = "";
    if (data.length > 0) {
      data.forEach((food) => {
        const div = document.createElement("div");
        div.className = "p-2 border-bottom search-result";
        div.style.cursor = "pointer";
        div.textContent = `${food.food_code}`;
        div.onclick = () => selectFood(input, food);
        resultsDiv.appendChild(div);
      });
      resultsDiv.classList.remove("d-none");
    } else {
      resultsDiv.classList.add("d-none");
    }
  } catch (error) {
    console.error("Error searching foods:", error);
    resultsDiv.classList.add("d-none");
  }
}

// Select a food from search results
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

  input.parentElement.querySelector(".search-results").classList.add("d-none");
}

// Update tolerance value display
function updateToleranceValue(value) {
  document.getElementById("toleranceValue").textContent = `${value}%`;
}

// Calculate portions
async function calculatePortions() {
  if (selectedFoods.size === 0) {
    alert("Por favor, selecione pelo menos um alimento.");
    return;
  }

  // Get target values
  const targets = {
    calories: parseFloat(document.getElementById("targetCalories").value) || 0,
    proteins: parseFloat(document.getElementById("targetProteins").value) || 0,
    carbs: parseFloat(document.getElementById("targetCarbs").value) || 0,
    fats: parseFloat(document.getElementById("targetFats").value) || 0,
  };

  // Get tolerance value
  const tolerance =
    parseFloat(document.getElementById("tolerance").value) / 100;

  // Check if at least one target is set
  if (Object.values(targets).every((v) => v === 0)) {
    alert(
      "Por favor, defina pelo menos um valor desejado (calorias, proteínas, carboidratos ou gorduras)."
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

  // Prepare foods data for calculation
  const foods = Array.from(selectedFoods.values());

  try {
    const response = await fetch("/api/calculate_portions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        targets: targets,
        tolerance: tolerance,
        foods: foods.map((food) => ({
          code: food.code,
          min: food.min,
          max: food.max,
        })),
      }),
    });

    const data = await response.json();
    if (data.success) {
      displayResults(data.portions);
    } else {
      alert(data.error || "Erro ao calcular porções.");
    }
  } catch (error) {
    console.error("Error calculating portions:", error);
    alert("Erro ao calcular porções. Por favor, tente novamente.");
  }
}

// Display calculation results
function displayResults(portions) {
  const resultsDiv = document.getElementById("results");
  const resultsBody = document.getElementById("resultsBody");
  const totalCaloriesSpan = document.getElementById("totalCalories");
  const totalProteinsSpan = document.getElementById("totalProteins");
  const totalCarbsSpan = document.getElementById("totalCarbs");
  const totalFatsSpan = document.getElementById("totalFats");
  const ratioCaloriesSpan = document.getElementById("ratioCalories");
  const ratioProteinsSpan = document.getElementById("ratioProteins");
  const ratioCarbsSpan = document.getElementById("ratioCarbs");
  const ratioFatsSpan = document.getElementById("ratioFats");

  resultsBody.innerHTML = "";
  let totals = {
    calories: 0,
    proteins: 0,
    carbs: 0,
    fats: 0,
  };

  portions.forEach((portion) => {
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
    resultsBody.appendChild(row);

    // Add to totals
    totals.calories += portion.calories;
    totals.proteins += portion.proteins;
    totals.carbs += portion.carbs;
    totals.fats += portion.fats;
  });

  // Update totals display
  totalCaloriesSpan.textContent = totals.calories.toFixed(1);
  totalProteinsSpan.textContent = totals.proteins.toFixed(1);
  totalCarbsSpan.textContent = totals.carbs.toFixed(1);
  totalFatsSpan.textContent = totals.fats.toFixed(1);

  // Get user's weight from hidden input
  const userWeight = parseFloat(document.getElementById("userWeight").value);

  // Calculate and update ratios (per kg of body weight)
  if (userWeight > 0) {
    ratioCaloriesSpan.textContent = (totals.calories / userWeight).toFixed(2);
    ratioProteinsSpan.textContent = (totals.proteins / userWeight).toFixed(2);
    ratioCarbsSpan.textContent = (totals.carbs / userWeight).toFixed(2);
    ratioFatsSpan.textContent = (totals.fats / userWeight).toFixed(2);
  } else {
    ratioCaloriesSpan.textContent = "0";
    ratioProteinsSpan.textContent = "0";
    ratioCarbsSpan.textContent = "0";
    ratioFatsSpan.textContent = "0";
  }

  resultsDiv.classList.remove("d-none");
}

// Handle form submission
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
      div.classList.add("d-none");
    });
  }
});

// Import user goals from hidden inputs
function importUserGoals() {
  // Get goals from hidden inputs
  const caloriesGoal =
    parseFloat(document.getElementById("userCaloriesGoal").value) || 0;
  const proteinsGoal =
    parseFloat(document.getElementById("userProteinsGoal").value) || 0;
  const carbsGoal =
    parseFloat(document.getElementById("userCarbsGoal").value) || 0;
  const fatsGoal =
    parseFloat(document.getElementById("userFatsGoal").value) || 0;

  // Set form values
  document.getElementById("targetCalories").value = caloriesGoal;
  document.getElementById("targetProteins").value = proteinsGoal;
  document.getElementById("targetCarbs").value = carbsGoal;
  document.getElementById("targetFats").value = fatsGoal;
}
