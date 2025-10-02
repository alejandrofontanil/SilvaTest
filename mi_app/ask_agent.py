# --- Importaciones (sin cambios) ---
import os
from dotenv import load_dotenv
import json
from google.cloud import aiplatform
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_vertexai import ChatVertexAI
from langchain_pinecone import Pinecone as PineconeVectorStore 
from langchain.chains import RetrievalQA
from pinecone import Pinecone 
from datetime import datetime # Para añadir el timestamp de inicio

# --- 1. CONFIGURACIÓN DE INFRAESTRUCTURA Y AGENTE (Inicialización Global) ---
load_dotenv()

# Variables de Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "silvatest-rag" 

# Variables de Vertex AI
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Inicialización de Vertex AI (Necesario para autenticar)
try:
    if GOOGLE_CREDS_JSON:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        # Escribimos las credenciales a un archivo temporal si no existe (solo necesario en desarrollo local)
        # En Render, se asume que las credenciales son leídas directamente o vía variables.
        temp_key_path = "gcp_service_account_key.json"
        if not os.path.exists(temp_key_path) and 'private_key' in creds_info:
            with open(temp_key_path, "w") as f:
                json.dump(creds_info, f)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_key_path
    
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Vertex AI inicializado para RAG.")
    
except Exception as e:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Error al inicializar Vertex AI: {e}")
    QA_AGENT = None
    # No llamamos a exit() aquí para que Flask pueda arrancar (aunque el agente falle)

def setup_rag_agent():
    """Inicializa y devuelve la cadena RAG. Se ejecuta una sola vez al arrancar Flask."""
    
    # Se añade un bloque try/except para aislar el error de conexión de Pinecone/Vertex
    try:
        # 1. Inicializar Embeddings (DEBE COINCIDIR con la ingesta)
        embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004")
        
        # 2. Conectar al VectorStore (Pinecone)
        # La clave API se lee de la variable de entorno y se usa aquí.
        pc = Pinecone(api_key=PINECONE_API_KEY) 
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=INDEX_NAME, 
            embedding=embeddings_model
        )
        
        # 3. Inicializar el LLM de Gemini
        # CAMBIO CLAVE: De 'gemini-2.5-pro' a 'gemini-2.5-flash' para optimización
        llm = ChatVertexAI(
            model_name="gemini-2.5-flash", 
            temperature=0.2,
            project=GCP_PROJECT_ID,
            location=GCP_REGION,
        )
        
        # 4. Crear la cadena RAG (RetrievalQA)
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Agente RAG con Gemini 2.5 Flash listo.")
        return qa_chain
        
    except Exception as e:
        # El error 403 o de Pinecone caerá aquí
        print(f"\n❌ ERROR al configurar el agente RAG: {e}")
        return None

# Inicializa el agente globalmente. Si falla, QA_AGENT será None.
QA_AGENT = setup_rag_agent()

# --- 3. FUNCIÓN DE CONSULTA REUTILIZABLE PARA FLASK ---

def get_rag_response(query: str):
    """
    Función principal que las rutas de Flask importarán para obtener una respuesta RAG.
    Devuelve la respuesta del Agente y las fuentes citadas.
    """
    if not QA_AGENT:
        return {
            "result": "Error: El Agente RAG no se pudo inicializar. Revisa la configuración del servidor y los permisos de GCP.",
            "sources": []
        }
    
    try:
        # Ejecutar la cadena RAG
        response = QA_AGENT.invoke({"query": query})
        
        # Extraer fuentes citadas
        sources = set([doc.metadata.get('source', 'Fuente Desconocida') for doc in response.get('source_documents', [])])
        
        return {
            "result": response.get('result', 'No se pudo generar una respuesta.'),
            "sources": list(sources)
        }
        
    except Exception as e:
        print(f"Error durante la consulta RAG: {e}")
        return {
            "result": "Error interno del Agente al procesar la consulta. (Verifica si el error 403 persiste)",
            "sources": []
        }

# --- 4. EJECUCIÓN (Modo de prueba en terminal) ---
if __name__ == "__main__":
    if QA_AGENT:
        print("\n--- Modo de Prueba RAG (Escribe 'salir' para terminar) ---")
        while True:
            query = input("Tú: ")
            if query.lower() == 'salir':
                break
            
            print("Agente: Pensando...")
            
            result = get_rag_response(query)
            
            print("\nAgente:", result['result'])
            if result['sources']:
                print(f"\n[Fuentes del Temario: {', '.join(result['sources'])}]")
            print("-" * 20)
            
    # Limpiamos el archivo temporal (solo si se está ejecutando el script directamente)
    temp_key_path = "gcp_service_account_key.json"
    if os.path.exists(temp_key_path):
        os.remove(temp_key_path)
