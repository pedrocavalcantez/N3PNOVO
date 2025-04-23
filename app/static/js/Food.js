// Food Row Management
class Food {
  // === Construtor e propriedades ===
  constructor(food = null, mealType = null) {
    this.id = food?.id || null;
    this.food_code = food?.food_code || "";
    this.quantity = food?.quantity || 0;
    this.mealType = mealType;
    this.calories = food?.calories || 0;
    this.proteins = food?.proteins || 0;
    this.carbs = food?.carbs || 0;
    this.fats = food?.fats || 0;
  }

  // === Métodos estáticos ===
  static createFoodRow(food = null, mealType = null) {
    const row = new Food(food, mealType).setupRow(false); // força modo inputable
    const tbody = document.getElementById(`${mealType}-foods`);
    const totalRow = tbody.querySelector(".table-secondary");

    if (totalRow) {
      tbody.insertBefore(row, totalRow);
    } else {
      tbody.appendChild(row);
    }
    if (window.untoggleMeals) {
      window.untoggleMeals(mealType);
    }

    return row;
  }
  static async addMealTemplate(mealType, templateId) {
    try {
      const response = await fetch(`/api/meal_templates/${templateId}`);
      const data = await response.json();

      if (!data.success) throw new Error("Erro ao carregar template");

      for (const food of data.template.foods) {
        const foodResponse = await fetch(
          `/api/food_nutrition/${food.food_code}`
        );
        const foodData = await foodResponse.json();

        if (!foodData.success) continue;

        const foodObj = {
          food_code: food.food_code,
          quantity: food.quantity,
          meal_type: mealType,
          nutrition: {
            calories: (foodData.calories * food.quantity) / foodData.quantity,
            proteins: (foodData.proteins * food.quantity) / foodData.quantity,
            carbs: (foodData.carbs * food.quantity) / foodData.quantity,
            fats: (foodData.fats * food.quantity) / foodData.quantity,
          },
        };

        const response2 = await fetch("/api/add_food", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(foodObj),
        });

        const result = await response2.json();
        if (result.success) {
          const section = document.getElementById(`${mealType}-foods`);
          const row = Food.setupFoodRow(
            {
              id: result.food.id,
              food_code: food.food_code,
              quantity: food.quantity,
              calories: foodObj.nutrition.calories,
              proteins: foodObj.nutrition.proteins,
              carbs: foodObj.nutrition.carbs,
              fats: foodObj.nutrition.fats,
            },
            mealType,
            true
          );
          section.appendChild(row);
        }
      }

      updateMealTotals(mealType);
      updateDailyTotals();

      const modal = document.getElementById(`mealTemplateModal-${mealType}`);
      if (modal) bootstrap.Modal.getInstance(modal)?.hide();
    } catch (error) {
      console.error("Erro ao adicionar template:", error);
    }
  }
  static setupFoodRow(food = null, mealType = null, isFromTemplate = false) {
    return new Food(food, mealType).setupRow(isFromTemplate);
  }
  static async saveFood(button) {
    const row = button.closest("tr");
    if (!row) {
      Food.logError(
        new Error("Linha da tabela não encontrada"),
        "Erro ao salvar alimento"
      );
      return;
    }

    const foodCodeInput = row.querySelector(".food-code");
    const quantityInput = row.querySelector(".quantity");
    const code = foodCodeInput?.value?.trim();
    const quantity = parseFloat(quantityInput?.value);
    const mealType = Food.getMealType(row);

    if (!code) {
      Food.logError(
        new Error("Código do alimento é obrigatório"),
        "Erro ao salvar alimento"
      );
      return;
    }

    if (isNaN(quantity) || quantity <= 0) {
      Food.logError(
        new Error("Quantidade inválida"),
        "Erro ao salvar alimento"
      );
      return;
    }

    if (!mealType) {
      Food.logError(
        new Error("Tipo de refeição não identificado"),
        "Erro ao salvar alimento"
      );
      return;
    }

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

      const food = new Food(data.food, mealType);
      const newRow = food.setupRow(true);
      row.replaceWith(newRow);
      Food.updateTotalsFor(newRow);
    } catch (error) {
      Food.logError(error, "Erro ao salvar alimento");
      button.style.display = "inline-block";
    }
  }
  static async searchFood(input) {
    let searchResults = document.querySelector("#global-search-results");
    if (!searchResults) {
      searchResults = document.createElement("div");
      searchResults.id = "global-search-results";
      searchResults.className =
        "search-results position-absolute w-100 bg-white border rounded-bottom shadow-sm";
      document.body.appendChild(searchResults);
    }

    const query = input.value.trim();
    if (query.length < 2) {
      searchResults.classList.add("d-none");
      return;
    }

    const rect = input.getBoundingClientRect();
    searchResults.style.top = `${rect.bottom + window.scrollY}px`;
    searchResults.style.left = `${rect.left + window.scrollX}px`;
    searchResults.style.width = `${rect.width}px`;
    searchResults.style.zIndex = "99999";
    searchResults.innerHTML = "<div class='p-2'>Buscando...</div>";
    searchResults.classList.remove("d-none");

    try {
      const data = await makeDietApiCall(
        `/api/search_food?query=${encodeURIComponent(query)}`
      );
      searchResults.innerHTML = "";
      if (!Array.isArray(data)) throw new Error("Formato de resposta inválido");
      if (data.length === 0) {
        searchResults.innerHTML =
          "<div class='p-2 text-muted'>Nenhum alimento encontrado</div>";
        return;
      }
      data.forEach((food) => {
        const div = document.createElement("div");
        div.className = "search-result p-2 border-bottom";
        div.textContent = food.food_code;
        div.onclick = () => {
          Food.selectFood(input, food);
          searchResults.classList.add("d-none");
        };
        searchResults.appendChild(div);
      });
    } catch (error) {
      Food.logError(error, "Erro ao buscar alimentos");
      searchResults.innerHTML = `<div class='p-2 text-danger'>Erro: ${
        error.message || "Erro desconhecido"
      }</div>`;
    }

    // Evita múltiplos listeners
    document.removeEventListener("click", Food._closeSearchHandler);
    Food._closeSearchHandler = (e) => {
      if (!input.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.classList.add("d-none");
        document.removeEventListener("click", Food._closeSearchHandler);
      }
    };
    document.addEventListener("click", Food._closeSearchHandler);
  }

  static selectFood(input, food) {
    input.value = food.food_code;
    input.nextElementSibling.classList.add("d-none");
    const row = input.closest("tr");
    const quantityInput = row.querySelector(".quantity");
    quantityInput.value = food.qtd;
    quantityInput.dispatchEvent(new Event("input"));
    quantityInput.focus();
  }

  static async updateNutrition(input) {
    const row = input.closest("tr");
    const code = row.querySelector(".food-code");
    const quantity = parseFloat(input.value) || 0;
    if (!row || !code || quantity < 0) return;

    if (code.value) {
      try {
        const data = await makeDietApiCall(
          `/api/food_nutrition/${encodeURIComponent(
            code.value
          )}?quantity=${quantity}`
        );
        new Food().setNutritionalValues(row, data);
        const saveButton = row.querySelector(".save-food");
        if (saveButton)
          saveButton.style.display = quantity > 0 ? "inline-block" : "none";
      } catch (error) {
        Food.logError(error, "Erro ao atualizar valores nutricionais");
        new Food().resetNutritionalValues(row);
        const saveButton = row.querySelector(".save-food");
        if (saveButton) saveButton.style.display = "none";
      }
    }
  }

  static getMealType(row) {
    const tbody = row.closest("tbody");
    return tbody?.id ? tbody.id.replace("-foods", "") : null;
  }
  static extractFoodId(row) {
    const match = row.id?.match(/^food-(\d+)$/);
    return match ? match[1] : null;
  }

  static updateTotalsFor(mealType) {
    if (!mealType) return;
    updateMealTotals(mealType);
    updateDailyTotals();
  }
  static logError(error, context) {
    console.error(`[${context}]`, error);
    handleApiError(error, context);
  }

  static deleteFood(button) {
    const row = button.closest("tr");
    if (!row) return;

    const foodId = Food.extractFoodId(row);
    const mealType = Food.getMealType(row); // ✅ salvar antes de remover

    if (!foodId) {
      row.remove(); // ✅ remove primeiro
      Food.updateTotalsFor(mealType); // ✅ depois atualiza os totais corretamente
      return;
    }

    makeDietApiCall(`/api/delete_food/${foodId}`, { method: "DELETE" })
      .then(() => {
        row.remove(); // ✅ remove primeiro
        Food.updateTotalsFor(mealType); // ✅ depois atualiza
      })
      .catch((error) => Food.logError(error, "Erro ao remover alimento"));
  }

  static editFoodRow(button) {
    const row = button.closest("tr");
    const cells = row.cells;
    const food = new Food(
      {
        id: Food.extractFoodId(row),
        food_code: cells[0].textContent.trim(),
        quantity: parseFloat(cells[1].textContent.replace("g", "")),
        calories: parseFloat(cells[2].textContent),
        proteins: parseFloat(cells[3].textContent.replace("g", "")),
        carbs: parseFloat(cells[4].textContent.replace("g", "")),
        fats: parseFloat(cells[5].textContent.replace("g", "")),
      },
      Food.getMealType(row)
    );

    const editableRow = food.setupRow(false);
    row.replaceWith(editableRow);
  }

  // === Renderização ===
  createRowTemplate(isInputState = false) {
    return `
        <tr id="${this.id ? `food-${this.id}` : ""}">
          <td>
            ${
              isInputState
                ? `
              <div class="input-group">
                <input type="text" class="form-control food-code" value="${this.food_code}" onkeyup="Food.searchFood(this)">
                <div class="search-results d-none position-absolute w-100 bg-white border rounded-bottom shadow-sm" style="z-index: 1000; top: 100%"></div>
              </div>
            `
                : this.food_code
            }
          </td>
          <td>
            ${
              isInputState
                ? `
              <input type="number" class="form-control quantity" value="${this.quantity}" step="1" min="0" style="width: 80px" oninput="Food.updateNutrition(this)">
            `
                : `${this.quantity.toFixed(1)}g`
            }
          </td>
          ${this.createNutritionalCells()}
          <td>
            ${this.createActionButtons(isInputState)}
          </td>
        </tr>
      `;
  }

  createActionButtons(isInputState = false) {
    if (isInputState) {
      return `
          <div class="action-buttons">
            <button class="btn btn-success btn-sm save-food" onclick="Food.saveFood(this)" title="Confirmar">
              <i class="fas fa-check"></i>
            </button>
            <button class="btn btn-danger btn-sm" onclick="Food.deleteFood(this)" title="Remover">
              <i class="fas fa-trash"></i>
            </button>
          </div>
        `;
    }
    return `
        <div class="action-buttons">
          <button class="btn btn-primary btn-sm" onclick="Food.editFoodRow(this)" title="Editar">
            <i class="fas fa-edit"></i>
          </button>
          <button class="btn btn-danger btn-sm" onclick="Food.deleteFood(this)" title="Remover">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      `;
  }

  createNutritionalCells() {
    return `
        <td class="calories">${(this.calories || 0).toFixed(1)}</td>
        <td class="proteins">${(this.proteins || 0).toFixed(1)}g</td>
        <td class="carbs">${(this.carbs || 0).toFixed(1)}g</td>
        <td class="fats">${(this.fats || 0).toFixed(1)}g</td>
      `;
  }

  setupRow(isFromTemplate = false) {
    const wrapper = document.createElement("tbody");
    wrapper.innerHTML = this.createRowTemplate(!isFromTemplate);
    const row = wrapper.firstElementChild;
    if (!isFromTemplate) {
      row
        .querySelector(".food-code")
        ?.addEventListener("input", (e) => Food.searchFood(e.target));
      row
        .querySelector(".quantity")
        ?.addEventListener("input", (e) => Food.updateNutrition(e.target));
    }
    return row;
  }

  // === Utilitários de valor ===
  setNutritionalValues(row, values) {
    this.calories = parseFloat(values.calories) || 0;
    this.proteins = parseFloat(values.proteins) || 0;
    this.carbs = parseFloat(values.carbs) || 0;
    this.fats = parseFloat(values.fats) || 0;
    const elements = {
      calories: row.querySelector(".calories"),
      proteins: row.querySelector(".proteins"),
      carbs: row.querySelector(".carbs"),
      fats: row.querySelector(".fats"),
    };
    if (elements.calories)
      elements.calories.textContent = this.calories.toFixed(1);
    if (elements.proteins)
      elements.proteins.textContent = `${this.proteins.toFixed(1)}g`;
    if (elements.carbs)
      elements.carbs.textContent = `${this.carbs.toFixed(1)}g`;
    if (elements.fats) elements.fats.textContent = `${this.fats.toFixed(1)}g`;
  }

  resetNutritionalValues(row) {
    this.setNutritionalValues(row, {
      calories: 0,
      proteins: 0,
      carbs: 0,
      fats: 0,
    });
  }
}

window.Food = Food;
