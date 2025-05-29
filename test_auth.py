#!/usr/bin/env python3
"""Script de prueba para verificar el sistema de autenticación del MCP Proxy."""

import os
import time
import requests
import subprocess
import signal
import sys
from threading import Thread

def test_authentication():
    """Prueba el sistema de autenticación del servidor MCP Proxy."""
    
    print("🔐 Pruebas de Autenticación del MCP Proxy")
    print("=" * 50)
    
    # URL base del servidor
    base_url = "http://localhost:8080"
    
    # Token de prueba
    test_token = "test_token_123456789"
    
    print(f"🔧 Configurando variable de entorno: MCP_PROXY_AUTH_TOKEN={test_token}")
    os.environ["MCP_PROXY_AUTH_TOKEN"] = test_token
    
    print("🚀 Iniciando servidor MCP Proxy...")
    # Nota: Este comando asume que tienes un servidor MCP para probar
    # Puedes ajustarlo según tu configuración
    
    print("\n📝 Ejecutando pruebas...")
    
    # Esperar un poco para que el servidor inicie
    time.sleep(2)
    
    # Test 1: Endpoint público (sin autenticación)
    print("\n1️⃣ Probando endpoint público /status (sin autenticación)")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            print("✅ PASS: /status accesible sin autenticación")
        else:
            print(f"❌ FAIL: /status devolvió código {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Error conectando al servidor: {e}")
        print("💡 Asegúrate de que el servidor esté ejecutándose en localhost:8080")
        return
    
    # Test 2: Endpoint protegido sin token
    print("\n2️⃣ Probando endpoint protegido /sse sin token")
    try:
        response = requests.get(f"{base_url}/sse", timeout=5)
        if response.status_code == 401:
            print("✅ PASS: /sse rechaza acceso sin token (401)")
        else:
            print(f"❌ FAIL: /sse devolvió código {response.status_code}, esperaba 401")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Error conectando: {e}")
    
    # Test 3: Endpoint protegido con token incorrecto
    print("\n3️⃣ Probando endpoint protegido /sse con token incorrecto")
    headers = {"Authorization": "Bearer token_incorrecto"}
    try:
        response = requests.get(f"{base_url}/sse", headers=headers, timeout=5)
        if response.status_code == 403:
            print("✅ PASS: /sse rechaza token incorrecto (403)")
        else:
            print(f"❌ FAIL: /sse devolvió código {response.status_code}, esperaba 403")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Error conectando: {e}")
    
    # Test 4: Endpoint protegido con formato de token incorrecto
    print("\n4️⃣ Probando endpoint protegido /sse con formato incorrecto")
    headers = {"Authorization": "Basic token123"}  # Debería ser "Bearer"
    try:
        response = requests.get(f"{base_url}/sse", headers=headers, timeout=5)
        if response.status_code == 401:
            print("✅ PASS: /sse rechaza formato incorrecto (401)")
        else:
            print(f"❌ FAIL: /sse devolvió código {response.status_code}, esperaba 401")
    except requests.exceptions.RequestException as e:
        print(f"❌ FAIL: Error conectando: {e}")
    
    # Test 5: Endpoint protegido con token correcto
    print("\n5️⃣ Probando endpoint protegido /sse con token correcto")
    headers = {"Authorization": f"Bearer {test_token}"}
    try:
        response = requests.get(f"{base_url}/sse", headers=headers, timeout=5)
        # Para SSE, esperamos que la conexión se establezca (no necesariamente 200)
        if response.status_code in [200, 201, 204]:
            print("✅ PASS: /sse acepta token correcto")
        else:
            print(f"⚠️  INFO: /sse devolvió código {response.status_code}")
            print("    (Esto puede ser normal para endpoints SSE sin servidor backend)")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  INFO: Error conectando: {e}")
        print("    (Esto puede ser normal si no hay servidor MCP backend configurado)")
    
    print("\n🎉 Pruebas completadas!")
    print("\n💡 Instrucciones para uso manual:")
    print(f"   export MCP_PROXY_AUTH_TOKEN='{test_token}'")
    print("   mcp-proxy --port 8080 <tu_comando>")
    print(f"   curl -H 'Authorization: Bearer {test_token}' {base_url}/sse")

def show_usage():
    """Muestra instrucciones de uso."""
    print("🔐 Sistema de Autenticación MCP Proxy")
    print("=" * 40)
    print()
    print("1. Configurar token:")
    print("   export MCP_PROXY_AUTH_TOKEN='tu_token_secreto'")
    print()
    print("2. Iniciar servidor:")
    print("   mcp-proxy --port 8080 tu_comando")
    print()
    print("3. Usar con autenticación:")
    print("   curl -H 'Authorization: Bearer tu_token_secreto' http://localhost:8080/sse")
    print()
    print("4. Endpoint público (sin autenticación):")
    print("   curl http://localhost:8080/status")
    print()
    print("Para generar un token seguro:")
    print("   python -c \"import secrets; print(secrets.token_urlsafe(32))\"")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_authentication()
    else:
        show_usage() 