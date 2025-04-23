// api.js

async function makeDietApiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    // Search endpoints return arrays directly
    if (url.includes("/api/search_food")) return data;

    // Handle error responses
    if (data.success === false) {
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
