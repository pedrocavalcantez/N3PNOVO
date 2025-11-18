# Configuração de Variáveis de Ambiente

Este guia explica como configurar as variáveis secretas do projeto usando um arquivo `.env` local e variáveis de ambiente no Render.

## 📋 Variáveis Necessárias

O projeto precisa das seguintes variáveis de ambiente:

- `SECRET_KEY` - Chave secreta do Flask (obrigatória)
- `DATABASE_URL` - URL de conexão com o banco de dados
- `MAIL_USERNAME` - Email para envio de mensagens
- `MAIL_PASSWORD` - Senha do email (ou senha de app do Gmail)
- `OPENAI_API_KEY` - Chave da API OpenAI para o Nutri AI
- `APP_URL` - URL da aplicação (para links em emails)

## 🏠 Configuração Local (Desenvolvimento)

### Passo 1: Instalar python-dotenv

```bash
pip install python-dotenv
```

Ou instale todas as dependências:

```bash
pip install -r requirements.txt
```

### Passo 2: Criar arquivo .env

1. Copie o arquivo `.env.example` para `.env`:

```bash
# Windows (CMD)
copy .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

2. Abra o arquivo `.env` e preencha com seus valores reais:

```env
# Flask Secret Key
SECRET_KEY=sua-secret-key-aqui

# Database (SQLite para desenvolvimento local)
DATABASE_URL=sqlite:///users.db

# Email Configuration
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app-gmail
MAIL_DEFAULT_SENDER=seu-email@gmail.com

# App URL
APP_URL=http://localhost:5000

# OpenAI API Key
OPENAI_API_KEY=sk-sua-chave-openai-aqui
```

### Passo 3: Gerar SECRET_KEY

Para gerar uma SECRET_KEY segura, execute:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie o resultado e cole no arquivo `.env`.

### Passo 4: Configurar Senha de App do Gmail

Se estiver usando Gmail:

1. Acesse [Google Account Security](https://myaccount.google.com/security)
2. Ative a verificação em duas etapas
3. Vá em "Senhas de app"
4. Crie uma nova senha de app para "Email"
5. Use essa senha no `MAIL_PASSWORD` (não use sua senha normal do Gmail)

### Passo 5: Testar

Execute a aplicação:

```bash
python app.py
```

A aplicação deve carregar as variáveis do arquivo `.env` automaticamente.

## ☁️ Configuração no Render (Produção)

### Passo 1: Acessar Configurações do Serviço

1. Acesse o [Dashboard do Render](https://dashboard.render.com/)
2. Selecione seu serviço (Web Service)
3. Vá em **Environment** (Ambiente) no menu lateral

### Passo 2: Adicionar Variáveis de Ambiente

Clique em **Add Environment Variable** e adicione cada variável:

#### SECRET_KEY

- **Key**: `SECRET_KEY`
- **Value**: Gere uma chave segura (use o mesmo comando Python acima)

#### DATABASE_URL

- **Key**: `DATABASE_URL`
- **Value**: O Render geralmente fornece isso automaticamente se você conectou um banco PostgreSQL
- Se não estiver disponível, copie a connection string do seu banco PostgreSQL no Render

#### MAIL_USERNAME

- **Key**: `MAIL_USERNAME`
- **Value**: Seu email (ex: `seu-email@gmail.com`)

#### MAIL_PASSWORD

- **Key**: `MAIL_PASSWORD`
- **Value**: Senha de app do Gmail (não a senha normal)

#### MAIL_DEFAULT_SENDER

- **Key**: `MAIL_DEFAULT_SENDER`
- **Value**: Mesmo email do MAIL_USERNAME

#### APP_URL

- **Key**: `APP_URL`
- **Value**: URL do seu serviço no Render (ex: `https://seu-app.onrender.com`)

#### OPENAI_API_KEY

- **Key**: `OPENAI_API_KEY`
- **Value**: Sua chave da API OpenAI (obtenha em [platform.openai.com/api-keys](https://platform.openai.com/api-keys))

### Passo 3: Verificar Variáveis

Após adicionar todas as variáveis, você deve ver algo assim:

```
SECRET_KEY = ****************
DATABASE_URL = postgresql://...
MAIL_USERNAME = seu-email@gmail.com
MAIL_PASSWORD = ****************
MAIL_DEFAULT_SENDER = seu-email@gmail.com
APP_URL = https://seu-app.onrender.com
OPENAI_API_KEY = sk-...
```

### Passo 4: Fazer Deploy

Após adicionar todas as variáveis:

1. Clique em **Save Changes**
2. O Render fará um novo deploy automaticamente
3. Aguarde o deploy completar

## 🔒 Segurança

### ✅ O que fazer:

- ✅ Sempre use o arquivo `.env` localmente
- ✅ Adicione `.env` ao `.gitignore` (já está configurado)
- ✅ Use variáveis de ambiente no Render
- ✅ Use senhas de app do Gmail (não senhas normais)
- ✅ Gere SECRET_KEYs seguras e únicas

### ❌ O que NÃO fazer:

- ❌ **NUNCA** commite o arquivo `.env` no Git
- ❌ **NUNCA** compartilhe suas chaves de API
- ❌ **NUNCA** use senhas normais do Gmail (use senhas de app)
- ❌ **NUNCA** coloque valores hardcoded no código

## 🐛 Troubleshooting

### Erro: "SECRET_KEY não configurada"

**Solução**: Certifique-se de que o arquivo `.env` existe e contém `SECRET_KEY`, ou configure a variável de ambiente.

### Erro: "API key não configurada"

**Solução**: Adicione `OPENAI_API_KEY` no `.env` (local) ou nas variáveis de ambiente do Render.

### Erro ao enviar emails

**Solução**:

- Verifique se `MAIL_USERNAME` e `MAIL_PASSWORD` estão corretos
- Se usar Gmail, certifique-se de usar uma senha de app, não a senha normal
- Verifique se a verificação em duas etapas está ativada no Gmail

### Erro de conexão com banco de dados

**Solução**:

- Local: Verifique se `DATABASE_URL` está correto no `.env`
- Render: Verifique se o banco PostgreSQL está conectado ao serviço e se `DATABASE_URL` está configurado

## 📝 Checklist

Antes de fazer deploy, verifique:

- [ ] Arquivo `.env` criado localmente (não commitado)
- [ ] Todas as variáveis preenchidas no `.env`
- [ ] Todas as variáveis adicionadas no Render
- [ ] SECRET_KEY gerada e única
- [ ] Senha de app do Gmail configurada
- [ ] APP_URL aponta para a URL correta do Render
- [ ] OPENAI_API_KEY válida

## 📚 Referências

- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
