// Store selected foods data
let selectedFoods = new Map();

// Add a new food item input
function addFoodItem() {
  const templateItem = document.querySelector(".food-item");
  if (!templateItem) {
    console.error("Não achei nenhum .food-item para clonar");
    return;
  }
  const foodItem = templateItem.cloneNode(true);

  // Clear the inputs in the cloned item
  foodItem.querySelector(".food-code").value = "";
  foodItem.querySelector(".food-min").value = "";
  foodItem.querySelector(".food-max").value = "";

  // Clear and hide previous search results in the clone
  const searchResults = foodItem.querySelector(".search-results");
  if (searchResults) {
    searchResults.classList.add("d-none");
    searchResults.innerHTML = "";
  }

  const foodsList = document.getElementById("foodsList");
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
  const foodCode = foodItem.querySelector(".food-code").value;

  // Remove from selectedFoods if it exists
  if (foodCode) {
    selectedFoods.delete(foodCode);
  }

  const allItems = document.querySelectorAll(".food-item");
  if (allItems.length > 1) {
    // Animate removal
    foodItem.style.transition = "all 0.3s ease-out";
    foodItem.style.opacity = "0";
    foodItem.style.transform = "translateY(-10px)";
    setTimeout(() => {
      foodItem.remove();
    }, 300);
  } else {
    // If it's the last item, just clear the inputs
    foodItem.querySelector(".food-code").value = "";
    foodItem.querySelector(".food-min").value = "";
    foodItem.querySelector(".food-max").value = "";
    // Also clear any search-results
    const results = foodItem.querySelector(".search-results");
    if (results) {
      results.classList.add("d-none");
      results.innerHTML = "";
    }
    // Clear from selectedFoods
    selectedFoods.clear();
  }
}

// Search for foods with improved feedback
function searchFood(input) {
  const group = input.closest(".input-group");
  const searchResults = group ? group.querySelector(".search-results") : null;
  if (!searchResults) {
    console.error("Não achei .search-results relativo a esse input");
    return;
  }

  const query = input.value.trim();
  if (query.length < 2) {
    searchResults.classList.add("d-none");
    return;
  }

  fetch(`/api/search_food?query=${encodeURIComponent(query)}`)
    .then((response) => response.json())
    .then((data) => {
      searchResults.innerHTML = "";
      if (Array.isArray(data) && data.length > 0) {
        data.forEach((food) => {
          const div = document.createElement("div");
          div.className = "p-2 border-bottom";
          div.style.cursor = "pointer";
          div.textContent = food.food_code;
          div.onclick = () => {
            input.value = food.food_code;
            searchResults.classList.add("d-none");

            fetch(`/api/food_nutrition/${food.food_code}`)
              .then((res) => res.json())
              .then((foodData) => {
                if (foodData.success) {
                  selectedFoods.set(food.food_code, {
                    code: food.food_code,
                    calories: foodData.calories,
                    proteins: foodData.proteins,
                    carbs: foodData.carbs,
                    fats: foodData.fats,
                    quantity: foodData.quantity,
                    min: null,
                    max: null,
                  });
                } else {
                  showAlert(
                    foodData.error || "Erro no retorno da API",
                    "danger"
                  );
                }
              })
              .catch((err) => {
                console.error("Error fetching food details:", err);
                showAlert("Erro ao buscar detalhes do alimento", "danger");
              });
          };
          searchResults.appendChild(div);
        });
        searchResults.classList.remove("d-none");
      } else {
        searchResults.classList.add("d-none");
      }
    })
    .catch((err) => {
      console.error("Error:", err);
      searchResults.classList.add("d-none");
    });
}

// Update tolerance value display
function updateToleranceValue(value) {
  document.getElementById("toleranceValue").textContent = value + "%";
}

