# Arquitectura de Soluciones TI

> Documento de referencia. Describe el diseño de infraestructura en nube implementado en AWS para soportar los sistemas WMS (Warehouse Management System) y TMS (Transportation Management System).

---

## Diagrama de Arquitectura

![Arquitectura](AAWS Active–Passive HA Architecture.svg)

---

## Descripción General

La arquitectura desplegada en AWS soporta ambientes de **producción y pruebas** para los sistemas WMS y TMS, además de componentes de integración, seguridad y conectividad híbrida con la infraestructura on-premise de la organización. El diseño prioriza la eficiencia en costos manteniendo los niveles de disponibilidad y recuperación requeridos por el negocio.

---

## Topología de Red y Conectividad

### Acceso de Usuarios

| Origen | Método de acceso |
|--------|-----------------|
| Usuarios públicos (Internet) | Route 53 → Internet Gateway (IGW) |
| Usuarios internos / on-premise | SD-WAN → Customer Gateway → Transit Gateway |

### Componentes de Entrada

- **Route 53**: Servicio de DNS administrado. Resuelve los nombres de dominio y enruta el tráfico entrante hacia los recursos correctos dentro de la VPC de aplicación.
- **Internet Gateway (IGW)**: Punto de entrada para el tráfico proveniente de Internet hacia la VPC.
- **SD-WAN / Customer Gateway**: Establece la conectividad segura entre la red corporativa on-premise y el entorno cloud. Permite que los usuarios internos y los servidores legacy accedan a los sistemas alojados en AWS sin exponer tráfico por Internet.
- **Transit Gateway**: Hub central de enrutamiento que interconecta las VPCs internas. Facilita la comunicación entre la VPC de seguridad/red y la VPC de aplicaciones de forma escalable y controlada.

---

## VPCs y Subredes

La arquitectura se organiza en dos VPCs principales:

### VPC 1 — Seguridad / Firewall

Contiene los firewalls virtuales **FortiGate** desplegados en dos Availability Zones independientes, en subredes privadas. FortiGate actúa como barrera de seguridad perimetral para el tráfico que transita entre la red on-premise y las aplicaciones en la nube.

### VPC 2 — Aplicaciones y Datos

VPC principal donde residen todos los servicios de aplicación y bases de datos. Se subdivide en múltiples subredes privadas distribuidas en dos Availability Zones.

---

## Modelo de Alta Disponibilidad — Activo / Pasivo

La arquitectura utiliza un modelo de **dos Availability Zones en configuración activo/pasivo**:

- **AZ izquierda (Activo)**: Recibe y procesa el 100% del tráfico de producción en condiciones normales.
- **AZ derecha (Pasivo)**: Réplica en espera lista para asumir operaciones en caso de falla de la AZ activa.

Esta decisión fue tomada conscientemente por **restricciones de presupuesto**. Un modelo activo/activo, si bien ofrece mayor resiliencia y distribución de carga, implica el doble de recursos de cómputo corriendo simultáneamente. El modelo activo/pasivo reduce significativamente el costo operativo al mantener la AZ pasiva en un estado de baja utilización hasta que sea necesaria su activación.

El **Network Load Balancer (ELB/NLB)** se encarga de dirigir el tráfico hacia la AZ activa y, ante un evento de falla, de redirigir las conexiones hacia la AZ pasiva de manera transparente para los usuarios.

---

## Componentes de Aplicación

Todos los servicios de aplicación se despliegan en instancias **EC2** dentro de subredes privadas, organizados por ambiente:

| Sistema | Ambiente | AZ Activa | AZ Pasiva |
|---------|----------|-----------|-----------|
| WMS | Producción | ✅ EC2 | ✅ EC2 (pasivo) |
| TMS | Producción | ✅ EC2 | ✅ EC2 (pasivo) |
| WMS | Pruebas | ✅ EC2 | ✅ EC2 (pasivo) |
| TMS | Pruebas | ✅ EC2 | ✅ EC2 (pasivo) |
| N8N (Automatización) | Producción | ✅ EC2 | ✅ EC2 (pasivo) |
| SVN (Control de versiones) | Producción | ✅ EC2 | ✅ EC2 (pasivo) |

Los ambientes de producción y pruebas se encuentran aislados en subredes privadas separadas dentro de la misma VPC, garantizando segmentación de red entre ellos.

**Auto Scaling Groups** protegen los ambientes de producción y pruebas, permitiendo escalar horizontalmente el número de instancias ante incrementos de demanda, sin intervención manual.

---

## Bases de Datos — EC2 vs RDS

### Decisión de Arquitectura: EC2 sobre RDS

Las bases de datos de WMS y TMS (tanto producción como pruebas) se implementaron sobre **instancias EC2** en lugar de utilizar el servicio administrado **Amazon RDS**.

**Justificación por costo:**

Amazon RDS ofrece capacidades nativas de alta disponibilidad (Multi-AZ), backups automáticos, actualizaciones de motor gestionadas y réplicas de lectura. Sin embargo, estas características tienen un costo significativamente mayor al de una instancia EC2 equivalente. En escenarios donde el presupuesto es una restricción primaria, RDS puede representar entre 2x y 3x el costo de una instancia EC2 con el mismo motor de base de datos.

Al desplegar las bases de datos en EC2, la organización obtiene un control granular sobre el tamaño de la instancia, el motor, los parámetros de configuración y el costo total, a cambio de asumir la gestión operativa del motor de base de datos (patching, tuning, monitoreo).

