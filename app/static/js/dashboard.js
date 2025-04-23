// ------------------------------------------------------------
// dashboard.js — refatorado (v3‑corrigido)
// ------------------------------------------------------------
// 1. Carrega automaticamente a última dieta salva do usuário
//    (endpoint /api/last_diet) ao abrir o dashboard.
// 2. searchFood(): mantém o dropdown global criado no v2.
// 3. Correção dos TypeError/ReferenceError — bind seguro
//    + exportação correta das funções globais.
// ------------------------------------------------------------

const NUTRIENT_TYPES = {
  calories: { label: 'Calorias',     unit: ''  },
  proteins: { label: 'Proteínas',    unit: 'g' },
  carbs:    { label: 'Carboidratos', unit: 'g' },
  fats:     { label: 'Gorduras',     unit: 'g' }
};

function isGuestMode () { return !document.querySelector('.progress-wrapper'); }

async function makeDietApiCall (url, opt = {}) {
  const r = await fetch(url, opt);
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || `HTTP ${r.status}`);
  if (!url.includes('/api/search_food') && d.success === false)
    throw new Error(d.error || 'Unknown error');
  return d;
}

function handleApiError (e, msg) { console.error(e); alert(`${msg}: ${e.message}`); }
function closeModal (id)         { const m = bootstrap.Modal.getInstance(document.getElementById(id)); if (m) m.hide(); }

function updateNutrientBoxes (totals) {
  document.querySelectorAll('.nutrient-box').forEach(box => {
    const p = box.querySelector('p');
    if (!p) return;
    for (const [key, i] of Object.entries(NUTRIENT_TYPES)) {
      if (box.textContent.includes(i.label)) {
        p.textContent = `${totals[key].toFixed(1)}${i.unit}`;
        break;
      }
    }
  });
}
function toggleMealSection (mealType) {
  const content = document.getElementById(`${mealType}-content`);
  const icon    = content.closest('.card').querySelector('.expand-btn i');

  const opened  = content.style.display !== 'none';
  if (opened) {
    content.style.display = 'none';
    icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
  } else {
    content.style.display = 'block';
    icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
  }
}

/* exporta para que o HTML entenda o onclick="toggleMealSection(...)" */

function updateProgressBar (totalCalories) {
  const wrap = document.querySelector('.progress-wrapper');
  if (!wrap) return;
  const display = wrap.querySelector('.d-flex span:last-child');
  const bar     = wrap.querySelector('.progress-bar');
  const goal    = parseFloat(display.textContent.split('/')[1]) || 0;
  display.textContent = `${totalCalories.toFixed(1)} / ${goal.toFixed(1)} kcal`;
  if (goal > 0) bar.style.width = `${Math.min(100, (totalCalories / goal) * 100)}%`;
}

/* ------------------------------------------------------------------
 *  Tenta carregar a última dieta salva
 * ------------------------------------------------------------------ */
async function loadLastDietIfExists () {
  try {
    const data = await makeDietApiCall('/api/last_diet');
    if (data.success) {
      // limpa tabelas
      document.querySelectorAll('tbody[id$="-foods"]').forEach(tb => tb.innerHTML = '');
      Object.entries(data.meals_data).forEach(([mealType, foods]) => {
        const tbody = document.getElementById(`${mealType}-foods`);
        foods.forEach(food => tbody.appendChild(__fm.setupFoodRow(food, mealType, true)));
      });
      console.log(`Dieta “${data.name}” carregada automaticamente.`);
      return true;
    }
  } catch (err) {
    console.warn('Nenhuma dieta anterior para carregar:', err.message);
  }
  return false;
}

/* ------------------------------------------------------------------ */

class FoodManager {
  constructor (mealTypes) {
    this.mealTypes = Array.isArray(mealTypes)
      ? mealTypes
      : Object.keys(mealTypes || {});

    const methodsToBind = [
      'addNewRow', 'editFoodRow', 'saveFood', 'deleteFood',
      'searchFood', 'selectFood', 'updateNutrition',
      'updateMealTotals', 'updateDailyTotals',
      'addMealTemplate', 'populateMealTemplates'
    ];
    methodsToBind.forEach(m => {
      if (typeof this[m] === 'function') {
        this[m] = this[m].bind(this);
      } else {
        console.warn(`FoodManager: método ausente -> ${m}`);
      }
    });

    /* Callback principal da página -------------------------------- */
    document.addEventListener('DOMContentLoaded', async () => {
      await loadLastDietIfExists();                // tenta carregar última dieta
      this.mealTypes.forEach(mt => this.updateMealTotals(mt));
      this.updateDailyTotals();

      // esconde dropdowns ao clicar fora
      document.addEventListener('click', e => {
        if (!e.target.classList.contains('food-code'))
          document.querySelectorAll('.search-results').forEach(d => d.classList.add('d-none'));
      });
    });
  }

