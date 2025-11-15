// dashboard.js

function toggleMealSection(mealType) {
  const content = document.getElementById(`${mealType}-content`);
  const btn = content.closest(".card").querySelector(".expand-btn i");

  if (content.style.display === "none") {
    content.style.display = "block";
    btn.classList.remove("fa-chevron-down");
    btn.classList.add("fa-chevron-up");
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

function expandAllSections() {
  Object.keys(MEAL_TYPES).forEach((mealType) => {
    const content = document.getElementById(`${mealType}-content`);
    const btn = content.closest(".card").querySelector(".expand-btn i");
    const tbody = document.getElementById(`${mealType}-foods`);

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
      content.style.opacity = "1";
      content.style.transform = "translateY(0)";
    }
  });
}

function initializeDashboardEvents() {
  document.addEventListener("click", (event) => {
    if (!event.target.classList.contains("food-code")) {
      const results = document.querySelectorAll(".search-results");
      results.forEach((result) => result.classList.add("d-none"));
    }

    if (
      !event.target.closest("#dietName") &&
      !event.target.closest("#dietSuggestions")
    ) {
      document.getElementById("dietSuggestions")?.classList.add("d-none");
    }
  });

  // Adiciona listener para o formulário de salvar dieta
  const saveDietForm = document.getElementById("saveDietForm");
  if (saveDietForm) {
    saveDietForm.addEventListener("submit", (event) => {
      event.preventDefault();
      saveDiet();
    });
  }

  // Adiciona listener para o formulário de salvar no diário
  const saveDailyDietForm = document.getElementById("saveDailyDietForm");
  if (saveDailyDietForm) {
    saveDailyDietForm.addEventListener("submit", (event) => {
      event.preventDefault();
      saveDailyDiet();
    });
  }

  // Adiciona listener para Enter no campo de nome do diário
  const dailyDietNameInput = document.getElementById("dailyDietName");
  if (dailyDietNameInput) {
    dailyDietNameInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        const saveDailyDietModal = document.getElementById("saveDailyDietModal");
        if (saveDailyDietModal && saveDailyDietModal.classList.contains("show")) {
          saveDailyDiet();
        }
      }
    });
  }

  const dietNameInput = document.getElementById("dietName");
  if (dietNameInput) {
    dietNameInput.addEventListener("input", () =>
      Diet.showSuggestions(dietNameInput)
    );
    dietNameInput.addEventListener("focus", () =>
      Diet.showSuggestions(dietNameInput)
    );

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
              const next = activeItem.nextElementSibling;
              if (next) {
                activeItem.classList.remove("active");
                next.classList.add("active");
              }
            }
          }
          break;

        case "ArrowUp":
          event.preventDefault();
          if (!suggestions.classList.contains("d-none")) {
            if (activeItem) {
              const prev = activeItem.previousElementSibling;
              if (prev) {
                activeItem.classList.remove("active");
                prev.classList.add("active");
              }
            }
          }
          break;

        case "Enter":
          if (!suggestions.classList.contains("d-none") && activeItem) {
            event.preventDefault();
            Diet.selectSuggestion(
              activeItem.textContent.trim(),
              activeItem.dataset.id
            );
          } else {
            // Se não há sugestão ativa, salva a dieta
            event.preventDefault();
            const saveDietModal = document.getElementById("saveDietModal");
            if (saveDietModal && saveDietModal.classList.contains("show")) {
              saveDiet();
            }
          }
          break;

        case "Escape":
          suggestions.classList.add("d-none");
          break;
      }
    });
  }
}

function initDashboard() {
  expandAllSections();
  initializeDashboardEvents();
  Object.keys(MEAL_TYPES).forEach((mealType) =>
    Totals.updateMealTotals(mealType)
  );
  Totals.updateDailyTotals();
}

async function exportToExcel() {
  try {
    // Collect all meal data
    const mealsData = collectMealsData();

    // Get the selected date from the date input, or use today
    const dateInput = document.getElementById('dietDate');
    const selectedDate = dateInput ? dateInput.value : new Date().toISOString().split("T")[0];
    const filename = `dieta_${selectedDate}.xlsx`;

    // Make API call to get the Excel file
    const response = await fetch("/api/export_diet", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        meals_data: mealsData,
        date: selectedDate
      }),
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

function loadMealTemplates(mealType) {
  var container = document.getElementById("meal-templates-" + mealType);
  if (!container) return;

  var request = new XMLHttpRequest();
  request.open("GET", "/api/meal_templates?meal_type=" + mealType, true);

  request.onload = function () {
    if (request.status >= 200 && request.status < 400) {
      var data = JSON.parse(request.responseText);

      if (!data.success) {
        showAlert("Erro ao carregar templates de refeições", "danger");
        return;
      }

      container.innerHTML = "";

      data.templates.forEach(function (template) {
        var mealsData = template.meals_data || [];
        var foodNames = mealsData
          .map(function (food) {
            return food.food_code;
          })
          .join(", ");

        var listItem = document.createElement("div");
        listItem.className = "list-group-item";

        var itemText = mealsData.length > 1 ? " itens" : " item";

        // Criar elementos separadamente para melhor controle
        var mainDiv = document.createElement("div");
        mainDiv.className = "d-flex justify-content-between align-items-center";

        var leftDiv = document.createElement("div");
        leftDiv.className = "flex-grow-1";
        leftDiv.style.cursor = "pointer";
        leftDiv.onclick = function () {
          Food.addMealTemplate(mealType, template.id);
        };

        var title = document.createElement("h6");
        title.className = "mb-1";
        title.textContent = template.name;

        var description = document.createElement("small");
        description.className = "text-muted";
        description.textContent = foodNames;

        leftDiv.appendChild(title);
        leftDiv.appendChild(description);

        var rightDiv = document.createElement("div");
        rightDiv.className = "d-flex align-items-center";
        rightDiv.style.gap = "8px";

        var badge = document.createElement("span");
        badge.className = "badge bg-primary rounded-pill";
        badge.textContent = mealsData.length + itemText;

        var deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.className = "btn btn-sm btn-danger";
        deleteBtn.style.marginLeft = "8px";
        deleteBtn.style.flexShrink = "0";
        deleteBtn.title = "Excluir refeição";
        deleteBtn.onclick = function (e) {
          e.stopPropagation();
          e.preventDefault();
          Food.deleteMealTemplate(mealType, template.id);
        };

        var icon = document.createElement("i");
        icon.className = "fas fa-trash";
        deleteBtn.appendChild(icon);

        rightDiv.appendChild(badge);
        rightDiv.appendChild(deleteBtn);

        mainDiv.appendChild(leftDiv);
        mainDiv.appendChild(rightDiv);

        listItem.appendChild(mainDiv);
        container.appendChild(listItem);
      });
    }
  };

  request.send();
}

document.addEventListener("DOMContentLoaded", initDashboard);

window.Dashboard = {
  toggleMealSection,
  expandAllSections,
  initializeDashboardEvents,
  initDashboard,
  exportToExcel,
  loadMealTemplates,
};

async function sendChatbotMessage() {
  const userMessage = document.getElementById("chatInput").value;
  const response = await fetch("/api/chatbot", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: userMessage }),
  });
  const data = await response.json();
  document.getElementById("chatOutput").textContent = data.response;
}