**Justificación por RTO/RPO:**

La viabilidad de esta decisión se sustenta en que los objetivos de tiempo de recuperación (RTO) y punto de recuperación (RPO) definidos para estos sistemas **permiten una estrategia de respaldo basada en snapshots** en lugar de réplicas síncronas en tiempo real:

- El **RPO** (máxima pérdida de datos tolerable) es compatible con ventanas de backup periódicas. No se requiere replicación transaccional continua, lo que elimina la necesidad de RDS Multi-AZ o Read Replicas.
- El **RTO** (tiempo máximo tolerable de indisponibilidad) permite un proceso de restauración desde backup antes de que el impacto al negocio sea crítico. Esto hace viable la restauración de un snapshot de EBS en lugar de un failover automático de segundos.

### Estrategia de Respaldo — AWS Backup

El respaldo de las instancias EC2 que alojan las bases de datos se gestiona mediante **AWS Backup**, que centraliza y automatiza la creación de snapshots de los volúmenes EBS asociados.

AWS Backup permite definir políticas de retención, frecuencia de backups y ventanas de mantenimiento desde una consola unificada, sin necesidad de scripts personalizados. Los snapshots se almacenan en S3 de forma duradera y pueden restaurarse en minutos a una nueva instancia EC2, cumpliendo con el RTO acordado.

---

## Balanceo de Carga

- **Network Load Balancer (NLB/ELB)**: Distribuye el tráfico de red de capa 4 (TCP/UDP) hacia las instancias de aplicación en la AZ activa. Proporciona alta disponibilidad a nivel de cómputo y actúa como punto de conmutación ante fallos.

---

## Almacenamiento Compartido

- **Amazon EFS (Elastic File System)**: Sistema de archivos NFS administrado y elástico, compartido entre instancias EC2 cuando se requiere acceso concurrente a archivos desde múltiples servidores (configuraciones, logs compartidos, artefactos de integración).
- **AWS Transfer for SFTP**: Servicio administrado que expone un endpoint SFTP para la transferencia segura de archivos hacia y desde Amazon S3 o EFS. Utilizado para integraciones de datos con terceros y sistemas externos.

---

## Seguridad

La arquitectura implementa un enfoque de seguridad en capas (*defense in depth*):

| Servicio | Función |
|---------|---------|
| **FortiGate (EC2)** | Firewall de próxima generación (NGFW) para inspección de tráfico norte-sur entre on-premise y cloud |
| **AWS WAF** | Firewall de aplicaciones web. Protege contra ataques OWASP Top 10, SQL injection, XSS y reglas personalizadas |
| **Security Groups** | Firewall stateful a nivel de instancia. Controla el tráfico entrante y saliente por puerto, protocolo e IP origen/destino |
| **Amazon Inspector** | Evaluación continua de vulnerabilidades en instancias EC2. Detecta exposiciones de software y configuraciones inseguras |
| **Amazon GuardDuty** | Servicio de detección de amenazas basado en inteligencia artificial. Analiza logs de VPC Flow, DNS y CloudTrail para identificar comportamientos anómalos |
| **AWS Security Hub** | Consola centralizada de gestión de hallazgos de seguridad. Agrega alertas de GuardDuty, Inspector y otros servicios para priorización y respuesta |

---

## Observabilidad

| Servicio | Función |
|---------|---------|
| **Amazon CloudWatch** | Recolección de métricas, logs y alarmas. Monitoreo de salud de instancias EC2, métricas de red, uso de recursos y eventos de aplicación |

---

## Resumen de Decisiones Arquitectónicas

| Decisión | Alternativa considerada | Razón de la elección |
|----------|------------------------|----------------------|
| EC2 para bases de datos | Amazon RDS | Reducción de costo. El RTO/RPO del negocio es compatible con restauración desde backup, eliminando la necesidad de las capacidades premium de RDS |
| AWS Backup para respaldo | Backups nativos de RDS / scripts custom | Centralización, automatización y menor costo operativo. Compatible con el RPO definido |
| Modelo activo/pasivo | Activo/activo Multi-AZ | Reducción de costo de infraestructura. El negocio acepta el tiempo de conmutación del modelo pasivo a cambio de menor gasto en recursos de cómputo |
| FortiGate en EC2 | AWS Network Firewall / Transit Gateway con inspección | Reuso de licencias existentes de Fortinet y familiaridad operativa del equipo de seguridad |
| Transit Gateway | VPC Peering directo | Escalabilidad y mantenibilidad. Permite agregar nuevas VPCs sin rediseño de la conectividad |

---

## Tecnologías y Servicios Utilizados

**AWS:** Route 53, Internet Gateway, Transit Gateway, VPC, Subredes privadas, EC2, Auto Scaling, Network Load Balancer, EFS, AWS Transfer for SFTP, AWS Backup, CloudWatch, WAF, Inspector, GuardDuty, Security Hub

**Software sobre EC2:** FortiGate (NGFW), WMS, TMS, N8N (automatización de workflows), SVN (control de versiones)

**Conectividad híbrida:** SD-WAN, Customer Gateway

---
## Autor

**Juan Esteban Peláez**  
Arquitecto de Soluciones TI  

---

*Arquitectura de soluciones TI — documentación técnica de proyectos reales con decisiones justificadas.*