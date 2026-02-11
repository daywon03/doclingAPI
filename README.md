# Docling to Markdown API

**Base URL:** `http://localhost:8000`

## Endpoints

### POST /convert-url
Convertit un document depuis une URL.

```bash
curl -X POST "http://localhost:8000/convert-url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/document.pdf"}'
```

**Réponse:**
```json
{
  "source": "https://example.com/document.pdf",
  "markdown": "# Contenu..."
}
```

---

### POST /convert-file
Convertit un fichier uploadé.

```bash
curl -X POST "http://localhost:8000/convert-file" \
  -F "file=@/path/to/document.pdf"
```

**Réponse:**
```json
{
  "filename": "document.pdf",
  "markdown": "# Contenu..."
}
```

---

**Erreurs:** Code 500 si la conversion échoue.