  /* ---------- helpers internos ---------- */
  _getNutritionalValues (row) {
    return ['calories', 'proteins', 'carbs', 'fats'].reduce((acc, k) => {
      const el = row.querySelector(`.${k}`);
      acc[k] = el ? (parseFloat(el.textContent) || 0) : 0;
      return acc;
    }, {});
  }

  _setNutritionalValues (row, values, includeUnits = false) {
    const isTotal = !!row.querySelector('strong');
    const cell = (i, cls) => isTotal
      ? row.cells[i].querySelector('strong')
      : row.querySelector('.' + cls);

    ['calories', 'proteins', 'carbs', 'fats'].forEach((k, i) => {
      const el = cell(i + 2, k);
      if (el) el.textContent = values[k].toFixed(1) + (includeUnits && k !== 'calories' ? 'g' : '');
    });
  }

  _resetValues (row) {
    this._setNutritionalValues(row, { calories: 0, proteins: 0, carbs: 0, fats: 0 });
  }

  getMealType (row) { return row.closest('tbody').id.replace('-foods', ''); }

  _cloneTemplate () {
    return document.getElementById('food-row-template')
      .content.cloneNode(true).querySelector('tr');
  }

  /* ---------- criação / edição de linhas ---------- */
  setupFoodRow (food = null, mealType = null, staticRow = false) {
    const row = this._cloneTemplate();
    if (food?.id) row.id = `food-${food.id}`;

    const codeIn = row.querySelector('.food-code');
    const qtyIn  = row.querySelector('.quantity');

    if (food && (staticRow || food.id)) {
      row.innerHTML = `
        <td>${food.food_code}</td>
        <td>${parseFloat(food.quantity).toFixed(1)}g</td>
        <td class="calories">${parseFloat(food.calories).toFixed(1)}</td>
        <td class="proteins">${parseFloat(food.proteins).toFixed(1)}g</td>
        <td class="carbs">${parseFloat(food.carbs).toFixed(1)}g</td>
        <td class="fats">${parseFloat(food.fats).toFixed(1)}g</td>
        <td>
          <div class="action-buttons">
            <button class="btn btn-primary btn-sm" onclick="editFoodRow(this)"><i class="fas fa-edit"></i></button>
            <button class="btn btn-danger btn-sm"  onclick="deleteFood(${food.id})"><i class="fas fa-trash"></i></button>
          </div>
        </td>`;
      return row;
    }

    if (food) {
      codeIn.value = food.food_code;
      qtyIn.value  = food.quantity;
      this._setNutritionalValues(row, food, true);
    }

    codeIn.addEventListener('input', () => this.searchFood(codeIn));
    qtyIn.addEventListener('input',  () => this.updateNutrition(qtyIn));
    row.querySelector('.save-food').onclick = () => this.saveFood(row.querySelector('.save-food'), mealType);

    return row;
  }

  editFoodRow (btn) {
    const row = btn.closest('tr');
    const cells = row.cells;
    const code  = cells[0].textContent.trim();
    const qty   = parseFloat(cells[1].textContent);

    cells[0].innerHTML = `
      <div class="input-group">
        <input type="text" class="form-control food-code" value="${code}" onkeyup="searchFood(this)">
        <div class="search-results d-none position-absolute w-100 bg-white border rounded-bottom shadow-sm" style="z-index:1000;top:100%"></div>
      </div>`;
    cells[1].innerHTML = `
      <input type="number" class="form-control quantity" value="${qty}" min="0" step="1" style="width:80px" oninput="updateNutrition(this)">`;

    ['calories', 'proteins', 'carbs', 'fats'].forEach((k, i) => {
      cells[i + 2].innerHTML = `<span class="${k}">${parseFloat(cells[i + 2].textContent)}</span>`;
    });

    const id = row.id.replace('food-', '');
    cells[6].querySelector('.action-buttons').innerHTML = `
      <button class="btn btn-success save-food" onclick="saveFood(this,'${this.getMealType(row)}')"><i class="fas fa-check"></i></button>
      <button class="btn btn-danger" onclick="deleteFood(${id})"><i class="fas fa-trash"></i></button>`;
  }

  addNewRow (mealType) {
    const content = document.getElementById(`${mealType}-content`);
    const icon    = content.closest('.card').querySelector('.expand-btn i');

    if (content.style.display === 'none') {
      content.style.display = 'block';
      icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
    }

    const tbody = document.getElementById(`${mealType}-foods`);
    const row   = this.setupFoodRow(null, mealType);
    const total = tbody.querySelector('.table-secondary');
    total ? tbody.insertBefore(row, total) : tbody.appendChild(row);
  }

