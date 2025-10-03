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
LLM_MODEL_NAME = "gemini-2.5-flash" 

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
        3.  **Fuentes Legales:** Finaliza siempre con una sección `## 📚 Fuentes Legales/Temario` donde **identificas y nombras** el documento o la ley de origen (ej: "Ley 42/2007 de Patrimonio Natural", "Tema 8. Especies de Pesca (nuevo)"). Pide al LLM que identifique el título legal del documento, no el nombre del archivo.

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
        
    # 1. Elimina el prefijo del directorio raíz (ej: documentos_para_ia/AGMN ASTURIAS/)
    cleaned_name = re.sub(r'documentos_para_ia/[^/]+/', '', source_path, count=1)
    
    # 2. Elimina la extensión del archivo (.pdf, .txt)
    cleaned_name = re.sub(r'\.(pdf|txt)$', '', cleaned_name, flags=re.IGNORECASE)
    
    # 3. Reemplaza guiones bajos o puntos (si los hay) por espacios y capitaliza
    cleaned_name = cleaned_name.replace('_', ' ').replace('.', ' ').strip()
    
    return cleaned_name.title()


# La función principal
def get_rag_response(query: str, mode: str = "formal"):
    """
    Busca en el índice de Pinecone y genera una respuesta con Vertex AI.
    Permite seleccionar el modo de respuesta (formal o didáctico).
    """
    try:
        credentials = service_account.Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON))
    except Exception:
        credentials = None 
        
    try:
        # --- AJUSTE DE PARÁMETROS CLAVE ---
        TEMPERATURE = 0.3
        RETRIEVAL_K = 3 
        
        # Inicializa los embeddings y el LLM, pasando las credenciales
        embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004", credentials=credentials)
        llm = VertexAI(
            model_name=LLM_MODEL_NAME, 
            credentials=credentials,
            temperature=TEMPERATURE # Control de temperatura
        )

        # Conexión a Pinecone
        vectorstore = Pinecone.from_existing_index(
            index_name=INDEX_NAME, 
            embedding=embeddings_model
        )
        
        # Retrieval: k=3 para obtener 3 fragmentos, lo más relevante posible.
        retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K}) 
        
        prompt_template_str = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["formal"])
        prompt = PromptTemplate(template=prompt_template_str, input_variables=["context", "question"])

        # Creación de la cadena RAG
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True 
        )
        
        response = qa.invoke({"query": query})
        
        # 1. Obtener las rutas de las fuentes brutas
        raw_sources = response.get('source_documents', [])
        
        # 2. Limpiar los nombres de las fuentes usando la nueva función
        cleaned_sources = sorted(list(set([clean_source_name(doc.metadata.get('source', doc.metadata.get('tema', 'Fuente no identificada'))) for doc in raw_sources])))
        
        final_result = response.get('result', "No se encontró una respuesta.")
        
        # 3. Si el modo es didáctico o si hay fuentes, adjuntamos la lista limpia
        # NOTA: En modo didáctico, el prompt ya le pide a Gemini que incorpore el título legal,
        # pero esto asegura que la lista de temas esté siempre disponible y limpia.
        if mode == "didactico" and cleaned_sources:
             final_result += "\n\n" + "## 📚 Fuentes Legales/Temario:\n" + "\n".join([f"- {s}" for s in cleaned_sources])
        elif cleaned_sources:
            # En modo formal, simplemente la añadimos al final sin formato notebook
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
