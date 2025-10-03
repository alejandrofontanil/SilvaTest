import os
import json
from dotenv import load_dotenv
from google.cloud import aiplatform
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain_pinecone import Pinecone
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from google.oauth2 import service_account 
import re # Importamos para la limpieza de texto

# Carga las variables de entorno
load_dotenv()

# Variables de Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "silvatest-rag" 

# Variables de Vertex AI
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = 'us-central1' 
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON") 

# Modelo con enfoque en velocidad y calidad
LLM_MODEL_NAME = "gemini-1.5-flash-001" 

# --- CONFIGURACIÓN DE CREDENCIALES ---
try:
    credentials = None
    if GOOGLE_CREDS_JSON:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION, credentials=credentials)
    print("✅ Vertex AI inicializado para el agente RAG.")

except Exception as e:
    print(f"Error al inicializar Vertex AI en rag_agent.py: {e}")

# Diccionario de templates de prompts con Meta Prompting Potente
PROMPT_TEMPLATES = {
    "formal": """
        ## 🎯 Meta Prompt: Modo Formal (Precisión Legal)

        Eres un asistente RAG especializado en el temario oficial (Oposición Agente Medioambiental de Castilla y León/Asturias).
        Tu rol es actuar como un **experto legal y técnico**.

        **REGLAS ESTRICTAS:**
        1.  **Exclusividad del Contexto:** Responde ÚNICA y EXCLUSIVAMENTE con la información contenida en la sección {context}.
        2.  **Concisión:** Sé lo más breve y directo posible. Usa una lista si la información lo permite, pero sin preámbulos.
        3.  **Tono:** Objetivo, técnico y neutro.

        Contexto:
        {context}

        Pregunta del usuario: {question}

        Respuesta concisa:
    """,
    "didactico": """
        ## 🧑‍🏫 Meta Prompt: Modo Didáctico (Tutoría de Oposiciones)

        Eres Silva, un preparador de oposiciones de élite con una personalidad **motivadora y didáctica**. Tu misión es transformar el contexto en **apuntes de estudio memorables**.

        **REGLAS Y FORMATO (Notebook Style):**
        1.  **Formato:** Utiliza Markdown enriquecido (##, viñetas, **negritas**) para crear secciones.
        2.  **Estructura:** La respuesta DEBE contener estas secciones (o las más relevantes):
            * **## 📖 Concepto Clave:** Define el término principal.
            * **## 🐟 Ejemplo/Aplicación:** Proporciona un ejemplo práctico del temario.
            * **## 💡 Nota de Estudio:** Añade un dato relacionado o una diferencia clave para memorizar.
        3.  **¡IMPORTANTE! No incluyas una sección final sobre "Fuentes" o "Temario".** El sistema lo añadirá automáticamente. Tu respuesta debe terminar con la "Nota de Estudio".
        4.  **Inicio Directo:** Comienza la respuesta directamente con el saludo o con el primer título `## 📖 Concepto Clave`. No añadas viñetas, guiones (`---`) ni ningún otro separador al principio.

        Contexto para el análisis: {context}

        Pregunta del usuario: {question}

        Respuesta en formato de estudio:
    """
}

# --- FUNCIÓN DE LIMPIEZA DE FUENTES ---
def clean_source_name(source_path):
    """Limpia la ruta del archivo para mostrar un título amigable."""
    if not isinstance(source_path, str):
        return 'Fuente no identificada'
        
    # Asumimos que la ruta completa está en 'source', la limpiamos para mostrarla
    # y también para usarla en el filtrado si fuera necesario.
    cleaned_name = re.sub(r'documentos_para_ia/[^/]+/', '', source_path, count=1)
    cleaned_name = re.sub(r'\.(pdf|txt)$', '', cleaned_name, flags=re.IGNORECASE)
    cleaned_name = cleaned_name.replace('_', ' ').replace('.', ' ').strip()
    
    return cleaned_name.title()


# La función principal
def get_rag_response(query: str, mode: str = "formal", selected_sources: list | None = None):
    """
    Busca en el índice de Pinecone y genera una respuesta con Vertex AI.
    Permite seleccionar el modo de respuesta y filtrar por documentos específicos.
    
    Args:
        query (str): La pregunta del usuario.
        mode (str): "formal" o "didactico".
        selected_sources (list | None): Una lista con las rutas completas de los 
                                         documentos a consultar (ej: ['documentos_para_ia/CYL/ley_montes.pdf']).
    """
    try:
        credentials = service_account.Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON))
    except Exception:
        credentials = None 
        
    try:
        TEMPERATURE = 0.3
        RETRIEVAL_K = 3 
        
        embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004", credentials=credentials)
        llm = VertexAI(
            model_name=LLM_MODEL_NAME, 
            credentials=credentials,
            temperature=TEMPERATURE
        )

        vectorstore = Pinecone.from_existing_index(
            index_name=INDEX_NAME, 
            embedding=embeddings_model
        )
        
        # --- ¡NUEVA LÓGICA DE FILTRADO! ---
        # Prepara los argumentos de búsqueda. Por defecto, busca en todo.
        search_kwargs = {"k": RETRIEVAL_K}
        
        # Si el usuario ha seleccionado fuentes, añadimos un filtro de metadatos.
        # IMPORTANTE: Asume que en tus metadatos de Pinecone, el campo que contiene
        # la ruta del documento se llama 'source'.
        if selected_sources and isinstance(selected_sources, list):
            search_kwargs["filter"] = {"source": {"$in": selected_sources}}
            print(f"🔎 Búsqueda filtrada activada. Fuentes: {selected_sources}")

        # Configura el retriever con los argumentos de búsqueda (con o sin filtro).
        retriever = vectorstore.as_retriever(search_kwargs=search_kwargs) 
        
        prompt_template_str = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["formal"])
        prompt = PromptTemplate(template=prompt_template_str, input_variables=["context", "question"])

        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True 
        )
        
        response = qa.invoke({"query": query})
        
        raw_sources = response.get('source_documents', [])
        cleaned_sources = sorted(list(set([clean_source_name(doc.metadata.get('source', 'Fuente no identificada')) for doc in raw_sources])))
        final_result = response.get('result', "No se encontró una respuesta.").strip()
        
        if cleaned_sources:
            if mode == "didactico":
                final_result += "\n\n" + "## 📚 Fuentes Legales/Temario\n" + "\n".join([f"- {s}" for s in cleaned_sources])
            else:
                final_result += "\n\n[Fuentes consultadas: " + "; ".join(cleaned_sources) + "]"

        return {
            "result": final_result,
            "sources": cleaned_sources
        }

    except Exception as e:
        print(f"Error en get_rag_response: {e}")
        return {
            "result": f"Error: No se pudo conectar a Google AI. Detalles: {e}",
            "sources": []
        }