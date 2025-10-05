import os
import json
from dotenv import load_dotenv
from google.cloud import aiplatform
# LangChain: Corregimos la importación del retriever
from langchain_google_vertexai import VertexAI
from langchain_community.retrievers import GoogleVertexAISearchRetriever
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from google.oauth2 import service_account
import re

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- CONFIGURACIÓN DE GOOGLE CLOUD ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
# La localización de tu Data Store (normalmente 'global')
LOCATION = "global"
DATA_STORE_ID = os.getenv("GCP_DATA_STORE_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Modelo LLM a utilizar
LLM_MODEL_NAME = "gemini-1.5-flash-001"

# --- INICIALIZACIÓN DE SERVICIOS ---
try:
    credentials = None
    if GOOGLE_CREDS_JSON:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
    
    # Esta inicialización es útil si usas otros servicios de Vertex AI
    aiplatform.init(project=GCP_PROJECT_ID, location='europe-west1', credentials=credentials)
    print("✅ Vertex AI inicializado para el agente RAG.")

except Exception as e:
    print(f"Error al inicializar Vertex AI en rag_agent.py: {e}")

# --- PLANTILLAS DE PROMPTS ---
PROMPT_TEMPLATES = {
    "formal": """
        ## 🎯 Meta Prompt: Modo Formal (Precisión Legal)
        Eres un asistente RAG especializado en el temario oficial de Agente Medioambiental. Tu rol es actuar como un experto legal y técnico.
        REGLAS ESTRICTAS:
        1.  **Exclusividad del Contexto:** Responde ÚNICA y EXCLUSIVAMENTE con la información contenida en la sección {context}.
        2.  **Concisión:** Sé lo más breve y directo posible.
        3.  **Tono:** Objetivo, técnico y neutro.

        Contexto:
        {context}
        Pregunta del usuario: {question}
        Respuesta concisa:
    """,
    "didactico": """
        ## 🧑‍🏫 Meta Prompt: Modo Didáctico (Tutoría de Oposiciones)
        Eres Silva, un preparador de oposiciones motivador y didáctico. Tu misión es transformar el contexto en apuntes de estudio memorables.
        REGLAS Y FORMATO (Notebook Style):
        1.  **Formato:** Utiliza Markdown enriquecido (##, viñetas, **negritas**).
        2.  **Estructura:** La respuesta DEBE contener estas secciones (o las más relevantes):
            * **## 📖 Concepto Clave:** Define el término principal.
            * **## 🐟 Ejemplo/Aplicación:** Proporciona un ejemplo práctico del temario.
            * **## 💡 Nota de Estudio:** Añade un dato relacionado o una diferencia clave para memorizar.
        3.  **No incluyas "Fuentes":** No incluyas una sección final sobre "Fuentes" o "Temario". El sistema lo añadirá automáticamente.
        4.  **Inicio Directo:** Comienza la respuesta directamente con el primer título `## 📖 Concepto Clave`.

        Contexto para el análisis: {context}
        Pregunta del usuario: {question}
        Respuesta en formato de estudio:
    """
}

# --- FUNCIÓN DE LIMPIEZA DE FUENTES ---
def clean_source_name(source_path: str) -> str:
    """Limpia la ruta GCS del archivo para mostrar un título amigable."""
    if not isinstance(source_path, str):
        return 'Fuente no identificada'
    
    file_name = source_path.split('/')[-1]
    cleaned_name = re.sub(r'\.(pdf|txt)$', '', file_name, flags=re.IGNORECASE)
    cleaned_name = cleaned_name.replace('_', ' ').replace('.', ' ').strip()
    return cleaned_name.title()


# --- FUNCIÓN PRINCIPAL DEL AGENTE RAG ---
def get_rag_response(query: str, mode: str = "formal", selected_sources: list | None = None):
    """
    Busca en Vertex AI Search y genera una respuesta usando LangChain.
    """
    try:
        TEMPERATURE = 0.2
        RETRIEVAL_K = 5

        llm = VertexAI(
            model_name=LLM_MODEL_NAME,
            credentials=credentials,
            temperature=TEMPERATURE
        )

        # Lógica de filtrado para Vertex AI Search
        filter_string = None
        if selected_sources and isinstance(selected_sources, list):
            # Formato del filtro: 'source:"gs://bucket/doc1" OR source:"gs://bucket/doc2"'
            quoted_sources = [f'"{source}"' for source in selected_sources]
            filter_string = " OR ".join(f"source:{s}" for s in quoted_sources)
            print(f"🔎 Búsqueda filtrada activada. Filtro: {filter_string}")

        # Usamos la clase e importación correctas
        retriever = GoogleVertexAISearchRetriever(
            project_id=GCP_PROJECT_ID,
            location=LOCATION,
            data_store_id=DATA_STORE_ID,
            filter=filter_string,
            max_documents=RETRIEVAL_K,
        )
        
        prompt_template_str = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["formal"])
        prompt = PromptTemplate(template=prompt_template_str, input_variables=["context", "question"])

        # Usamos la cadena de LangChain que ya tenías
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        response = qa_chain.invoke({"query": query})
        
        raw_sources = response.get('source_documents', [])
        cleaned_sources = sorted(list(set([clean_source_name(doc.metadata.get('source', '')) for doc in raw_sources if doc.metadata.get('source')])))
        final_result = response.get('result', "No se encontró una respuesta.").strip()
        
        # Añadimos las fuentes al final de la respuesta
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