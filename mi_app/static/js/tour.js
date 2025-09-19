// mi_app/static/js/tour.js

// --- TOUR PARA LA PÁGINA PRINCIPAL ---
function iniciarVisitaGuiada() {
    const tour = new Shepherd.Tour({ /* ... opciones ... */ });
    // ... (pasos del tour principal sin cambios) ...
    tour.addStep({
        title: '¡Bienvenido a SilvaTest!',
        text: 'Te mostraremos rápidamente las funciones principales.',
        buttons: [{ action() { return this.next(); }, text: 'Empezar' }]
    });
    tour.addStep({
        title: 'Elige tu Examen',
        text: 'Todo empieza aquí. Selecciona la oposición o licencia que quieres preparar para ver su temario.',
        attachTo: { element: '.card-convocatoria', on: 'bottom' },
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.next(); }, text: 'Siguiente' }]
    });
    tour.addStep({
        title: 'Tu Progreso',
        text: 'Una vez registrado, en "Mi Cuenta" podrás ver todas tus estadísticas, resultados y preguntas favoritas.',
        attachTo: { element: '#mi-cuenta-link', on: 'bottom' },
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.next(); }, text: 'Siguiente' }]
    });
    tour.addStep({
        title: '¡Listo para Empezar!',
        text: 'Ya conoces lo básico. ¡Mucha suerte con tu preparación!',
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.complete(); }, text: 'Finalizar' }]
    });
    tour.start();
}

// --- TOUR PARA LA PÁGINA "MI CUENTA" ---
function iniciarTourCuenta() {
    const tourCuenta = new Shepherd.Tour({ /* ... opciones ... */ });
    // ... (pasos del tour de "Mi Cuenta" sin cambios) ...
    const mostrarTab = (elementId) => {
        return new Promise((resolve) => {
            const tabElement = document.getElementById(elementId);
            if (tabElement) {
                const tab = new bootstrap.Tab(tabElement);
                tab.show();
            }
            setTimeout(resolve, 300); 
        });
    };
    tourCuenta.addStep({
        title: 'Tu Panel Personal',
        text: 'Este es tu centro de control. Vamos a ver rápidamente qué puedes hacer aquí.',
        buttons: [{ action() { return this.next(); }, text: 'Empezar' }]
    });
    tourCuenta.addStep({
        title: 'Filtra tus Resultados',
        text: 'Usa este menú para ver tus estadísticas de una convocatoria específica o de todas a la vez.',
        attachTo: { element: '.filtro-convocatoria', on: 'bottom' },
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.next(); }, text: 'Siguiente' }]
    });
    tourCuenta.addStep({
        title: 'Tu Evolución',
        text: 'Aquí verás un gráfico con la media de tus notas a lo largo del tiempo. ¡Ideal para ver tu progreso!',
        attachTo: { element: '#evolucion-link', on: 'right' },
        beforeShowPromise: () => mostrarTab('evolucion-link'),
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.next(); }, text: 'Siguiente' }]
    });
    tourCuenta.addStep({
        title: 'Estadísticas Detalladas',
        text: 'En esta sección podrás ver tu porcentaje de aciertos por bloque y por tema para saber dónde tienes que mejorar.',
        attachTo: { element: '#estadisticas-link', on: 'right' },
        beforeShowPromise: () => mostrarTab('estadisticas-link'),
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.next(); }, text: 'Siguiente' }]
    });
    tourCuenta.addStep({
        title: 'Repasar Fallos',
        text: '¡Esta es una de las herramientas más potentes! Al hacer clic aquí, generarás un test solo con las preguntas que has fallado.',
        attachTo: { element: '#repasar-fallos-link', on: 'right' },
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.next(); }, text: 'Siguiente' }]
    });
    tourCuenta.addStep({
        title: 'Preguntas Favoritas',
        text: 'Las preguntas que marques con la estrella ⭐ en los tests aparecerán aquí para que puedas repasarlas cuando quieras.',
        attachTo: { element: '#preguntas-favoritas-link', on: 'right' },
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.next(); }, text: 'Siguiente' }]
    });
    tourCuenta.addStep({
        title: 'Zona de Peligro',
        text: 'Ten cuidado aquí. Este botón borrará TODO tu historial de tests y estadísticas de forma permanente.',
        attachTo: { element: '.zona-peligro', on: 'top' },
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.complete(); }, text: 'Finalizar' }]
    });
    tourCuenta.start();
}


// --- CÓDIGO ACTUALIZADO PARA ACTIVAR LOS BOTONES ---
document.addEventListener('DOMContentLoaded', function() {
    // Busca el botón del tour principal (solo existe en la home)
    const botonTourPrincipal = document.getElementById('iniciar-tour');
    if (botonTourPrincipal) {
        botonTourPrincipal.addEventListener('click', function(e) {
            e.preventDefault();
            iniciarVisitaGuiada();
        });
    }

    // Busca el botón del tour de "Mi Cuenta" (solo existe en esa página)
    const botonTourCuenta = document.getElementById('iniciar-tour-cuenta');
    if (botonTourCuenta) {
        botonTourCuenta.addEventListener('click', function(e) {
            e.preventDefault();
            iniciarTourCuenta();
        });
    }
});