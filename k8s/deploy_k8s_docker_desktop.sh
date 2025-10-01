#!/bin/bash

# Script de deployment para Finance Agent en Docker Desktop Kubernetes
# Autor: Trabajo Práctico #2 - Kubernetes
# Uso: ./deploy_k8s_docker_desktop.sh

echo "=========================================="
echo "  Finance Agent - Deployment K8s"
echo "  Docker Desktop"
echo "=========================================="
echo ""

# Verificar que kubectl está disponible
if ! command -v kubectl &> /dev/null
then
    echo "❌ kubectl no está instalado o no está en el PATH"
    echo "   Habilita Kubernetes en Docker Desktop primero"
    exit 1
fi

# Verificar que estamos en el contexto correcto
CONTEXT=$(kubectl config current-context)
if [[ "$CONTEXT" != "docker-desktop" ]]; then
    echo "⚠️  Contexto actual: $CONTEXT"
    echo "   Cambiando a docker-desktop..."
    kubectl config use-context docker-desktop
fi

echo "✓ Usando contexto: docker-desktop"
echo ""

# Paso 1: Namespace
echo "1. Creando namespace..."
kubectl apply -f namespace.yaml

# Paso 2: Secrets y ConfigMaps
echo ""
echo "2. Configurando secrets y configmaps..."
kubectl apply -f postgres-secret.yaml
kubectl apply -f postgres-configmap.yaml

# Paso 3: Persistencia
echo ""
echo "3. Creando volumen persistente..."
kubectl apply -f postgres-pvc.yaml

# Paso 4: PostgreSQL
echo ""
echo "4. Desplegando PostgreSQL..."
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml

# Esperar a que PostgreSQL esté listo
echo ""
echo "5. Esperando que PostgreSQL inicie (puede tardar 1-2 min)..."
kubectl wait --for=condition=ready pod/postgres-0 -n finance-agent --timeout=180s

if [ $? -eq 0 ]; then
    echo "   ✓ PostgreSQL está listo"
else
    echo "   ❌ PostgreSQL tardó demasiado en iniciar"
    echo "   Verifica los logs: kubectl logs postgres-0 -n finance-agent"
    exit 1
fi

# Paso 6: Finance Agent
echo ""
echo "6. Desplegando Finance Agent..."
kubectl apply -f agent-deployment.yaml
kubectl apply -f agent-service.yaml

# Verificar deployment
echo ""
echo "7. Verificando pods..."
sleep 5
kubectl get pods -n finance-agent

echo ""
echo "=========================================="
echo "  ✅ Deployment completado!"
echo "=========================================="
echo ""
echo "Acceder a la aplicación:"
echo "  👉 http://localhost:30080"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:  kubectl logs -f deployment/agent-deployment -n finance-agent"
echo "  Ver pods:  kubectl get pods -n finance-agent"
echo "  Limpiar:   ./cleanup.sh"
echo ""
