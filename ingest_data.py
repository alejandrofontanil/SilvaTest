import os
import PyPDF2
from dotenv import load_dotenv
import pinecone
import vertexai
from vertexai.language_models import TextEmbeddingModel
import time
import traceback
from pinecone import Pinecone, ServerlessSpec

# --- 1. CONFIGURACIÓN INICIAL ---
print("Cargando configuración...")
load_dotenv()

# Leemos el ID del proyecto y la REGIÓN desde el .env
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_REGION")

# Inicializa Vertex AI explícitamente con tu ID de proyecto y tu REGIÓN
vertexai.init(project=PROJECT_ID, location=LOCATION)

# CAMBIO: Usamos el modelo más reciente
model = TextEmbeddingModel.from_pretrained("text-embedding-004")

# Inicializa la conexión con Pinecone
print("Conectando a Pinecone...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

INDEX_NAME = "silvatest-temario"

# --- 2. CREACIÓN DEL ÍNDICE EN PINECONE ---
if INDEX_NAME not in pc.list_indexes().names():
    print(f"Creando índice serverless '{INDEX_NAME}' en Pinecone...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=768,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1' 
        )
    )
    print("Índice creado con éxito. Esperando a que esté listo...")
    time.sleep(10)
else:
    print(f"El índice '{INDEX_NAME}' ya existe.")

index = pc.Index(INDEX_NAME)

# --- 3. FUNCIONES PARA PROCESAR DOCUMENTOS ---
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

# --- 4. FUNCIÓN PRINCIPAL DEL SCRIPT ---
def main():
    docs_folder = "documentos_para_ia"
    if not os.path.exists(docs_folder) or not os.listdir(docs_folder):
        print(f"La carpeta '{docs_folder}' no existe o está vacía.")
        return

    for filename in os.listdir(docs_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(docs_folder, filename)
            print(f"\n--- Procesando archivo: {filename} ---")
            
            text = get_pdf_text(pdf_path)
            if not text:
                print(f"No se pudo extraer texto de {filename}. Saltando archivo.")
                continue

            chunks = get_text_chunks(text)
            print(f"Documento dividido en {len(chunks)} trozos.")
            
            vectors_to_upsert = []
            for i, chunk in enumerate(chunks):
                print(f"  - Generando vector para el trozo {i+1}/{len(chunks)}...")
                embedding = get_embedding(chunk)
                
                if embedding:
                    vector_id = f"{filename}-chunk-{i}"
                    metadata = {'text': chunk, 'source': filename}
                    vectors_to_upsert.append((vector_id, embedding, metadata))

            if vectors_to_upsert:
                print(f"Subiendo {len(vectors_to_upsert)} vectores a Pinecone...")
                index.upsert(vectors=vectors_to_upsert, batch_size=100)
                print("¡Vectores subidos con éxito!")

    print("\n--- ¡Proceso de ingesta completado! ---")
    stats = index.describe_index_stats()
    print(f"Total de vectores en el índice: {stats['total_vector_count']}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n--- Ha ocurrido un error crítico durante la ejecución ---")
        print(e)
        traceback.print_exc()