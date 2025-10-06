// mi_app/static/js/agente_ia.js

document.addEventListener('DOMContentLoaded', function() {

    // --- 1. REFERENCIAS A ELEMENTOS DEL DOM ---
    const sourceItems = document.querySelectorAll('.source-item');
    const pdfViewer = document.getElementById('pdf-viewer');
    const viewerPlaceholder = document.getElementById('viewer-placeholder');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');
    const chatHistory = document.getElementById('chat-history');

    // --- 2. CONFIGURACIÓN DE PDF.js ---
    // Asegúrate de que la librería esté cargada en tu base.html o agente_ia.html
    const { pdfjsLib } = globalThis;
    if (pdfjsLib) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = `https://mozilla.github.io/pdf.js/build/pdf.worker.mjs`;
    } else {
        console.error("PDF.js no está cargado. Asegúrate de incluir el script en tu HTML.");
        return;
    }

    // --- 3. FUNCIÓN PARA CARGAR Y RENDERIZAR EL PDF ---
    async function loadPdf(pdfUrl) {
        // Limpia el visor y muestra un indicador de carga
        pdfViewer.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100 text-muted">
                <div class="spinner-border me-3" role="status"></div>
                <strong>Cargando documento...</strong>
            </div>`;
        viewerPlaceholder.style.display = 'none';
        pdfViewer.style.display = 'block';

        try {
            const pdf = await pdfjsLib.getDocument(pdfUrl).promise;
            pdfViewer.innerHTML = ''; // Limpia el indicador de carga

            // Itera sobre cada página y la renderiza en un <canvas>
            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
                const page = await pdf.getPage(pageNum);
                // Ajusta la escala para una mejor resolución
                const viewport = page.getViewport({ scale: 1.75 });
                
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                pdfViewer.appendChild(canvas);

                await page.render({ canvasContext: context, viewport: viewport }).promise;
            }
        } catch (error) {
            console.error('Error al cargar el PDF:', error);
            pdfViewer.innerHTML = '<div class="alert alert-danger m-3">Error al cargar el documento. Asegúrate de que es públicamente accesible.</div>';
        }
    }

    // --- 4. AÑADIR EVENT LISTENERS A LA LISTA DE TEMAS ---
    sourceItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Gestiona el estilo "activo" en la lista
            sourceItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');

            const gcsPath = this.dataset.path; // ej: "gs://bucket-name/file.pdf"
            
            // Convierte la ruta de GCS a una URL pública HTTPS
            const publicUrl = `https://storage.googleapis.com/${gcsPath.substring(5)}`;
            
            loadPdf(publicUrl);
        });
    });

    // --- 5. LÓGICA DEL CHAT (Simplificada para este archivo) ---
    // (Puedes añadir aquí la lógica completa de tu chat que ya tenías)
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const userMessage = userInput.value.trim();
            if (!userMessage) return;

            // Aquí iría tu lógica de fetch al /api/consulta-rag
            // Por ejemplo:
            // addMessageToChat('user', userMessage);
            // fetch(...)
            // .then(...)
            // .catch(...)

            console.log("Mensaje enviado:", userMessage);
            userInput.value = '';
            // addMessageToChat('agent', 'Respuesta de ejemplo...'); // Simulación
        });
    }
});