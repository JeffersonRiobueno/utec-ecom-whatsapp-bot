# Backlog - ecom-whatsapp-bot

Fecha: 2026-01-07

## Resumen de lo aplicado
- Se añadió/actualizó `app/metrics/langfuse_config.py` con la versión simplificada provista por el usuario.
- Se importó y verificó dentro del contenedor `ecom-whatsapp-bot` que `app.metrics.langfuse_config` carga correctamente.
- Se eliminaron dependencias pesadas de proveedores (Google/Ollama/Gemini) en versiones previas del proyecto para acelerar builds (cambios previos en `requirements.txt`).
- Se envió una traza de prueba al webhook (`/webhook`) y la aplicación respondió 200 OK.

## Estado actual
- `app/metrics/langfuse_config.py`: implementado y probado en import dentro del contenedor. (COMPLETADO)
- Variables de entorno `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` disponibles en el contenedor `ecom-whatsapp-bot`. (COMPROBADO)
- Webhook `/webhook`: responde y procesa peticiones. (COMPROBADO)
- Postgres Langfuse (`langfuse_postgres`): tabla `traces` cuenta = 0 tras prueba. (PENDIENTE INGESTIÓN)

## Problemas detectados
- Las trazas no llegan a la base de Langfuse (SELECT COUNT(*) FROM traces => 0).
- En ejecuciones previas, los intentos de export/flush devolvían respuesta HTTP 404 con HTML (Next.js 404), lo que indica posible ruta API incorrecta o falta de proyecto/permiso en el servidor Langfuse.

## Próximos pasos (priorizados)
1. Capturar logs del servicio `langfuse` para revisar peticiones de export y respuestas (buscar 404s y errores de proyecto). (PRIORIDAD ALTA)
2. Verificar que `LANGFUSE_HOST` incluye el sufijo `/api` (ya se ajustó en el helper, pero confirmar en runtime y que el host resuelve correctamente). (PRIORIDAD ALTA)
3. Revisar en la UI/Admin de Langfuse si existe el proyecto asociado a la `public_key` usada o si las claves corresponden a un proyecto activo. (PRIORIDAD ALTA)
4. Forzar una exportación manual desde dentro del contenedor (crear span/event y llamar `flush()`), capturando completamente la respuesta HTTP para analizar la causa del 404. (PRIORIDAD ALTA)
5. Si la ruta del servidor es diferente, ajustar `LANGFUSE_HOST` o la configuración del reverse-proxy para exponer la API en `/api`. (PRIORIDAD MEDIA)
6. Añadir reintento y mejor manejo de errores en `app/metrics/langfuse_config.py` para loguear el payload de export y errores del servidor para diagnósticos futuros. (PRIORIDAD MEDIA)
7. Documentar pasos de verificación y rollback en `BACKLOG.md` para poder retomar fácilmente. (PRIORIDAD BAJA)

## Cómo retomar este punto rápidamente
- Comandos útiles:

```bash
# Import test dentro del contenedor de la app
docker exec -it ecom-whatsapp-bot python3 -c "import sys; sys.path.insert(0,'/app'); import app.metrics.langfuse_config; print('ok')"

# Enviar traza de prueba
curl -X POST http://localhost:8000/webhook -H 'Content-Type: application/json' -d '{"session_id":"trace-test-1","text":"Prueba trazas","mimetype":"text"}'

# Contar trazas en Postgres
docker exec -i langfuse_postgres psql -U langfuse -d langfuse -c "SELECT COUNT(*) FROM traces;"

# Ver logs del servicio langfuse
docker logs langfuse --since 1h | sed -n '1,200p'
```

---
Mantener este archivo actualizado con resultados y decisiones tomadas.
