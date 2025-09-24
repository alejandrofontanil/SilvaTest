// mi_app/static/js/tour.js

/**
 * Esta es la función principal del tour de bienvenida para nuevos usuarios.
 * Se activa automáticamente después del registro.
 */
function iniciarTourBienvenida() {
    const tour = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            classes: 'shadow-md',
            scrollTo: { behavior: 'smooth', block: 'center' },
            cancelIcon: {
                enabled: true
            }
        }
    });

    // Paso 1: Saludo inicial
    tour.addStep({
        title: '¡Bienvenido a tu Panel!',
        text: 'Este es tu centro de operaciones. Te mostraré rápidamente las herramientas clave para que saques el máximo partido a la plataforma.',
        attachTo: { element: 'h2[data-aos="fade-right"]', on: 'bottom' },
        buttons: [{ action: tour.next, text: '¡Vamos! &rarr;' }]
    });

    // Paso 2: Gráfico de Evolución
    tour.addStep({
        title: 'Tu Evolución de Notas',
        text: 'Este gráfico te mostrará la tendencia de tus notas a lo largo del tiempo. ¡Es tu mejor indicador de progreso!',
        attachTo: { element: '#evolucionNotasChart', on: 'bottom' },
        buttons: [
            { classes: 'shepherd-button-secondary', action: tour.back, text: '&larr; Atrás' },
            { action: tour.next, text: 'Siguiente &rarr;' }
        ]
    });

    // Paso 3: Gráfico Radar
    tour.addStep({
        title: 'Tus Puntos Débiles',
        text: 'Este radar te muestra de un vistazo en qué bloques tienes mejor y peor rendimiento para que sepas dónde debes reforzar.',
        attachTo: { element: '#radarCompetenciasChart', on: 'bottom' },
        buttons: [
            { classes: 'shepherd-button-secondary', action: tour.back, text: '&larr; Atrás' },
            { action: tour.next, text: 'Siguiente &rarr;' }
        ]
    });
    
    // Paso 4: Lista de Convocatorias
    tour.addStep({
        title: 'Continúa tu Preparación',
        text: 'Desde aquí puedes acceder a los temarios de tus convocatorias para empezar a practicar los tests. ¡Vamos a ello!',
        attachTo: { element: '#convocatorias', on: 'top' },
        buttons: [
            { classes: 'shepherd-button-secondary', action: tour.back, text: '&larr; Atrás' },
            { action: tour.next, text: 'Casi listo &rarr;' }
        ]
    });

    // Paso 5: Final del Tour
    tour.addStep({
        title: '¡Todo Listo!',
        text: 'Ya conoces lo básico. Explora el resto de herramientas en "Mi Cuenta" y empieza a practicar. ¡Mucho éxito en tu preparación!',
        buttons: [
            {
                text: 'Finalizar Tour',
                action: tour.complete
            }
        ]
    });

    /**
     * Esta función se ejecuta cuando el tour termina (ya sea completado o cancelado).
     * Envía una petición al servidor para marcar que el usuario ya ha visto el tour.
     */
    function marcarTourComoVisto() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        fetch('/auth/marcar_tour_visto', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        }).catch(err => console.error('Error al marcar el tour como visto:', err));
    }

    tour.on('complete', marcarTourComoVisto);
    tour.on('cancel', marcarTourComoVisto);

    tour.start();
}

/**
 * Este es el tour que se puede activar manualmente desde la página "Mi Cuenta".
 * Es más detallado sobre las herramientas específicas de esa sección.
 */
function iniciarTourCuenta() {
    const tourCuenta = new Shepherd.Tour({
        useModalOverlay: true,
        defaultStepOptions: {
            classes: 'shadow-md',
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
        buttons: [{ action: tourCuenta.next, text: 'Empezar' }]
    });

    tourCuenta.addStep({
        id: 'filtro-convocatoria',
        text: 'Usa este menú para ver tus estadísticas de una convocatoria específica o de todas a la vez.',
        attachTo: { element: '.filtro-convocatoria', on: 'bottom' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.next, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'evolucion',
        text: 'Aquí verás un gráfico con la media de tus notas a lo largo del tiempo. ¡Ideal para ver tu progreso!',
        attachTo: { element: '#evolucion-link', on: 'right' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.next, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'estadisticas-detalladas',
        text: 'En esta sección podrás ver tu porcentaje de aciertos por bloque y por tema para saber dónde tienes que mejorar.',
        attachTo: { element: '#estadisticas-link', on: 'right' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.next, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'historial-detallado',
        text: 'Consulta aquí el detalle de todos los tests que has realizado, tus notas y la opción de repasarlos.',
        attachTo: { element: '#historial-link', on: 'right' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.next, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'analizador-ia',
        text: '¡Nuestra función estrella! Próximamente, este analizador usará IA para detectar tus puntos débiles y darte recomendaciones de estudio personalizadas.',
        attachTo: { element: '#analizador-link', on: 'right' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.next, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'repasar-fallos',
        text: '¡Esta es una de las herramientas más potentes! Al hacer clic aquí, generarás un test solo con las preguntas que has fallado.',
        attachTo: { element: '#repasar-fallos-link', on: 'right' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.next, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'preguntas-favoritas',
        text: 'Las preguntas que marques con la estrella ⭐ en los tests aparecerán aquí para que puedas repasarlas cuando quieras.',
        attachTo: { element: '#preguntas-favoritas-link', on: 'right' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.next, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'generador-tests',
        text: 'Crea tests personalizados seleccionando los bloques y temas que te interesen. ¡Ideal para enfocar tu estudio!',
        attachTo: { element: '#generador-tests-link', on: 'right' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.next, text: 'Siguiente' }
        ]
    });

    tourCuenta.addStep({
        id: 'zona-peligro',
        text: 'Ten cuidado aquí. Este botón borrará TODO tu historial de tests y estadísticas de forma permanente.',
        attachTo: { element: '.zona-peligro', on: 'top' },
        buttons: [
            { action: tourCuenta.back, classes: 'shepherd-button-secondary', text: 'Anterior' },
            { action: tourCuenta.complete, text: 'Finalizar' }
        ]
    });

    tourCuenta.start();
}


/**
 * Este bloque se asegura de que los tours se inicien correctamente con los botones,
 * evitando conflictos.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Escucha el botón del tour en la página de "Mi Cuenta"
    const botonTourCuenta = document.getElementById('iniciar-tour-cuenta');
    if (botonTourCuenta) {
        botonTourCuenta.addEventListener('click', function(e) {
            e.preventDefault();
            iniciarTourCuenta();
        });
    }
});