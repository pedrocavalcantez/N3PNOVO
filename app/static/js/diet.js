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
            const foodCode = cells[0].textContent.trim();
            const quantity = cells[1].textContent.trim();
            return foodCode && quantity;
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
      alert("Por favor, insira um nome para a dieta modelo");
      return;
    }
    
    const mealsData = collectMealsData();
    const url = existingDietId
      ? `/api/save_diet?diet_id=${existingDietId}`
      : "/api/save_diet";

    const response = await makeDietApiCall(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        name: dietName, 
        meals_data: mealsData
        // Não envia date - será NULL (dieta modelo)
      }),
    });

    closeModal("saveDietModal");
    alert(response.message || "Dieta modelo salva com sucesso!");
  } catch (error) {
    alert("Erro ao salvar dieta modelo: " + error.message);
  }
}

async function saveDailyDiet() {
  try {
    const dietNameInput = document.getElementById("dailyDietName");
    const dietName = dietNameInput ? dietNameInput.value.trim() : "Registro do Dia";
    
    if (!dietName) {
      alert("Por favor, insira um nome para o registro no diário");
      return;
    }
    
    // Obtém a data selecionada
    const dateInput = document.getElementById("dietDate");
    if (!dateInput || !dateInput.value) {
      alert("Por favor, selecione uma data");
      return;
    }
    const dietDate = dateInput.value;
    
    const mealsData = collectMealsData();
    const url = "/api/save_daily_diet";

    const response = await makeDietApiCall(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        name: dietName, 
        meals_data: mealsData,
        date: dietDate
      }),
    });

    closeModal("saveDailyDietModal");
    alert(response.message || "Registro salvo no diário com sucesso!");
    
    // NÃO recarrega automaticamente - mantém os alimentos na tela
    // Apenas atualiza os totais se necessário
    Object.keys(MEAL_TYPES).forEach((mealType) => {
      if (typeof Food !== 'undefined' && Food.updateTotalsFor) {
        Food.updateTotalsFor(mealType);
      }
    });
  } catch (error) {
    alert("Erro ao salvar no diário: " + error.message);
  }
}

async function loadDietByDate(dateStr) {
  try {
    if (!dateStr) {
      console.warn("Data não fornecida para carregar diário");
      clearAllTables();
      Object.keys(MEAL_TYPES).forEach((mealType) => {
        Food.updateTotalsFor(mealType);
      });
      return;
    }

    const data = await makeDietApiCall(`/api/load_diet_by_date?date=${dateStr}`);
    
    // Limpa as tabelas primeiro
    clearAllTables();
    
    if (data.success && data.meals_data) {
      // Garante que todas as seções estão visíveis no DOM
      Object.keys(MEAL_TYPES).forEach((mealType) => {
        const content = document.getElementById(`${mealType}-content`);
        if (content) {
          const btn = content.closest(".card")?.querySelector(".expand-btn i");
          if (content.style.display === "none") {
            content.style.display = "block";
            if (btn) {
              btn.classList.remove("fa-chevron-down");
              btn.classList.add("fa-chevron-up");
            }
            content.style.opacity = "1";
          }
        }
      });

      // Carrega os alimentos de cada refeição
      Object.keys(data.meals_data).forEach((mealType) => {
        const foods = data.meals_data[mealType] || [];
        foods.forEach((food) => {
          const foodObj = new Food(food, mealType);
          const row = foodObj.setupRow(true);
          const table = document.querySelector(`#${mealType}-foods tbody`);
          if (table) {
            table.appendChild(row);
          }
        });
      });
    }
    // Se não houver diário para esta data (data.success === false ou sem meals_data),
    // as tabelas já foram limpas acima, então apenas atualiza os totais

    // Atualiza os totais
    Object.keys(MEAL_TYPES).forEach((mealType) => {
      Food.updateTotalsFor(mealType);
    });

    // Atualiza a data selecionada
    const dateInput = document.getElementById("dietDate");
    if (dateInput) {
      dateInput.value = dateStr;
    }
  } catch (error) {
    console.error("Erro ao carregar diário:", error);
    // Se houver erro, limpa as tabelas
    clearAllTables();
    Object.keys(MEAL_TYPES).forEach((mealType) => {
      Food.updateTotalsFor(mealType);
    });
  }
}

async function loadDiet(dietId) {
  try {
    const data = await makeDietApiCall(`/api/load_diet/${dietId}`);
    clearAllTables();

    // Garante que todas as seções estão visíveis no DOM
    Object.keys(MEAL_TYPES).forEach((mealType) => {
      const content = document.getElementById(`${mealType}-content`);
      const btn = content.closest(".card").querySelector(".expand-btn i");
      if (content.style.display === "none") {
        content.style.display = "block";
        btn.classList.remove("fa-chevron-down");
        btn.classList.add("fa-chevron-up");
        content.style.opacity = "1";
        content.style.transform = "translateY(0)";
      }
    });

    // Adiciona os alimentos por refeição
    Object.entries(data.meals_data).forEach(([mealType, foods]) => {
      const tbody = document.querySelector(`#${mealType}-foods`);
      if (!tbody) {
        console.warn(`⚠️ Tbody não encontrado para ${mealType}`);
        return;
      }

      foods.forEach((food, index) => {
        try {
          const row = new Food(food, mealType).setupRow(true); // modo de exibição (não editável)
          const totalRow = tbody.querySelector(".table-secondary");
          if (totalRow) {
            tbody.insertBefore(row, totalRow);
          } else {
            tbody.appendChild(row);
          }
        } catch (err) {
          console.error(
            `❌ Erro ao renderizar alimento ${index} em ${mealType}:`,
            food,
            err
          );
        }
      });

      // Atualiza os totais da refeição após todos os alimentos
      updateMealTotals(mealType);
    });

    // Atualiza totais do dia inteiro
    updateDailyTotals();

    // Fecha o modal
    closeModal("loadDietModal");
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

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    const modalInstance = bootstrap.Modal.getInstance(modal);
    if (modalInstance) {
      modalInstance.hide();
    }
  }
}

function clearAllTables() {
  Object.keys(MEAL_TYPES).forEach((mealType) => {
    const tbody = document.querySelector(`#${mealType}-foods`);
    if (tbody) {
      // Remove all rows except the totals row
      const rows = tbody.querySelectorAll("tr:not(.table-secondary)");
      rows.forEach((row) => row.remove());
    }
  });
}

window.Diet = {
  collectMealsData,
  loadDietByDate,
  showSuggestions: showDietSuggestions,
  selectSuggestion: selectDietSuggestion,
  getDietInfo,
  saveDiet,
  saveDailyDiet,
  loadDiet,
  deleteDiet,
};

// Torna saveDailyDiet globalmente acessível
window.saveDailyDiet = saveDailyDiet;
