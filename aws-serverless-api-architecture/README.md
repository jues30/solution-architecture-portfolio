# 📚 La Trama Infinita — Plataforma Serverless en AWS

> Portal web para la gestión y difusión de escritores, obras literarias y noticias culturales, desplegado completamente sobre infraestructura serverless en Amazon Web Services.

---

## 📐 Descripción General

Aplicación web full-stack sin servidores (serverless) con el backend construido en **FastAPI** (Python) y expuesto a través de **AWS Lambda + API Gateway HTTP API**. El tráfico se distribuye globalmente mediante **Amazon CloudFront**, que actúa como CDN y capa de caché frente al API Gateway. El contenido estático y los archivos binarios (fotos, PDFs) se almacenan en **Amazon S3**, los datos estructurados en **Amazon DynamoDB**, y las credenciales del administrador se gestionan de forma segura en **AWS Secrets Manager**. El despliegue de la infraestructura se gestiona con **AWS SAM (Serverless Application Model)**.

---

## 🏗️ Diagrama de Arquitectura

```
                    ┌──────────────────────────────────────────────────┐
                    │                    CLIENTE                        │
                    │      Navegador Web (HTML + CSS + JS vanilla)      │
                    └──────────────────────┬───────────────────────────┘
                                           │ HTTPS
                                           ▼
                    ┌──────────────────────────────────────────────────┐
                    │           Amazon CloudFront (CDN)                 │
                    │   • Distribución global con baja latencia         │
                    │   • Caché de respuestas estáticas                 │
                    │   • HTTPS terminado en el edge                    │
                    └──────────────────────┬───────────────────────────┘
                                           │ Forward
                                           ▼
                    ┌──────────────────────────────────────────────────┐
                    │         AWS API Gateway (HTTP API)                │
                    │         Ruta: /{proxy+}  ANY method               │
                    └──────────────────────┬───────────────────────────┘
                                           │ Invoke
                                           ▼
                    ┌──────────────────────────────────────────────────┐
                    │            AWS Lambda Function                    │
                    │   Runtime: Python 3.9  |  Memory: 256 MB         │
                    │   Timeout: 30s  |  Handler: app.handler           │
                    │                                                   │
                    │   ┌───────────────────────────────────────────┐  │
                    │   │     FastAPI + Mangum (ASGI adapter)       │  │
                    │   │                                           │  │
                    │   │  • Routers: /writers, /noticias           │  │
                    │   │  • Auth: HTTP Basic (credenciales         │  │
                    │   │    obtenidas de Secrets Manager)          │  │
                    │   │  • File upload: multipart/form-data       │  │
                    │   └───────────────────────────────────────────┘  │
                    └───────┬───────────────────────┬──────────────────┘
                            │                       │
          DynamoDB SDK (boto3)                       │  S3 SDK (boto3)
                            ▼                       ▼
       ┌──────────────────────────┐   ┌─────────────────────────────┐
       │     Amazon DynamoDB      │   │        Amazon S3            │
       │                          │   │  Bucket: juan-s3-20260306   │
       │  Tabla: Writers          │   │                             │
       │  PK: writerId (String)   │   │  /writers/{id}/photo.webp  │
       │  Atributos: name,        │   │  /writers/{id}/works/*.pdf  │
       │  biography, photoKey,    │   │  /noticias/{id}/imagen*.*   │
       │  works[], country,       │   │                             │
       │  instagram, facebook,    │   │  Acceso vía Presigned URLs  │
       │  tiktok, website         │   │  (expiración: 1 hora)       │
       │                          │   └─────────────────────────────┘
       │  Tabla: Noticias         │
       │  PK: noticiaId (String)  │             ┌────────────────────────────┐
       │  Atributos: texto,       │             │   AWS Secrets Manager      │
       │  link, imagen1Key,       │             │                            │
       │  imagen2Key, createdAt   │             │  Secret:                   │
       └──────────────────────────┘             │  pagina-serverless/        │
                                                │  admin-credentials         │
                                                │                            │
                                                │  { username, password }    │
                                                └────────────────────────────┘
```

---

## 🧩 Componentes de la Solución

