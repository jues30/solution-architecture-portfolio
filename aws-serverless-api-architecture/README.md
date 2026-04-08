# 📚 Plataforma de Escritores — Arquitectura Serverless en AWS

> Portal web para la gestión y difusión de escritores, obras literarias y noticias culturales, desplegado completamente sobre infraestructura serverless en Amazon Web Services.

---

## 📐 Descripción General

Esta solución implementa una aplicación web full-stack sin servidores (serverless), donde el backend está construido con **FastAPI** (Python) y expuesto a través de **AWS Lambda + API Gateway HTTP API**. El contenido estático y los archivos binarios (fotos, PDFs) se almacenan en **Amazon S3**, y los datos estructurados residen en tablas de **Amazon DynamoDB**. El despliegue de la infraestructura se gestiona con **AWS SAM (Serverless Application Model)**.

---

## 🏗️ Diagrama de Arquitectura

```
                        ┌─────────────────────────────────────────────┐
                        │                  CLIENTE                     │
                        │     Navegador Web (HTML + CSS + JS vanilla)  │
                        └───────────────────┬─────────────────────────┘
                                            │ HTTPS
                                            ▼
                        ┌─────────────────────────────────────────────┐
                        │         AWS API Gateway (HTTP API)           │
                        │         Ruta: /{proxy+}  ANY method          │
                        └───────────────────┬─────────────────────────┘
                                            │ Invoke
                                            ▼
                        ┌─────────────────────────────────────────────┐
                        │           AWS Lambda Function                │
                        │   Runtime: Python 3.9  |  Memory: 256 MB    │
                        │   Timeout: 10s  |  Handler: app.handler      │
                        │                                              │
                        │   ┌──────────────────────────────────────┐  │
                        │   │  FastAPI + Mangum (ASGI adapter)     │  │
                        │   │                                      │  │
                        │   │  • Routers: /writers, /noticias      │  │
                        │   │  • Auth: HTTP Basic (admin)          │  │
                        │   │  • File upload: multipart/form-data  │  │
                        │   └──────────────────────────────────────┘  │
                        └──────┬──────────────────────┬───────────────┘
                               │                      │
                 DynamoDB SDK  │                      │  S3 SDK (boto3)
                               ▼                      ▼
          ┌────────────────────────┐     ┌────────────────────────────┐
          │     Amazon DynamoDB    │     │       Amazon S3             │
          │                        │     │   Bucket: juan-s3-20260306  │
          │  Tabla: Writers        │     │                            │
          │  PK: writerId (String) │     │  /writers/{id}/photo.*     │
          │  Atributos: name,      │     │  /writers/{id}/works/*.pdf │
          │  biography, photoKey,  │     │  /noticias/{id}/imagen*.* │
          │  works[], country,     │     │                            │
          │  instagram, facebook,  │     │  Acceso vía Presigned URLs │
          │  tiktok, website       │     │  (expiración: 1 hora)      │
          │                        │     └────────────────────────────┘
          │  Tabla: Noticias       │
          │  PK: noticiaId (String)│
          │  Atributos: texto,     │
          │  link, imagen1Key,     │
          │  imagen2Key, createdAt │
          └────────────────────────┘
```

---

## 🧩 Componentes de la Solución

### 1. Frontend (Estático)
- Tres páginas HTML: `index.html` (pública), `escritores.html` y `admin.html` (protegida).
- Renderizado del lado del cliente mediante JavaScript vanilla.
- Estilos en `style.css` con tema oscuro (design system propio con variables CSS).
- Consumo de la API REST mediante `fetch()`.
- Funcionalidades: catálogo de escritores, filtro por géneros literarios, buscador con autocompletado, visor de noticias, galería de obras con rastreo de clics.
- Las plantillas HTML son servidas por **Jinja2** a través del motor de templates de FastAPI.

### 2. Backend — FastAPI sobre AWS Lambda
- Framework: **FastAPI** con adaptador **Mangum** para compatibilidad ASGI ↔ Lambda.
- Autenticación del panel de administración mediante **HTTP Basic Auth** (usuario/contraseña con comparación constante para prevenir timing attacks).
- El handler de Lambda es `app.handler` generado por Mangum.

#### Endpoints disponibles

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Página principal | — |
| GET | `/admin` | Panel de administración | ✅ Admin |
| GET | `/writers` | Listar todos los escritores | — |
| POST | `/writers` | Crear escritor | — |
| GET | `/writers/{id}` | Obtener escritor por ID | — |
| PUT | `/writers/{id}` | Actualizar escritor | — |
| DELETE | `/writers/{id}` | Eliminar escritor | — |
| POST | `/writers/{id}/upload-photo` | Subir foto de perfil | — |
| POST | `/writers/{id}/works` | Agregar obra | — |
| PUT | `/writers/{id}/works/{wid}` | Actualizar obra | — |
| DELETE | `/writers/{id}/works/{wid}` | Eliminar obra | — |
| POST | `/writers/{id}/works/{wid}/upload-pdf` | Subir PDF de obra | — |
| POST | `/writers/{id}/works/{wid}/track` | Registrar clic (PDF o link) | — |
| GET | `/noticias` | Listar noticias | — |
| POST | `/noticias` | Crear noticia | ✅ Admin |
| PUT | `/noticias/{id}` | Actualizar noticia | ✅ Admin |
| DELETE | `/noticias/{id}` | Eliminar noticia | ✅ Admin |
| POST | `/noticias/{id}/upload-image/{slot}` | Subir imagen (slot 1 ó 2) | ✅ Admin |

