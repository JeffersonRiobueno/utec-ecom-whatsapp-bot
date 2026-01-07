#!/usr/bin/env python3
"""
Script de prueba para verificar la integración de observabilidad.
Prueba las métricas de Prometheus y la conectividad con Langfuse.
"""

import requests
import time
import json
import os
from typing import Dict, Any

def test_prometheus_metrics():
    """Probar que las métricas de Prometheus están disponibles."""
    try:
        response = requests.get("http://localhost:8000/metrics")
        if response.status_code == 200:
            print("✅ Métricas de Prometheus disponibles")
            # Verificar que contienen métricas específicas
            metrics_text = response.text
            if "orchestrator_requests_total" in metrics_text:
                print("✅ Métricas del orquestador encontradas")
            if "orchestrator_agent_requests_total" in metrics_text:
                print("✅ Métricas de agentes encontradas")
            return True
        else:
            print(f"❌ Error al obtener métricas: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando a métricas: {e}")
        return False

def test_langfuse_connection():
    """Probar la conexión con Langfuse."""
    langfuse_host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
    try:
        response = requests.get(f"{langfuse_host}/api/public/health", timeout=5)
        if response.status_code == 200:
            print("✅ Langfuse está disponible")
            return True
        else:
            print(f"⚠️  Langfuse respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  No se pudo conectar a Langfuse: {e}")
        return False

def test_orchestrator_health():
    """Probar que el orquestador está saludable."""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Orquestador saludable - Provider: {data.get('provider')}, Model: {data.get('model')}")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al orquestador: {e}")
        return False

def test_sample_request():
    """Enviar una solicitud de prueba para generar métricas."""
    try:
        payload = {
            "session_id": "test_session_observability",
            "text": "Hola, ¿qué productos tienes disponibles?",
            "mimetype": "text",
            "filename": ""
        }
        response = requests.post("http://localhost:8000/webhook", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Solicitud de prueba exitosa - Reply: {data.get('reply')[:50]}...")
            return True
        else:
            print(f"❌ Error en solicitud de prueba: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en solicitud de prueba: {e}")
        return False

def main():
    """Función principal de prueba."""
    print("🚀 Probando integración de observabilidad...\n")

    # Esperar un poco para que los servicios estén listos
    print("⏳ Esperando que los servicios estén listos...")
    time.sleep(3)

    results = []

    print("\n1. Probando health del orquestador...")
    results.append(("Health Check", test_orchestrator_health()))

    print("\n2. Probando métricas de Prometheus...")
    results.append(("Prometheus Metrics", test_prometheus_metrics()))

    print("\n3. Probando conexión con Langfuse...")
    results.append(("Langfuse Connection", test_langfuse_connection()))

    print("\n4. Enviando solicitud de prueba...")
    results.append(("Sample Request", test_sample_request()))

    print("\n5. Verificando métricas después de la solicitud...")
    time.sleep(1)  # Dar tiempo para que se actualicen las métricas
    results.append(("Metrics After Request", test_prometheus_metrics()))

    # Resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE PRUEBAS:")
    print("="*50)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if success:
            passed += 1

    print(f"\nResultado: {passed}/{total} pruebas pasaron")

    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La observabilidad está funcionando correctamente.")
    elif passed >= total * 0.7:  # Al menos 70%
        print("⚠️  La mayoría de las pruebas pasaron. Revisa las configuraciones opcionales.")
    else:
        print("❌ Varias pruebas fallaron. Revisa la configuración de los servicios.")

    print("\n💡 URLs importantes:")
    print("- Orquestador: http://localhost:8000")
    print("- Métricas Prometheus: http://localhost:8000/metrics")
    print("- Prometheus: http://localhost:9090")
    print("- Grafana: http://localhost:3001 (admin/admin)")
    print("- Langfuse: http://localhost:3000")

if __name__ == "__main__":
    main()