### 1. Frontend (Estático)
- Tres páginas HTML: `index.html` (pública), `escritores.html` (redirección a index) y `admin.html` (protegida por HTTP Basic Auth).
- Renderizado del lado del cliente mediante JavaScript vanilla.
- Estilos en `style.css` con tema oscuro (design system propio con variables CSS).
- Consumo de la API REST mediante `fetch()`.
- Funcionalidades: catálogo de escritores, filtro por géneros literarios, buscador con autocompletado, visor de noticias, galería de obras con rastreo de clics.
- Las plantillas HTML son servidas por **Jinja2** a través del motor de templates de FastAPI.
- El ícono de la aplicación (`icono.png`) se sirve desde `/static/`.

### 2. CDN — Amazon CloudFront
- Distribución global que actúa como punto de entrada único para toda la aplicación.
- Termina las conexiones HTTPS en el edge, reduciendo la latencia percibida por el usuario.
- Reenvía las solicitudes al API Gateway como origen.
- Permite agregar caché de respuestas para rutas de solo lectura (p. ej. `/writers`, `/noticias`).

### 3. Backend — FastAPI sobre AWS Lambda
- Framework: **FastAPI** con adaptador **Mangum** para compatibilidad ASGI ↔ Lambda.
- Autenticación del panel de administración mediante **HTTP Basic Auth** con `secrets.compare_digest` (resistente a timing attacks).
- Las credenciales del admin **no están en el código**: se obtienen en tiempo de ejecución desde **AWS Secrets Manager** (secreto `pagina-serverless/admin-credentials`).
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
| POST | `/writers/{id}/upload-photo` | Subir foto de perfil (→ S3) | — |
| POST | `/writers/{id}/works` | Agregar obra | — |
| PUT | `/writers/{id}/works/{wid}` | Actualizar obra | — |
| DELETE | `/writers/{id}/works/{wid}` | Eliminar obra | — |
| GET | `/writers/{id}/works/{wid}/upload-url` | Presigned URL para subida directa de PDF | — |
| POST | `/writers/{id}/works/{wid}/confirm-pdf` | Confirmar PDF subido directamente a S3 | — |
| POST | `/writers/{id}/works/{wid}/track` | Registrar clic (PDF o link) | — |
| GET | `/noticias` | Listar noticias | — |
| POST | `/noticias` | Crear noticia | ✅ Admin |
| PUT | `/noticias/{id}` | Actualizar noticia | ✅ Admin |
| DELETE | `/noticias/{id}` | Eliminar noticia | ✅ Admin |
| POST | `/noticias/{id}/upload-image/{slot}` | Subir imagen (slot 1 ó 2) | ✅ Admin |

### 4. Gestión de Secretos — AWS Secrets Manager
- El secreto `pagina-serverless/admin-credentials` almacena las credenciales del administrador en formato JSON:
  ```json
  { "username": "<usuario>", "password": "<contraseña>" }
  ```
- Lambda recupera el secreto una sola vez al arrancar (fuera del handler), evitando llamadas repetidas por invocación.
- La función Lambda tiene permiso IAM `secretsmanager:GetSecretValue` restringido al ARN exacto del secreto.

### 5. Almacenamiento — Amazon DynamoDB
- Modelo **NoSQL** con dos tablas independientes, facturación **Pay-per-request**.
- `Writers`: perfil del escritor con lista embebida de obras (`works[]`).
- `Noticias`: publicaciones culturales con hasta dos imágenes referenciadas por clave de S3.
- Las imágenes y PDFs **no se guardan en DynamoDB**; sólo se persiste la `key` del objeto en S3 (`photoKey`, `pdfKey`, `imagen1Key`, `imagen2Key`).

### 6. Almacenamiento de Archivos — Amazon S3
- Bucket único (`juan-s3-20260306`) en la región `us-east-1`.
- Estructura de prefijos organizada por entidad:
  ```
  writers/{writerId}/photo.webp
  writers/{writerId}/works/{workId}.pdf
  noticias/{noticiaId}/imagen{1|2}.{ext}
  ```
- Las fotos de perfil se procesan con **Pillow** antes de subir: redimensionadas a 800×800 px máximo y convertidas a **WebP** (calidad 85).
- Los PDFs se suben **directamente desde el navegador a S3** mediante una Presigned URL de tipo `PUT` generada por Lambda (sin pasar por Lambda el payload binario).
- El acceso a los objetos se realiza exclusivamente mediante **Presigned URLs GET** con vigencia de 3 600 segundos.
- Los objetos **no son públicos**; el bucket tiene CORS configurado dinámicamente para permitir `PUT` desde el navegador.

