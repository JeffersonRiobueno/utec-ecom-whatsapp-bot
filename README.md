
# ecom-whatsapp-bot
Proyecto base para un bot de ecommerce por WhatsApp con FastAPI + LangChain + Qdrant + Redis.

## Setup
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
