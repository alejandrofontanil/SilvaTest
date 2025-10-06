document.addEventListener('DOMContentLoaded', function() {

    // --- 1. REFERENCIAS A ELEMENTOS DEL DOM ---
    const sourceItems = document.querySelectorAll('.source-item');
    const pdfViewer = document.getElementById('pdf-viewer');
    const viewerPlaceholder = document.getElementById('viewer-placeholder');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatHistory = document.getElementById('chat-history');
    const tokensDisplay = document.getElementById('remaining-tokens-value');

    // --- 2. CONFIGURACIÓN DE PDF.js ---
    const { pdfjsLib } = globalThis;
    if (!pdfjsLib) {
        console.error("PDF.js no está cargado.");
        return;
    }
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://mozilla.github.io/pdf.js/build/pdf.worker.mjs`;

    // --- 3. FUNCIÓN PARA CARGAR Y RENDERIZAR EL PDF (OPTIMIZADA) ---
    async function loadPdf(pdfUrl) {
        // <-- CAMBIO: Solo se ejecuta si el visor existe
        if (!pdfViewer || !viewerPlaceholder) return;

        pdfViewer.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100 text-muted">
                <div class="spinner-border me-3" role="status"></div>
                <strong>Cargando documento...</strong>
            </div>`;
        viewerPlaceholder.style.display = 'none';
        pdfViewer.style.display = 'block';

        try {
            const pdf = await pdfjsLib.getDocument(pdfUrl).promise;
            pdfViewer.innerHTML = '';

            // <-- CAMBIO: Renderizado de páginas en paralelo para mayor velocidad
            const renderPromises = [];
            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
                const renderPromise = pdf.getPage(pageNum).then(page => {
                    const viewport = page.getViewport({ scale: 1.75 });
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    canvas.style.marginBottom = '10px'; // Espacio entre páginas

                    return { canvas, renderTask: page.render({ canvasContext: context, viewport: viewport }).promise };
                });
                renderPromises.push(renderPromise);
            }

            // Esperamos a que todas las páginas se procesen para obtener los canvas
            const pagesData = await Promise.all(renderPromises);
            
            // Añadimos los canvas al DOM en el orden correcto
            pagesData.forEach(data => pdfViewer.appendChild(data.canvas));
            
            // Esperamos a que todas las tareas de renderizado finalicen
            await Promise.all(pagesData.map(data => data.renderTask));

        } catch (error) {
            console.error('Error al cargar el PDF:', error);
            pdfViewer.innerHTML = '<div class="alert alert-danger m-3">Error al cargar el documento. Asegúrate de que es públicamente accesible.</div>';
        }
    }

    // --- 4. EVENT LISTENERS PARA LA LISTA DE TEMAS ---
    // <-- CAMBIO: Solo se activa si hay temas y un visor
    if (sourceItems.length > 0 && pdfViewer) {
        sourceItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                
                sourceItems.forEach(i => i.classList.remove('active'));
                this.classList.add('active');

                const gcsPath = this.dataset.path;
                const publicUrl = `https://storage.googleapis.com/${gcsPath.substring(5)}`;
                loadPdf(publicUrl);
            });
        });
    }

    // --- 5. LÓGICA DEL CHAT ---
    function scrollToBottom() {
        if (chatHistory) { // <-- CAMBIO: Guarda de seguridad
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }

    function addMessageToChat(sender, content, isThinking = false) {
        if (!chatHistory) return; // <-- CAMBIO: Guarda de seguridad
        
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', sender === 'user' ? 'user-message' : 'bot-message');
        
        if (sender === 'user') {
            messageDiv.textContent = content;
        } else if (isThinking) {
            messageDiv.innerHTML = `<div class="d-flex align-items-center"><div class="spinner-border spinner-border-sm me-2" role="status"></div><span>Consultando...</span></div>`;
        } else {
            // Se asume que la librería 'marked' está disponible globalmente si se usa
            messageDiv.innerHTML = typeof marked !== 'undefined' ? marked.parse(content) : content.replace(/\n/g, '<br>');
        }
        
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }

    // <-- CAMBIO: Se mantiene la guarda principal para toda la lógica del formulario
    if (chatForm && userInput && chatHistory) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const userMessage = userInput.value.trim();
            if (!userMessage) return;

            const activeSource = document.querySelector('.source-item.active');
            const selectedSources = activeSource ? [activeSource.dataset.path] : [];

            addMessageToChat('user', userMessage);
            userInput.value = '';
            
            const thinkingMessage = addMessageToChat('bot', '', true);

            fetch("/api/consulta-rag", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ 
                    message: userMessage, 
                    mode: "didactico",
                    selected_sources: selectedSources
                })
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { 
                        throw new Error(err.error || 'Error desconocido del servidor.'); 
                    });
                }
                return response.json();
            })
            .then(data => {
                thinkingMessage.remove();
                addMessageToChat('bot', data.response);
                
                if (tokensDisplay && data.remaining_tokens !== undefined) {
                    tokensDisplay.textContent = data.remaining_tokens;
                }
            })
            .catch(error => {
                console.error('Error en la consulta RAG:', error);
                thinkingMessage.remove();
                addMessageToChat('bot', `❌ Lo siento, ha ocurrido un error: ${error.message}`);
            });
        });
    }
});