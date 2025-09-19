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
                action() { return this.next(); },
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


// --- INICIO DEL NUEVO TOUR PARA LA PÁGINA "MI CUENTA" ---

function iniciarTourCuenta() {
    const tourCuenta = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            classes: 'shadow-md',
            cancelIcon: { enabled: true },
            scrollTo: { behavior: 'smooth', block: 'center' }
        }
    });

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
        buttons: [{ action() { return this.back(); }, text: 'Anterior' }, { action() { return this.next(); }, text: 'Siguiente' }]
    });

    tourCuenta.addStep({
        title: 'Repasar Fallos',
        text: '¡Esta es una de las herramientas más potentes! Aquí podrás hacer tests solo con las preguntas que has fallado.',
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

// --- CÓDIGO PARA ACTIVAR LOS BOTONES DE LOS TOURS ---
document.addEventListener('DOMContentLoaded', function() {
    // Para el tour de la página principal
    const botonTourPrincipal = document.getElementById('iniciar-tour');
    if (botonTourPrincipal) {
        botonTourPrincipal.addEventListener('click', function(e) {
            e.preventDefault();
            iniciarVisitaGuiada();
        });
    }

    // Para el tour de la página "Mi Cuenta"
    const botonTourCuenta = document.getElementById('iniciar-tour-cuenta');
    if (botonTourCuenta) {
        botonTourCuenta.addEventListener('click', function(e) {
            e.preventDefault();
            iniciarTourCuenta();
        });
    }
});