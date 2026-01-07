
# E-commerce WhatsApp Bot

Bot inteligente de e-commerce para WhatsApp construido con FastAPI, LangChain, Qdrant y Redis. Utiliza arquitectura de **Orquestador + Workers** con agentes especializados para diferentes tipos de consultas.

## 🏗️ Arquitectura

### Patrón Orquestador - Worker
- **Orquestador**: Clasifica intenciones y enruta consultas al agente apropiado
- **Workers**: Agentes especializados que procesan consultas específicas
- **Guardrail**: Sistema de seguridad que valida respuestas antes de enviarlas

### Flujo de Procesamiento
1. **Clasificación**: El orquestador analiza el mensaje y determina la intención
2. **Enrutamiento**: La consulta se envía al agente correspondiente
3. **Procesamiento**: El agente procesa la consulta usando herramientas especializadas
4. **Validación**: El guardrail verifica que la respuesta sea apropiada
5. **Respuesta**: Se envía la respuesta final al usuario

## 🤖 Agentes Disponibles

| Agente | Responsabilidad | Endpoint |
|--------|----------------|----------|
| **Products** | Consultas de catálogo, recomendaciones, detalles de productos | `/products_agent_search` |
| **Orders** | Registro y gestión de pedidos | `/orders_agent` |
| **Knowledge** | Preguntas frecuentes, métodos de pago, entregas, tallas | `/products_agent_search` |
| **Greetings** | Saludos y conversaciones iniciales | `/greeting_agent` |
| **Tracking** | Seguimiento de estado de pedidos | `/tracking_agent` |

## 🚀 Inicio Rápido

### Con Docker (Recomendado)
```bash
# Clonar repositorios de agentes
git clone https://github.com/JeffersonRiobueno/utec_agent_product.git
git clone https://github.com/JeffersonRiobueno/utec_agent_pedidos.git
git clone https://github.com/JeffersonRiobueno/utec_agent_saludos.git
git clone https://github.com/JeffersonRiobueno/utec_agent_otros.git
git clone https://github.com/JeffersonRiobueno/utec_agent_seguimiento.git

# Levantar todos los servicios
docker compose up -d

# Ver logs
docker compose logs -f ecom-whatsapp-bot
```

### Desarrollo Local
```bash
# Crear entorno virtual
python -m venv .venv && source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Ejecutar servidor
uvicorn app.main:app --reload --port 8000
```

## 📋 Requisitos

- Python 3.9+
- Docker & Docker Compose
- Redis (para memoria de conversaciones)
- Qdrant (para bases de datos vectoriales)

## ⚙️ Configuración

### Variables de Entorno (.env)
```bash
# LLM Configuration
LLM_PROVIDER=openai|gemini|ollama
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
OLLAMA_BASE_URL=http://localhost:11434

# Agent URLs
AGENT_PRODUCTS_URL=http://agent_product:8000
AGENT_ORDERS_URL=http://agent_orders:8000
AGENT_KNOWLEDGE_URL=http://agent_otros:8000
AGENT_GREETINGS_URL=http://agent_saludos:8000
AGENT_TRACKING_URL=http://agent_seguimiento:8000

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_qdrant_key

# Redis
REDIS_URL=redis://localhost:6379
```

## 🔌 API Endpoints

### POST `/chat`
Endpoint principal para procesar mensajes de WhatsApp.

**Request:**
```json
{
  "session_id": "5491133344455",
  "text": "¿Cuáles son los tiempos de entrega?",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "temperature": 0.2
}
```

**Response:**
```json
{
  "response": "Los pedidos en Lima se entregan entre 1 y 3 días hábiles...",
  "intent": "otro",
  "agent": "knowledge"
}
```

### GET `/health`
Verifica el estado de salud del sistema.

## 🧠 Sistema de Clasificación de Intenciones

El orquestador utiliza un LLM para clasificar automáticamente las consultas en:

- **consulta_producto**: Búsqueda de productos específicos
- **pedido**: Gestión de pedidos
- **otro**: Preguntas generales (FAQs, métodos de pago, entregas, etc.)
- **saludo**: Conversaciones iniciales
- **seguimiento**: Estado de pedidos

## 🔧 Desarrollo

### Estructura del Proyecto
```
ecom-whatsapp-bot/
├── app/
│   ├── main.py          # API FastAPI principal
│   ├── graph.py         # Grafo de LangGraph (orquestador)
│   ├── prompts.py       # Prompts del sistema
│   ├── router.py        # Lógica de enrutamiento
│   ├── memory.py        # Gestión de memoria Redis
│   ├── llm_utils.py     # Utilidades LLM
│   └── tools/
│       └── intent_tools.py  # Herramientas para agentes
├── docker-compose.yml   # Servicios Docker
├── requirements.txt     # Dependencias Python
└── README.md
```

### Agregar Nuevo Agente
1. Crear repositorio del agente siguiendo el patrón establecido
2. Agregar configuración en `docker-compose.yml`
3. Actualizar `intent_tools.py` con la nueva herramienta
4. Modificar `graph.py` para incluir el nuevo nodo
5. Actualizar el router en `prompts.py`

## 🔍 Troubleshooting

### Problemas Comunes

**Error de conexión con agentes:**
```bash
# Verificar que todos los contenedores estén corriendo
docker compose ps

# Revisar logs de un agente específico
docker compose logs agent_otros
```

**Clasificación incorrecta de intenciones:**
- Revisar el prompt en `app/prompts.py`
- Verificar que las reglas cubran el caso específico

**Problemas con embeddings:**
```bash
# Para Ollama
ollama pull nomic-embed-text

# Verificar Qdrant
curl http://localhost:6333/health
```

**Respuestas rechazadas por guardrail:**
- El guardrail puede rechazar respuestas demasiado vagas
- Revisar logs para ver el motivo del rechazo

## 📊 Monitoreo

### Logs
```bash
# Ver todos los logs
docker compose logs -f

# Logs de un servicio específico
docker compose logs -f ecom-whatsapp-bot
```

### Métricas
- **Latencia**: Tiempo de respuesta promedio < 3s
- **Precisión**: Tasa de clasificación correcta > 90%
- **Disponibilidad**: Uptime de servicios > 99%

## 🤝 Contribución

1. Fork el repositorio
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🔗 Enlaces Relacionados

- [Agente Products](https://github.com/JeffersonRiobueno/utec_agent_product)
- [Agente Orders](https://github.com/JeffersonRiobueno/utec_agent_pedidos)
- [Agente Knowledge](https://github.com/JeffersonRiobueno/utec_agent_otros)
- [Agente Greetings](https://github.com/JeffersonRiobueno/utec_agent_saludos)
- [Agente Tracking](https://github.com/JeffersonRiobueno/utec_agent_seguimiento)
- [MCP WooCommerce](https://github.com/JeffersonRiobueno/mcp_woo)