### 3. Almacenamiento — Amazon DynamoDB
- Modelo **NoSQL** con dos tablas independientes, facturación **Pay-per-request** (sin capacidad aprovisionada).
- `Writers`: almacena el perfil del escritor con una lista embebida de obras (`works[]`) como atributo de tipo lista en el mismo ítem.
- `Noticias`: almacena publicaciones culturales con hasta dos imágenes referenciadas por clave de S3.
- Las imágenes y PDFs **no se guardan en DynamoDB**; sólo se persiste la `key` del objeto en S3 (`photoKey`, `pdfKey`, `imagen1Key`, `imagen2Key`).

### 4. Almacenamiento de Archivos — Amazon S3
- Bucket único (`juan-s3-20260306`) en la región `us-east-1`.
- Estructura de prefijos organizada por entidad:
  ```
  writers/{writerId}/photo.{ext}
  writers/{writerId}/works/{workId}.pdf
  noticias/{noticiaId}/imagen{1|2}.{ext}
  ```
- El acceso a los objetos se realiza exclusivamente mediante **Presigned URLs** generadas con boto3, con una vigencia de 3600 segundos (1 hora).
- Los objetos **no son públicos**; la generación de URL falla de forma silenciosa si el objeto no existe.

### 5. Infraestructura como Código — AWS SAM
- El archivo `template.yaml` define todos los recursos: tablas DynamoDB, función Lambda y permisos IAM.
- Permisos IAM aplicados con **políticas mínimas** (least privilege):
  - `DynamoDBCrudPolicy` sobre las tablas `Writers` y `Noticias`.
  - `S3CrudPolicy` sobre el bucket de archivos.
- El archivo `samconfig.toml` parametriza el despliegue para el stack `pagina-serverless` en `us-east-1`.

---

## 🗂️ Estructura del Proyecto

```
pagina-escritores/
├── app.py                  # Aplicación FastAPI + handler Lambda (Mangum)
├── requirements.txt        # Dependencias Python
├── template.yaml           # Infraestructura AWS SAM (IaC)
├── samconfig.toml          # Configuración de despliegue SAM
├── static/
│   └── style.css           # Hoja de estilos global
└── templates/
    ├── index.html          # Página pública (escritores + noticias)
    ├── escritores.html     # Redirección a index
    └── admin.html          # Panel de administración (protegido)
```

---

## ⚙️ Dependencias

```
fastapi          # Framework web ASGI
mangum           # Adaptador FastAPI ↔ AWS Lambda
boto3            # SDK de AWS para Python (DynamoDB, S3)
jinja2           # Motor de templates HTML
uvicorn          # Servidor ASGI (desarrollo local)
python-multipart # Soporte para subida de archivos multipart
```

---

## 🚀 Despliegue

### Prerrequisitos
- AWS CLI configurado con credenciales válidas.
- AWS SAM CLI instalado.
- Python 3.9+.

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd pagina-escritores

# 2. Construir el paquete de despliegue
sam build

# 3. Desplegar en AWS (primera vez — modo guiado)
sam deploy --guided

# 4. Despliegues posteriores
sam deploy
```

> El parámetro `confirm_changeset = true` en `samconfig.toml` solicita confirmación manual antes de aplicar cambios en cada despliegue.

### Ejecución local (desarrollo)

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

> En ejecución local, las llamadas a DynamoDB y S3 requieren credenciales AWS activas en el entorno.

---

## 🔐 Seguridad

| Aspecto | Implementación |
|---------|----------------|
| Autenticación admin | HTTP Basic Auth con `secrets.compare_digest` (resistente a timing attacks) |
| Acceso a archivos | Presigned URLs con expiración de 1 hora (sin exposición pública del bucket) |
| CORS | Configurado con `allow_origins=["*"]` — restringir en producción |
| Permisos IAM | Políticas mínimas por recurso (DynamoDB y S3 por separado) |
| Credenciales | Hardcodeadas en código — **migrar a AWS Secrets Manager en producción** |

---

## 📊 Métricas y Analítica

La solución incorpora rastreo de interacciones de usuario directamente en DynamoDB:

- `pdf_clicks`: contador de apertura de PDF por obra.
- `link_clicks`: contador de clics en enlaces externos por obra.

Estos contadores se actualizan mediante el endpoint `POST /writers/{id}/works/{wid}/track` y se persisten en el ítem del escritor en DynamoDB.

---

## ⚠️ Consideraciones para Producción

1. **Credenciales**: mover usuario/contraseña de admin a **AWS Secrets Manager** o variables de entorno cifradas.
2. **CORS**: restringir `allow_origins` al dominio del frontend.
3. **Runtime**: actualizar de `python3.9` a `python3.12` o superior (3.9 alcanza fin de soporte en AWS Lambda en 2025).
4. **Timeout**: evaluar aumentar el timeout de Lambda para subidas de archivos grandes.
5. **CloudFront**: agregar una distribución de CloudFront frente al API Gateway para caché, HTTPS y mejor latencia global.
6. **Monitoreo**: habilitar **AWS X-Ray** para trazabilidad distribuida y **CloudWatch Alarms** para errores y throttling de Lambda.

---

## 🌐 Región AWS

Todos los recursos se despliegan en **`us-east-1` (Norte de Virginia)**.
