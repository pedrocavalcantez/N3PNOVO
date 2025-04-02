// Dashboard JavaScript functionality

// Add new row to meal table
function addNewRow(mealType) {
  const tbody = document.getElementById(`${mealType}-foods`);
  const template = document.getElementById("food-row-template");
  const clone = template.content.cloneNode(true);
  const row = clone.querySelector("tr");

  // Set up food search
  const searchInput = row.querySelector(".food-code");
  searchInput.addEventListener("input", function () {
    searchFood(this);
  });

  // Set up quantity input event
  const quantityInput = row.querySelector(".quantity");
  quantityInput.addEventListener("input", () => updateNutrition(quantityInput));

  // Set up save button
  const saveButton = row.querySelector(".save-food");
  if (document.querySelector(".progress-wrapper")) {
    // Logged-in mode
    saveButton.onclick = () => saveFood(saveButton, mealType);
  } else {
    // Guest mode
    saveButton.onclick = () => saveGuestFood(saveButton);
  }

  // Set up delete button
  const deleteButton = row.querySelector(".btn-danger");
  if (deleteButton) {
    deleteButton.onclick = () => {
      const row = deleteButton.closest("tr");
      if (row.id) {
        // If the row has an ID, it's a saved food entry
        const foodId = row.id.replace("food-", "");
        deleteFood(foodId);
      } else {
        // If the row has no ID, it's an unsaved entry
        row.remove();
        updateDailyTotals();
      }
    };
  }

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
function searchFood(input) {
  const searchResults = input.nextElementSibling;
  const query = input.value.trim();

  if (query.length < 2) {
    searchResults.classList.add("d-none");
    return;
  }
  console.log("Procurando alimento");

  // Make API call to search food
  fetch(`/api/search_food?query=${encodeURIComponent(query)}`)
    .then((response) => response.json())
    .then((data) => {
      searchResults.innerHTML = "";
      data.forEach((food) => {
        const div = document.createElement("div");
        div.className = "p-2 border-bottom";
        div.style.cursor = "pointer";
        div.textContent = `${food.code} - ${food.name}`;
        div.onclick = () => selectFood(input, food);
        searchResults.appendChild(div);
      });
      searchResults.classList.remove("d-none");
    })
    .catch((error) => console.error("Error:", error));
}

// Select food from search results
function selectFood(input, food) {
  input.value = food.code;
  input.nextElementSibling.classList.add("d-none");
  const row = input.closest("tr");
  const quantityInput = row.querySelector(".quantity");
  quantityInput.value = food.qtd;
  quantityInput.dispatchEvent(new Event("input")); // Trigger nutrition update
  quantityInput.focus();
}

// Update nutrition values based on quantity
function updateNutrition(input) {
  const row = input.closest("tr");
  const code = row.querySelector(".food-code").value;
  const quantity = parseFloat(input.value) || 0;

  if (code && quantity >= 0) {
    // Changed to >= 0 to allow zero quantity
    // Make API call to get nutrition values
    fetch(
      `/api/food_nutrition/${encodeURIComponent(code)}?quantity=${quantity}`
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.error) {
          console.error("Error:", data.error);
          return;
        }
        row.querySelector(".calories").textContent = data.calories.toFixed(1);
        row.querySelector(".proteins").textContent = data.proteins.toFixed(1);
        row.querySelector(".carbs").textContent = data.carbs.toFixed(1);
        row.querySelector(".fats").textContent = data.fats.toFixed(1);
        row.querySelector(".save-food").style.display =
          quantity > 0 ? "inline-block" : "none";
      })
      .catch((error) => {
        console.error("Error:", error);
        // Reset values on error
        row.querySelector(".calories").textContent = "0.0";
        row.querySelector(".proteins").textContent = "0.0";
        row.querySelector(".carbs").textContent = "0.0";
        row.querySelector(".fats").textContent = "0.0";
        row.querySelector(".save-food").style.display = "none";
      });
  } else {
    // Reset values when quantity is empty or invalid
    row.querySelector(".calories").textContent = "0.0";
    row.querySelector(".proteins").textContent = "0.0";
    row.querySelector(".carbs").textContent = "0.0";
    row.querySelector(".fats").textContent = "0.0";
    row.querySelector(".save-food").style.display = "none";
  }
}

