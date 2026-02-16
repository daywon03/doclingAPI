# 🔄 DoclingAPI — Convertisseur de Documents en Markdown

> API FastAPI utilisant [Docling](https://github.com/DS4SD/docling) (IBM) pour convertir automatiquement des documents (PDF, DOCX, PPTX, HTML, images…) en **Markdown** propre et structuré.

Conçue pour s'intégrer avec **n8n** et **Google Drive** dans un pipeline RAG (Retrieval-Augmented Generation).

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Google Drive                           │
│                                                             │
│  📁 input/          📁 markdown/         📁 done/           │
│  (PDF, DOCX...)     (fichiers .md)       (archives)         │
│       │                  ▲                   ▲              │
│       │                  │                   │              │
└───────┼──────────────────┼───────────────────┼──────────────┘
        │                  │                   │
        ▼                  │                   │
┌─────────────────────────────────────────────────────────────┐
│                     n8n Workflow                             │
│                                                             │
│  🔔 Trigger  →  📥 Download  →  🌐 HTTP Request             │
│  (input/)       (file)          (DoclingAPI)                 │
│                                      │                      │
│                                      ▼                      │
│                                 📝 Code Node                │
│                                 (prépare .md)               │
│                                   │     │                   │
│                                   ▼     ▼                   │
│                          📤 Upload   📦 Move                │
│                          (markdown/) (done/)                │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────┐
│   DoclingAPI         │
│   FastAPI + Docling  │
│   localhost:8000     │
└─────────────────────┘
```

---

## 🚀 Installation

### Prérequis

- Python 3.10+
- pip

### Installation des dépendances

```bash
cd doclingAPI
pip install -r requierments.txt
```

### Lancer l'API

```bash
python3 docApi.py
```

L'API démarre sur `http://localhost:8000`.  
Documentation Swagger automatique : `http://localhost:8000/docs`

---

## 📡 Endpoints de l'API

### `GET /health` — Health Check

Vérifie que l'API est en ligne.

```bash
curl http://localhost:8000/health
```

```json
{ "status": "ok", "service": "docling-api", "version": "1.1.0" }
```

---

### `POST /convert-url` — Conversion depuis une URL

Convertit un document accessible par URL en Markdown.

```bash
curl -X POST "http://localhost:8000/convert-url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://arxiv.org/pdf/2408.09869"}'
```

**Réponse :**

```json
{
  "source": "https://arxiv.org/pdf/2408.09869",
  "markdown": "# Titre du document\n\nContenu converti..."
}
```

---

### `POST /convert-file` — Conversion d'un fichier (JSON)

Upload un fichier et reçoit le Markdown en JSON. **C'est cet endpoint que n8n utilise.**

```bash
curl -X POST "http://localhost:8000/convert-file" \
  -F "file=@document.pdf"
```

**Réponse :**

```json
{
  "filename": "document.pdf",
  "markdown": "# Titre du document\n\nContenu converti..."
}
```

---

### `POST /convert-file-raw` — Conversion d'un fichier (Markdown brut)

Upload un fichier et reçoit directement le texte Markdown (pas de JSON).

```bash
curl -X POST "http://localhost:8000/convert-file-raw" \
  -F "file=@document.pdf"
```

**Réponse :** (text/plain)

```markdown
# Titre du document

Contenu converti en markdown...
```

---

## 📄 Formats supportés

| Format     | Extension      | Support                             |
| ---------- | -------------- | ----------------------------------- |
| PDF        | `.pdf`         | ✅ Complet (texte + OCR + tableaux) |
| Word       | `.docx`        | ✅ Complet                          |
| PowerPoint | `.pptx`        | ✅ Complet                          |
| HTML       | `.html`        | ✅ Complet                          |
| Images     | `.png`, `.jpg` | ✅ Via OCR                          |
| Markdown   | `.md`          | ✅ Pass-through                     |
| AsciiDoc   | `.adoc`        | ✅ Complet                          |
| Excel      | `.xlsx`        | ✅ Tableaux                         |
| CSV        | `.csv`         | ✅ Tableaux                         |

---

## ⚡ Intégration n8n — Guide étape par étape

### Prérequis

- n8n installé et lancé (`http://localhost:5678`)
- DoclingAPI lancée (`http://localhost:8000`)
- Google Drive OAuth2 configuré dans n8n
- 3 dossiers créés dans Google Drive : `input/`, `markdown/`, `done/`

### Étape 1 : Importer le workflow

1. Ouvre n8n → **Workflows** → **Import from File**
2. Importe le fichier `n8n-workflow.json` fourni dans ce repo
3. **⚠️ Remplace les 2 IDs de dossiers** dans les nodes :
   - **Upload Markdown** → `folderId` → ID de ton dossier `markdown/`
   - **Move to Done** → `folderId` → ID de ton dossier `done/`

> **💡 Comment trouver l'ID d'un dossier Google Drive ?**  
> Ouvre le dossier dans Google Drive. L'URL ressemble à :  
> `https://drive.google.com/drive/folders/1ABCxyz123456789`  
> L'ID est la partie après `/folders/` → `1ABCxyz123456789`

### Étape 2 : Comprendre chaque node

| #   | Node                     | Rôle                             | Config clé                                              |
| --- | ------------------------ | -------------------------------- | ------------------------------------------------------- |
| 1   | **Google Drive Trigger** | Surveille `input/` chaque minute | Event: `fileCreated`                                    |
| 2   | **Download File**        | Télécharge le fichier détecté    | FileID: `{{ $json.id }}`                                |
| 3   | **Convert to Markdown**  | Envoie le fichier à DoclingAPI   | POST `localhost:8000/convert-file`, body: binary `file` |

> ⚠️ **n8n dans Docker ?** Utilise `http://host.docker.internal:8000` au lieu de `http://localhost:8000`. Docker isole le réseau du container — `localhost` pointe vers le container, pas vers ta machine.
> | 4 | **Prepare Markdown File** | Crée le fichier .md binaire | Code JavaScript (voir ci-dessous) |
> | 5 | **Upload Markdown** | Upload le .md dans `markdown/` | Binary field: `data` |
> | 6 | **Move to Done** | Déplace l'original dans `done/` | FileID depuis le trigger |

### Étape 3 : Le Code Node expliqué

```javascript
// Récupère le markdown retourné par DoclingAPI
const markdown = $input.first().json.markdown;
const originalName = $("Google Drive Trigger").first().json.name;
const originalFileId = $("Google Drive Trigger").first().json.id;

// Remplace l'extension par .md (ex: "rapport.pdf" → "rapport.md")
const mdFilename = originalName.replace(/\.[^.]+$/, ".md");

// Convertit le texte markdown en binaire pour l'upload Google Drive
const binaryData = Buffer.from(markdown, "utf-8");

return [
  {
    json: {
      originalFileId: originalFileId,
      mdFilename: mdFilename,
      markdownLength: markdown.length,
    },
    binary: {
      data: {
        data: binaryData.toString("base64"),
        mimeType: "text/markdown",
        fileName: mdFilename,
        fileExtension: "md",
      },
    },
  },
];
```

**Ce que fait ce code :**

1. Récupère le contenu markdown de la réponse DoclingAPI
2. Construit le nom du fichier `.md` (même nom que l'original, juste l'extension change)
3. Convertit le texte en données binaires (base64) pour que Google Drive puisse l'uploader comme fichier
4. Passe aussi l'ID du fichier original pour le node "Move to Done"

### Étape 4 : Configuration du HTTP Request (détail)

Dans le node **Convert to Markdown** :

1. **Method** : `POST`
2. **URL** : `http://localhost:8000/convert-file`
3. **Body Content Type** : `Multipart Form Data`
4. **Body Parameters** :
   - **Parameter Type** : `Binary Data`
   - **Name** : `file`
   - **Input Data Field Name** : `data`
5. **Options** → **Timeout** : `120000` (2 minutes, les gros PDF peuvent être longs)

### Étape 5 : Activer le workflow

1. Vérifie que DoclingAPI est lancée : `curl http://localhost:8000/health`
2. Active le workflow dans n8n (toggle en haut à droite)
3. Dépose un fichier PDF dans le dossier `input/` de Google Drive
4. Attends ~1 minute, le trigger poll chaque minute
5. Vérifie que le `.md` apparaît dans `markdown/` et l'original dans `done/`

---

## 🧠 Pour aller plus loin : Pipeline RAG complet

Ce workflow est la **première brique** d'un système RAG. Voici comment l'étendre :

```
Documents → [Ce workflow] → Markdown → Chunking → Embeddings → Vector DB → Retrieval → LLM
                                          │           │              │           │
                                     Code Node   OpenAI/Ollama   Pinecone    GPT-4/Llama
                                     (~500 tokens)               Qdrant
                                                                 Supabase
```

| Étape suivante   | Description                                     | Outil recommandé                          |
| ---------------- | ----------------------------------------------- | ----------------------------------------- |
| **Chunking**     | Découper le markdown en morceaux de ~500 tokens | n8n Code Node + `semchunk`                |
| **Embedding**    | Générer des vecteurs pour chaque chunk          | OpenAI `text-embedding-3-small` ou Ollama |
| **Vector Store** | Stocker les vecteurs avec métadonnées           | Pinecone, Qdrant, ou Supabase pgvector    |
| **Retrieval**    | Chercher les chunks pertinents                  | Recherche par similarité cosinus          |
| **Generation**   | Répondre avec le contexte récupéré              | GPT-4, Claude, ou Llama via Ollama        |

---

## 🐛 Troubleshooting

| Problème                      | Solution                                                |
| ----------------------------- | ------------------------------------------------------- |
| `Connection refused` sur n8n  | Vérifie que DoclingAPI est lancée (`python docApi.py`)  |
| Timeout sur les gros fichiers | Augmente le timeout dans le HTTP Request node (120s+)   |
| Fichier .md vide              | Vérifie les logs de DoclingAPI dans le terminal         |
| Le trigger ne détecte rien    | Vérifie que le fichier est dans le bon dossier `input/` |
| Erreur Google Drive auth      | Reconnecte les credentials OAuth2 dans n8n              |

---

## 📜 Licence

MIT
