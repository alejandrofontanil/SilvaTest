from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, session, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import func, desc, case
from sqlalchemy.sql.expression import func as sql_func
from datetime import date, timedelta # <-- IMPORTACIÓN MODIFICADA
import random
from collections import defaultdict
from itertools import groupby
from flask_wtf import FlaskForm

from mi_app import db
from mi_app.models import Convocatoria, Bloque, Tema, Pregunta, Respuesta, ResultadoTest, RespuestaUsuario
from mi_app.forms import FiltroCuentaForm

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
    if current_user.is_authenticated and current_user.es_admin:
        convocatorias = Convocatoria.query.order_by(Convocatoria.nombre).all()
        return render_template('home.html', convocatorias=convocatorias)
    elif current_user.is_authenticated:
        convocatorias = current_user.convocatorias_accesibles.all()
        resultados_totales = ResultadoTest.query.filter_by(autor=current_user).all()
        nota_media_global = 0
        if resultados_totales:
            # Evitar división por cero
            if len(resultados_totales) > 0:
                nota_media_global = sum([r.nota for r in resultados_totales]) / len(resultados_totales)
        ultimo_resultado = ResultadoTest.query.filter_by(autor=current_user).order_by(desc(ResultadoTest.fecha)).first()
        ultimas_favoritas = current_user.preguntas_favoritas.order_by(Pregunta.id.desc()).limit(3).all()
        return render_template('home.html', 
                                  convocatorias=convocatorias,
                                  nota_media_global=nota_media_global,
                                  ultimo_resultado=ultimo_resultado,
                                  ultimas_favoritas=ultimas_favoritas)
    else:
        convocatorias = Convocatoria.query.filter_by(es_publica=True).order_by(Convocatoria.nombre).all()
        return render_template('home.html', convocatorias=convocatorias)


