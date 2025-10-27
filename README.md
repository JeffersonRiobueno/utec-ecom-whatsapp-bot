
# ecom-whatsapp-bot
Proyecto base para un bot de ecommerce por WhatsApp con FastAPI + LangChain + Qdrant + Redis.

## Setup
```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Enjambre de Agentes
| Agente | Detalle| Repo |
|---------|--|----|
| Agente Products | Agentes para gestionar todo lo relacionado a productos. Consultas de productos, Detalles de productos, recomendaciones | https://github.com/JeffersonRiobueno/utec_agent_product |
| Agente Pedidos | Agente encargado de registrar pedidos y hacer seguimineto a Pedidos | https://github.com/JeffersonRiobueno/utec_agent_pedidos |
| Agente Saludos | Agente basico para gestionar mensajes de saludos del usuario | https://github.com/JeffersonRiobueno/utec_agent_saludos |
| Agente Pagos | Agente encargado de atender consultas relacionadas a metodos de pago | https://github.com/JeffersonRiobueno/utec_agent_pagos |
| Agente Otros | Agente para responder otros mensajes, como de preguntas frecuentes | https://github.com/JeffersonRiobueno/utec_agent_otros |