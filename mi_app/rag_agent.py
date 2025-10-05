import os
import json
from dotenv import load_dotenv
from google.oauth2 import service_account
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import re

# LangChain: Importaciones actualizadas
from langchain_google_vertexai import VertexAI
from langchain_google_community import VertexAISearchRetriever

# Carga las variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATA_STORE_ID = os.getenv("GCP_DATA_STORE_ID")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")
LLM_MODEL_NAME = "gemini-1.5-flash-001"
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

# --- INICIALIZACIÓN DE CREDENCIALES ---
credentials = None
if GOOGLE_CREDS_JSON:
    try:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        print("✅ Credenciales de Google Cloud cargadas correctamente.")
    except Exception as e:
        print(f"❌ ERROR al cargar las credenciales de Google Cloud: {e}")

# --- FUNCIÓN DE LIMPIEZA DE FUENTES ---
def clean_source_name(source_path: str) -> str:
    if not isinstance(source_path, str): return 'Fuente no identificada'
    file_name = source_path.split('/')[-1]
    cleaned_name = re.sub(r'\.(pdf|txt)$', '', file_name, flags=re.IGNORECASE)
    cleaned_name = cleaned_name.replace('_', ' ').replace('.', ' ').strip()
    return cleaned_name.title()

# --- FUNCIÓN PRINCIPAL DEL AGENTE RAG ---
def get_rag_response(query: str, mode: str = "formal", selected_sources: list | None = None):
    if not credentials:
        return {"result": "Error crítico: Las credenciales de Google Cloud no están configuradas en el servidor.", "sources": []}

    try:
        TEMPERATURE = 0.2
        RETRIEVAL_K = 5

        # CORRECCIÓN 1: Especificamos la región correcta para el modelo
        llm = VertexAI(
            model_name=LLM_MODEL_NAME,
            credentials=credentials,
            temperature=TEMPERATURE,
            project=GCP_PROJECT_ID,
            location="europe-west1"  # <-- ARREGLADO
        )

        filter_string = None
        if selected_sources and isinstance(selected_sources, list):
            quoted_sources = [f'"{source}"' for source in selected_sources]
            # CORRECCIÓN 2: Usamos el nombre de campo correcto para el filtro
            filter_string = " OR ".join(f"gcs_uri:{s}" for s in quoted_sources) # <-- ARREGLADO

        retriever = VertexAISearchRetriever(
            project_id=GCP_PROJECT_ID,
            data_store_id=DATA_STORE_ID,
            credentials=credentials,
            filter=filter_string,
            max_documents=RETRIEVAL_K,
        )
        
        prompt_template_str = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["formal"])
        prompt = PromptTemplate(template=prompt_template_str, input_variables=["context", "question"])

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm, chain_type="stuff", retriever=retriever,
            chain_type_kwargs={"prompt": prompt}, return_source_documents=True
        )
        
        response = qa_chain.invoke({"query": query})
        
        raw_sources = response.get('source_documents', [])
        cleaned_sources = sorted(list(set([clean_source_name(doc.metadata.get('source', '')) for doc in raw_sources if doc.metadata.get('source')])))
        final_result = response.get('result', "No se encontró una respuesta.").strip()
        
        if cleaned_sources:
            if mode == "didactico":
                final_result += "\n\n" + "## 📚 Fuentes Legales/Temario\n" + "\n".join([f"- {s}" for s in cleaned_sources])
            else:
                final_result += "\n\n[Fuentes consultadas: " + "; ".join(cleaned_sources) + "]"

        return {"result": final_result, "sources": cleaned_sources}

    except Exception as e:
        print(f"Error en get_rag_response: {e}")
        return {"result": f"Error: No se pudo conectar a Google AI. Detalles: {e}", "sources": []}