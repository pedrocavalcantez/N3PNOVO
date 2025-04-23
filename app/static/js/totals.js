// totals.js
function isGuestMode() {
  return !document.querySelector(".progress-wrapper");
}
function updateMealTotals(mealType) {
  const tbody = document.getElementById(`${mealType}-foods`);
  if (!tbody) {
    console.warn(`Table body not found for meal type: ${mealType}`);
    return { calories: 0, proteins: 0, carbs: 0, fats: 0 };
  }

  const totals = { calories: 0, proteins: 0, carbs: 0, fats: 0 };

  tbody
    .querySelectorAll("tr:not(.table-secondary):not(.template-row)")
    .forEach((row) => {
      const cells = row.cells;
      if (cells.length >= 6) {
        totals.calories += parseFloat(cells[2].textContent) || 0;
        totals.proteins += parseFloat(cells[3].textContent) || 0;
        totals.carbs += parseFloat(cells[4].textContent) || 0;
        totals.fats += parseFloat(cells[5].textContent) || 0;
      }
    });

  const tfoot = tbody.closest("table")?.querySelector("tfoot");
  const totalRow = tfoot?.querySelector("tr");
  if (totalRow) {
    const cells = totalRow.cells;
    if (cells.length >= 6) {
      const strongs = {
        calories: cells[2].querySelector("strong"),
        proteins: cells[3].querySelector("strong"),
        carbs: cells[4].querySelector("strong"),
        fats: cells[5].querySelector("strong"),
      };
      if (strongs.calories)
        strongs.calories.textContent = totals.calories.toFixed(1);
      if (strongs.proteins)
        strongs.proteins.textContent = totals.proteins.toFixed(1) + "g";
      if (strongs.carbs)
        strongs.carbs.textContent = totals.carbs.toFixed(1) + "g";
      if (strongs.fats) strongs.fats.textContent = totals.fats.toFixed(1) + "g";
    }
  }

  return totals;
}

function updateDailyTotals() {
  const totals = { calories: 0, proteins: 0, carbs: 0, fats: 0 };
  Object.keys(MEAL_TYPES).forEach((mealType) => {
    const mealTotals = updateMealTotals(mealType);
    totals.calories += mealTotals.calories;
    totals.proteins += mealTotals.proteins;
    totals.carbs += mealTotals.carbs;
    totals.fats += mealTotals.fats;
  });
  Totals.updateTotalsDisplay(totals);
  Totals.untoggleMeals(); // ← aqui
}

function updateTotalsDisplay(totals) {
  if (isGuestMode()) {
    document.getElementById("total-calories").textContent =
      totals.calories.toFixed(1);
    document.getElementById("total-proteins").textContent =
      totals.proteins.toFixed(1);
    document.getElementById("total-carbs").textContent =
      totals.carbs.toFixed(1);
    document.getElementById("total-fats").textContent = totals.fats.toFixed(1);
  } else {
    updateNutrientBoxes(totals);
    updateProgressBar(totals.calories);
  }
}

function updateNutrientBoxes(totals) {
  const boxes = document.querySelectorAll(".nutrient-box");
  boxes.forEach((box) => {
    const p = box.querySelector("p");
    if (!p) return;
    for (const [type, info] of Object.entries(NUTRIENT_TYPES)) {
      if (box.textContent.includes(info.label)) {
        p.textContent = `${totals[type].toFixed(1)}${info.unit}`;
        break;
      }
    }
  });
}

function updateProgressBar(calories) {
  const wrapper = document.querySelector(".progress-wrapper");
  if (!wrapper) return;
  const display = wrapper.querySelector(".d-flex span:last-child");
  const bar = wrapper.querySelector(".progress-bar");
  if (!display || !bar) return;
  const goal = parseFloat(display.textContent.split("/")[1]) || 0;
  display.textContent = `${calories.toFixed(1)} / ${goal.toFixed(1)} kcal`;
  if (goal > 0) bar.style.width = `${Math.min(100, (calories / goal) * 100)}%`;
}

function untoggleMeals(mealType = null) {
  const mealTypesToCheck = mealType ? [mealType] : Object.keys(MEAL_TYPES);

  mealTypesToCheck.forEach((type) => {
    const content = document.getElementById(`${type}-content`);
    const btn = content?.closest(".card")?.querySelector(".expand-btn i");
    const tbody = document.getElementById(`${type}-foods`);

    if (!content || !btn || !tbody) return;

    const hasFoodRow = Array.from(tbody.children).some((row) => {
      return (
        !row.classList.contains("table-secondary") &&
        !row.classList.contains("template-row") &&
        row.querySelector(".food-code, .calories")
      );
    });

    if (hasFoodRow && content.style.display === "none") {
      content.style.display = "block";
      btn.classList.remove("fa-chevron-down");
      btn.classList.add("fa-chevron-up");
      content.style.opacity = "1";
      content.style.transform = "translateY(0)";
    }
  });
}
window.untoggleMeals = untoggleMeals;

window.Totals = {
  updateMealTotals,
  updateDailyTotals,
  updateTotalsDisplay,
  updateNutrientBoxes,
  updateProgressBar,
  untoggleMeals,
};