@main_bp.route('/convocatoria/<int:convocatoria_id>')
@login_required
def convocatoria_detalle(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    if not current_user.es_admin and convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    
    breadcrumbs = [
        ('Inicio', url_for('main.home')),
        (convocatoria.nombre, None)
    ]

    return render_template('convocatoria_detalle.html', 
                           convocatoria=convocatoria,
                           breadcrumbs=breadcrumbs)

@main_bp.route('/bloque/<int:bloque_id>')
@login_required
def bloque_detalle(bloque_id):
    bloque = Bloque.query.get_or_404(bloque_id)
    if not current_user.es_admin and bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    temas = bloque.temas.filter_by(parent_id=None).order_by(Tema.nombre).all()
    
    convocatoria = bloque.convocatoria
    breadcrumbs = [
        ('Inicio', url_for('main.home')),
        (convocatoria.nombre, url_for('main.convocatoria_detalle', convocatoria_id=convocatoria.id)),
        (bloque.nombre, None)
    ]

    return render_template('bloque_detalle.html', 
                           bloque=bloque, 
                           temas=temas,
                           breadcrumbs=breadcrumbs)

@main_bp.route('/cuenta', methods=['GET', 'POST'])
@login_required
def cuenta():
    form = FiltroCuentaForm()
    opciones = [(0, 'Todas mis convocatorias')] + [(c.id, c.nombre) for c in current_user.convocatorias_accesibles.order_by('nombre').all()]
    form.convocatoria.choices = opciones
    
    convocatoria_id = request.args.get('convocatoria_id', 0, type=int)
    active_tab = request.args.get('tab', 'evolucion')

    if form.validate_on_submit():
        id_seleccionado = form.convocatoria.data
        tab_activa_al_enviar = request.form.get('tab', 'evolucion')
        return redirect(url_for('main.cuenta', convocatoria_id=id_seleccionado, tab=tab_activa_al_enviar))
    
    form.convocatoria.data = convocatoria_id

    query_resultados = ResultadoTest.query.filter_by(autor=current_user)
    if convocatoria_id != 0:
        query_resultados = query_resultados.join(Tema).join(Bloque).filter(Bloque.convocatoria_id == convocatoria_id)
    
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
    total_preguntas_hechas = db.session.query(RespuestaUsuario).filter_by(autor=current_user).count()
    nota_media_global = db.session.query(func.avg(ResultadoTest.nota)).filter_by(autor=current_user).scalar() or 0

    stats_temas = []
    stats_bloques = []
    
    query_stats_base = db.session.query(
        func.count(RespuestaUsuario.id).label('total'),
        func.sum(case((RespuestaUsuario.es_correcta, 1), else_=0)).label('aciertos')
    ).select_from(RespuestaUsuario).join(Pregunta).filter(RespuestaUsuario.usuario_id == current_user.id)
    
    stats_por_tema_query = query_stats_base.join(Tema)
    if convocatoria_id != 0:
        stats_por_tema_query = stats_por_tema_query.join(Bloque).filter(Bloque.convocatoria_id == convocatoria_id)
    resultados_temas = stats_por_tema_query.group_by(Tema.id).add_columns(Tema.nombre.label('nombre')).all()

    stats_por_bloque_query = query_stats_base.join(Tema).join(Bloque)
    if convocatoria_id != 0:
        stats_por_bloque_query = stats_por_bloque_query.filter(Bloque.convocatoria_id == convocatoria_id)
    resultados_bloques = stats_por_bloque_query.group_by(Bloque.id).add_columns(Bloque.nombre.label('nombre')).all()

    for r in resultados_temas:
        porcentaje = (r.aciertos / r.total * 100) if r.total > 0 else 0
        stats_temas.append({'nombre': r.nombre, 'total': r.total, 'aciertos': r.aciertos, 'porcentaje': round(porcentaje)})

    for r in resultados_bloques:
        porcentaje = (r.aciertos / r.total * 100) if r.total > 0 else 0
        stats_bloques.append({'nombre': r.nombre, 'total': r.total, 'aciertos': r.aciertos, 'porcentaje': round(porcentaje)})
    
    stats_temas.sort(key=lambda x: x['porcentaje'])
    stats_bloques.sort(key=lambda x: x['porcentaje'])

    iniciar_tour = request.args.get('tour', 'false').lower() == 'true'

    return render_template(
        'cuenta.html', title='Mi Cuenta', form=form, 
        resultados=resultados_tabla,
        labels_grafico=labels_grafico, datos_grafico=datos_grafico,
        total_preguntas_hechas=total_preguntas_hechas, 
        nota_media_global=nota_media_global,
        stats_temas=stats_temas,
        stats_bloques=stats_bloques,
        active_tab=active_tab,
        iniciar_tour_automaticamente=iniciar_tour
    )

@main_bp.route('/cuenta/resetear', methods=['POST'])
@login_required
def resetear_estadisticas():
    RespuestaUsuario.query.filter_by(autor=current_user).delete()
    ResultadoTest.query.filter_by(autor=current_user).delete()
    db.session.commit()
    flash('¡Tus estadísticas han sido reseteadas con éxito!', 'success')
    return redirect(url_for('main.cuenta'))

@main_bp.route('/cuenta/favoritas')
@login_required
def preguntas_favoritas():
    preguntas = current_user.preguntas_favoritas.order_by(Pregunta.id.desc()).all()
    return render_template('favoritas.html', title="Mis Preguntas Favoritas", preguntas=preguntas)

@main_bp.route('/tema/<int:tema_id>/test')
@login_required
def hacer_test(tema_id):
    form = FlaskForm()
    tema = Tema.query.get_or_404(tema_id)
    if not current_user.es_admin and tema.bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    
    bloque = tema.bloque
    convocatoria = bloque.convocatoria
    breadcrumbs = [
        ('Inicio', url_for('main.home')),
        (convocatoria.nombre, url_for('main.convocatoria_detalle', convocatoria_id=convocatoria.id)),
        (bloque.nombre, url_for('main.bloque_detalle', bloque_id=bloque.id)),
        (tema.nombre, None)
    ]

    preguntas_test = obtener_preguntas_recursivas(tema)
    if not preguntas_test:
        flash('Este tema no contiene preguntas (ni en sus subtemas).', 'warning')
        return redirect(url_for('main.bloque_detalle', bloque_id=tema.bloque_id))
    
    random.shuffle(preguntas_test)
    for pregunta in preguntas_test:
        if pregunta.tipo_pregunta == 'opcion_multiple':
            lista_respuestas = list(pregunta.respuestas)
            random.shuffle(lista_respuestas)
            pregunta.respuestas_barajadas = lista_respuestas
    
    return render_template('hacer_test.html', 
                           title=f"Test de {tema.nombre}", 
                           tema=tema, 
                           preguntas=preguntas_test, 
                           form=form,
                           breadcrumbs=breadcrumbs)

@main_bp.route('/tema/<int:tema_id>/corregir', methods=['POST'])
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
                respuesta_usuario = RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta_id=pregunta.id, respuesta_seleccionada_id=int(id_respuesta_marcada), resultado_test=nuevo_resultado)
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
    form = FlaskForm()
    respuestas_falladas = RespuestaUsuario.query.filter_by(autor=current_user, es_correcta=False).all()
    ids_preguntas_falladas = list({r.pregunta_id for r in respuestas_falladas})
    preguntas_a_repasar = Pregunta.query.filter(Pregunta.id.in_(ids_preguntas_falladas)).all()
    random.shuffle(preguntas_a_repasar)
    
    for pregunta in preguntas_a_repasar:
        if pregunta.tipo_pregunta == 'opcion_multiple':
            respuestas_barajadas = list(pregunta.respuestas)
            random.shuffle(respuestas_barajadas)
            pregunta.respuestas_barajadas = respuestas_barajadas
            
    return render_template('repaso_global_test.html', preguntas=preguntas_a_repasar, form=form)

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
            if respuesta_texto_usuario:
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

