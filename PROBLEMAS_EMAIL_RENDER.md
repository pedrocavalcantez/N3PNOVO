# Problemas com "Esqueci minha senha" no Render

Este documento lista os problemas mais comuns que impedem o funcionamento do "esqueci minha senha" no Render e suas soluções.

## 🔴 Problemas Mais Comuns

### ⚠️ **ERRO CRÍTICO: "Network is unreachable" (Errno 101)**

**Este é o erro que você está enfrentando!**

**Problema:** O Render não consegue estabelecer conexão de rede com o servidor SMTP do Gmail. Isso é uma limitação conhecida do Render - conexões SMTP diretas para Gmail frequentemente falham devido a restrições de rede.

**Sintoma:**

```
OSError: [Errno 101] Network is unreachable
```

**Solução RECOMENDADA: Usar SendGrid (API, não SMTP)**

O SendGrid funciona perfeitamente no Render e é gratuito até 100 emails/dia. Vamos configurar:

1. **Criar conta no SendGrid:**

   - Acesse [SendGrid](https://sendgrid.com) e crie uma conta gratuita
   - Complete a verificação de email e domínio (pode usar domínio de teste inicialmente)

2. **Gerar API Key:**

   - Vá em Settings → API Keys
   - Clique em "Create API Key"
   - Dê um nome (ex: "Render App")
   - Selecione "Full Access" ou "Restricted Access" (com permissões de Mail Send)
   - Copie a API Key gerada (ela só aparece uma vez!)

3. **Configurar no Render:**

   ```
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=sua_api_key_do_sendgrid_aqui
   MAIL_DEFAULT_SENDER=seuemail@seudominio.com
   ```

4. **Alternativa: Usar Mailgun**
   - Similar ao SendGrid, também funciona bem no Render
   - Crie conta em [Mailgun](https://www.mailgun.com)
   - Use as credenciais SMTP fornecidas

**Por que Gmail não funciona no Render?**

- O Render tem restrições de rede que bloqueiam conexões SMTP para alguns servidores
- Gmail pode estar bloqueando IPs do Render por segurança
- Mesmo com App Password, a conexão de rede pode falhar

**Solução Temporária (não recomendada):**
Se precisar usar Gmail urgentemente, tente:

- Porta 465 com SSL (não TLS):
  ```
  MAIL_PORT=465
  MAIL_USE_TLS=false
  MAIL_USE_SSL=true
  ```
- Mas isso provavelmente também não funcionará devido às restrições de rede do Render
- **Recomendação:** Use SendGrid ou Mailgun em vez disso

---

### 1. **Variáveis de Ambiente Não Configuradas**

**Problema:** As variáveis de ambiente necessárias para envio de email não estão configuradas no Render.

**Variáveis necessárias:**

- `MAIL_USERNAME` - Email do remetente (ex: seuemail@gmail.com)
- `MAIL_PASSWORD` - Senha do email ou "App Password" (para Gmail)
- `MAIL_SERVER` - Servidor SMTP (padrão: smtp.gmail.com)
- `MAIL_PORT` - Porta SMTP (padrão: 587)
- `MAIL_USE_TLS` - Usar TLS (padrão: true)
- `APP_URL` - URL completa da aplicação no Render (ex: https://seuapp.onrender.com)

**Solução:**

1. No painel do Render, vá em **Environment** (Variáveis de Ambiente)
2. Adicione todas as variáveis acima
3. Para `APP_URL`, use a URL completa do seu serviço no Render (com https://)
4. Reinicie o serviço após adicionar as variáveis

---

### 2. **Gmail Bloqueando Tentativas de Login**

**Problema:** O Gmail pode bloquear tentativas de login de servidores externos por segurança.

**Soluções:**

#### Opção A: Usar "App Password" do Gmail

1. Ative a verificação em duas etapas na sua conta Google
2. Vá em [App Passwords](https://myaccount.google.com/apppasswords)
3. Gere uma senha de app específica
4. Use essa senha no `MAIL_PASSWORD` (não use sua senha normal)

#### Opção B: Permitir "Aplicativos Menos Seguros" (não recomendado)

- Esta opção está descontinuada pelo Google
- Use a Opção A (App Password) em vez disso

#### Opção C: Usar outro provedor de email

- SendGrid (recomendado para produção)
- Mailgun
- Amazon SES
- Outros serviços SMTP

---

### 3. **URL Incorreta no Link de Reset**

**Problema:** O link de reset pode estar usando `localhost` em vez da URL do Render.

**Solução:**

- Configure `APP_URL` no Render com a URL completa: `https://seuapp.onrender.com`
- O código tenta detectar automaticamente, mas é melhor configurar explicitamente

**Verificação:**

- Verifique os logs do Render após solicitar reset de senha
- Procure por "Auto-detected APP_URL" ou "Using fallback APP_URL"
- Se aparecer "fallback", significa que `APP_URL` não está configurado

---

### 4. **Timeout do Worker no Render**

**Problema:** O envio de email pode demorar e causar timeout do worker.

**Solução:**

- O código já envia emails de forma assíncrona para evitar isso
- Se ainda houver problemas, considere usar um serviço de email mais rápido (SendGrid, Mailgun)

---

### 5. **Porta ou Configuração SMTP Incorreta**

**Problema:** Configurações SMTP incorretas podem impedir o envio.

**Configurações recomendadas para Gmail:**

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=seuemail@gmail.com
MAIL_PASSWORD=senha_de_app_gerada
```

**Configurações para SendGrid:**

```
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=apikey
MAIL_PASSWORD=sua_api_key_do_sendgrid
```

---

### 6. **Erros Silenciosos no Envio Assíncrono**

**Problema:** O código envia email de forma assíncrona e pode não capturar erros adequadamente.

**Solução:**

- O código foi melhorado para adicionar mais logging
- Verifique os logs do Render após tentar reset de senha
- Procure por mensagens de erro relacionadas a SMTP, autenticação ou timeout

---

## 🔍 Como Diagnosticar

### 1. Verificar Logs no Render

1. Vá no painel do Render
2. Clique em **Logs**
3. Solicite um reset de senha
4. Procure por mensagens como:
   - "Email not configured"
   - "SMTP error"
   - "Email sending timeout"
   - "Auto-detected APP_URL"

### 2. Verificar Variáveis de Ambiente

No código, adicione temporariamente um endpoint de debug (apenas em desenvolvimento):

```python
@app.route('/debug/email-config')
def debug_email_config():
    return {
        'MAIL_SERVER': app.config.get('MAIL_SERVER'),
        'MAIL_PORT': app.config.get('MAIL_PORT'),
        'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
        'MAIL_USERNAME_SET': bool(app.config.get('MAIL_USERNAME')),
        'MAIL_PASSWORD_SET': bool(app.config.get('MAIL_PASSWORD')),
        'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER'),
        'APP_URL': app.config.get('APP_URL'),
    }
```

**⚠️ IMPORTANTE:** Remova este endpoint antes de colocar em produção!

### 3. Testar Configuração de Email Localmente

1. Configure as mesmas variáveis no seu `.env` local
2. Teste o envio de email localmente
3. Se funcionar localmente mas não no Render, o problema é específico do ambiente Render

---

## ✅ Checklist de Verificação

Antes de reportar problemas, verifique:

- [ ] `MAIL_USERNAME` está configurado no Render
- [ ] `MAIL_PASSWORD` está configurado no Render (use App Password para Gmail)
- [ ] `APP_URL` está configurado com a URL completa do Render (https://...)
- [ ] `MAIL_SERVER` está correto (smtp.gmail.com para Gmail)
- [ ] `MAIL_PORT` está correto (587 para Gmail com TLS)
- [ ] `MAIL_USE_TLS` está como `true`
- [ ] O serviço foi reiniciado após adicionar as variáveis
- [ ] Verificou os logs do Render para erros específicos
- [ ] Para Gmail, está usando App Password (não senha normal)

---

## 🚀 Solução Recomendada para Produção

Para produção, recomenda-se usar um serviço de email profissional:

### SendGrid (Recomendado)

1. Crie conta em [SendGrid](https://sendgrid.com)
2. Gere uma API Key
3. Configure no Render:
   ```
   MAIL_SERVER=smtp.sendgrid.net
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=apikey
   MAIL_PASSWORD=sua_api_key_aqui
   ```

### Mailgun

1. Crie conta em [Mailgun](https://www.mailgun.com)
2. Configure as credenciais SMTP fornecidas
3. Adicione as variáveis no Render

---

## 📝 Notas Adicionais

- O código foi melhorado para adicionar mais logging e tratamento de erros
- Emails são enviados de forma assíncrona para evitar timeout
- O código tenta detectar automaticamente a URL, mas é melhor configurar `APP_URL` explicitamente
- Verifique sempre os logs do Render para identificar problemas específicos