// Save food entry
function saveFood(button, mealType) {
  const row = button.closest("tr");
  const code = row.querySelector(".food-code").value;
  const quantity = parseFloat(row.querySelector(".quantity").value);

  const data = {
    code: code,
    quantity: quantity,
    meal_type: mealType,
  };

  fetch("/api/add_food", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })
    .then(async (response) => {
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        // Update the row with the returned data
        row.querySelector(".calories").textContent =
          data.food.calories.toFixed(1);
        row.querySelector(".proteins").textContent =
          data.food.proteins.toFixed(1);
        row.querySelector(".carbs").textContent = data.food.carbs.toFixed(1);
        row.querySelector(".fats").textContent = data.food.fats.toFixed(1);

        // Set the row ID using the returned food ID
        row.id = `food-${data.food.id}`;

        // Hide the save button
        button.style.display = "none";

        // Set up delete button with the correct food ID
        const deleteButton = row.querySelector(".btn-danger");
        if (deleteButton) {
          deleteButton.onclick = () => deleteFood(data.food.id);
          deleteButton.style.display = "inline-block";
        }

        // Update totals
        updateDailyTotals();
      } else {
        throw new Error(data.error || "Unknown error occurred");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Erro ao salvar alimento: " + error.message);
      // Keep the save button visible in case of error
      button.style.display = "inline-block";
    });
}

// Delete food entry
function deleteFood(foodId) {
  console.log("Deletando alimento");
  fetch(`/api/delete_food/${foodId}`, {
    method: "DELETE",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        alert("Erro ao remover alimento: " + data.error);
        return;
      }

      console.log("ALOW");
      // Remove row from table using the correct ID selector
      const row = document.getElementById(`food-${foodId}`);
      if (row) {
        row.remove();
        // Update totals after removing the row
        console.log("Removendo alimento");
        updateDailyTotals();
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Erro ao remover alimento. Por favor, tente novamente.");
    });
}

// Save food for guest users
function saveGuestFood(button) {
  const row = button.closest("tr");
  row.classList.remove("food-row");
  row.classList.add("saved-food-row");
  button.style.display = "none";
  // Remove the click handler from the delete button and add the remove handler
  const deleteBtn = row.querySelector(".btn-danger");
  if (deleteBtn) {
    deleteBtn.onclick = () => removeGuestFood(deleteBtn);
  }
  console.log("Salvando alimento");
  updateDailyTotals();
}

// Remove food for guest users
function removeGuestFood(button) {
  const row = button.closest("tr");
  row.remove();
  console.log("Removendo alimento");
  updateDailyTotals();
}

