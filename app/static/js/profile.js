document.addEventListener("DOMContentLoaded", () => {
  const sliders = ["proteins", "carbs", "fats"];
  const saveBtn = document.getElementById("saveGoals");
  const errorBox = document.getElementById("percentageError");

  // Atualiza visual e valida porcentagens
  function updateSliders() {
    const total = sliders.reduce((sum, key) => {
      const val = parseInt(
        document.getElementById(`${key}_percentage`).value || "0"
      );
      document.getElementById(`${key}_value`).textContent = val;
      return sum + val;
    }, 0);

    const isValid = Math.abs(total - 100) <= 0.1;
    errorBox.classList.toggle("d-none", isValid);
    saveBtn.disabled = !isValid;
    return isValid;
  }

  // Aplica listener nos sliders
  sliders.forEach((key) => {
    document
      .getElementById(`${key}_percentage`)
      .addEventListener("input", updateSliders);
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

  // Envia metas nutricionais
  saveBtn.addEventListener("click", () => {
    if (!updateSliders()) return;

    const formData = new FormData(document.getElementById("goalsForm"));
    fetch(document.getElementById("goalsForm").action, {
      method: "POST",
      body: formData,
    })
      .then((res) => {
        if (res.ok) location.reload();
        else throw new Error("Falha ao salvar.");
      })
      .catch((err) => {
        console.error(err);
        alert("Erro ao salvar metas.");
      });
  });

  updateSliders();
});
