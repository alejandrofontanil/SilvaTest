import os
import json
import vertexai
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient, ServerlessSpec
from google.oauth2 import service_account

# --- CONFIGURACIÓN ---
load_dotenv()

# --- INICIO DEL CAMBIO: Carga explícita de credenciales ---
try:
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    GCP_REGION = os.getenv('GCP_REGION')
    creds_json_str = os.getenv('GOOGLE_CREDS_JSON')

    if not all([GCP_PROJECT_ID, GCP_REGION, creds_json_str]):
        raise ValueError("Faltan variables de entorno de Google Cloud (GCP_PROJECT_ID, GCP_REGION, GOOGLE_CREDS_JSON)")

    creds_info = json.loads(creds_json_str)
    credentials = service_account.Credentials.from_service_account_info(creds_info)
    
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION, credentials=credentials)
    print("✅ Vertex AI inicializado correctamente.")
except Exception as e:
    print(f"🔥 Error inicializando Vertex AI o cargando credenciales: {e}")
    exit()
# --- FIN DEL CAMBIO ---

DOCUMENTS_PATH = "documentos_para_ia/"
PINECONE_INDEX_NAME = "silvatest-rag"
EMBEDDING_DIMENSION = 768

def ingest_docs():
    print("Inicializando Pinecone...")
    pc = PineconeClient(api_key=os.environ.get("PINECONE_API_KEY"))

    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"El índice '{PINECONE_INDEX_NAME}' no existe. Creándolo ahora...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        print("Índice creado con éxito.")
    else:
        print(f"El índice '{PINECONE_INDEX_NAME}' ya existe.")

    print(f"Cargando documentos desde la carpeta: {DOCUMENTS_PATH}")
    documents = []
    for file in os.listdir(DOCUMENTS_PATH):
        if file.lower().endswith('.pdf'):
            pdf_path = os.path.join(DOCUMENTS_PATH, file)
            loader = PyPDFLoader(pdf_path)
            documents.extend(loader.load())
    
    if not documents:
        print("❌ No se encontraron documentos PDF para procesar. Saliendo.")
        return

    print(f"Se cargaron {len(documents)} páginas de los documentos.")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs_split = text_splitter.split_documents(documents)
    print(f"Documentos divididos en {len(docs_split)} trozos.")

    print("Creando embeddings con 'text-embedding-004' y subiendo a Pinecone...")
    
    # --- INICIO DEL CAMBIO: Pasar credenciales a LangChain ---
    embeddings = VertexAIEmbeddings(
        model_name="text-embedding-004",
        project=GCP_PROJECT_ID,
        credentials=credentials
    )
    # --- FIN DEL CAMBIO ---
    
    PineconeVectorStore.from_documents(
        docs_split,
        embeddings,
        index_name=PINECONE_INDEX_NAME
    )
    
    print("🚀 ¡Proceso completado! Tus documentos ya están en Pinecone.")
    
    index = pc.Index(PINECONE_INDEX_NAME)
    print(f"Estadísticas del índice: {index.describe_index_stats()}")

if __name__ == "__main__":
    ingest_docs()