### 7. Infraestructura como Código — AWS SAM
- `template.yaml` define todos los recursos: tablas DynamoDB, función Lambda y permisos IAM.
- Permisos IAM con **principio de mínimo privilegio**:
  - `DynamoDBCrudPolicy` sobre `Writers` y `Noticias`.
  - `S3CrudPolicy` + permisos de multipart upload sobre el bucket.
  - `s3:PutBucketCors` para configuración de CORS en runtime.
  - `secretsmanager:GetSecretValue` restringido al ARN del secreto de admin.
- `samconfig.toml` parametriza el despliegue para el stack `pagina-serverless` en `us-east-1`.

---

## 🗂️ Estructura del Proyecto

```
pagina-escritores/
├── app.py                  # Aplicación FastAPI + handler Lambda (Mangum)
├── requirements.txt        # Dependencias Python
├── template.yaml           # Infraestructura AWS SAM (IaC)
├── samconfig.toml          # Configuración de despliegue SAM
├── static/
│   ├── style.css           # Hoja de estilos global (tema oscuro)
│   └── icono.png           # Ícono / logotipo de La Trama Infinita
└── templates/
    ├── index.html          # Página pública (escritores + noticias)
    ├── escritores.html     # Redirección permanente (301) a index
    └── admin.html          # Panel de administración (protegido)
```

---

## ⚙️ Dependencias

```
fastapi          # Framework web ASGI
mangum           # Adaptador FastAPI ↔ AWS Lambda
boto3            # SDK de AWS (DynamoDB, S3, Secrets Manager)
jinja2           # Motor de templates HTML
uvicorn          # Servidor ASGI (desarrollo local)
python-multipart # Soporte para subida de archivos multipart
Pillow           # Procesamiento de imágenes (resize + conversión WebP)
```

---

## 🚀 Despliegue

### Prerrequisitos
- AWS CLI configurado con credenciales válidas.
- AWS SAM CLI instalado.
- Python 3.9+.
- Secreto `pagina-serverless/admin-credentials` creado en AWS Secrets Manager (región `us-east-1`) con la estructura:
  ```json
  { "username": "<usuario>", "password": "<contraseña>" }
  ```

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

> `confirm_changeset = true` en `samconfig.toml` solicita confirmación manual antes de aplicar cambios.

### Ejecución local (desarrollo)

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

> En local, las llamadas a DynamoDB, S3 y Secrets Manager requieren credenciales AWS activas en el entorno.

---

## 🔐 Seguridad

| Aspecto | Implementación |
|---------|----------------|
| Credenciales de admin | Almacenadas en **AWS Secrets Manager** (no en código ni variables de entorno en texto plano) |
| Autenticación admin | HTTP Basic Auth con `secrets.compare_digest` (resistente a timing attacks) |
| Acceso a archivos | Presigned URLs GET con expiración de 1 hora (bucket no público) |
| Subida de PDFs | Presigned URL PUT directa al bucket (payload nunca pasa por Lambda) |
| CDN | CloudFront termina TLS en el edge y oculta el endpoint de API Gateway |
| CORS | Configurado con `allow_origins=["*"]` — restringir al dominio de CloudFront en producción |
| Permisos IAM | Políticas mínimas por recurso |

---

## 📊 Métricas y Analítica

Rastreo de interacciones de usuario persistido directamente en DynamoDB:

- `pdf_clicks`: contador de aperturas de PDF por obra.
- `link_clicks`: contador de clics en enlaces externos por obra.

Se actualizan mediante `POST /writers/{id}/works/{wid}/track` con el cuerpo `{ "type": "pdf" }` o `{ "type": "link" }`.

---

## ⚠️ Consideraciones para Producción

1. **CORS**: restringir `allow_origins` al dominio de la distribución CloudFront.
2. **Runtime**: actualizar de `python3.9` a `python3.12` (Python 3.9 alcanza fin de soporte en Lambda en 2025).
3. **Timeout**: evaluar aumentar el timeout de Lambda para subidas de archivos grandes.
4. **Monitoreo**: habilitar **AWS X-Ray** para trazabilidad distribuida y **CloudWatch Alarms** para errores y throttling.
5. **Caché CloudFront**: configurar TTLs diferenciados por ruta (más agresivo para `/static/`, más corto para `/writers` y `/noticias`).
6. **Rotación de secretos**: habilitar rotación automática del secreto de admin en Secrets Manager.

---

## 🌐 Región AWS

Todos los recursos se despliegan en **`us-east-1` (Norte de Virginia)**.
