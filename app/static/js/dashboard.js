// Dashboard JavaScript functionality

// Add new row to meal table
function addNewRow(mealType) {
  const tbody = document.querySelector(`#${mealType}-table tbody`);
  const template = document.getElementById("food-row-template");
  const newRow = template.content.cloneNode(true);

  // Update form action and meal type
  const form = newRow.querySelector("form");
  form.dataset.mealType = mealType;

  // Add event listeners
  const searchInput = newRow.querySelector(".search-input");
  const quantityInput = newRow.querySelector(".quantity-input");
  const saveBtn = newRow.querySelector(".btn-save");
  const removeBtn = newRow.querySelector(".btn-remove");

  searchInput.addEventListener("input", function () {
    searchFood(this);
  });

  quantityInput.addEventListener("input", function () {
    updateNutrition(this);
  });

  saveBtn.addEventListener("click", function () {
    saveFood(this, mealType);
  });

  removeBtn.addEventListener("click", function () {
    this.closest("tr").remove();
  });

  tbody.appendChild(newRow);
}

// Search for food items
function searchFood(input) {
  const query = input.value.trim();
  if (query.length < 2) {
    const results = input.parentElement.querySelector(".search-results");
    if (results) results.remove();
    return;
  }

  fetch(`/search_food?q=${encodeURIComponent(query)}`)
    .then((response) => response.json())
    .then((data) => {
      let results = input.parentElement.querySelector(".search-results");
      if (!results) {
        results = document.createElement("div");
        results.className = "search-results";
        input.parentElement.appendChild(results);
      }

      results.innerHTML = "";
      data.forEach((food) => {
        const div = document.createElement("div");
        div.textContent = food.Alimento;
        div.onclick = () => selectFood(div, food);
        results.appendChild(div);
      });
    })
    .catch((error) => console.error("Error:", error));
}

// Select food from search results
function selectFood(element, food) {
  const row = element.closest("tr");
  const nameInput = row.querySelector(".search-input");
  const quantityInput = row.querySelector(".quantity-input");
  const caloriesInput = row.querySelector(".calories-input");
  const proteinsInput = row.querySelector(".proteins-input");
  const carbsInput = row.querySelector(".carbs-input");
  const fatsInput = row.querySelector(".fats-input");

  nameInput.value = food.Alimento;
  quantityInput.value = food.Porção;
  caloriesInput.value = food.Calorias;
  proteinsInput.value = food.Proteínas;
  carbsInput.value = food.Carboidratos;
  fatsInput.value = food.Gorduras;

  element.parentElement.remove();
}

// Update nutrition values based on quantity
function updateNutrition(input) {
  const row = input.closest("tr");
  const baseQuantity = parseFloat(row.querySelector(".quantity-input").value);
  const caloriesInput = row.querySelector(".calories-input");
  const proteinsInput = row.querySelector(".proteins-input");
  const carbsInput = row.querySelector(".carbs-input");
  const fatsInput = row.querySelector(".fats-input");

  if (baseQuantity > 0) {
    const calories = parseFloat(caloriesInput.value);
    const proteins = parseFloat(proteinsInput.value);
    const carbs = parseFloat(carbsInput.value);
    const fats = parseFloat(fatsInput.value);

    const multiplier = baseQuantity / 100;
    caloriesInput.value = (calories * multiplier).toFixed(1);
    proteinsInput.value = (proteins * multiplier).toFixed(1);
    carbsInput.value = (carbs * multiplier).toFixed(1);
    fatsInput.value = (fats * multiplier).toFixed(1);
  }
}

// Save food entry
function saveFood(button, mealType) {
  const row = button.closest("tr");
  const data = {
    name: row.querySelector(".search-input").value,
    quantity: parseFloat(row.querySelector(".quantity-input").value),
    calories: parseFloat(row.querySelector(".calories-input").value),
    proteins: parseFloat(row.querySelector(".proteins-input").value),
    carbs: parseFloat(row.querySelector(".carbs-input").value),
    fats: parseFloat(row.querySelector(".fats-input").value),
    meal_type: mealType,
  };

  fetch("/add_food", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        alert("Erro ao salvar alimento: " + data.error);
        return;
      }

      // Update row with saved data
      row.querySelector(".search-input").readOnly = true;
      row.querySelector(".quantity-input").readOnly = true;
      row.querySelector(".calories-input").readOnly = true;
      row.querySelector(".proteins-input").readOnly = true;
      row.querySelector(".carbs-input").readOnly = true;
      row.querySelector(".fats-input").readOnly = true;

      button.textContent = "Remover";
      button.className = "btn btn-danger btn-sm btn-remove";
      button.onclick = () => deleteFood(data.id);

      // Update daily totals
      updateDailyTotals();
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Erro ao salvar alimento. Por favor, tente novamente.");
    });
}

// Delete food entry
function deleteFood(foodId) {
  if (!confirm("Tem certeza que deseja remover este alimento?")) {
    return;
  }

  fetch(`/delete_food/${foodId}`, {
    method: "DELETE",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        alert("Erro ao remover alimento: " + data.error);
        return;
      }

      // Remove row from table
      const row = document.querySelector(`tr[data-food-id="${foodId}"]`);
      if (row) row.remove();

      // Update daily totals
      updateDailyTotals();
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Erro ao remover alimento. Por favor, tente novamente.");
    });
}

// Update daily totals
function updateDailyTotals() {
  fetch("/dashboard")
    .then((response) => response.text())
    .then((html) => {
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");

      // Update progress bars
      const newProgressBars = doc.querySelectorAll(".progress-bar");
      const currentProgressBars = document.querySelectorAll(".progress-bar");

      newProgressBars.forEach((newBar, index) => {
        if (currentProgressBars[index]) {
          currentProgressBars[index].style.width = newBar.style.width;
          currentProgressBars[index].textContent = newBar.textContent;
        }
      });
    })
    .catch((error) => console.error("Error:", error));
}

// Close search results when clicking outside
document.addEventListener("click", function (event) {
  if (!event.target.classList.contains("search-input")) {
    const results = document.querySelectorAll(".search-results");
    results.forEach((result) => result.remove());
  }
});
