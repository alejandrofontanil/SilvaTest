// mi_app/static/js/tour.js

function iniciarVisitaGuiada() {
    const tour = new Shepherd.Tour({
        useModalOverlay: true, // Pone un fondo oscuro para enfocar la atención
        defaultStepOptions: {
            classes: 'shadow-md',
            cancelIcon: {
                enabled: true
            },
            scrollTo: { behavior: 'smooth', block: 'center' }
        }
    });

    // PASO 1: Bienvenida
    tour.addStep({
        title: '¡Bienvenido a SilvaTest!',
        text: 'Te mostraremos rápidamente las funciones principales. Puedes cancelar en cualquier momento.',
        buttons: [
            {
                action() {
                    return this.next();
                },
                text: 'Empezar'
            }
        ]
    });

    // PASO 2: Elegir Examen
    tour.addStep({
        title: 'Elige tu Examen',
        text: 'Todo empieza aquí. Selecciona la oposición o licencia que quieres preparar para ver su temario.',
        attachTo: {
            element: '.card-convocatoria', // Resalta la primera tarjeta de la lista
            on: 'bottom'
        },
        buttons: [
            { action() { return this.back(); }, text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });

    // PASO 3: Mi Cuenta
    tour.addStep({
        title: 'Tu Progreso',
        text: 'Una vez registrado, en "Mi Cuenta" podrás ver todas tus estadísticas, resultados y preguntas favoritas.',
        attachTo: {
            element: '#mi-cuenta-link', // Apunta al enlace al que le pusimos el id
            on: 'bottom'
        },
        buttons: [
            { action() { return this.back(); }, text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });
    
    // PASO 4: Final
    tour.addStep({
        title: '¡Listo para Empezar!',
        text: 'Ya conoces lo básico. ¡Mucha suerte con tu preparación!',
        buttons: [
            { action() { return this.back(); }, text: 'Anterior' },
            { action() { return this.complete(); }, text: 'Finalizar' }
        ]
    });

    tour.start();
}