from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from mangum import Mangum
import boto3
import uuid
import secrets
import datetime

app = FastAPI()
security = HTTPBasic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

s3 = boto3.client("s3")
BUCKET = "juan-s3-20260306"
dynamodb = boto3.resource("dynamodb")
writers_bio_table = dynamodb.Table("Writers")
noticias_table = dynamodb.Table("Noticias")


# ---------- AUTH ----------

def check_admin(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, "jpelaez")
    ok_pass = secrets.compare_digest(credentials.password, "Meladriel.2023")
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=401,
            detail="Acceso denegado",
            headers={"WWW-Authenticate": "Basic"},
        )


# ---------- S3 HELPER ----------

def presigned_get(key: str, expires: int = 3600):
    if not key:
        return None
    try:
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": key},
            ExpiresIn=expires,
        )
    except Exception:
        return None


def enrich_writer(writer: dict) -> dict:
    writer = dict(writer)
    if writer.get("photoKey"):
        writer["photoUrl"] = presigned_get(writer["photoKey"])
    writer["works"] = [
        {**dict(w), "pdfUrl": presigned_get(w.get("pdfKey", ""))}
        for w in writer.get("works", [])
    ]
    return writer


# ---------- HTML ROUTES ----------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/escritores")
def escritores_page():
    return RedirectResponse(url="/", status_code=301)


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, _: HTTPBasicCredentials = Depends(check_admin)):
    return templates.TemplateResponse("admin.html", {"request": request})


# ---------- WRITERS API ----------

@app.get("/writers")
def list_writers():
    response = writers_bio_table.scan()
    return {"writers": [enrich_writer(w) for w in response.get("Items", [])]}


@app.post("/writers")
async def create_writer(request: Request):
    body = await request.json()
    writer_id = str(uuid.uuid4())
    writers_bio_table.put_item(
        Item={
            "writerId": writer_id,
            "name": body["name"],
            "biography": body.get("biography", ""),
            "photoKey": "",
            "works": [],
            "country": body.get("country", ""),
            "instagram": body.get("instagram", ""),
            "facebook": body.get("facebook", ""),
            "tiktok": body.get("tiktok", ""),
            "website": body.get("website", ""),
        }
    )
    return {"writerId": writer_id}


@app.get("/writers/{writer_id}")
def get_writer(writer_id: str):
    resp = writers_bio_table.get_item(Key={"writerId": writer_id})
    writer = resp.get("Item")
    if not writer:
        raise HTTPException(status_code=404, detail="Writer not found")
    return enrich_writer(writer)


@app.put("/writers/{writer_id}")
async def update_writer(writer_id: str, request: Request):
    body = await request.json()
    writers_bio_table.update_item(
        Key={"writerId": writer_id},
        UpdateExpression="SET #n = :name, biography = :bio, country = :country, instagram = :instagram, facebook = :facebook, tiktok = :tiktok, website = :website",
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":name": body["name"],
            ":bio": body.get("biography", ""),
            ":country": body.get("country", ""),
            ":instagram": body.get("instagram", ""),
            ":facebook": body.get("facebook", ""),
            ":tiktok": body.get("tiktok", ""),
            ":website": body.get("website", ""),
        },
    )
    return {"writerId": writer_id}


@app.delete("/writers/{writer_id}")
def delete_writer(writer_id: str):
    writers_bio_table.delete_item(Key={"writerId": writer_id})
    return {"status": "deleted"}


@app.post("/writers/{writer_id}/upload-photo")
async def upload_photo(writer_id: str, file: UploadFile = File(...)):
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    ext = ext_map.get(file.content_type, "jpg")
    photo_key = f"writers/{writer_id}/photo.{ext}"
    content = await file.read()
    s3.put_object(
        Bucket=BUCKET,
        Key=photo_key,
        Body=content,
        ContentType=file.content_type or "image/jpeg",
    )
    writers_bio_table.update_item(
        Key={"writerId": writer_id},
        UpdateExpression="SET photoKey = :pk",
        ExpressionAttributeValues={":pk": photo_key},
    )
    return {"photoKey": photo_key}


@app.post("/writers/{writer_id}/works")
async def add_work(writer_id: str, request: Request):
    body = await request.json()
    work_id = str(uuid.uuid4())
    writers_bio_table.update_item(
        Key={"writerId": writer_id},
        UpdateExpression="SET works = list_append(if_not_exists(works, :empty), :work)",
        ExpressionAttributeValues={
            ":work": [{
                "workId": work_id,
                "title": body["title"],
                "pdfKey": "",
                "link": body.get("link", ""),
                "genre": body.get("genre", ""),
                "pdf_clicks": 0,
                "link_clicks": 0,
            }],
            ":empty": [],
        },
    )
    return {"workId": work_id}


@app.post("/writers/{writer_id}/works/{work_id}/track")
async def track_work(writer_id: str, work_id: str, request: Request):
    body = await request.json()
    track_type = body.get("type")
    resp = writers_bio_table.get_item(Key={"writerId": writer_id})
    writer = resp.get("Item")
    if not writer:
        raise HTTPException(status_code=404, detail="Writer not found")
    works = [dict(w) for w in writer.get("works", [])]
    for w in works:
        if w.get("workId") == work_id:
            if track_type == "pdf":
                w["pdf_clicks"] = int(w.get("pdf_clicks", 0)) + 1
            elif track_type == "link":
                w["link_clicks"] = int(w.get("link_clicks", 0)) + 1
            break
    writers_bio_table.update_item(
        Key={"writerId": writer_id},
        UpdateExpression="SET works = :works",
        ExpressionAttributeValues={":works": works},
    )
    return {"status": "ok"}