// Calculate portions with improved feedback
async function calculatePortions() {
  // Verificar alimentos selecionados nos inputs atuais
  const currentFoods = new Set();
  document.querySelectorAll(".food-item").forEach((item) => {
    const code = item.querySelector(".food-code").value;
    if (code) {
      currentFoods.add(code);
    }
  });

  // Limpar alimentos que não estão mais nos inputs
  for (const code of selectedFoods.keys()) {
    if (!currentFoods.has(code)) {
      selectedFoods.delete(code);
    }
  }

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

  // Atualizar limites min/max para os alimentos
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

  // Limpar resultados anteriores
  clearResults();

  const submitBtn = document.querySelector('button[type="submit"]');
  const originalContent = submitBtn.innerHTML;
  submitBtn.innerHTML =
    '<i class="fas fa-spinner fa-spin me-2"></i>Calculando...';
  submitBtn.disabled = true;

  try {
    const res = await fetch("/api/calculate_portions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        targets,
        tolerance,
        foods: Array.from(selectedFoods.values()).map((f) => ({
          code: f.code,
          min: f.min,
          max: f.max,
        })),
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      if (res.status === 400) {
        showAlert(
          data.error ||
            "Não foi possível encontrar uma solução com as restrições fornecidas. Tente aumentar a tolerância ou ajustar os limites dos alimentos.",
          "warning"
        );
      } else {
        showAlert(data.error || "Erro ao calcular porções.", "danger");
      }
      return;
    }

    if (data.success) {
      displayResults(data.portions);
      showAlert("Cálculo realizado com sucesso!", "success");
    } else {
      showAlert(data.error || "Erro ao calcular porções.", "danger");
    }
  } catch (err) {
    console.error("Error calculating portions:", err);
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
  if (!resultsDiv || !resultsBody) {
    console.error("Results elements not found");
    return;
  }

  resultsBody.innerHTML = "";
  let totals = { calories: 0, proteins: 0, carbs: 0, fats: 0 };

  portions.forEach((portion, i) => {
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

    row.style.opacity = "0";
    row.style.transform = "translateY(-10px)";
    setTimeout(() => {
      row.style.transition = "all 0.3s ease-out";
      row.style.opacity = "1";
      row.style.transform = "translateY(0)";
    }, i * 100);

    resultsBody.appendChild(row);
    totals.calories += portion.calories;
    totals.proteins += portion.proteins;
    totals.carbs += portion.carbs;
    totals.fats += portion.fats;
  });

  // Update totals
  animateValue("totalCalories", totals.calories);
  animateValue("totalProteins", totals.proteins);
  animateValue("totalCarbs", totals.carbs);
  animateValue("totalFats", totals.fats);

  // Calculate and update ratios if weight is available
  const userWeight = parseFloat(
    document.getElementById("userWeight")?.value || 0
  );
  if (userWeight > 0) {
    const ratioCalories = document.getElementById("ratioCalories");
    const ratioProteins = document.getElementById("ratioProteins");
    const ratioCarbs = document.getElementById("ratioCarbs");
    const ratioFats = document.getElementById("ratioFats");

    if (ratioCalories)
      animateValue("ratioCalories", totals.calories / userWeight);
    if (ratioProteins)
      animateValue("ratioProteins", totals.proteins / userWeight);
    if (ratioCarbs) animateValue("ratioCarbs", totals.carbs / userWeight);
    if (ratioFats) animateValue("ratioFats", totals.fats / userWeight);
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
  const el = document.getElementById(elementId);
  if (!el) {
    console.warn(`Element with id ${elementId} not found`);
    return;
  }

  const start = parseFloat(el.textContent) || 0;
  const duration = 500;
  const t0 = performance.now();

  function tick(t1) {
    const p = Math.min((t1 - t0) / duration, 1);
    el.textContent = (start + (value - start) * p).toFixed(2);
    if (p < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

// Show alert message
function showAlert(message, type) {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  const form = document.getElementById("calculatorForm");
  form?.parentNode.insertBefore(alertDiv, form);
  setTimeout(() => {
    alertDiv.classList.remove("show");
    setTimeout(() => alertDiv.remove(), 150);
  }, 5000);
}

// Form submission handler
document.getElementById("calculatorForm")?.addEventListener("submit", (e) => {
  e.preventDefault();
  calculatePortions();
});

// Close search results when clicking outside
document.addEventListener("click", (e) => {
  if (
    !e.target.closest(".search-results") &&
    !e.target.classList.contains("food-code")
  ) {
    document
      .querySelectorAll(".search-results")
      .forEach((div) => div.classList.add("d-none"));
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
    input.style.transition = "all 0.3s ease-out";
    input.style.backgroundColor = "rgba(180, 217, 87, 0.1)";
    input.value = value;
    setTimeout(() => {
      input.style.backgroundColor = "";
    }, 500);
  });
  // showAlert("Metas importadas com sucesso!", "success");
}

// Função para limpar os resultados
function clearResults() {
  const resultsDiv = document.getElementById("results");
  const resultsBody = document.getElementById("resultsBody");

  if (resultsDiv) {
    resultsDiv.classList.add("d-none");
  }

  if (resultsBody) {
    resultsBody.innerHTML = "";
  }

  // Limpar totais
  [
    "totalCalories",
    "totalProteins",
    "totalCarbs",
    "totalFats",
    "ratioCalories",
    "ratioProteins",
    "ratioCarbs",
    "ratioFats",
  ].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.textContent = "0";
  });
}

// Import complement values from dashboard
function importComplement() {
  // Get the parent window (dashboard) values
  const parentWindow = window.parent;
  if (!parentWindow || parentWindow === window) {
    console.warn("Não estamos em um iframe do dashboard");
    return;
  }

  try {
    // Get user goals from dashboard
    const userGoals = {
      calories:
        parseFloat(
          parentWindow.document
            .querySelector(".progress-wrapper .d-flex span:last-child")
            ?.textContent.split("/")[1]
            .split("kcal")[0]
            .trim()
        ) || 0,
      proteins:
        parseFloat(
          parentWindow.document
            .querySelector("#user-goals-proteins")
            ?.textContent.trim()
        ) || 0,
      carbs:
        parseFloat(
          parentWindow.document
            .querySelector("#user-goals-carbs")
            ?.textContent.trim()
        ) || 0,
      fats:
        parseFloat(
          parentWindow.document
            .querySelector("#user-goals-fats")
            ?.textContent.trim()
        ) || 0,
    };

    // Get daily totals from dashboard
    const dailyTotals = {
      calories:
        parseFloat(
          parentWindow.document
            .querySelector(".progress-wrapper .d-flex span:last-child")
            ?.textContent.split("/")[0]
            .trim()
        ) || 0,
      proteins: 0,
      carbs: 0,
      fats: 0,
    };

    // Get all meal sections and sum their totals
    parentWindow.document.querySelectorAll(".card").forEach((card) => {
      const totalsRow = card.querySelector("tfoot tr.table-secondary");
      if (totalsRow) {
        const cells = totalsRow.querySelectorAll("td");
        if (cells.length >= 6) {
          dailyTotals.proteins += parseFloat(cells[3].textContent) || 0;
          dailyTotals.carbs += parseFloat(cells[4].textContent) || 0;
          dailyTotals.fats += parseFloat(cells[5].textContent) || 0;
        }
      }
    });

    console.log("Metas:", userGoals);
    console.log("Totais:", dailyTotals);

    // Calculate remaining values
    const remaining = {
      calories: Math.max(
        0,
        Math.round(userGoals.calories - dailyTotals.calories)
      ),
      proteins: Math.max(
        0,
        Math.round(userGoals.proteins - dailyTotals.proteins)
      ),
      carbs: Math.max(0, Math.round(userGoals.carbs - dailyTotals.carbs)),
      fats: Math.max(0, Math.round(userGoals.fats - dailyTotals.fats)),
    };

    console.log("Restantes:", remaining);

    // Update input fields with animation
    const fields = [
      { id: "targetCalories", value: remaining.calories },
      { id: "targetProteins", value: remaining.proteins },
      { id: "targetCarbs", value: remaining.carbs },
      { id: "targetFats", value: remaining.fats },
    ];

    fields.forEach(({ id, value }) => {
      const input = document.getElementById(id);
      if (input) {
        input.style.transition = "all 0.3s ease-out";
        input.style.backgroundColor = "rgba(180, 217, 87, 0.1)";
        input.value = value;

        setTimeout(() => {
          input.style.backgroundColor = "";
        }, 500);
      }
    });

    // showAlert("Valores de complemento atualizados!", "success");
  } catch (error) {
    console.error("Erro ao importar valores:", error);
    showAlert("Erro ao atualizar valores de complemento", "danger");
  }
}

// Import meals to dashboard's supper section
function importMealsToDashboard() {
  const parentWindow = window.parent;
  const selectedMeal =
    document.getElementById("mealTargetSelect")?.value || "ceia";

  try {
    const portions = [];
    document.querySelectorAll("#resultsBody tr").forEach((row) => {
      const cells = row.querySelectorAll("td");
      if (cells.length >= 6) {
        portions.push({
          food_code: cells[0].textContent.trim(),
          quantity: parseFloat(cells[1].textContent),
          meal_type: selectedMeal,
          nutrition: {
            calories: parseFloat(cells[2].textContent),
            proteins: parseFloat(cells[3].textContent),
            carbs: parseFloat(cells[4].textContent),
            fats: parseFloat(cells[5].textContent),
          },
        });
      }
    });

    if (portions.length === 0) {
      showAlert("Nenhuma refeição para importar", "warning");
      return;
    }

    Promise.all(
      portions.map((portion) =>
        fetch("/api/add_food", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(portion),
        }).then(async (res) => {
          const data = await res.json();
          if (!res.ok) throw new Error(data.error);
          return { ...data.food, nutrition: portion.nutrition };
        })
      )
    )
      .then((results) => {
        const section = parentWindow.document.getElementById(
          `${selectedMeal}-foods`
        );
        const template =
          parentWindow.document.getElementById("food-row-template");

        results.forEach((food) => {
          const row = template.content.cloneNode(true).querySelector("tr");
          row.id = `food-${food.id}`;
          const cells = row.querySelectorAll("td");
          cells[0].innerHTML = food.food_code;
          cells[1].innerHTML = `${food.quantity}g`;
          cells[2].textContent = food.nutrition.calories.toFixed(1);
          cells[3].textContent = food.nutrition.proteins.toFixed(1);
          cells[4].textContent = food.nutrition.carbs.toFixed(1);
          cells[5].textContent = food.nutrition.fats.toFixed(1);
          const actions = cells[6].querySelector(".action-buttons");
          actions.innerHTML = `
          <button class="btn btn-primary btn-sm" onclick="editFoodRow(this)" title="Editar">
            <i class="fas fa-edit"></i>
          </button>
          <button class="btn btn-danger" onclick="deleteFood(${food.id})" title="Remover">
            <i class="fas fa-trash"></i>
          </button>`;
          section.appendChild(row);
        });

        const card = section.closest(".card");
        if (card && typeof parentWindow.updateMealTotals === "function") {
          parentWindow.updateMealTotals(selectedMeal);
        }
        if (typeof parentWindow.updateDailyTotals === "function") {
          parentWindow.updateDailyTotals();
        }

        parentWindow.document
          .querySelector("#calculatorModal .btn-close")
          ?.click();
        showAlert("Refeições importadas com sucesso!", "success");
      })
      .catch((err) => {
        console.error(err);
        showAlert("Erro ao importar refeições: " + err.message, "danger");
      });
  } catch (error) {
    console.error(error);
    showAlert("Erro inesperado ao importar refeições", "danger");
  }
}
function showMealSelect() {
  document.getElementById("importInitialBtn").classList.add("d-none");
  document.getElementById("mealSelectContainer").classList.remove("d-none");
}
function openMealSelectModal() {
  const modal = new bootstrap.Modal(document.getElementById("mealSelectModal"));
  modal.show();
}

function confirmImport(mealType) {
  const modalEl = document.getElementById("mealSelectModal");
  const modal = bootstrap.Modal.getInstance(modalEl);
  if (modal) modal.hide();

  // Criar dinamicamente o select no DOM para reutilizar função já existente
  const select = document.createElement("select");
  select.id = "mealTargetSelect";
  select.innerHTML = `<option value="${mealType}" selected>${mealType}</option>`;
  document.body.appendChild(select);

  // Executa importação usando a função existente
  importMealsToDashboard();

  // Remove seletor temporário
  setTimeout(() => select.remove(), 1000);
}