@main_bp.route('/generador-simulacro', methods=['GET', 'POST'])
@login_required
def generador_simulacro():
    form = FlaskForm()
    if form.validate_on_submit():
        preguntas_para_el_test_ids = []
        temas_seleccionados_ids = request.form.getlist('tema_seleccionado', type=int)
        
        if not temas_seleccionados_ids:
            flash('Debes seleccionar al menos un tema.', 'warning')
            return redirect(url_for('main.generador_simulacro'))
            
        for tema_id in temas_seleccionados_ids:
            try:
                num_preguntas = int(request.form.get(f'num_preguntas_{tema_id}', 10))
            except (ValueError, TypeError):
                num_preguntas = 10
            
            if num_preguntas == 0:
                continue

            tema = Tema.query.get_or_404(tema_id)
            preguntas_disponibles = obtener_preguntas_recursivas(tema)
            num_a_seleccionar = min(num_preguntas, len(preguntas_disponibles))
            
            if num_a_seleccionar > 0:
                preguntas_seleccionadas = random.sample(preguntas_disponibles, k=num_a_seleccionar)
                preguntas_para_el_test_ids.extend([p.id for p in preguntas_seleccionadas])
                
        if not preguntas_para_el_test_ids:
            flash('No se pudieron generar preguntas con los criterios seleccionados.', 'warning')
            return redirect(url_for('main.generador_simulacro'))
        
        session['id_preguntas_simulacro'] = preguntas_para_el_test_ids
        return redirect(url_for('main.simulacro_personalizado_test'))
    
    convocatorias_accesibles = current_user.convocatorias_accesibles.order_by(Convocatoria.nombre).all()
    return render_template('generador_simulacro.html', title="Generador de Simulacros", convocatorias=convocatorias_accesibles, form=form)

@main_bp.route('/simulacro/empezar')
@login_required
def simulacro_personalizado_test():
    ids_preguntas = session.get('id_preguntas_simulacro', [])
    if not ids_preguntas:
        flash('No hay un simulacro personalizado para empezar. Por favor, genera uno nuevo.', 'warning')
        return redirect(url_for('main.generador_simulacro'))
    
    preguntas_test = db.session.query(Pregunta).filter(Pregunta.id.in_(ids_preguntas)).all()
    random.shuffle(preguntas_test)
    
    for pregunta in preguntas_test:
        if pregunta.tipo_pregunta == 'opcion_multiple':
            lista_respuestas = list(pregunta.respuestas)
            random.shuffle(lista_respuestas)
            pregunta.respuestas_barajadas = lista_respuestas
            
    form = FlaskForm()
    tema_dummy = {'nombre': 'Simulacro Personalizado', 'es_simulacro': True}
    return render_template('hacer_test.html', 
                           title="Simulacro Personalizado", 
                           tema=tema_dummy, 
                           preguntas=preguntas_test, 
                           is_personalizado=True,
                           form=form)

