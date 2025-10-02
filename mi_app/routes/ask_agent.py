import os
import json
from dotenv import load_dotenv
from google.cloud import aiplatform
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_pinecone import Pinecone
from urllib.parse import urlparse 

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
        temp_key_path = "gcp_service_account_key.json"
        
        # Corregido: Forzar la carga de credenciales para Codespaces
        # Si el archivo JSON existe O si la clave privada está en el JSON
        if os.path.exists(temp_key_path) or 'private_key' in creds_info:
            if not os.path.exists(temp_key_path) and 'private_key' in creds_info:
                with open(temp_key_path, "w") as f:
                    json.dump(creds_info, f)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_key_path
    
    # Inicializa Vertex AI
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    print("✅ Vertex AI inicializado y autenticado con éxito.")

except Exception as e:
    # Capturamos errores de autenticación comunes de Codespaces/GCP
    print(f"Error al inicializar Vertex AI o al autenticar: {e}")
    print("Asegúrate de que GOOGLE_CREDS_JSON está bien formateado y los permisos IAM son correctos.")
    exit()

# --- 2. DEFINICIÓN DE FUENTES DE DATOS Y PROCESAMIENTO ---
# Directorio raíz donde se encuentran los documentos PDF
DATA_PATH = "documentos_para_ia"

# Función para cargar y procesar documentos de forma recursiva
def process_documents():
    documents = []
    
    # os.walk recorre el directorio de forma recursiva
    for root, dirs, files in os.walk(DATA_PATH):
        for file_name in files:
            if file_name.endswith(".pdf"):
                file_path = os.path.join(root, file_name)
                print(f"Cargando archivo: {file_path}")
                
                # --- Lógica de Extracción de Metadatos por Carpeta ---
                
                # Obtenemos la ruta relativa desde DATA_PATH
                relative_path = os.path.relpath(file_path, DATA_PATH)
                
                # Dividimos la ruta en segmentos
                path_parts = relative_path.split(os.sep)
                
                # Asignamos Bloque y Tema basándonos en la estructura de carpetas
                # Ejemplo: AGMN ASTURIAS/PARTE ESPECIFICA/PESCA/TEMA.pdf
                
                # El Bloque Principal es el primer directorio
                bloque_principal = path_parts[0] if len(path_parts) > 1 else 'General'
                
                # El Tema será el resto de la ruta (ej: PARTE ESPECIFICA/PESCA/TEMA.pdf)
                tema_completo = os.sep.join(path_parts[1:])
                
                # 1. Cargar documento
                loader = PyPDFLoader(file_path)
                data = loader.load()
                
                # 2. Asignar metadatos a cada página
                for doc in data:
                    doc.metadata['bloque'] = bloque_principal
                    doc.metadata['tema'] = tema_completo
                    doc.metadata['source'] = file_path   
                
                documents.extend(data)

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

    # 3. Dividir los documentos
    print(f"Dividiendo {len(documents)} documentos en fragmentos...")
    chunks = text_splitter.split_documents(documents)
    print(f"Total de fragmentos (chunks) creados: {len(chunks)}")
    return chunks

# --- 3. CREACIÓN DE EMBEDDINGS Y SUBIDA A PINECONE ---

def ingest_to_pinecone(chunks):
    # Inicializa el modelo de embeddings de Vertex AI 
    print("Inicializando modelo de Embeddings de Vertex AI...")
    embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004")

    # Ingestar los documentos a Pinecone
    print(f"Conectando al índice de Pinecone: {INDEX_NAME}...")
    try:
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

    # Limpiamos el archivo temporal solo si estamos en un entorno de desarrollo local
    temp_key_path = "gcp_service_account_key.json"
    if os.path.exists(temp_key_path):
        os.remove(temp_key_path)

if __name__ == "__main__":
    main()