  /* ---------- BUSCA de alimentos ---------- */
  async searchFood (input) {
    let dd = input.nextElementSibling;
    if (!dd || !dd.classList.contains('search-results')) {
      // cria/usa dropdown global
      dd = document.getElementById('global-search-results');
      if (!dd) {
        dd = document.createElement('div');
        dd.id = 'global-search-results';
        dd.className = 'search-results position-absolute w-100 bg-white border rounded-bottom shadow-sm';
        document.body.appendChild(dd);
      }
    }

    const q = input.value.trim();
    if (q.length < 2) { dd.classList.add('d-none'); return; }

    if (dd.id === 'global-search-results') {
      const r = input.getBoundingClientRect();
      dd.style.top  = `${r.bottom + window.scrollY}px`;
      dd.style.left = `${r.left  + window.scrollX}px`;
      dd.style.width = `${r.width}px`;
    }

    dd.innerHTML = '<div class="p-2">Buscando...</div>';
    dd.classList.remove('d-none');

    try {
      const foods = await makeDietApiCall(`/api/search_food?query=${encodeURIComponent(q)}`);
      dd.innerHTML = '';
      if (!foods.length) {
        dd.innerHTML = '<div class="p-2 text-muted">Nenhum alimento encontrado</div>';
        return;
      }
      foods.forEach(f => {
        const d = document.createElement('div');
        d.className = 'p-2 border-bottom';
        d.style.cursor = 'pointer';
        d.textContent  = f.food_code;
        d.onclick      = () => this.selectFood(input, f);
        dd.appendChild(d);
      });
    } catch (e) {
      handleApiError(e, 'Erro ao buscar alimentos');
    }
  }

  selectFood (input, food) {
    input.value = food.food_code;
    const localDD = input.nextElementSibling;
    localDD ? localDD.classList.add('d-none')
            : document.getElementById('global-search-results')?.classList.add('d-none');

    const row = input.closest('tr');
    const qty = row.querySelector('.quantity');
    qty.value = food.qtd;
    qty.dispatchEvent(new Event('input'));
    qty.focus();
  }

  /* ---------- nutricional / salvar / deletar ---------- */
  async updateNutrition (qtyIn) {
    const row  = qtyIn.closest('tr');
    const code = row.querySelector('.food-code').value;
    const qty  = parseFloat(qtyIn.value) || 0;
    if (!code) { this._resetValues(row); return; }

    try {
      const d = await makeDietApiCall(`/api/food_nutrition/${encodeURIComponent(code)}?quantity=${qty}`);
      this._setNutritionalValues(row, d);
      row.querySelector('.save-food').style.display = qty > 0 ? 'inline-block' : 'none';
    } catch (e) {
      handleApiError(e, 'Erro ao atualizar valores nutricionais');
      this._resetValues(row);
      row.querySelector('.save-food').style.display = 'none';
    }
  }

  async saveFood (btn, mealType) {
    const row  = btn.closest('tr');
    const code = row.querySelector('.food-code').value;
    const qty  = parseFloat(row.querySelector('.quantity').value);

    try {
      const res = await makeDietApiCall('/api/add_food', {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ food_code: code, quantity: qty, meal_type: mealType })
      });

      const f = res.food;
      this._setNutritionalValues(row, f);
      row.id = `food-${f.id}`;

      // converte inputs para texto fixo
      row.querySelector('.food-code').closest('td').textContent = code;
      row.querySelector('.quantity').closest('td').textContent  = `${qty.toFixed(1)}g`;
      row.querySelector('.action-buttons').innerHTML = `
        <button class="btn btn-primary btn-sm" onclick="editFoodRow(this)"><i class="fas fa-edit"></i></button>
        <button class="btn btn-danger btn-sm"  onclick="deleteFood(${f.id})"><i class="fas fa-trash"></i></button>`;

