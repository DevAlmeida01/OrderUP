# 🚀 Guia de Setup — OrderUP v2

## Instalação rápida

```bash
cd OrderUP-v2
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
cp .env.example .env
# Edite o .env com suas credenciais

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## ⚙️ Configurar MercadoPago (pagamentos reais)

1. Acesse **mercadopago.com.br/developers/panel**
2. Crie uma conta grátis e um novo app
3. Copie as chaves de **TESTE** (começam com `TEST-`)
4. Cole no `.env`:
```
MERCADOPAGO_ACCESS_TOKEN=TEST-sua-chave
MERCADOPAGO_PUBLIC_KEY=TEST-sua-chave-publica
```
5. Para receber pagamentos reais, troque por chaves de **produção** e configure o `SITE_URL` com seu domínio real

### Como testar pagamentos em modo sandbox
Use os cartões de teste do MercadoPago:
- Cartão aprovado: `5031 7557 3453 0604` | CVV: `123` | Validade: `11/25`
- Cartão recusado: `4000 0000 0000 0002`
- PIX: funciona automaticamente no sandbox

---

## 📧 Configurar emails (Gmail)

1. Ative **verificação em 2 etapas** na sua conta Google
2. Acesse: `myaccount.google.com/apppasswords`
3. Crie uma senha de app (selecione "Outro — OrderUP")
4. Cole a senha gerada no `.env`:
```
EMAIL_HOST_USER=seuemail@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
```

### Para desenvolvimento (sem configurar Gmail)
Deixe assim no `.env` — os emails aparecem no terminal:
```
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

---

## 🔄 Notificações em tempo real (HTMX)

O sistema já usa HTMX para atualizar o status do pedido automaticamente a cada 10 segundos na página do pedido. **Não precisa configurar nada** — funciona out-of-the-box.

Quando o dono do restaurante muda o status (ex: PREPARING → READY), o cliente vê a atualização na tela sem precisar recarregar.

---

## 🌍 Deploy no Railway

```bash
git init && git add . && git commit -m "OrderUP v2"
```
1. railway.app → New Project → Deploy from GitHub
2. Adicione PostgreSQL como serviço
3. Configure as variáveis de ambiente do `.env`
4. O deploy roda automaticamente via `Procfile`
