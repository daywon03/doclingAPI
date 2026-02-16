from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from docling.document_converter import DocumentConverter
import tempfile
import os
import uvicorn
import logging

# --- Configuration du logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- App FastAPI ---
app = FastAPI(
    title="Docling to Markdown API",
    description="API de conversion de documents (PDF, DOCX, PPTX, HTML...) en Markdown via Docling",
    version="1.1.0"
)

# --- CORS (permet les appels depuis n8n ou d'autres services) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Initialisation du convertisseur Docling ---
converter = DocumentConverter()
logger.info("✅ Docling converter initialized")


# --- Modèles Pydantic ---
class ConvertUrlRequest(BaseModel):
    url: str


# --- Health Check ---
@app.get("/health")
def health_check():
    """Vérifie que l'API est en ligne. Utile pour n8n avant d'envoyer des fichiers."""
    return {"status": "ok", "service": "docling-api", "version": "1.1.0"}


# --- Convertir depuis une URL (retourne JSON) ---
@app.post("/convert-url")
def convert_from_url(payload: ConvertUrlRequest):
    """Convertit un document depuis une URL publique en Markdown (réponse JSON)."""
    logger.info(f"📥 Converting from URL: {payload.url}")
    try:
        doc = converter.convert(payload.url).document
        markdown = doc.export_to_markdown()
        logger.info(f"✅ URL conversion successful: {len(markdown)} chars")
        return {
            "source": payload.url,
            "markdown": markdown
        }
    except Exception as e:
        logger.error(f"❌ URL conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Docling conversion failed: {str(e)}")


# --- Convertir depuis un fichier uploadé (retourne JSON) ---
@app.post("/convert-file")
async def convert_from_file(file: UploadFile = File(...)):
    """Convertit un fichier uploadé en Markdown (réponse JSON avec filename + markdown)."""
    logger.info(f"📥 Converting file: {file.filename}")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        doc = converter.convert(tmp_path).document
        markdown = doc.export_to_markdown()
        logger.info(f"✅ File conversion successful: {file.filename} → {len(markdown)} chars")
        return {
            "filename": file.filename,
            "markdown": markdown
        }

    except Exception as e:
        logger.error(f"❌ File conversion failed: {file.filename} — {str(e)}")
        raise HTTPException(status_code=500, detail=f"Docling conversion failed: {str(e)}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# --- Convertir depuis un fichier uploadé (retourne du Markdown brut) ---
@app.post("/convert-file-raw", response_class=PlainTextResponse)
async def convert_from_file_raw(file: UploadFile = File(...)):
    """
    Convertit un fichier uploadé et retourne le Markdown brut (text/plain).
    Idéal pour n8n → upload direct dans Google Drive sans parsing JSON.
    """
    logger.info(f"📥 Converting file (raw): {file.filename}")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        doc = converter.convert(tmp_path).document
        markdown = doc.export_to_markdown()
        logger.info(f"✅ Raw conversion successful: {file.filename} → {len(markdown)} chars")
        return markdown

    except Exception as e:
        logger.error(f"❌ Raw conversion failed: {file.filename} — {str(e)}")
        raise HTTPException(status_code=500, detail=f"Docling conversion failed: {str(e)}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# --- Lancer le serveur directement si on exécute ce script ---
if __name__ == "__main__":
    uvicorn.run("docApi:app", host="0.0.0.0", port=8000, reload=True)
