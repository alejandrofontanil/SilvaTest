// mi_app/static/js/ia-disclaimer.js

document.addEventListener('DOMContentLoaded', function () {
    const disclaimerModalElement = document.getElementById('iaDisclaimerModal');
    if (!disclaimerModalElement) return;

    const disclaimerModal = new bootstrap.Modal(disclaimerModalElement);
    const acceptButton = document.getElementById('acceptIaDisclaimer');

    // Función para manejar la ejecución de una acción de IA
    window.handleAIAction = function(aiFunction) {
        // Comprobar si el usuario ya ha aceptado el disclaimer
        if (localStorage.getItem('iaDisclaimerAccepted') === 'true') {
            aiFunction(); // Si ya aceptó, ejecuta la función de IA directamente
        } else {
            // Si no ha aceptado, muestra el modal
            disclaimerModal.show();
            
            // Cuando el usuario haga clic en "Aceptar", guarda la preferencia y ejecuta la función
            acceptButton.onclick = function() {
                localStorage.setItem('iaDisclaimerAccepted', 'true');
                disclaimerModal.hide();
                aiFunction();
            };
        }
    };
});