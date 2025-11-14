// api.js

async function makeDietApiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    // Search endpoints return arrays directly
    if (url.includes("/api/search_food")) return data;

    // Handle error responses
    // Mas não trata como erro se for apenas "não encontrado" (isso é normal)
    if (data.success === false && data.error) {
      throw new Error(data.error || "Erro desconhecido");
    }

    return data;
  } catch (error) {
    console.error("[API Error]", error);
    throw error;
  }
}

function handleApiError(error, customMessage) {
  console.error("[API Error]", error);
  alert(`${customMessage}: ${error.message}`);
}
