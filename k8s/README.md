# Manifiestos Kubernetes - Finance Agent

Archivos YAML para desplegar la aplicación Finance Agent en Kubernetes (Docker Desktop).

## Estructura de Archivos

```
k8s/
├── namespace.yaml                      # Namespace dedicado
├── postgres-secret.yaml                # Credenciales de PostgreSQL
├── postgres-configmap.yaml             # Script SQL de inicialización
├── postgres-pvc.yaml                   # Volumen persistente
├── postgres-statefulset.yaml           # StatefulSet de PostgreSQL
├── postgres-service.yaml               # Service para PostgreSQL
├── agent-deployment.yaml               # Deployment del agente (2 replicas)
├── agent-service.yaml                  # Service NodePort
├── agent-hpa.yaml                      # Autoscaling (opcional)
├── deploy_k8s_docker_desktop.sh        # Script de deployment
└── cleanup.sh                          # Script para limpiar recursos
```

## Deployment Rápido

### 1. Habilitar Kubernetes en Docker Desktop
Ir a Settings > Kubernetes > Enable Kubernetes

### 2. Construir la imagen
```bash
# Desde el directorio raíz (donde está el Dockerfile)
docker build -t finance-agent:latest .
```

### 3. Desplegar con el script automatizado
```bash
cd k8s
chmod +x deploy_k8s_docker_desktop.sh
./deploy_k8s_docker_desktop.sh
```

### 4. Acceder a la aplicación
```
http://localhost:30080
```

---

## Deployment Manual (paso a paso)

Si prefieres hacerlo manual:

```bash
# 1. Namespace
kubectl apply -f namespace.yaml

# 2. Secrets y ConfigMaps
kubectl apply -f postgres-secret.yaml
kubectl apply -f postgres-configmap.yaml

# 3. Persistencia
kubectl apply -f postgres-pvc.yaml

# 4. PostgreSQL
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml

# 5. Esperar que PostgreSQL esté listo
kubectl wait --for=condition=ready pod/postgres-0 -n finance-agent --timeout=180s

# 6. Finance Agent
kubectl apply -f agent-deployment.yaml
kubectl apply -f agent-service.yaml
```

---

## Comandos Útiles

### Ver estado de los pods
```bash
kubectl get pods -n finance-agent
```

Deberías ver algo así:
```
NAME                                READY   STATUS    RESTARTS   AGE
agent-deployment-xxxx-yyyy          1/1     Running   0          2m
agent-deployment-xxxx-zzzz          1/1     Running   0          2m
postgres-0                          1/1     Running   0          3m
```

### Ver logs
```bash
# Logs del agente
kubectl logs -f deployment/agent-deployment -n finance-agent

# Logs de PostgreSQL
kubectl logs -f postgres-0 -n finance-agent
```

### Ver servicios
```bash
kubectl get services -n finance-agent
```

### Ver todos los recursos
```bash
kubectl get all -n finance-agent
```

---

## Probar la Persistencia

1. Abrir http://localhost:30080 y registrar una transacción
2. Ejemplo: "Registra un ingreso de 1500 por venta de teclado"
3. Consultar balance: "¿Cuál es mi balance actual?" → debería mostrar 1500
4. Eliminar el pod de PostgreSQL:
   ```bash
   kubectl delete pod postgres-0 -n finance-agent
   ```
5. Esperar que se recree:
   ```bash
   kubectl wait --for=condition=ready pod/postgres-0 -n finance-agent --timeout=120s
   ```
6. Volver a consultar el balance → debería seguir mostrando 1500 ✅

Esto confirma que los datos persisten en el PersistentVolumeClaim.

---

## Autoscaling (Opcional)

Si quieres probar el escalamiento automático:

```bash
kubectl apply -f agent-hpa.yaml
kubectl get hpa -n finance-agent
```

El HPA escalará de 2 a 5 replicas cuando el CPU supere el 70%.

---

## Limpiar Todo

```bash
./cleanup.sh
```

O manualmente:
```bash
kubectl delete namespace finance-agent
```

---

## Troubleshooting

### Error: ImagePullBackOff
La imagen no está disponible localmente.

Solución:
```bash
docker images | grep finance-agent
# Si no existe, construirla:
docker build -t finance-agent:latest .
```

### Error: CrashLoopBackOff
La aplicación está crasheando.

Solución:
```bash
# Ver logs para identificar el problema
kubectl logs <pod-name> -n finance-agent
```

Problemas comunes:
- PostgreSQL no está listo → esperar más tiempo
- Falta `credentials.json` → verificar que está en la imagen

### No puedo acceder a localhost:30080
Verificar que el servicio está corriendo:
```bash
kubectl get service agent-service -n finance-agent
```

Alternativa (port-forward):
```bash
kubectl port-forward service/agent-service 8000:8000 -n finance-agent
# Acceder en: http://localhost:8000
```

### PostgreSQL no inicia
Ver logs y eventos:
```bash
kubectl logs postgres-0 -n finance-agent
kubectl describe pod postgres-0 -n finance-agent
kubectl get pvc -n finance-agent
```

Si el PVC está en `Pending`, verificar que el `storageClassName` sea `hostpath` (para Docker Desktop).
