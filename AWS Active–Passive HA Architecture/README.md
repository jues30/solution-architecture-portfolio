# 🏗️ AWS High Availability Architecture (Active–Passive, Cost-Optimized)

## 📌 1. Contexto de Negocio

Esta arquitectura soporta sistemas críticos de una empresa del sector logístico (TMS y WMS), responsables de la operación diaria a nivel nacional.

### Características del sistema:
- +10.000 transacciones diarias
- Operación en múltiples sedes
- Alta dependencia operativa (impacto directo en negocio)
- Sistemas legacy migrados desde on-premise

---

## 🎯 2. Objetivo de la Arquitectura

Diseñar una solución en AWS que permita:

- Alta disponibilidad controlada
- Reducción de costos frente a soluciones fully-managed
- Migración eficiente desde on-premise
- Cumplimiento de RTO/RPO definidos por el negocio

---

## ⚠️ 3. Restricciones (Constraints)

- 💰 Presupuesto limitado (driver principal)
- ⏱️ RTO: minutos (no inmediato)
- 💾 RPO: basado en backups (no cero pérdida)
- 🏗️ Aplicaciones legacy (no cloud-native)
- 👥 Equipo técnico reducido

---

## 🏛️ 4. Descripción de la Arquitectura

Arquitectura desplegada en AWS bajo un modelo **Multi-AZ Active–Passive**:

### 🔹 Componentes principales:
- VPC con subredes en múltiples AZ
- EC2 para capa de aplicación
- EC2 para bases de datos (MySQL)
- Application Load Balancer (ALB)
- EFS para almacenamiento compartido
- CloudWatch para monitoreo
- AWS Backup para recuperación

### 🔹 Modelo de operación:
- AZ primaria: Activa
- AZ secundaria: Pasiva (failover manual/semiautomático)
- Bases de datos respaldadas mediante backups

---

## 🧠 5. Decisiones Arquitectónicas Clave

### 🔸 EC2 vs RDS

**Decisión:** EC2 para bases de datos  

**Motivación:**
- Reducción de costos
- Control total sobre configuración

**Trade-off:**
- Mayor carga operativa
- Sin failover automático nativo

---

### 🔸 Active–Passive vs Active–Active

**Decisión:** Active–Passive  

**Motivación:**
- Menor costo
- Simplicidad

**Trade-off:**
- Mayor tiempo de recuperación
- Sin balanceo activo

---

### 🔸 Backup vs Replicación en tiempo real

**Decisión:** AWS Backup  

**Motivación:**
- Cumple RPO
- Menor costo

**Trade-off:**
- Posible pérdida de datos reciente
- Mayor RTO

---

## ⚖️ 6. Trade-offs Globales

| Decisión | Beneficio | Sacrificio |
|----------|----------|-----------|
| EC2 vs RDS | Menor costo | Mayor operación |
| Active–Passive | Simplicidad | Mayor RTO |
| Backup | Bajo costo | Mayor RPO |

---

## 📊 7. Resultados

- 99.9% disponibilidad
- 0 caídas desde abril 2025
- -10% costos de infraestructura
- Estabilidad operativa multi-sede

---

## 🔍 8. Evaluación Well-Architected

- Reliability: Alta disponibilidad limitada  
- Cost Optimization: optimización efectiva  
- Performance: adecuada para la carga  
- Operational Excellence: monitoreo activo  
- Security: base implementada, mejoras futuras  

---

## 🚀 9. Mejoras Futuras

- Migración a RDS  
- Evolución a Active–Active  
- Replicación en tiempo real  
- IaC (CloudFormation/Terraform)  
- Serverless parcial  

---

## 📷 10. Diagrama

![AWS Active–Passive HA Architecture](AWS%20Active%E2%80%93Passive%20HA%20Architecture.svg)

---

## 🧩 11. Lecciones Aprendidas

- El costo es un driver crítico  
- La simplicidad reduce riesgos  
- No siempre se necesita HA máxima  
- Arquitectura debe alinearse al negocio  

---

## 👤 Autor

Juan Esteban Peláez García  
Arquitecto de Soluciones de TI  
Bogotá, Colombia  
jues30@gmail.com
