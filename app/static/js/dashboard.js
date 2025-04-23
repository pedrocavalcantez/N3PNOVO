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

document.addEventListener("DOMContentLoaded", initDashboard);

window.Dashboard = {
  toggleMealSection,
  expandAllSections,
  initializeDashboardEvents,
  initDashboard,
};