@app.put("/writers/{writer_id}/works/{work_id}")
async def update_work(writer_id: str, work_id: str, request: Request):
    body = await request.json()
    resp = writers_bio_table.get_item(Key={"writerId": writer_id})
    writer = resp.get("Item")
    if not writer:
        raise HTTPException(status_code=404, detail="Writer not found")
    works = [dict(w) for w in writer.get("works", [])]
    for w in works:
        if w.get("workId") == work_id:
            w["title"] = body.get("title", w.get("title", ""))
            w["genre"] = body.get("genre", w.get("genre", ""))
            w["link"]  = body.get("link",  w.get("link",  ""))
            break
    writers_bio_table.update_item(
        Key={"writerId": writer_id},
        UpdateExpression="SET works = :works",
        ExpressionAttributeValues={":works": works},
    )
    return {"status": "ok"}


@app.delete("/writers/{writer_id}/works/{work_id}")
def delete_work(writer_id: str, work_id: str):
    resp = writers_bio_table.get_item(Key={"writerId": writer_id})
    writer = resp.get("Item")
    if not writer:
        raise HTTPException(status_code=404, detail="Writer not found")
    works = [dict(w) for w in writer.get("works", []) if w.get("workId") != work_id]
    writers_bio_table.update_item(
        Key={"writerId": writer_id},
        UpdateExpression="SET works = :works",
        ExpressionAttributeValues={":works": works},
    )
    return {"status": "deleted"}


@app.post("/writers/{writer_id}/works/{work_id}/upload-pdf")
async def upload_pdf(writer_id: str, work_id: str, file: UploadFile = File(...)):
    pdf_key = f"writers/{writer_id}/works/{work_id}.pdf"
    content = await file.read()
    s3.put_object(
        Bucket=BUCKET,
        Key=pdf_key,
        Body=content,
        ContentType="application/pdf",
    )
    resp = writers_bio_table.get_item(Key={"writerId": writer_id})
    writer = resp.get("Item")
    if not writer:
        raise HTTPException(status_code=404, detail="Writer not found")
    works = [dict(w) for w in writer.get("works", [])]
    for w in works:
        if w.get("workId") == work_id:
            w["pdfKey"] = pdf_key
            break
    writers_bio_table.update_item(
        Key={"writerId": writer_id},
        UpdateExpression="SET works = :works",
        ExpressionAttributeValues={":works": works},
    )
    return {"pdfKey": pdf_key}


# ---------- NOTICIAS API ----------

def enrich_noticia(n: dict) -> dict:
    n = dict(n)
    if n.get("imagen1Key"):
        n["imagen1Url"] = presigned_get(n["imagen1Key"])
    if n.get("imagen2Key"):
        n["imagen2Url"] = presigned_get(n["imagen2Key"])
    return n


@app.get("/noticias")
def list_noticias():
    response = noticias_table.scan()
    items = sorted(
        [enrich_noticia(n) for n in response.get("Items", [])],
        key=lambda x: x.get("createdAt", ""),
        reverse=True,
    )
    return {"noticias": items}


@app.post("/noticias")
async def create_noticia(request: Request, _: HTTPBasicCredentials = Depends(check_admin)):
    body = await request.json()
    noticia_id = str(uuid.uuid4())
    noticias_table.put_item(
        Item={
            "noticiaId": noticia_id,
            "texto": body["texto"],
            "link": body.get("link", ""),
            "imagen1Key": "",
            "imagen2Key": "",
            "createdAt": datetime.datetime.utcnow().isoformat(),
        }
    )
    return {"noticiaId": noticia_id}


@app.put("/noticias/{noticia_id}")
async def update_noticia(noticia_id: str, request: Request, _: HTTPBasicCredentials = Depends(check_admin)):
    body = await request.json()
    noticias_table.update_item(
        Key={"noticiaId": noticia_id},
        UpdateExpression="SET texto = :t, link = :l",
        ExpressionAttributeValues={
            ":t": body["texto"],
            ":l": body.get("link", ""),
        },
    )
    return {"noticiaId": noticia_id}


@app.delete("/noticias/{noticia_id}")
def delete_noticia(noticia_id: str, _: HTTPBasicCredentials = Depends(check_admin)):
    noticias_table.delete_item(Key={"noticiaId": noticia_id})
    return {"status": "deleted"}


@app.post("/noticias/{noticia_id}/upload-image/{slot}")
async def upload_noticia_image(noticia_id: str, slot: int, file: UploadFile = File(...), _: HTTPBasicCredentials = Depends(check_admin)):
    if slot not in (1, 2):
        raise HTTPException(status_code=400, detail="slot debe ser 1 o 2")
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    ext = ext_map.get(file.content_type, "jpg")
    img_key = f"noticias/{noticia_id}/imagen{slot}.{ext}"
    content = await file.read()
    s3.put_object(
        Bucket=BUCKET,
        Key=img_key,
        Body=content,
        ContentType=file.content_type or "image/jpeg",
    )
    field = f"imagen{slot}Key"
    noticias_table.update_item(
        Key={"noticiaId": noticia_id},
        UpdateExpression=f"SET {field} = :k",
        ExpressionAttributeValues={":k": img_key},
    )
    return {field: img_key}


# ---------- LAMBDA HANDLER ----------

handler = Mangum(app)
