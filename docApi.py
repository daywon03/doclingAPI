from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from docling.document_converter import DocumentConverter
import tempfile
import os
import uvicorn

app = FastAPI(title="Docling to Markdown API")

converter = DocumentConverter()

class ConvertUrlRequest(BaseModel):
    url: str

# --- Convertir depuis une URL ---
@app.post("/convert-url")
def convert_from_url(payload: ConvertUrlRequest):
    try:
        # Docling gère directement le téléchargement depuis l'URL
        doc = converter.convert(payload.url).document
        markdown = doc.export_to_markdown()
        return {
            "source": payload.url,
            "markdown": markdown
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Docling conversion failed: {str(e)}")


# --- Convertir depuis un fichier uploadé ---
@app.post("/convert-file")
async def convert_from_file(file: UploadFile = File(...)):
    tmp_path = None
    try:
        # On écrit temporairement le fichier
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        doc = converter.convert(tmp_path).document
        markdown = doc.export_to_markdown()
        return {
            "filename": file.filename,
            "markdown": markdown
        }

    except Exception as e:
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
