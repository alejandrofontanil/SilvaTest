// mi_app/static/js/tour.js

// Tour para la página de inicio (home.html)
function iniciarVisitaGuiada() {
    const tourHome = new Shepherd.Tour({
        use  ModalOverlay: true,
        defaultStepOptions: {
            classes: 'shadow-md bg-purple-dark',
            scrollTo: true,
            cancelIcon: {
                enabled: true
            }
        }
    });

    tourHome.addStep({
        id: 'bienvenida',
        text: '¡Bienvenido a SilvaTest! Te guiaremos para que conozcas las funciones principales.',
        attachTo: { element: 'h1', on: 'bottom' },
        buttons: [
            {
                action() { return this.next(); },
                text: 'Empezar'
            }
        ]
    });

    tourHome.addStep({
        id: 'elige-examen',
        text: 'Todo empieza aquí. Selecciona la oposición o licencia que quieres preparar para ver su temario y empezar a practicar.',
        attachTo: { element: '.grid-examenes > div:first-child', on: 'top' }, // Apunta al primer card visible
        buttons: [
            {
                action() { return this.back(); },
                classes: 'shepherd-button-secondary',
                text: 'Anterior'
            },
            {
                action() { return this.next(); },
                text: 'Siguiente'
            }
        ]
    });

    tourHome.addStep({
        id: 'mi-progreso',
        text: 'Una vez registrado, en "Mi Cuenta" podrás ver todas tus estadísticas, resultados y preguntas favoritas.',
        attachTo: { element: '#mi-cuenta-link', on: 'left' },
        buttons: [
            {
                action() { return this.back(); },
                classes: 'shepherd-button-secondary',
                text: 'Anterior'
            },
            {
                action() { return this.next(); },
                text: 'Siguiente'
            }
        ]
    });

    tourHome.addStep({
        id: 'final-home',
        text: '¡Listo para Empezar! Ya conoces lo básico. Mucha suerte con tu preparación!',
        buttons: [
            {
                action() { return this.back(); },
                classes: 'shepherd-button-secondary',
                text: 'Anterior'
            },
            {
                action() { return this.complete(); },
                text: 'Finalizar'
            }
        ]
    });

    tourHome.start();
}


// Tour para la página "Mi Cuenta" (cuenta.html)
function iniciarTourCuenta() {
    const tourCuenta = new Shepherd.Tour({
        use  ModalOverlay: true,
        defaultStepOptions: {
            classes: 'shadow-md bg-purple-dark',
            scrollTo: true,
            cancelIcon: {
                enabled: true
            }
        }
    });

    tourCuenta.addStep({
        id: 'panel-personal',
        text: '¡Bienvenido a tu Panel Personal! Este es tu centro de control para gestionar tu progreso y herramientas de estudio. ¡Vamos a ver rápidamente qué puedes hacer aquí!',
        attachTo: { element: '#panel-menu', on: 'right' },
        buttons: [
            {
                action() { return this.next(); },
                text: 'Empezar'
            }
        ]
    });

    tourCuenta.addStep({
        id: 'filtro-convocatoria',
        text: 'Usa este menú para ver tus estadísticas de una convocatoria específica o de todas a la vez.',
        attachTo: { element: '.filtro-convocatoria', on: 'bottom' },
        buttons: [
            { action() { return this.back(); }, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'evolucion',
        text: 'Aquí verás un gráfico con la media de tus notas a lo largo del tiempo. ¡Ideal para ver tu progreso!',
        attachTo: { element: '#evolucion-link', on: 'right' },
        buttons: [
            { action() { return this.back(); }, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'estadisticas-detalladas',
        text: 'En esta sección podrás ver tu porcentaje de aciertos por bloque y por tema para saber dónde tienes que mejorar.',
        attachTo: { element: '#estadisticas-link', on: 'right' },
        buttons: [
            { action() { return this.back(); }, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'historial-detallado',
        text: 'Consulta aquí el detalle de todos los tests que has realizado, tus notas y la opción de repasarlos.',
        attachTo: { element: '#historial-link', on: 'right' },
        buttons: [
            { action() { return this.back(); }, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'repasar-fallos',
        text: '¡Esta es una de las herramientas más potentes! Al hacer clic aquí, generarás un test solo con las preguntas que has fallado.',
        attachTo: { element: '#repasar-fallos-link', on: 'right' },
        buttons: [
            { action() { return this.back(); }, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'preguntas-favoritas',
        text: 'Las preguntas que marques con la estrella ⭐ en los tests aparecerán aquí para que puedas repasarlas cuando quieras.',
        attachTo: { element: '#preguntas-favoritas-link', on: 'right' },
        buttons: [
            { action() { return this.back(); }, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'generador-tests',
        text: 'Crea tests personalizados seleccionando los bloques y temas que te interesen. ¡Ideal para enfocar tu estudio!',
        attachTo: { element: '#generador-tests-link', on: 'right' },
        buttons: [
            { action() { return this.back(); }, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action() { return this.next(); }, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'zona-peligro',
        text: 'Ten cuidado aquí. Este botón borrará TODO tu historial de tests y estadísticas de forma permanente.',
        attachTo: { element: '.zona-peligro', on: 'top' },
        buttons: [
            { action() { return this.back(); }, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action() { return this.complete(); }, text: 'Finalizar' }
        ]
    });

    tourCuenta.start();
}


// Este bloque se asegura de que los tours se inicien correctamente con los botones,
// evitando conflictos si se pulsan varias veces o si el DOM no está cargado.
document.addEventListener('DOMContentLoaded', function() {
    // Escucha el botón del tour principal (en la navbar, para usuarios no autenticados)
    const botonTourPrincipal = document.getElementById('iniciar-tour');
    if (botonTourPrincipal) {
        botonTourPrincipal.addEventListener('click', function(e) {
            e.preventDefault();
            iniciarVisitaGuiada();
        });
    }

    // Escucha el botón del tour de "Mi Cuenta" (en la página de cuenta, para usuarios autenticados)
    const botonTourCuenta = document.getElementById('iniciar-tour-cuenta');
    if (botonTourCuenta) {
        botonTourCuenta.addEventListener('click', function(e) {
            e.preventDefault();
            iniciarTourCuenta();
        });
    }
});