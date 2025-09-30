# ingest_data.py (versión actualizada)
import os
import PyPDF2
from dotenv import load_dotenv
import pinecone
import vertexai
from vertexai.language_models import TextEmbeddingModel
import time
import traceback
from pinecone import Pinecone, ServerlessSpec

print("Cargando configuración...")
load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_REGION")
vertexai.init(project=PROJECT_ID, location=LOCATION)

# CAMBIO: Usamos un modelo de embedding más estable
model = TextEmbeddingModel.from_pretrained("textembedding-gecko@003")

print("Conectando a Pinecone...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = "silvatest-temario"

if INDEX_NAME not in pc.list_indexes().names():
    print(f"Creando índice serverless '{INDEX_NAME}'...")
    pc.create_index(
        name=INDEX_NAME, dimension=768, metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )
    time.sleep(10)
else:
    print(f"El índice '{INDEX_NAME}' ya existe.")

index = pc.Index(INDEX_NAME)

def get_pdf_text(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error al leer el PDF {pdf_path}: {e}")
    return text

def get_text_chunks(text, chunk_size=1500, chunk_overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    return chunks

def get_embedding(text):
    try:
        time.sleep(1)
        embeddings = model.get_embeddings([text])
        return embeddings[0].values
    except Exception as e:
        print(f"Error al obtener embedding: {e}")
        return None

def main():
    docs_folder = "documentos_para_ia"
    if not os.path.exists(docs_folder) or not os.listdir(docs_folder):
        print(f"La carpeta '{docs_folder}' está vacía o no existe.")
        return

    for filename in os.listdir(docs_folder):
        if filename.lower().endswith(".pdf"):
            print(f"\n--- Procesando archivo: {filename} ---")
            text = get_pdf_text(os.path.join(docs_folder, filename))
            if not text:
                continue
            chunks = get_text_chunks(text)
            vectors_to_upsert = []
            for i, chunk in enumerate(chunks):
                print(f"  - Generando vector para el trozo {i+1}/{len(chunks)}...")
                embedding = get_embedding(chunk)
                if embedding:
                    vectors_to_upsert.append((f"{filename}-chunk-{i}", embedding, {'text': chunk, 'source': filename}))
            if vectors_to_upsert:
                print(f"Subiendo {len(vectors_to_upsert)} vectores a Pinecone...")
                index.upsert(vectors=vectors_to_upsert, batch_size=100)
    print("\n--- ¡Proceso de ingesta completado! ---")
    print(f"Total de vectores en el índice: {index.describe_index_stats()['total_vector_count']}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n--- Error crítico ---: {e}")
        traceback.print_exc()