@main_bp.route('/simulacro/corregir', methods=['POST'])
@login_required
def corregir_simulacro_personalizado():
    ids_preguntas_en_test = session.get('id_preguntas_simulacro', [])
    if not ids_preguntas_en_test:
        flash('La sesión de tu simulacro ha expirado. Por favor, genera uno nuevo.', 'danger')
        return redirect(url_for('main.generador_simulacro'))
    
    preguntas_en_test = db.session.query(Pregunta).filter(Pregunta.id.in_(ids_preguntas_en_test)).all()
    aciertos = 0
    total_preguntas = len(preguntas_en_test)
    
    tema_simulacro_personalizado = Tema.query.filter_by(nombre="Simulacros Personalizados").first()
    if not tema_simulacro_personalizado:
        bloque_general = Bloque.query.filter_by(nombre="General").first()
        if not bloque_general:
            convo_general = Convocatoria.query.filter_by(nombre="General").first()
            if not convo_general:
                convo_general = Convocatoria(nombre="General")
                db.session.add(convo_general)
                db.session.flush()
            bloque_general = Bloque(nombre="General", convocatoria_id=convo_general.id)
            db.session.add(bloque_general)
            db.session.flush()
        tema_simulacro_personalizado = Tema(nombre="Simulacros Personalizados", bloque_id=bloque_general.id, es_simulacro=True)
        db.session.add(tema_simulacro_personalizado)
        db.session.commit()
        
    nuevo_resultado = ResultadoTest(nota=0, tema_id=tema_simulacro_personalizado.id, autor=current_user)
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
                respuesta_usuario = RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta_id=pregunta.id, respuesta_seleccionada_id=int(id_respuesta_marcada), resultado_test=nuevo_resultado)
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
    session.pop('id_preguntas_simulacro', None)
    db.session.commit()
    
    flash(f'¡Simulacro finalizado! Tu nota es: {nota_final:.2f}/10', 'success')
    return redirect(url_for('main.resultado_test', resultado_id=nuevo_resultado.id))

@main_bp.route('/guardar_preferencias', methods=['POST'])
@login_required
def guardar_preferencias():
    # La forma correcta de comprobar un checkbox es ver si existe en el form
    recibir_resumen = 'resumen_semanal' in request.form
    
    current_user.recibir_resumen_semanal = recibir_resumen
    db.session.commit() # ¡Esta es la línea clave que guarda en la BBDD!
    
    flash('Tus preferencias han sido guardadas.', 'success')
    return redirect(url_for('main.cuenta'))

