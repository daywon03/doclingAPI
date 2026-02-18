"""
init_weaviate.py — Initialise la collection CoursBUT dans Weaviate

Ce script crée la "table" (collection) qui va stocker les chunks de tes cours.
Chaque chunk a 4 propriétés :
  - content     : le texte du chunk
  - source      : le nom du fichier d'origine (ex: "cours-java.pdf")
  - section     : le titre de la section markdown (ex: "## Héritage")
  - chunk_index : la position du chunk dans le document (0, 1, 2...)

Le vectorizer utilise Gemini text-embedding-004 pour transformer
automatiquement le champ 'content' en vecteur 768D à chaque insertion.
"""
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "ta_clé_gemini_ici":
    print("❌ Configure ta GEMINI_API_KEY dans le fichier .env !")
    print("   → https://aistudio.google.com/apikey")
    exit(1)

print("🔌 Connexion à Weaviate (localhost:8080)...")

with weaviate.connect_to_local(
    headers={"X-Goog-Api-Key": GEMINI_API_KEY}
) as client:

    # Vérifie que Weaviate est prêt
    if not client.is_ready():
        print("❌ Weaviate n'est pas prêt. Lance 'docker compose up -d' d'abord !")
        exit(1)

    print("✅ Connecté à Weaviate")

    # Supprime la collection si elle existe déjà (utile en dev)
    if client.collections.exists("CoursBUT"):
        client.collections.delete("CoursBUT")
        print("🗑️  Ancienne collection CoursBUT supprimée")

    # Crée la collection avec le vectorizer Gemini
    client.collections.create(
        name="CoursBUT",
        description="Chunks de cours de BUT Informatique",
        vector_config=Configure.Vectors.text2vec_google_aistudio(
            model="text-embedding-004",
            # Vectorise uniquement le champ 'content' (pas source, section...)
            source_properties=["content"],
        ),
        properties=[
            Property(
                name="content",
                data_type=DataType.TEXT,
                description="Le texte du chunk de cours",
            ),
            Property(
                name="source",
                data_type=DataType.TEXT,
                description="Nom du fichier source (ex: cours-java.pdf)",
                skip_vectorization=True,  # Pas besoin de vectoriser le nom du fichier
            ),
            Property(
                name="section",
                data_type=DataType.TEXT,
                description="Titre de la section markdown",
                skip_vectorization=True,
            ),
            Property(
                name="chunk_index",
                data_type=DataType.INT,
                description="Position du chunk dans le document",
                skip_vectorization=True,
            ),
        ],
    )

    print("✅ Collection 'CoursBUT' créée avec succès !")
    print("   → Vectorizer : Gemini text-embedding-004")
    print("   → Propriétés : content, source, section, chunk_index")
