document.addEventListener("DOMContentLoaded", () => {
  const sliders = ["proteins", "carbs", "fats"];
  const saveBtn = document.getElementById("saveGoals");
  const errorBox = document.getElementById("percentageError");

  // Atualiza visual e valida porcentagens
  function updateSliders() {
    // Verifica se os elementos existem
    const hasSliders = sliders.every((key) =>
      document.getElementById(`${key}_percentage`)
    );
    if (!hasSliders) {
      return true; // Se não há sliders, retorna true para não bloquear o submit
    }

    const total = sliders.reduce((sum, key) => {
      const element = document.getElementById(`${key}_percentage`);
      if (!element) return sum;
      const val = parseInt(element.value || "0");
      const valueElement = document.getElementById(`${key}_value`);
      if (valueElement) {
        valueElement.textContent = val;
      }
      return sum + val;
    }, 0);

    const isValid = Math.abs(total - 100) <= 0.1;
    if (errorBox) {
      errorBox.classList.toggle("d-none", isValid);
    }
    if (saveBtn) {
      saveBtn.disabled = !isValid;
    }
    return isValid;
  }

  // Aplica listener nos sliders (se existirem)
  sliders.forEach((key) => {
    const slider = document.getElementById(`${key}_percentage`);
    if (slider) {
      slider.addEventListener("input", updateSliders);
    }
  });

  // Limita inputs numéricos com até 2 casas decimais
  function bindDecimalField(name) {
    const input = document.querySelector(`input[name="${name}"]`);
    if (!input) return;

    input.step = "0.01";
    input.addEventListener("blur", () => {
      const v = parseFloat(input.value);
      if (!isNaN(v)) input.value = v.toFixed(2);
    });
    input.addEventListener("input", () => {
      input.value = input.value.replace(/[^\d.]/g, "");
      const [intPart, decPart = ""] = input.value.split(".");
      input.value = intPart + (decPart ? "." + decPart.slice(0, 2) : "");
    });
  }

  bindDecimalField("altura");
  bindDecimalField("peso");

  // Função para mostrar mensagem de feedback
  function showMessage(message, type = "success") {
    // Remove mensagens anteriores
    const existingAlert = document.querySelector(".goals-alert");
    if (existingAlert) {
      existingAlert.remove();
    }

    // Cria nova mensagem
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type} alert-dismissible fade show goals-alert`;
    alertDiv.setAttribute("role", "alert");
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Insere a mensagem no topo do card de metas
    const goalsCard = document.querySelector(".goals-card .card-body");
    if (goalsCard) {
      goalsCard.insertBefore(alertDiv, goalsCard.firstChild);

      // Remove a mensagem após 5 segundos
      setTimeout(() => {
        if (alertDiv && alertDiv.parentNode) {
          alertDiv.classList.remove("show");
          setTimeout(() => alertDiv.remove(), 150);
        }
      }, 5000);
    }
  }

  // Função para atualizar valores exibidos na página
  function updateDisplayedValues(data) {
    // Atualiza calorias
    const caloriesSpan = document.querySelector(".calories-goal h2 span");
    if (caloriesSpan && data.calories_goal) {
      caloriesSpan.textContent = Math.round(data.calories_goal);
    }

    // Atualiza macros (proteínas, carboidratos, gorduras)
    const macros = [
      { key: "proteins", label: "Proteínas" },
      { key: "carbs", label: "Carboidratos" },
      { key: "fats", label: "Gorduras" },
    ];

    macros.forEach((macro, index) => {
      const macroBars = document.querySelectorAll(".macro-bar");
      if (macroBars[index]) {
        const valueSpan = macroBars[index].querySelector(".fw-bold");
        if (valueSpan && data[`${macro.key}_goal`]) {
          valueSpan.textContent = Math.round(data[`${macro.key}_goal`]) + "g";
        }
      }
    });
  }

  // Função para configurar o formulário de metas
  function setupGoalsForm() {
    const goalsForm = document.getElementById("goalsForm");
    if (!goalsForm) {
      console.log(
        "Formulário goalsForm ainda não encontrado, tentando novamente..."
      );
      return;
    }

    // Verifica se já tem listener (evita duplicar)
    if (goalsForm.dataset.listenerAdded === "true") {
      console.log("Listener já adicionado ao formulário");
      return;
    }

    console.log("Adicionando listener ao formulário goalsForm");
    goalsForm.dataset.listenerAdded = "true";

    // Intercepta o submit do formulário
    goalsForm.addEventListener("submit", (e) => {
      e.preventDefault();
      e.stopPropagation();

      console.log("Formulário interceptado!");

      // Verifica se há sliders de porcentagem (sistema antigo)
      const hasPercentageSliders = document.getElementById(
        "proteins_percentage"
      );

      if (hasPercentageSliders && !updateSliders()) {
        return;
      }

      const formData = new FormData(goalsForm);
      const caloriesGoal = parseFloat(formData.get("calories_goal")) || 0;
      const proteinsGoal = parseFloat(formData.get("proteins_goal")) || 0;
      const carbsGoal = parseFloat(formData.get("carbs_goal")) || 0;
      const fatsGoal = parseFloat(formData.get("fats_goal")) || 0;

      console.log("Valores:", {
        caloriesGoal,
        proteinsGoal,
        carbsGoal,
        fatsGoal,
      });

      // Se não há sliders de porcentagem, calcula as porcentagens a partir dos valores em gramas
      if (!hasPercentageSliders && caloriesGoal > 0) {
        // Calcula porcentagens: (gramas * calorias_por_grama) / calorias_totais * 100
        const proteinsPercentage = ((proteinsGoal * 4) / caloriesGoal) * 100;
        const carbsPercentage = ((carbsGoal * 4) / caloriesGoal) * 100;
        const fatsPercentage = ((fatsGoal * 9) / caloriesGoal) * 100;

        console.log("Porcentagens calculadas:", {
          proteinsPercentage,
          carbsPercentage,
          fatsPercentage,
        });

        // Valida se a soma das porcentagens está próxima de 100%
        const totalPercentage =
          proteinsPercentage + carbsPercentage + fatsPercentage;
        if (Math.abs(totalPercentage - 100) > 1) {
          showMessage(
            `A soma das porcentagens deve ser igual a 100%. Atual: ${totalPercentage.toFixed(
              1
            )}%`,
            "danger"
          );
          return;
        }

        // Adiciona as porcentagens ao formData
        formData.set("proteins_percentage", proteinsPercentage.toString());
        formData.set("carbs_percentage", carbsPercentage.toString());
        formData.set("fats_percentage", fatsPercentage.toString());
      }

      fetch(goalsForm.action, {
        method: "POST",
        body: formData,
      })
        .then((res) => {
          console.log("Resposta recebida:", res.status);
          if (!res.ok) {
            return res.json().then((data) => {
              throw new Error(data.message || "Erro na requisição");
            });
          }
          return res.json();
        })
        .then((data) => {
          console.log("Dados recebidos:", data);
          if (data.success) {
            showMessage(
              data.message || "Metas nutricionais atualizadas com sucesso!",
              "success"
            );

            // Atualiza valores exibidos
            updateDisplayedValues({
              calories_goal: caloriesGoal,
              proteins_goal: proteinsGoal,
              carbs_goal: carbsGoal,
              fats_goal: fatsGoal,
            });

            // Fecha o modal
            const modal = bootstrap.Modal.getInstance(
              document.getElementById("editGoalsModal")
            );
            if (modal) {
              modal.hide();
            }
          } else {
            showMessage(
              data.message || "Erro ao atualizar metas nutricionais.",
              "danger"
            );
          }
        })
        .catch((err) => {
          console.error("Erro completo:", err);
          showMessage(
            err.message || "Erro ao salvar metas. Por favor, tente novamente.",
            "danger"
          );
        });

      return false;
    });
  }

  // Configura o formulário quando o modal é aberto
  const editGoalsModal = document.getElementById("editGoalsModal");
  if (editGoalsModal) {
    editGoalsModal.addEventListener("shown.bs.modal", function () {
      console.log("Modal aberto, configurando formulário...");
      // Pequeno delay para garantir que o DOM está pronto
      setTimeout(() => {
        setupGoalsForm();
      }, 100);
    });

    // Também tenta configurar imediatamente caso o modal já esteja no DOM
    console.log("Tentando configurar formulário imediatamente...");
    setupGoalsForm();
  } else {
    console.error("Modal editGoalsModal não encontrado!");
  }

  // Fallback: tenta configurar após um pequeno delay
  setTimeout(() => {
    console.log("Fallback: tentando configurar formulário após delay...");
    setupGoalsForm();
  }, 500);

  // Atualiza sliders se existirem
  if (document.getElementById("proteins_percentage")) {
    updateSliders();
  }
});
