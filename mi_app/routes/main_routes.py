from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date
import random
from collections import defaultdict
from itertools import groupby

from mi_app import db
from mi_app.models import Convocatoria, Bloque, Tema, Pregunta, Respuesta, ResultadoTest, RespuestaUsuario
from mi_app.forms import FiltroCuentaForm # <-- IMPORTAMOS EL NUEVO FORMULARIO

main_bp = Blueprint('main', __name__)

def obtener_preguntas_recursivas(tema):
    preguntas = []
    preguntas.extend(tema.preguntas)
    for subtema in tema.subtemas:
        preguntas.extend(obtener_preguntas_recursivas(subtema))
    return preguntas

@main_bp.route('/')
@main_bp.route('/home')
def home():
    if current_user.is_authenticated and not current_user.es_admin:
        convocatorias = current_user.convocatorias_accesibles.all()
    else:
        convocatorias = Convocatoria.query.order_by(Convocatoria.nombre).all()
    return render_template('home.html', convocatorias=convocatorias)

@main_bp.route('/convocatoria/<int:convocatoria_id>')
@login_required
def convocatoria_detalle(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    if not current_user.es_admin and convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    return render_template('convocatoria_detalle.html', convocatoria=convocatoria)

@main_bp.route('/bloque/<int:bloque_id>')
@login_required
def bloque_detalle(bloque_id):
    bloque = Bloque.query.get_or_404(bloque_id)
    if not current_user.es_admin and bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    temas = bloque.temas.filter_by(parent_id=None).order_by(Tema.nombre).all()
    return render_template('bloque_detalle.html', bloque=bloque, temas=temas)

# --- FUNCIÓN 'CUENTA' ACTUALIZADA CON LÓGICA DE FILTRADO ---
@main_bp.route('/cuenta', methods=['GET', 'POST'])
@login_required
def cuenta():
    form = FiltroCuentaForm()

    # Preparamos las opciones para el menú desplegable del formulario
    opciones = [(0, 'Todas mis convocatorias')] + [(c.id, c.nombre) for c in current_user.convocatorias_accesibles.order_by('nombre').all()]
    form.convocatoria.choices = opciones

    # Obtenemos la convocatoria seleccionada desde la URL (si existe)
    convocatoria_id = request.args.get('convocatoria_id', 0, type=int)

    # Base de la consulta: todos los resultados del usuario
    query_resultados = ResultadoTest.query.filter_by(autor=current_user)

    # Si el usuario ha filtrado por una convocatoria específica, modificamos la consulta
    if convocatoria_id != 0:
        query_resultados = query_resultados.join(ResultadoTest.tema).join(Tema.bloque).filter(Bloque.convocatoria_id == convocatoria_id)

    # --- El resto de la lógica para calcular estadísticas y gráficos ---

    resultados_del_periodo = query_resultados.order_by(ResultadoTest.fecha.asc()).all()

    resultados_agrupados = defaultdict(lambda: {'notas': [], 'nota_media': 0})
    for fecha, grupo in groupby(resultados_del_periodo, key=lambda r: r.fecha.date()):
        notas_del_dia = [r.nota for r in grupo]
        if notas_del_dia:
            resultados_agrupados[fecha]['nota_media'] = sum(notas_del_dia) / len(notas_del_dia)

    dias_ordenados = sorted(resultados_agrupados.keys())
    labels_grafico = [dia.strftime('%d/%m/%Y') for dia in dias_ordenados]
    datos_grafico = [round(resultados_agrupados[dia]['nota_media'], 2) for dia in dias_ordenados]

    resultados_tabla = query_resultados.order_by(ResultadoTest.fecha.desc()).all()
    total_preguntas_hechas = RespuestaUsuario.query.filter_by(autor=current_user).count()

    nota_media_global = 0
    if resultados_tabla:
        # Recalculamos la nota media global solo con los resultados filtrados
        nota_media_global = sum([r.nota for r in resultados_tabla]) / len(resultados_tabla)

    # Si se envía el formulario, redirigimos a la misma página con el filtro en la URL
    if form.validate_on_submit():
        id_seleccionado = form.convocatoria.data
        return redirect(url_for('main.cuenta', convocatoria_id=id_seleccionado))

    # Pre-seleccionamos el valor del dropdown según la URL
    form.convocatoria.data = convocatoria_id

    return render_template(
        'cuenta.html', 
        title='Mi Cuenta', 
        form=form, # Pasamos el formulario a la plantilla
        resultados=resultados_tabla,
        labels_grafico=labels_grafico,
        datos_grafico=datos_grafico,
        total_preguntas_hechas=total_preguntas_hechas,
        nota_media_global=nota_media_global
    )

@main_bp.route('/cuenta/favoritas')
@login_required
def preguntas_favoritas():
    preguntas = current_user.preguntas_favoritas.order_by(Pregunta.id.desc()).all()
    return render_template('favoritas.html', title="Mis Preguntas Favoritas", preguntas=preguntas)

# (El resto de tus funciones: hacer_test, corregir_test, etc. no cambian)
# ...
@main_bp.route('/tema/<int:tema_id>/test')
@login_required
def hacer_test(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    if not current_user.es_admin and tema.bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    preguntas_test = obtener_preguntas_recursivas(tema)
    if not preguntas_test:
        flash('Este tema no contiene preguntas (ni en sus subtemas).', 'warning')
        return redirect(url_for('main.bloque_detalle', bloque_id=tema.bloque_id))
    random.shuffle(preguntas_test)
    for pregunta in preguntas_test:
        if pregunta.tipo_pregunta == 'opcion_multiple':
            respuestas_barajadas = list(pregunta.respuestas)
            random.shuffle(respuestas_barajadas)
            pregunta.respuestas_barajadas = respuestas_barajadas
    return render_template('hacer_test.html', title=f"Test de {tema.nombre}", tema=tema, preguntas=preguntas_test)

@main_bp.route('/tema/<int:tema_id>/corregir', methods=['GET', 'POST'])
@login_required
def corregir_test(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    if not current_user.es_admin and tema.bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    preguntas_en_test = obtener_preguntas_recursivas(tema)
    aciertos = 0
    total_preguntas = len(preguntas_en_test)
    if not preguntas_en_test:
        flash('No se puede corregir un test sin preguntas.', 'warning')
        return redirect(url_for('main.home'))

    nuevo_resultado = ResultadoTest(nota=0, tema_id=tema.id, autor=current_user)
    db.session.add(nuevo_resultado)
    db.session.flush()

    for pregunta in preguntas_en_test:
        es_correcta = False
        if pregunta.tipo_pregunta == 'opcion_multiple':
            id_respuesta_marcada = request.form.get(f'pregunta-{pregunta.id}')
            if id_respuesta_marcada:
                respuesta_seleccionada = Respuesta.query.get(id_respuesta_marcada)
                if respuesta_seleccionada and respuesta_seleccionada.es_correcta:
                    es_correcta = True
                respuesta_usuario = RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta_id=pregunta.id, respuesta_seleccionada_id=respuesta_seleccionada.id, resultado_test=nuevo_resultado)
                db.session.add(respuesta_usuario)
        elif pregunta.tipo_pregunta == 'respuesta_texto':
            respuesta_texto_usuario = request.form.get(f'pregunta-{pregunta.id}')
            if respuesta_texto_usuario and pregunta.respuesta_correcta_texto and \
               respuesta_texto_usuario.strip().lower() == pregunta.respuesta_correcta_texto.strip().lower():
                es_correcta = True
            if respuesta_texto_usuario is not None:
                respuesta_usuario = RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta_id=pregunta.id, respuesta_texto_usuario=respuesta_texto_usuario, resultado_test=nuevo_resultado)
                db.session.add(respuesta_usuario)
        if es_correcta:
            aciertos += 1

    nota_final = (aciertos / total_preguntas) * 10 if total_preguntas > 0 else 0
    nuevo_resultado.nota = nota_final
    db.session.commit()
    flash(f'¡Test finalizado! Tu nota es: {nota_final:.2f}/10', 'success')
    return redirect(url_for('main.resultado_test', resultado_id=nuevo_resultado.id))

@main_bp.route('/resultado/<int:resultado_id>')
@login_required
def resultado_test(resultado_id):
    resultado = ResultadoTest.query.get_or_404(resultado_id)
    if resultado.autor != current_user and not current_user.es_admin:
        abort(403)
    return render_template('resultado_test.html', title="Resultado del Test", resultado=resultado)

@main_bp.route('/resultado/<int:resultado_id>/repaso')
@login_required
def repaso_test(resultado_id):
    resultado = ResultadoTest.query.get_or_404(resultado_id)
    if resultado.autor != current_user and not current_user.es_admin:
        abort(403)
    return render_template('repaso_test.html', resultado=resultado)

@main_bp.route('/repaso_global')
@login_required
def repaso_global():
    respuestas_falladas = RespuestaUsuario.query.filter_by(autor=current_user, es_correcta=False).all()
    ids_preguntas_falladas = list({r.pregunta_id for r in respuestas_falladas})
    preguntas_a_repasar = Pregunta.query.filter(Pregunta.id.in_(ids_preguntas_falladas)).all()
    random.shuffle(preguntas_a_repasar)
    for pregunta in preguntas_a_repasar:
        if pregunta.tipo_pregunta == 'opcion_multiple':
            respuestas_barajadas = list(pregunta.respuestas)
            random.shuffle(respuestas_barajadas)
            pregunta.respuestas_barajadas = respuestas_barajadas
    return render_template('repaso_global_test.html', preguntas=preguntas_a_repasar)

@main_bp.route('/repaso_global/corregir', methods=['POST'])
@login_required
def corregir_repaso_global():
    aciertos = 0
    ids_preguntas_enviadas = [key.split('-')[1] for key in request.form if key.startswith('pregunta-')]
    total_preguntas = len(ids_preguntas_enviadas)
    for pregunta_id in ids_preguntas_enviadas:
        respuesta_texto_usuario = request.form.get(f'pregunta-{pregunta_id}')
        pregunta = Pregunta.query.get(pregunta_id)
        es_correcta = False
        if pregunta.tipo_pregunta == 'opcion_multiple':
            respuesta_marcada = Respuesta.query.get(int(respuesta_texto_usuario))
            if respuesta_marcada and respuesta_marcada.es_correcta:
                es_correcta = True
        elif pregunta.tipo_pregunta == 'respuesta_texto':
            if respuesta_texto_usuario and pregunta.respuesta_correcta_texto and \
               respuesta_texto_usuario.strip().lower() == pregunta.respuesta_correcta_texto.strip().lower():
                es_correcta = True
        if es_correcta:
            aciertos += 1
            respuestas_a_limpiar = RespuestaUsuario.query.filter_by(autor=current_user, pregunta_id=pregunta_id, es_correcta=False).all()
            for r in respuestas_a_limpiar:
                db.session.delete(r)
    db.session.commit()
    nota_string = f"Has acertado {aciertos} de {total_preguntas}."
    flash(f'¡Repaso finalizado! {nota_string}', 'success')
    return redirect(url_for('main.cuenta'))

@main_bp.route('/comprobar_respuesta', methods=['POST'])
@login_required
def comprobar_respuesta():
    datos = request.get_json()
    id_respuesta = datos.get('respuesta_id')
    if not id_respuesta:
        return jsonify({'error': 'No se recibió ID de respuesta'}), 400
    respuesta = Respuesta.query.get(id_respuesta)
    if not respuesta:
        return jsonify({'error': 'Respuesta no encontrada'}), 404
    if respuesta.es_correcta:
        return jsonify({'es_correcta': True, 'retroalimentacion': respuesta.pregunta.retroalimentacion})
    else:
        return jsonify({'es_correcta': False, 'retroalimentacion': respuesta.pregunta.retroalimentacion})

@main_bp.route('/pregunta/<int:pregunta_id>/toggle_favorito', methods=['POST'])
@login_required
def toggle_favorito(pregunta_id):
    pregunta = Pregunta.query.get_or_404(pregunta_id)
    if current_user.es_favorita(pregunta):
        current_user.desmarcar_favorita(pregunta)
        es_favorita_ahora = False
    else:
        current_user.marcar_favorita(pregunta)
        es_favorita_ahora = True
    db.session.commit()
    return jsonify({'success': True, 'es_favorita': es_favorita_ahora})

@main_bp.route('/pregunta/<int:pregunta_id>/reportar', methods=['POST'])
@login_required
def reportar_pregunta(pregunta_id):
    pregunta = Pregunta.query.get_or_404(pregunta_id)
    pregunta.necesita_revision = True
    db.session.commit()
    return jsonify({'success': True, 'message': '¡Gracias! La pregunta ha sido marcada para revisión.'})

@main_bp.route('/politica-de-privacidad')
def politica_privacidad():
    return render_template('politica_privacidad.html', title="Política de Privacidad")

@main_bp.route('/terminos-y-condiciones')
def terminos_condiciones():
    return render_template('terminos_condiciones.html', title="Términos y Condiciones")