# ☁️ Migración On-Premise a AWS (Cost-Optimized & Stability-Driven)

## 🚀 Executive Summary

Migración de una arquitectura on-premise basada en sistemas monolíticos hacia AWS, impulsada por la necesidad de **reducir deuda técnica, mejorar la estabilidad operativa y optimizar costos**.

La solución implementada permitió:
- Reducir costos mediante un modelo **pay-as-you-go**
- Mejorar la disponibilidad y resiliencia del sistema
- Eliminar limitaciones de infraestructura legacy

---

## 📌 1. Contexto de Negocio

La organización operaba sistemas críticos sobre infraestructura on-premise, con alta dependencia operativa y crecimiento sostenido.

### Problemáticas principales:
- Infraestructura sobredimensionada
- Limitaciones para escalar
- Alta dependencia de hardware físico
- Incremento de incidentes por deuda técnica

---

## 🎯 2. Objetivos de la Migración

- Reducir **deuda técnica**
- Mejorar **estabilidad y disponibilidad**
- Optimizar costos operativos
- Habilitar escalabilidad bajo demanda
- Modernizar la plataforma tecnológica

---

## ⚠️ 3. Restricciones (Constraints)

- Aplicaciones legacy (no cloud-native)
- Necesidad de continuidad operativa (sin downtime prolongado)
- Presupuesto controlado
- Equipo técnico limitado
- Dependencias entre sistemas

---

## 🏛️ 4. Arquitectura Objetivo en AWS

### 🔹 Componentes implementados:

- VPC con segmentación por capas
- EC2 para servidores de aplicación
- EFS para almacenamiento compartido
- Application Load Balancer (ALB)
- CloudWatch para monitoreo y alertas
- IAM para control de accesos
- AWS Backup para respaldo de datos

---

## 🔄 5. Estrategia de Migración

### 🔸 Enfoque adoptado: Lift & Shift (Rehost)

**Motivación:**
- Minimizar riesgos
- Reducir tiempos de migración
- Mantener compatibilidad con sistemas existentes

**Alternativas evaluadas:**

| Estrategia | Pros | Contras |
|----------|------|--------|
| Rehost (Lift & Shift) | Rápida implementación | No moderniza completamente |
| Replatform | Mejora parcial | Mayor complejidad |
| Refactor | Alta optimización | Alto costo y tiempo |

**Decisión final:** Rehost, con evolución progresiva posterior

---

## 🧠 6. Decisiones Arquitectónicas Clave

### 🔸 1. AWS vs On-Premise

**Motivación:**
- Eliminación de dependencia de hardware
- Escalabilidad bajo demanda
- Modelo de costos variable

---

### 🔸 2. EC2 vs Servicios Fully Managed

**Decisión:** Uso de EC2

**Motivación:**
- Compatibilidad con aplicaciones legacy
- Control total sobre entorno
- Optimización de costos

**Trade-off:**
- Mayor carga operativa
- Menor automatización

---

### 🔸 3. Uso de EFS

**Motivación:**
- Necesidad de almacenamiento compartido
- Soporte para múltiples instancias

---

### 🔸 4. ALB para distribución de tráfico

**Motivación:**
- Alta disponibilidad
- Balanceo eficiente entre instancias

---

## ⚖️ 7. Trade-offs Globales

| Decisión | Beneficio | Sacrificio |
|----------|----------|-----------|
| Rehost | Rápido y seguro | Menor modernización |
| EC2 | Menor costo | Mayor operación |
| AWS | Escalabilidad | Dependencia cloud |

---

## 📊 8. Resultados Obtenidos

- 10% reducción de costos de infraestructura
- Mejora significativa en estabilidad operativa
- Eliminación de sobredimensionamiento
- Arquitectura productiva sin indisponibilidad desde implementación

---

## 💼 9. Impacto en el Negocio

- Continuidad operativa garantizada
- Mayor capacidad de respuesta ante crecimiento
- Reducción de riesgos asociados a infraestructura física
- Optimización del gasto tecnológico (FinOps)

---

## 🔍 10. Evaluación Well-Architected

- Reliability: mejora frente a on-premise  
- Cost Optimization: pago por consumo  
- Performance Efficiency: recursos ajustados  
- Operational Excellence: monitoreo activo  
- Security: control de accesos con IAM  

---

## ⚠️ 11. Riesgos Identificados

- Dependencia de operación manual
- Aplicaciones no optimizadas para cloud
- Riesgo de incremento de costos sin control

---

## 🚀 12. Mejoras Futuras

- Migración a RDS  
- Arquitectura cloud-native  
- IaC (CloudFormation/Terraform)  
- CI/CD  
- Microservicios  

---

## 📷 13. Diagrama

![Migración monolito a AWS](./monolito_to_aws_architecture.svg)

---

## 🧩 14. Lecciones Aprendidas

- La migración no implica modernización inmediata  
- El enfoque incremental reduce riesgos  
- El costo es un driver clave  
- La deuda técnica se gestiona progresivamente  

---

## 👤 Autor

Juan Esteban Peláez García  
Arquitecto de Soluciones de TI  
Bogotá, Colombia  
jues30@gmail.com
