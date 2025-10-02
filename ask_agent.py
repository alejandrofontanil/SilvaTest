import os
from dotenv import load_dotenv
import json
from google.cloud import aiplatform
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_vertexai import ChatVertexAI
from langchain_pinecone import Pinecone as PineconeVectorStore # Renombrado para evitar conflicto con el cliente de Pinecone
from langchain.chains import RetrievalQA
from pinecone import Pinecone # Cliente para inicializar Pinecone

# --- 1. CONFIGURACIÓN DE INFRAESTRUCTURA ---
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
    exit()

# --- 2. CONFIGURACIÓN DEL AGENTE RAG ---

def setup_rag_agent():
    """Inicializa el modelo de embeddings, el VectorStore y la cadena RAG."""
    
    # 1. Inicializar Embeddings de Vertex AI (DEBE COINCIDIR con la ingesta)
    print("Inicializando modelo de Embeddings...")
    embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004")
    
    # 2. Conectar al VectorStore (Pinecone)
    # Inicializamos el cliente Pinecone para asegurar la conexión
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Cargamos el VectorStore desde el índice existente
    print(f"Conectando al índice de Pinecone: {INDEX_NAME}...")
    vector_store = PineconeVectorStore.from_existing_index(
        index_name=INDEX_NAME, 
        embedding=embeddings_model
    )
    
    # 3. Inicializar el LLM de Gemini (para la generación de la respuesta)
    # Usamos gemini-2.5-pro por su capacidad de razonamiento avanzado
    print("Inicializando LLM Gemini 2.5 Pro...")
    llm = ChatVertexAI(
        model_name="gemini-2.5-pro", 
        temperature=0.2,
        project=GCP_PROJECT_ID,
        location=GCP_REGION,
    )
    
    # 4. Crear la cadena RAG (RetrievalQA)
    print("Creando cadena RAG...")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff", # Simple técnica para "rellenar" el prompt con el contexto
        retriever=vector_store.as_retriever(search_kwargs={"k": 5}), # Recupera los 5 fragmentos más relevantes
        return_source_documents=True # Importante para citar la fuente
    )
    
    return qa_chain

# --- 3. FUNCIÓN DE CONSULTA ---

def run_chat():
    """Ejecuta el ciclo de chat interactivo con el Agente RAG."""
    
    try:
        qa_chain = setup_rag_agent()
    except Exception as e:
        print(f"\n❌ ERROR FATAL al configurar el agente: {e}")
        print("Asegúrate de que el índice de Pinecone esté activo y las claves de GCP/Pinecone sean correctas.")
        return

    print("\n--- Agente de Estudio RAG Gemini 2.5 Pro (Escribe 'salir' para terminar) ---")
    print("Pregunta sobre tu temario de Agente del Medio Natural (ej: ¿Cuáles son las categorías de la Ley de Pesca?)")
    
    while True:
        query = input("\nTú: ")
        if query.lower() == 'salir':
            break
        
        print("Agente: Pensando...")
        
        try:
            # Ejecutar la cadena RAG
            response = qa_chain.invoke({"query": query})
            
            # Formatear la salida
            print("\nAgente:", response['result'])
            
            # Mostrar fuentes
            sources = set([doc.metadata.get('source', 'Fuente Desconocida') for doc in response['source_documents']])
            if sources:
                print(f"\n[Fuentes del Temario: {', '.join(sources)}]")
            
        except Exception as e:
            print(f"Error al procesar la consulta: {e}")
    
    print("\nAgente: ¡Hasta luego! ¡A seguir estudiando para la oposición!")

# --- 4. EJECUCIÓN ---

if __name__ == "__main__":
    run_chat()