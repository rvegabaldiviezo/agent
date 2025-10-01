#!/bin/bash

# Script para limpiar todos los recursos de Finance Agent en Kubernetes
# Uso: ./cleanup.sh

set -e

echo "🧹 Limpiando Finance Agent de Kubernetes"
echo ""

# Colores para output
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

function print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning "Esto eliminará TODOS los recursos de Finance Agent, incluyendo datos de PostgreSQL."
read -p "¿Estás seguro? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Operación cancelada."
    exit 1
fi

echo "Eliminando recursos..."

# Opción 1: Eliminar todo el namespace (más rápido y limpio)
kubectl delete namespace finance-agent

# Opción 2: Eliminar recursos individuales (comentado, usar solo si necesitas más control)
# kubectl delete -f agent-hpa.yaml --ignore-not-found=true
# kubectl delete -f agent-service.yaml --ignore-not-found=true
# kubectl delete -f agent-service-loadbalancer.yaml --ignore-not-found=true
# kubectl delete -f agent-deployment.yaml --ignore-not-found=true
# kubectl delete -f postgres-service.yaml --ignore-not-found=true
# kubectl delete -f postgres-statefulset.yaml --ignore-not-found=true
# kubectl delete -f postgres-pvc.yaml --ignore-not-found=true
# kubectl delete -f postgres-configmap.yaml --ignore-not-found=true
# kubectl delete -f postgres-secret.yaml --ignore-not-found=true
# kubectl delete -f namespace.yaml --ignore-not-found=true

echo ""
echo "✅ Todos los recursos han sido eliminados."
echo ""
echo "Verificar:"
echo "  kubectl get all -n finance-agent"
echo "  (debería mostrar 'No resources found')"
