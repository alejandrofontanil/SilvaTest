import os
import json
from dotenv import load_dotenv
from google.cloud import aiplatform
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_pinecone import Pinecone

# --- 1. CONFIGURACIÓN INICIAL ---
# Carga las variables de entorno del archivo .env
load_dotenv()

# Variables de Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "silvatest-rag" 

# Variables de Vertex AI
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Verificar variables críticas
if not all([PINECONE_API_KEY, GCP_PROJECT_ID, GOOGLE_CREDS_JSON]):
    raise ValueError("Faltan variables de entorno críticas (Pinecone o GCP). Revisa tu archivo .env.")

# Configurar autenticación de Vertex AI usando el Service Account
try:
    if GOOGLE_CREDS_JSON:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        # Escribe temporalmente el Service Account para autenticación
        temp_key_path = "gcp_service_account_key.json"
        with open(temp_key_path, "w") as f:
            json.dump(creds_info, f)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_key_path
    
    # Inicializa Vertex AI
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    print("✅ Vertex AI inicializado y autenticado con éxito.")

except Exception as e:
    print(f"Error al inicializar Vertex AI o al autenticar: {e}")
    print("Asegúrate de que GOOGLE_CREDS_JSON está bien formateado en .env.")
    # Si la autenticación falla, salimos.
    exit()

# --- 2. DEFINICIÓN DE FUENTES DE DATOS Y PROCESAMIENTO ---
# Directorio donde se encuentran los documentos PDF
DATA_PATH = "documentos_para_ia"

# Función para cargar y procesar documentos
def process_documents():
    documents = []
    # Carga todos los archivos PDF en el directorio DATA_PATH
    for file in os.listdir(DATA_PATH):
        if file.endswith(".pdf"):
            print(f"Cargando archivo: {file}")
            loader = PyPDFLoader(os.path.join(DATA_PATH, file))
            # Carga el documento
            documents.extend(loader.load()) 

    if not documents:
        print(f"❌ No se encontraron documentos en {DATA_PATH}. ¿Has creado la carpeta y puesto PDFs dentro?")
        return None

    # Separador de texto para dividir los documentos en fragmentos manejables (chunks)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200, # Solapamiento para mantener el contexto
        length_function=len,
        is_separator_regex=False,
    )

    # Dividir los documentos
    print(f"Dividiendo {len(documents)} documentos en fragmentos...")
    chunks = text_splitter.split_documents(documents)
    print(f"Total de fragmentos (chunks) creados: {len(chunks)}")
    return chunks

# --- 3. CREACIÓN DE EMBEDDINGS Y SUBIDA A PINECONE ---

def ingest_to_pinecone(chunks):
    # Inicializa el modelo de embeddings de Vertex AI 
    print("Inicializando modelo de Embeddings de Vertex AI...")
    # Usamos text-embedding-004 por ser el más reciente y robusto
    embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004")

    # Ingestar los documentos a Pinecone
    print(f"Conectando al índice de Pinecone: {INDEX_NAME}...")
    try:
        # Usamos Pinecone.from_documents() sin 'environment' ni 'api_key'.
        # La conexión se realiza a través de la inicialización implícita de la librería Pinecone.
        Pinecone.from_documents(
            chunks, 
            embeddings_model, 
            index_name=INDEX_NAME
        )
        print("\n✨✨✨ Ingesta completada con éxito. Los documentos están vectorizados en Pinecone. ✨✨✨")
    except Exception as e:
        print(f"\n❌ ERROR durante la ingesta a Pinecone: {e}")
        print("Verifica que tu índice esté activo y las claves de Pinecone sean correctas.")


# --- 4. FUNCIÓN PRINCIPAL ---

def main():
    print("--- INICIANDO PROCESO DE INGESTA DE DATOS RAG ---")
    
    # 1. Procesar documentos
    processed_chunks = process_documents()
    
    if processed_chunks:
        # 2. Subir a Pinecone
        ingest_to_pinecone(processed_chunks)

    # Limpiar el archivo temporal del service account
    temp_key_path = "gcp_service_account_key.json"
    if os.path.exists(temp_key_path):
        os.remove(temp_key_path)

if __name__ == "__main__":
    main()