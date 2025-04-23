// diet.js

function collectMealsData() {
  const mealsData = {};

  Object.keys(MEAL_TYPES).forEach((mealType) => {
    mealsData[mealType] = Array.from(
      document.querySelectorAll(
        `#${mealType}-foods tr:not(.table-secondary):not(.template-row)`
      )
    )
      .filter((row) => {
        const foodCodeInput = row.querySelector(".food-code");
        const quantityInput = row.querySelector(".quantity");

        if (foodCodeInput && quantityInput) {
          return (
            foodCodeInput.value &&
            foodCodeInput.value.trim() !== "" &&
            quantityInput.value &&
            quantityInput.value.trim() !== ""
          );
        } else {
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
          const cells = row.cells;
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

function showDietSuggestions(input) {
  const value = input.value.toLowerCase().trim();
  const suggestionsDiv = document.getElementById("dietSuggestions");
  const savedDiets = Array.from(
    document.querySelectorAll("#loadDietModal .list-group-item button.btn-link")
  ).map((btn) => ({
    id: btn.getAttribute("onclick").match(/loadDiet\((\d+)\)/)[1],
    name: btn.textContent.trim(),
  }));

  suggestionsDiv.innerHTML = "";

  if (!value) {
    suggestionsDiv.classList.add("d-none");
    return;
  }

  const matches = savedDiets.filter((diet) =>
    diet.name.toLowerCase().includes(value)
  );

  matches.forEach((diet) => {
    const div = document.createElement("div");
    div.className = "diet-suggestion-item";
    div.textContent = diet.name;
    div.dataset.id = diet.id;
    div.onclick = () => selectDietSuggestion(diet.name, diet.id);
    suggestionsDiv.appendChild(div);
  });

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

async function saveDiet() {
  try {
    const { dietName, existingDietId } = getDietInfo();
    if (!dietName) {
      alert("Por favor, insira um nome para a dieta");
      return;
    }
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

async function loadDiet(dietId) {
  try {
    const data = await makeDietApiCall(`/api/load_diet/${dietId}`);
    clearAllTables();

    Object.entries(data.meals_data).forEach(([mealType, foods]) => {
      const tbody = document.querySelector(`#${mealType}-foods`);
      if (tbody) {
        foods.forEach((food) => {
          const row = Food.createFoodRow(food);
          tbody.appendChild(row);
          updateMealTotals(mealType);
        });
      }
    });

    closeModal("loadDietModal");
    updateDailyTotals();
  } catch (error) {
    alert("Erro ao carregar dieta: " + error.message);
  }
}

async function deleteDiet(dietId) {
  if (!confirm("Tem certeza que deseja excluir esta dieta?")) return;
  try {
    await makeDietApiCall(`/api/delete_diet/${dietId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });
    const dietItem = document
      .querySelector(`[onclick="deleteDiet(${dietId})"]`)
      .closest(".list-group-item");
    dietItem.remove();
    const remaining = document.querySelectorAll(".list-group-item");
    if (remaining.length === 0) closeModal("loadDietModal");
    alert("Dieta excluída com sucesso!");
  } catch (error) {
    handleApiError(error, "Erro ao excluir dieta");
  }
}

window.Diet = {
  collectMealsData,
  showDietSuggestions,
  selectDietSuggestion,
  getDietInfo,
  saveDiet,
  loadDiet,
  deleteDiet,
};
