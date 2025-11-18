# Configuração do Nutri AI (Chatbot Nutricional)

## Requisitos

1. **Biblioteca OpenAI**: A biblioteca `openai` já foi adicionada ao `requirements.txt`
2. **API Key da OpenAI**: Você precisa de uma chave de API da OpenAI

## Como obter a API Key

1. Acesse [https://platform.openai.com/](https://platform.openai.com/)
2. Crie uma conta ou faça login
3. Vá para [API Keys](https://platform.openai.com/api-keys)
4. Clique em "Create new secret key"
5. Copie a chave gerada (ela só será mostrada uma vez!)

## Configuração

### Opção 1: Variável de Ambiente (Recomendado)

**Windows (CMD):**

```cmd
set OPENAI_API_KEY=sua-chave-aqui
```

**Windows (PowerShell):**

```powershell
$env:OPENAI_API_KEY="sua-chave-aqui"
```

**Linux/Mac:**

```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

### Opção 2: Arquivo .env (Recomendado para produção)

Crie um arquivo `.env` na raiz do projeto:

```
OPENAI_API_KEY=sua-chave-aqui
```

E instale o pacote `python-dotenv`:

```bash
pip install python-dotenv
```

Depois, adicione ao início do `app/__init__.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Opção 3: Config.py (Já configurado!)

A API key já está configurada no `config.py`. Se você definir a variável de ambiente `OPENAI_API_KEY`, ela terá prioridade. Caso contrário, será usada a chave padrão do `config.py`.

## Instalação

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Configure a API key (veja opções acima)

3. Execute a aplicação:

```bash
python app.py
```

## Uso

1. Faça login na aplicação
2. Acesse "Nutri AI" no menu de navegação
3. Comece a conversar com o assistente nutricional!

O chatbot usa as informações do seu perfil (peso, altura, idade, objetivo, etc.) para fornecer recomendações personalizadas.

## Modelo Utilizado

O sistema usa o modelo `gpt-4o-mini` da OpenAI, que é:

- Mais econômico que o GPT-4
- Rápido e eficiente
- Adequado para conversas e recomendações nutricionais

## Custos

O modelo `gpt-4o-mini` tem custos muito baixos:

- Input: $0.15 por 1M tokens
- Output: $0.60 por 1M tokens

Uma conversa típica custa menos de $0.01.

## Troubleshooting

**Erro: "API key não configurada"**

- Verifique se a variável de ambiente `OPENAI_API_KEY` está definida
- Reinicie o servidor após definir a variável

**Erro: "Invalid API key"**

- Verifique se a chave está correta
- Certifique-se de que não há espaços extras na chave

**Erro de conexão**

- Verifique sua conexão com a internet
- Verifique se há firewall bloqueando a conexão