// Update daily totals
function updateDailyTotals() {
  const mealTypes = [
    "cafe_da_manha",
    "lanche_manha",
    "almoco",
    "lanche_tarde",
    "janta",
    "ceia",
  ];

  let totalCalories = 0;
  let totalProteins = 0;
  let totalCarbs = 0;
  let totalFats = 0;

  // Check if we're in guest mode or regular mode
  const isGuestMode = !document.querySelector(".progress-wrapper");

  // Calculate totals for each meal type
  mealTypes.forEach((mealType) => {
    const tbody = document.getElementById(`${mealType}-foods`);
    if (!tbody) return;

    let mealCalories = 0;
    let mealProteins = 0;
    let mealCarbs = 0;
    let mealFats = 0;

    // Get all food rows
    const rows = tbody.querySelectorAll("tr");

    rows.forEach((row) => {
      // Skip total rows and empty template rows
      if (row.classList.contains("table-secondary")) return;

      // Skip rows without calorie information
      const calorieElement = row.querySelector(".calories");
      if (!calorieElement) return;

      // For guest mode, only count saved rows
      if (isGuestMode && !row.classList.contains("saved-food-row")) return;

      const calories = parseFloat(calorieElement.textContent) || 0;
      const proteins =
        parseFloat(row.querySelector(".proteins").textContent) || 0;
      const carbs = parseFloat(row.querySelector(".carbs").textContent) || 0;
      const fats = parseFloat(row.querySelector(".fats").textContent) || 0;

      // Only add if there are actual values
      if (calories > 0) {
        mealCalories += calories;
        mealProteins += proteins;
        mealCarbs += carbs;
        mealFats += fats;
      }
    });

    // Update meal totals in the footer
    const table = tbody.closest("table");
    const tfoot = table.querySelector("tfoot");
    if (tfoot) {
      const totalRow = tfoot.querySelector("tr");
      if (totalRow) {
        totalRow.children[2].textContent = mealCalories.toFixed(1);
        totalRow.children[3].textContent = mealProteins.toFixed(1) + "g";
        totalRow.children[4].textContent = mealCarbs.toFixed(1) + "g";
        totalRow.children[5].textContent = mealFats.toFixed(1) + "g";
      }
    }

    // Add to daily totals
    totalCalories += mealCalories;
    totalProteins += mealProteins;
    totalCarbs += mealCarbs;
    totalFats += mealFats;
  });

  if (isGuestMode) {
    // Guest mode - update the simple summary boxes
    document.getElementById("total-calories").textContent =
      totalCalories.toFixed(1);
    document.getElementById("total-proteins").textContent =
      totalProteins.toFixed(1);
    document.getElementById("total-carbs").textContent = totalCarbs.toFixed(1);
    document.getElementById("total-fats").textContent = totalFats.toFixed(1);
  } else {
    // Regular mode - update the nutrient boxes
    const nutrientBoxes = document.querySelectorAll(".nutrient-box");
    nutrientBoxes.forEach((box) => {
      const valueElement = box.querySelector("p");
      if (valueElement) {
        let value = 0;
        if (box.textContent.includes("Calorias")) value = totalCalories;
        else if (box.textContent.includes("Proteínas")) value = totalProteins;
        else if (box.textContent.includes("Carboidratos")) value = totalCarbs;
        else if (box.textContent.includes("Gorduras")) value = totalFats;
        valueElement.textContent =
          value.toFixed(1) + (box.textContent.includes("Calorias") ? "" : "g");
      }
    });

    // Update progress bar and calories display
    const progressWrapper = document.querySelector(".progress-wrapper");
    if (progressWrapper) {
      // Update calories display
      const caloriesDisplay = progressWrapper.querySelector(
        ".d-flex span:last-child"
      );
      if (caloriesDisplay) {
        const [, total] = caloriesDisplay.textContent.split("/");
        const goalCalories = parseFloat(total) || 0;
        caloriesDisplay.textContent = `${totalCalories.toFixed(
          1
        )} / ${goalCalories.toFixed(1)} kcal`;
      }

      // Update progress bar
      const progressBar = progressWrapper.querySelector(".progress-bar");
      if (progressBar) {
        const goalCalories =
          parseFloat(
            progressWrapper.textContent.match(/\/\s*(\d+(?:\.\d+)?)/)?.[1]
          ) || 0;
        if (goalCalories > 0) {
          const percentage = Math.min(
            100,
            (totalCalories / goalCalories) * 100
          );
          progressBar.style.width = `${percentage}%`;
        }
      }
    }
  }
}

// Close search results when clicking outside
document.addEventListener("click", function (event) {
  if (!event.target.classList.contains("food-code")) {
    const results = document.querySelectorAll(".search-results");
    results.forEach((result) => result.classList.add("d-none"));
  }
});
