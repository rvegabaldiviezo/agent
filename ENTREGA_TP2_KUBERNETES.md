# Trabajo Práctico #2 - Migración a Kubernetes

## 1. Introducción

Este documento explica cómo migrar la aplicación **Finance Agent** (del TP #1) a Kubernetes, las decisiones técnicas tomadas y los cambios necesarios para lograr un buen escalamiento.

**Aplicación original:**
- Agente financiero en Python 3.11 usando Google ADK (Gemini)
- Base de datos PostgreSQL para persistencia de transacciones
- Servidor web FastAPI en puerto 8000
- Desplegado con Docker Compose

---

## 2. Análisis de la Arquitectura Actual

### Componentes del TP #1:
- **Agent:** Aplicación Python con FastAPI y Google ADK
- **DB:** PostgreSQL 15 con volumen persistente
- **Red:** Comunicación interna entre servicios
- **Persistencia:** Volumen Docker para datos

### Limitaciones para escalamiento:
Con Docker Compose es difícil escalar porque:
- No hay escalamiento horizontal automático
- Si un contenedor falla, hay que reiniciarlo manualmente
- No hay balanceo de carga entre múltiples instancias
- Los recursos (CPU/RAM) son fijos, no se ajustan automáticamente

---

## 3. Arquitectura Propuesta en Kubernetes

### ¿Por qué Kubernetes?

Kubernetes soluciona las limitaciones anteriores:

1. **Escalamiento automático:** Puede crear más pods cuando hay mucha carga y eliminarlos cuando baja
2. **Alta disponibilidad:** Si un pod falla, Kubernetes lo reinicia automáticamente
3. **Balanceo de carga:** Distribuye las peticiones entre todos los pods disponibles
4. **Rolling updates:** Actualiza la aplicación sin que deje de funcionar

### Cambios arquitectónicos propuestos:

#### 1. Separación de configuración
- Las credenciales de PostgreSQL van en **Secrets** (para datos sensibles)
- Las configuraciones generales van en **ConfigMaps**

#### 2. Escalamiento del agente
- Usar **Deployment** con 2 replicas iniciales
- Configurar **HorizontalPodAutoscaler (HPA)** para escalar automáticamente hasta 5 replicas cuando el CPU sube

#### 3. Persistencia de base de datos
- **StatefulSet** para PostgreSQL (mejor que Deployment para bases de datos)
- **PersistentVolumeClaim (PVC)** para que los datos no se pierdan cuando se reinicia un pod

#### 4. Red y exposición
- **Service ClusterIP** para PostgreSQL (solo interno)
- **Service NodePort** para el agente (acceso desde localhost:30080)

---

## 4. Componentes Kubernetes

### 4.1 Namespace
Creamos un namespace dedicado para aislar los recursos:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: finance-agent
```

### 4.2 Cómputo (Pods/Deployments)

#### Deployment del Finance Agent

Ver archivo completo: `k8s/agent-deployment.yaml`

Características principales:
- **2 replicas** del agente corriendo simultáneamente
- **RollingUpdate:** actualiza los pods de a uno sin downtime
- **Health checks:** Kubernetes verifica que el pod está funcionando
- **Límites de recursos:**
  - Requests: 250m CPU, 256Mi RAM (mínimo garantizado)
  - Limits: 500m CPU, 512Mi RAM (máximo permitido)

Fragmento relevante:
```yaml
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
  template:
    spec:
      containers:
      - name: finance-agent
        image: finance-agent:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

#### StatefulSet de PostgreSQL

Ver archivo completo: `k8s/postgres-statefulset.yaml`

Características:
- **1 replica** (suficiente para desarrollo)
- **Nombre estable:** siempre se llama `postgres-0`
- Monta el volumen persistente en `/var/lib/postgresql/data`
- Monta el script de inicialización desde un ConfigMap

### 4.3 Persistencia

#### PersistentVolumeClaim (PVC)

Ver archivo: `k8s/postgres-pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: finance-agent
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: hostpath
```

**Explicación:**
- **ReadWriteOnce:** solo un pod puede escribir a la vez (suficiente para PostgreSQL con 1 replica)
- **5Gi:** espacio de almacenamiento
- **hostpath:** storageClass para Docker Desktop (usa el disco local)

**¿Por qué es importante?**
Sin el PVC, si el pod de PostgreSQL se reinicia, se pierden todos los datos. Con el PVC, los datos persisten.

### 4.4 Red (Services)

#### Service para PostgreSQL

Ver archivo: `k8s/postgres-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: finance-agent
spec:
  type: ClusterIP
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None  # Headless service
```

**ClusterIP:** el servicio solo es accesible dentro del cluster (no se expone afuera).

#### Service para Finance Agent

Ver archivo: `k8s/agent-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-service
  namespace: finance-agent
spec:
  type: NodePort
  selector:
    app: finance-agent
  ports:
  - port: 8000
    targetPort: 8000
    nodePort: 30080
```

**NodePort:** expone el servicio en `localhost:30080` para poder acceder desde el browser.

### 4.5 Configuración

#### Secret para credenciales

Ver archivo: `k8s/postgres-secret.yaml`

Contiene las credenciales de PostgreSQL codificadas en base64:
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB

#### ConfigMap para init.sql

Ver archivo: `k8s/postgres-configmap.yaml`

Contiene el script SQL que crea la tabla `transacciones` al iniciar PostgreSQL.

---

## 5. Escalamiento y Alta Disponibilidad

### HorizontalPodAutoscaler (HPA)

Ver archivo: `k8s/agent-hpa.yaml`

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-hpa
spec:
  scaleTargetRef:
    kind: Deployment
    name: agent-deployment
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**¿Cómo funciona?**
- Mantiene mínimo **2 replicas** corriendo siempre
- Si el uso de CPU promedio supera **70%**, crea más pods (hasta 5)
- Cuando la carga baja, reduce los pods automáticamente

**Beneficio:** la aplicación puede manejar picos de tráfico sin intervención manual.

### Resource Requests y Limits

Los límites de recursos son importantes para dos cosas:

1. **Requests:** Kubernetes garantiza que cada pod tendrá al menos esos recursos
2. **Limits:** Evita que un pod consuma toda la CPU/RAM del servidor

Sin estos límites, el HPA no puede funcionar correctamente.

---

## 6. Cambios en la Arquitectura para Escalamiento

### Comparación: Docker Compose vs Kubernetes

| Aspecto | Docker Compose | Kubernetes |
|---------|----------------|------------|
| **Escalamiento** | Manual (`docker-compose scale`) | Automático (HPA) |
| **Alta disponibilidad** | No | Sí (self-healing) |
| **Balanceo de carga** | No | Sí (automático en Services) |
| **Persistencia** | Volúmenes locales | PV/PVC (más robusto) |
| **Actualizaciones** | Reinicio completo | Rolling updates (sin downtime) |
| **Configuración** | Variables en `.env` | Secrets y ConfigMaps |
| **Monitoreo** | Manual | Integrado (eventos, logs, métricas) |

### Mejoras implementadas:

1. **Múltiples replicas del agente:** Con 2 replicas, si una falla, la otra sigue funcionando
2. **Autoscaling:** Si hay mucho tráfico, Kubernetes crea más pods automáticamente
3. **Persistencia robusta:** El PVC asegura que los datos de PostgreSQL no se pierden
4. **Health checks:** Kubernetes reinicia pods que no responden correctamente
5. **Rolling updates:** Puedo actualizar el código sin que la app deje de funcionar

### Limitaciones actuales y mejoras futuras:

**PostgreSQL con 1 replica:**
- **Problema:** Si PostgreSQL falla, toda la app deja de funcionar
- **Mejora:** Usar un StatefulSet con 3 replicas (1 primaria + 2 secundarias)
- **Alternativa:** Usar una base de datos gestionada en la nube (ej: Cloud SQL)

**Sin monitoreo:**
- **Problema:** Es difícil saber si algo está fallando
- **Mejora:** Integrar Prometheus y Grafana para ver métricas en tiempo real

---

## 7. Instrucciones de Deployment

### Requisitos previos:
- Docker Desktop con Kubernetes habilitado
- Imagen construida: `docker build -t finance-agent:latest .`

### Deployment automatizado:

```bash
cd k8s
chmod +x deploy_k8s_docker_desktop.sh
./deploy_k8s_docker_desktop.sh
```

### Deployment manual (paso a paso):

```bash
# 1. Namespace
kubectl apply -f k8s/namespace.yaml

# 2. Secrets y ConfigMaps
kubectl apply -f k8s/postgres-secret.yaml
kubectl apply -f k8s/postgres-configmap.yaml

# 3. Persistencia
kubectl apply -f k8s/postgres-pvc.yaml

# 4. PostgreSQL
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/postgres-service.yaml

# 5. Esperar que PostgreSQL esté listo
kubectl wait --for=condition=ready pod/postgres-0 -n finance-agent --timeout=180s

# 6. Finance Agent
kubectl apply -f k8s/agent-deployment.yaml
kubectl apply -f k8s/agent-service.yaml

# 7. (Opcional) Autoscaling
kubectl apply -f k8s/agent-hpa.yaml
```

### Verificar deployment:

```bash
kubectl get all -n finance-agent
```

Deberías ver:
- 2 pods del agente (agent-deployment-xxx)
- 1 pod de PostgreSQL (postgres-0)
- 2 servicios (agent-service, postgres-service)

### Acceder a la aplicación:

```
http://localhost:30080
```

### Verificar persistencia:

1. Registrar una transacción en la app
2. Eliminar el pod de PostgreSQL: `kubectl delete pod postgres-0 -n finance-agent`
3. Esperar que se recree: `kubectl wait --for=condition=ready pod/postgres-0 -n finance-agent`
4. Verificar que los datos siguen ahí

✅ Si los datos persisten, el PVC está funcionando correctamente.

---

## 8. Conclusión

La migración a Kubernetes aporta mejoras significativas:

✅ **Escalamiento automático** con HPA
✅ **Alta disponibilidad** con múltiples replicas
✅ **Self-healing** (reinicio automático de pods fallidos)
✅ **Rolling updates** (actualizaciones sin downtime)
✅ **Persistencia robusta** con PVC

**Trade-offs:**
- Más complejidad operativa que Docker Compose
- Requiere aprender conceptos nuevos (pods, services, etc.)
- Necesita más recursos para correr el cluster

**Recomendación:**
Para desarrollo local, Docker Compose sigue siendo más simple. Pero para producción o ambientes donde necesitamos escalamiento y alta disponibilidad, Kubernetes es la mejor opción.

---

## 9. Referencias

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Docker Desktop Kubernetes](https://docs.docker.com/desktop/kubernetes/)