      this.updateDailyTotals();
    } catch (e) {
      handleApiError(e, 'Erro ao salvar alimento');
      btn.style.display = 'inline-block';
    }
  }

  async deleteFood (id) {
    try {
      await makeDietApiCall(`/api/delete_food/${id}`, { method: 'DELETE' });
      const row = document.getElementById(`food-${id}`);
      if (row) {
        const mt = this.getMealType(row);
        row.remove();
        this.updateMealTotals(mt);
        this.updateDailyTotals();
      }
    } catch (e) {
      handleApiError(e, 'Erro ao remover alimento');
    }
  }

  /* ---------- Templates de refeição ---------- */
  async addMealTemplate (mealType, templateId) {
    try {
      const { template } = await makeDietApiCall(`/api/meal_templates/${templateId}`);
      for (const food of template.foods) {
        const nutri = await makeDietApiCall(
          `/api/food_nutrition/${food.food_code}?quantity=${food.quantity}`
        );

        const row = this.setupFoodRow(
          {
            id        : nutri.food_code + Date.now(), // id único na UI
            food_code : nutri.food_code,
            quantity  : food.quantity,
            ...nutri
          },
          mealType,
          true
        );
        document.getElementById(`${mealType}-foods`).appendChild(row);
      }
      this.updateMealTotals(mealType);
      this.updateDailyTotals();
      closeModal(`mealTemplateModal-${mealType}`);
    } catch (e) {
      handleApiError(e, 'Erro ao adicionar template');
    }
  }

  async populateMealTemplates (mealType) {
    const box = document.getElementById(`meal-templates-${mealType}`);
    if (!box) return;
    box.innerHTML = '<div class="p-2">Carregando…</div>';
    try {
      const { templates } = await makeDietApiCall(`/api/meal_templates?meal_type=${mealType}`);
      box.innerHTML = '';
      templates.forEach(tpl => {
        const btn = document.createElement('button');
        btn.type  = 'button';
        btn.className = 'list-group-item list-group-item-action';
        btn.innerHTML = `
          <div class="d-flex justify-content-between align-items-center">
            <div>
              <h6 class="mb-1">${tpl.name}</h6>
              <small class="text-muted">${tpl.foods.map(f => f.food_code).join(', ')}</small>
            </div>
            <span class="badge bg-primary rounded-pill">${tpl.foods.length}</span>
          </div>`;
        btn.onclick = () => this.addMealTemplate(mealType, tpl.id);
        box.appendChild(btn);
      });
    } catch (e) {
      box.innerHTML = '<div class="p-2 text-danger">Erro ao carregar templates</div>';
    }
  }

  /* ---------- Totais ---------- */
  updateMealTotals (mealType) {
    const tbody = document.getElementById(`${mealType}-foods`);
    if (!tbody) return { calories: 0, proteins: 0, carbs: 0, fats: 0 };

    const totals = { calories: 0, proteins: 0, carbs: 0, fats: 0 };
    tbody.querySelectorAll('tr:not(.table-secondary):not(.template-row)').forEach(r => {
      const v = this._getNutritionalValues(r);
      Object.keys(totals).forEach(k => totals[k] += v[k]);
    });

    const tfoot = tbody.closest('table').querySelector('tfoot tr');
    if (tfoot) this._setNutritionalValues(tfoot, totals, true);
    return totals;
  }

  updateDailyTotals () {
    const d = { calories: 0, proteins: 0, carbs: 0, fats: 0 };
    this.mealTypes.forEach(mt => {
      const m = this.updateMealTotals(mt);
      Object.keys(d).forEach(k => d[k] += m[k]);
    });

    if (isGuestMode()) {
      document.getElementById('total-calories').textContent = d.calories.toFixed(1);
      document.getElementById('total-proteins').textContent = d.proteins.toFixed(1);
      document.getElementById('total-carbs').textContent    = d.carbs.toFixed(1);
      document.getElementById('total-fats').textContent     = d.fats.toFixed(1);
    } else {
      updateNutrientBoxes(d);
      updateProgressBar(d.calories);
    }
  }
}

/* ------------------------------------------------------------------
 * Instância global + export para o HTML
 * ------------------------------------------------------------------ */
const __fm = new FoodManager(
  typeof MEAL_TYPES === 'undefined'
    ? []
    : (Array.isArray(MEAL_TYPES) ? MEAL_TYPES : Object.keys(MEAL_TYPES))
);

const exportedFns = [
  'addNewRow', 'editFoodRow', 'saveFood', 'deleteFood',
  'searchFood', 'selectFood', 'updateNutrition',
  'updateMealTotals', 'updateDailyTotals',
  'addMealTemplate', 'populateMealTemplates'
];

exportedFns.forEach(name => {
  if (typeof __fm[name] === 'function') {
    window[name] = __fm[name].bind(__fm);   // agora correto
  } else {
    console.warn(`export: método ausente -> ${name}`);
  }
});

/* ------------------------------------------------------------------
 *  Demais funções (saveDiet, loadDiet, exportToExcel etc.) – sem
 *  alterações de lógica, pois já chamam os métodos de __fm.
 * ------------------------------------------------------------------ */
/* … (mantenha aqui o resto do arquivo sem mudanças) … */

/* ------------------------------------------------------------------
 * Listeners adicionais
 * ------------------------------------------------------------------ */
document.addEventListener('DOMContentLoaded', () => {
  const dietNameInput = document.getElementById('dietName');
  if (dietNameInput) {
    dietNameInput.addEventListener('input', ()  => showDietSuggestions(dietNameInput));
    dietNameInput.addEventListener('focus', ()  => showDietSuggestions(dietNameInput));
  }
});


window.toggleMealSection = toggleMealSection;
window.saveDiet       = saveDiet;
window.loadDiet       = loadDiet;
window.deleteDiet     = deleteDiet;
window.exportToExcel  = exportToExcel;