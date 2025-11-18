// Chat functionality
class ChatBot {
  constructor() {
    this.messages = [];
    this.isLoading = false;
    this.init();
  }

  init() {
    const messageInput = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    const suggestions = document.querySelectorAll(".suggestion-btn");

    // Send message on button click
    sendButton.addEventListener("click", () => this.sendMessage());

    // Send message on Enter key
    messageInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    // Suggestion buttons
    suggestions.forEach((btn) => {
      btn.addEventListener("click", () => {
        const message = btn.getAttribute("data-message");
        messageInput.value = message;
        this.sendMessage();
      });
    });

    // Focus input on load
    messageInput.focus();
  }

  async sendMessage() {
    const messageInput = document.getElementById("messageInput");
    const message = messageInput.value.trim();

    if (!message || this.isLoading) {
      return;
    }

    // Clear input
    messageInput.value = "";

    // Add user message to UI
    this.addMessage("user", message);

    // Show loading indicator
    this.setLoading(true);

    try {
      // Prepare conversation history for context
      const history = this.messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      // Send to API
      const response = await fetch("/api/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: message,
          history: history,
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Add assistant response to UI
        // Log para debug
        console.log("Resposta do chatbot:", data);
        console.log("Recomendação extraída:", data.recommendation);

        // Adicionar mensagem com recomendação
        this.addMessage("assistant", data.response, data.recommendation);
      } else {
        // Show error message
        this.addMessage(
          "assistant",
          `Desculpe, ocorreu um erro: ${
            data.error || "Erro desconhecido"
          }. Por favor, tente novamente.`
        );
      }
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);
      this.addMessage(
        "assistant",
        "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, verifique sua conexão e tente novamente."
      );
    } finally {
      this.setLoading(false);
      messageInput.focus();
    }
  }

  addMessage(role, content, recommendation = null) {
    const chatMessages = document.getElementById("chatMessages");
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;

    // Remover JSON da mensagem antes de formatar (se houver)
    let displayContent = content;
    if (recommendation) {
      // Remove o bloco JSON da mensagem para exibição
      displayContent = content.replace(/```json[\s\S]*?```/g, "").trim();
    }

    // Format content (basic markdown-like formatting)
    const formattedContent = this.formatMessage(displayContent);

    // Criar botões de ação se houver recomendação
    let actionButtons = "";
    if (
      recommendation &&
      recommendation.recommendation &&
      recommendation.meals
    ) {
      actionButtons = `
        <div class="recommendation-actions mt-3">
          <p class="mb-2"><strong>Gostaria de adicionar esta recomendação ao seu diário?</strong></p>
          <div class="d-flex gap-2">
            <button class="btn btn-sm btn-success add-to-diary-btn" data-recommendation='${JSON.stringify(
              recommendation
            )}'>
              <i class="fas fa-check me-1"></i>Sim, adicionar ao diário
            </button>
            <button class="btn btn-sm btn-outline-secondary dismiss-recommendation-btn">
              <i class="fas fa-times me-1"></i>Não, obrigado
            </button>
          </div>
        </div>
      `;
    }

    messageDiv.innerHTML = `
      <div class="message-avatar">
        <i class="fas ${role === "user" ? "fa-user" : "fa-robot"}"></i>
      </div>
      <div class="message-content">
        <div class="message-text">${formattedContent}${actionButtons}</div>
        <div class="message-time">${this.getCurrentTime()}</div>
      </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Adicionar event listeners aos botões de ação
    if (recommendation && recommendation.recommendation) {
      const addBtn = messageDiv.querySelector(".add-to-diary-btn");
      const dismissBtn = messageDiv.querySelector(
        ".dismiss-recommendation-btn"
      );

      if (addBtn) {
        addBtn.addEventListener("click", () =>
          this.addRecommendationToDiary(recommendation, addBtn)
        );
      }

      if (dismissBtn) {
        dismissBtn.addEventListener("click", () => {
          const actionsDiv = messageDiv.querySelector(
            ".recommendation-actions"
          );
          if (actionsDiv) {
            actionsDiv.style.display = "none";
          }
        });
      }
    }

    // Store message in history (incluindo recomendação se houver)
    const messageToStore = { role, content };
    if (recommendation) {
      messageToStore.recommendation = recommendation;
    }
    this.messages.push(messageToStore);
  }

  async addRecommendationToDiary(recommendation, button) {
    if (!recommendation || !recommendation.meals) {
      return;
    }

    // Desabilitar botão durante o processamento
    button.disabled = true;
    button.innerHTML =
      '<i class="fas fa-spinner fa-spin me-1"></i>Adicionando...';

    try {
      // Verificar se estamos no dashboard
      const dateInput = document.getElementById("dietDate");
      const isOnDashboard = dateInput !== null;

      if (!isOnDashboard) {
        this.addMessage(
          "assistant",
          "❌ Por favor, vá para o Dashboard para adicionar alimentos ao diário."
        );
        button.disabled = false;
        button.innerHTML =
          '<i class="fas fa-check me-1"></i>Sim, adicionar ao diário';
        return;
      }

      // 1. Coletar alimentos que já estão no dashboard
      let existingMealsData = {};
      if (typeof collectMealsData === "function") {
        existingMealsData = collectMealsData();
        console.log("Alimentos existentes no dashboard:", existingMealsData);
      } else {
        console.warn("Função collectMealsData não encontrada");
      }

      // 2. Converter recomendação para formato de meals_data
      const newMealsData = {};

      for (const meal of recommendation.meals) {
        const meal_type = meal.meal_type;
        if (!newMealsData[meal_type]) {
          newMealsData[meal_type] = [];
        }

        for (const food of meal.foods) {
          // Usar code ou food_code (dependendo do formato)
          const foodCode = food.code || food.food_code;

          if (!foodCode) {
            console.error("Alimento sem código encontrado:", food);
            continue; // Pular alimentos sem código
          }

          newMealsData[meal_type].push({
            food_code: foodCode,
            quantity: food.quantity || 100,
            calories: food.calories || 0,
            proteins: food.proteins || 0,
            carbs: food.carbs || 0,
            fats: food.fats || 0,
          });
        }
      }

      // 3. Mesclar alimentos existentes com os novos
      const combinedMealsData = { ...existingMealsData };

      // Adicionar novos alimentos às refeições existentes
      for (const meal_type in newMealsData) {
        if (!combinedMealsData[meal_type]) {
          combinedMealsData[meal_type] = [];
        }
        // Adicionar os novos alimentos
        combinedMealsData[meal_type].push(...newMealsData[meal_type]);
      }

      console.log("Dados combinados (existentes + novos):", combinedMealsData);

      // 4. Obter data do dashboard
      const dietDate =
        dateInput.value || new Date().toISOString().split("T")[0];
      const dietName = "Registro do Dia";

      // 5. Salvar usando o endpoint save_daily_diet (que já funciona)
      const response = await fetch("/api/save_daily_diet", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: dietName,
          meals_data: combinedMealsData,
          date: dietDate,
        }),
      });

      const data = await response.json();
      console.log("Resposta da API:", data);

      if (data.success) {
        // Sucesso
        button.innerHTML = '<i class="fas fa-check me-1"></i>Adicionado!';
        button.classList.remove("btn-success");
        button.classList.add("btn-success", "disabled");

        // Mostrar mensagem de sucesso
        let successMessage =
          "✅ Recomendação adicionada ao seu diário com sucesso!";
        if (data.warnings && data.warnings.length > 0) {
          successMessage += "\n\n⚠️ Avisos: " + data.warnings.join(", ");
        }
        this.addMessage("assistant", successMessage);

        // Aguardar 2 segundos para garantir que o salvamento foi concluído no servidor
        // antes de adicionar visualmente ou recarregar
        this.addMessage(
          "assistant",
          "⏳ Aguardando confirmação do servidor..."
        );

        setTimeout(() => {
          // Recarregar a página para atualizar o dashboard
          // Mas preservar o estado do modal (reabrir após recarregar)
          this.addMessage("assistant", "🔄 Atualizando dashboard...");

          // Salvar no sessionStorage que o modal deve ser reaberto após recarregar
          sessionStorage.setItem("reopenChatModal", "true");

          // Salvar o histórico da conversa antes de recarregar
          if (this.messages && this.messages.length > 0) {
            sessionStorage.setItem(
              "chatHistory",
              JSON.stringify(this.messages)
            );
            console.log("Histórico salvo:", this.messages.length, "mensagens");
          }

          // Recarregar a página após um pequeno delay para a mensagem aparecer
          setTimeout(() => {
            window.location.reload();
          }, 500);
        }, 2000); // Delay de 2 segundos como solicitado

        // Ocultar botões após alguns segundos
        setTimeout(() => {
          const actionsDiv = button.closest(".recommendation-actions");
          if (actionsDiv) {
            actionsDiv.style.display = "none";
          }
        }, 3000);
      } else {
        // Erro
        button.disabled = false;
        button.innerHTML =
          '<i class="fas fa-check me-1"></i>Sim, adicionar ao diário';
        this.addMessage(
          "assistant",
          `❌ Erro ao adicionar ao diário: ${data.error || "Erro desconhecido"}`
        );
      }
    } catch (error) {
      console.error("Erro ao adicionar recomendação ao diário:", error);
      button.disabled = false;
      button.innerHTML =
        '<i class="fas fa-check me-1"></i>Sim, adicionar ao diário';
      this.addMessage(
        "assistant",
        "❌ Erro ao adicionar ao diário. Por favor, tente novamente."
      );
    }
  }

  formatMessage(content) {
    // Escape HTML first to prevent XSS
    let formatted = content
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Convert markdown-like formatting to HTML
    // Bold **text** (but not if it's part of **)
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Italic *text* (but not if it's part of **)
    formatted = formatted.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, "<em>$1</em>");

    // Numbered lists
    formatted = formatted.replace(/^\d+\.\s(.+)$/gm, "<li>$1</li>");

    // Bullet lists
    formatted = formatted.replace(/^[-*]\s(.+)$/gm, "<li>$1</li>");

    // Wrap consecutive list items in ul tags
    formatted = formatted.replace(/(<li>.*?<\/li>\n?)+/g, (match) => {
      return `<ul>${match}</ul>`;
    });

    // Line breaks
    formatted = formatted.replace(/\n/g, "<br>");

    // Wrap paragraphs (split by double line breaks)
    const parts = formatted.split("<br><br>");
    formatted = parts
      .map((part) => {
        part = part.trim();
        if (!part) return "";
        // Don't wrap if already a list or heading
        if (
          part.startsWith("<ul>") ||
          part.startsWith("<ol>") ||
          part.startsWith("<h")
        ) {
          return part;
        }
        // Remove trailing <br> before wrapping
        part = part.replace(/<br>$/g, "");
        return `<p>${part}</p>`;
      })
      .join("");

    return formatted;
  }

  getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  setLoading(loading) {
    this.isLoading = loading;
    const loadingDiv = document.getElementById("chatLoading");
    const sendButton = document.getElementById("sendButton");
    const messageInput = document.getElementById("messageInput");

    if (loading) {
      loadingDiv.style.display = "block";
      sendButton.disabled = true;
      messageInput.disabled = true;
    } else {
      loadingDiv.style.display = "none";
      sendButton.disabled = false;
      messageInput.disabled = false;
    }
  }
}

// Initialize chat when page loads or when modal is shown
let chatBotInstance = null;

function initializeChatBot() {
  if (!chatBotInstance) {
    chatBotInstance = new ChatBot();
  }
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  // Verificar se o modal deve ser reaberto após recarregar a página
  if (sessionStorage.getItem("reopenChatModal") === "true") {
    sessionStorage.removeItem("reopenChatModal");

    // Restaurar histórico da conversa se existir
    const savedHistory = sessionStorage.getItem("chatHistory");
    let chatHistory = null;
    if (savedHistory) {
      try {
        chatHistory = JSON.parse(savedHistory);
        sessionStorage.removeItem("chatHistory");
        console.log("Histórico restaurado:", chatHistory.length, "mensagens");
      } catch (e) {
        console.error("Erro ao restaurar histórico:", e);
      }
    }

    // Aguardar um pouco para garantir que o Bootstrap está carregado
    setTimeout(() => {
      const modal = document.getElementById("nutriAIModal");
      if (modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        // Restaurar histórico após o modal abrir
        if (chatHistory && chatHistory.length > 0) {
          setTimeout(() => {
            if (chatBotInstance) {
              // Restaurar mensagens no histórico do chatbot
              chatBotInstance.messages = chatHistory;

              // Restaurar mensagens na UI
              const chatMessages = document.getElementById("chatMessages");
              if (chatMessages) {
                // Limpar mensagens existentes (exceto a mensagem de boas-vindas)
                const welcomeMessage =
                  chatMessages.querySelector(".welcome-message");
                chatMessages.innerHTML = "";
                if (welcomeMessage) {
                  chatMessages.appendChild(welcomeMessage);
                }

                // Adicionar todas as mensagens do histórico
                chatHistory.forEach((msg) => {
                  if (msg.role !== "system") {
                    // Extrair recomendação se houver
                    let recommendation = null;
                    if (msg.recommendation) {
                      recommendation = msg.recommendation;
                    }
                    chatBotInstance.addMessage(
                      msg.role,
                      msg.content,
                      recommendation
                    );
                  }
                });
              }
            }
          }, 500); // Aguardar o chatbot inicializar
        }
      }
    }, 300);
  }

  // Initialize immediately if modal is already visible (shouldn't happen, but just in case)
  if (document.getElementById("nutriAIModal")?.classList.contains("show")) {
    initializeChatBot();
  }

  // Initialize when modal is shown
  const modal = document.getElementById("nutriAIModal");
  if (modal) {
    modal.addEventListener("shown.bs.modal", () => {
      initializeChatBot();
      // Focus input when modal opens
      const messageInput = document.getElementById("messageInput");
      if (messageInput) {
        setTimeout(() => messageInput.focus(), 100);
      }
    });

    // Reset chat when modal is hidden (optional - remove if you want to keep history)
    modal.addEventListener("hidden.bs.modal", () => {
      // Optionally reset chat history when modal closes
      // chatBotInstance = null;
    });
  }
});