@main_bp.route('/sw.js')
def sw():
    response = send_from_directory('static', 'sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@main_bp.route('/offline')
def offline():
    return render_template('offline.html')

@main_bp.route('/debug-db')
@login_required
def debug_db():
    if not current_user.es_admin:
        abort(403)
    from .models import Usuario
    usuarios = Usuario.query.all()
    output = "<h1>Estado de la Base de Datos</h1>"
    output += "<table border='1'><tr><th>ID</th><th>Email</th><th>Recibir Resumen?</th></tr>"
    for usuario in usuarios:
        output += f"<tr><td>{usuario.id}</td><td>{usuario.email}</td><td><b>{usuario.recibir_resumen_semanal}</b></td></tr>"
    output += "</table>"
    return output

# === NUEVA RUTA PARA DATOS DEL GRÁFICO ===
@main_bp.route('/api/evolucion-notas')
@login_required
def api_evolucion_notas():
    """
    Esta ruta devuelve los datos de la evolución de notas del usuario
    en formato JSON para que Chart.js los pueda usar.
    """
    from datetime import datetime, timedelta

    # Filtramos los resultados de los últimos 30 días
    fecha_inicio = datetime.utcnow() - timedelta(days=30)

    resultados_periodo = ResultadoTest.query.filter(
        ResultadoTest.autor == current_user,
        ResultadoTest.fecha >= fecha_inicio
    ).order_by(ResultadoTest.fecha.asc()).all()

    # Agrupamos los resultados por día y calculamos la nota media
    resultados_agrupados = defaultdict(list)
    for resultado in resultados_periodo:
        resultados_agrupados[resultado.fecha.date()].append(resultado.nota)

    notas_medias_por_dia = {
        fecha: sum(notas) / len(notas)
        for fecha, notas in resultados_agrupados.items()
    }

    # Preparamos los datos para el gráfico
    dias_ordenados = sorted(notas_medias_por_dia.keys())
    labels_grafico = [dia.strftime('%d/%m') for dia in dias_ordenados]
    datos_grafico = [round(notas_medias_por_dia[dia], 2) for dia in dias_ordenados]

    return jsonify({'labels': labels_grafico, 'data': datos_grafico})


# === NUEVA RUTA PARA DATOS DEL GRÁFICO DE RADAR ===
@main_bp.route('/api/radar-competencias')
@login_required
def api_radar_competencias():
    """
    Calcula la nota media del usuario por cada bloque principal y la devuelve en JSON.
    """
    # Consulta para obtener el rendimiento agrupado por bloque
    stats_por_bloque = db.session.query(
        Bloque.nombre,
        func.avg(case((RespuestaUsuario.es_correcta, 10), else_=0)).label('nota_media')
    ).select_from(RespuestaUsuario).join(
        Pregunta, RespuestaUsuario.pregunta_id == Pregunta.id
    ).join(
        Tema, Pregunta.tema_id == Tema.id
    ).join(
        Bloque, Tema.bloque_id == Bloque.id
    ).filter(
        RespuestaUsuario.usuario_id == current_user.id
    ).group_by(
        Bloque.nombre
    ).order_by(
        Bloque.nombre
    ).all()

    # Preparamos los datos para Chart.js
    labels = [resultado[0] for resultado in stats_por_bloque]
    data = [round(resultado[1], 2) if resultado[1] is not None else 0 for resultado in stats_por_bloque]

    return jsonify({'labels': labels, 'data': data})

# ... al final de mi_app/routes/main_routes.py ...

# === NUEVA RUTA PARA DATOS DEL CALENDARIO DE ACTIVIDAD ===
@main_bp.route('/api/calendario-actividad')
@login_required
def api_calendario_actividad():
    """
    Devuelve el número de tests realizados por día durante el último año.
    """
    from datetime import datetime

    # Definimos el rango de fechas: desde hoy hasta hace 365 días
    fecha_fin = datetime.utcnow().date()
    fecha_inicio = fecha_fin - timedelta(days=365)

    # Contamos los tests por día
    resultados_por_dia = db.session.query(
        func.date(ResultadoTest.fecha).label('dia'),
        func.count(ResultadoTest.id).label('cantidad')
    ).filter(
        ResultadoTest.usuario_id == current_user.id,
        func.date(ResultadoTest.fecha).between(fecha_inicio, fecha_fin)
    ).group_by('dia').all()

    # Formateamos los datos para la librería del calendario
    # El formato es una lista de diccionarios: [{'date': 'YYYY-MM-DD', 'value': X}]
    data_para_calendario = [
        {'date': resultado.dia.strftime('%Y-%m-%d'), 'value': resultado.cantidad}
        for resultado in resultados_por_dia
    ]

    return jsonify(data_para_calendario)

# === RUTA TEMPORAL PARA RESETEAR EL HISTORIAL DE MIGRACIÓN ===
@main_bp.route('/reset-historial-migracion-secreto-12345')
@login_required
def reset_historial_migracion():
    # Solo el admin puede ejecutar esto
    if not current_user.es_admin:
        abort(403)
    try:
        # Este comando vacía la tabla que guarda el historial
        db.session.execute(db.text('TRUNCATE TABLE alembic_version;'))
        db.session.commit()
        flash('¡El historial de migración de la base de datos ha sido reseteado con éxito!', 'success')
        return redirect(url_for('main.home'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al resetear el historial: {e}', 'danger')
        return redirect(url_for('main.home'))
# === FIN DE LA RUTA TEMPORAL ===