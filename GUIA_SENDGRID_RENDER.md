# 🚀 Guia Rápido: Configurar SendGrid no Render

Este guia vai te ajudar a resolver o erro "Network is unreachable" configurando o SendGrid, que funciona perfeitamente no Render.

## 📋 Passo a Passo

### 1. Criar Conta no SendGrid (5 minutos)

1. Acesse [https://sendgrid.com](https://sendgrid.com)
2. Clique em "Start for Free"
3. Preencha o formulário de cadastro
4. Verifique seu email (você receberá um email de confirmação)
5. Complete o processo de verificação

### 2. Verificar Domínio (Opcional - pode pular inicialmente)

**Para começar rapidamente, você pode usar o domínio de teste do SendGrid:**
- O SendGrid permite enviar emails de um endereço de teste sem verificar domínio
- Você pode verificar o domínio depois

**Para verificar domínio (recomendado para produção):**
1. No painel do SendGrid, vá em **Settings → Sender Authentication**
2. Escolha **Domain Authentication** (recomendado) ou **Single Sender Verification**
3. Siga as instruções para verificar seu domínio

### 3. Gerar API Key (2 minutos)

1. No painel do SendGrid, vá em **Settings → API Keys**
2. Clique em **Create API Key**
3. Dê um nome (ex: "Render App - N3P")
4. Selecione **Restricted Access**
5. Em **Mail Send**, marque **Full Access**
6. Clique em **Create & View**
7. **IMPORTANTE:** Copie a API Key imediatamente! Ela só aparece uma vez.
   - Se perder, terá que criar uma nova

### 4. Configurar no Render (3 minutos)

1. No painel do Render, vá no seu serviço
2. Clique em **Environment** (no menu lateral)
3. Adicione ou atualize as seguintes variáveis:

```
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=apikey
MAIL_PASSWORD=SUA_API_KEY_AQUI
MAIL_DEFAULT_SENDER=seuemail@seudominio.com
APP_URL=https://seuapp.onrender.com
```

**Importante:**
- `MAIL_USERNAME` deve ser exatamente `apikey` (não seu email!)
- `MAIL_PASSWORD` deve ser a API Key que você copiou
- `MAIL_DEFAULT_SENDER` deve ser um email verificado no SendGrid (pode ser o de teste inicialmente)

### 5. Reiniciar o Serviço

1. No Render, vá em **Manual Deploy**
2. Clique em **Clear build cache & deploy** (ou apenas reinicie o serviço)

### 6. Testar

1. Acesse sua aplicação
2. Tente usar "Esqueci minha senha"
3. Verifique os logs do Render para confirmar que o email foi enviado
4. Verifique sua caixa de entrada (e spam, se necessário)

## ✅ Verificação

Após configurar, os logs do Render devem mostrar:
```
Email config - Server: smtp.sendgrid.net, Port: 587, TLS: True
Attempting to send email via smtp.sendgrid.net:587
Email sent successfully to ['seuemail@exemplo.com']
```

## 🔧 Troubleshooting

### Erro: "Authentication failed"
- Verifique se `MAIL_USERNAME` está como `apikey` (não seu email)
- Verifique se a API Key está correta
- Certifique-se de que a API Key tem permissão de "Mail Send"

### Erro: "Sender not verified"
- Verifique se o email em `MAIL_DEFAULT_SENDER` está verificado no SendGrid
- Use o email de teste do SendGrid inicialmente
- Ou verifique seu domínio no SendGrid

### Email não chega
- Verifique a pasta de spam
- Verifique os logs do SendGrid (Dashboard → Activity)
- Certifique-se de que o domínio/email está verificado

## 📊 Limites do Plano Gratuito

- **100 emails/dia** - suficiente para desenvolvimento e pequenos projetos
- Para mais, considere planos pagos ou outros serviços

## 🎯 Alternativas

Se SendGrid não funcionar para você:

### Mailgun
- Similar ao SendGrid
- 5.000 emails/mês grátis
- Configuração similar

### Amazon SES
- Muito barato (cobrança por uso)
- Requer configuração mais complexa
- Melhor para volumes altos

## 📝 Notas Finais

- O SendGrid é a solução mais simples e confiável para Render
- Funciona imediatamente após configuração
- Não tem problemas de "Network unreachable" como Gmail
- Plano gratuito é suficiente para começar

---

**Pronto!** Seu "esqueci minha senha" deve funcionar perfeitamente agora! 🎉

