# --- INICIO: IMPORTACIONES COMPLETAS ---
import os
import json
import vertexai
import re
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
from google.cloud import storage # <--- Importación para listar archivos del bucket

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, session, send_from_directory
from flask_login import login_required, current_user
from sqlalchemy import func, desc, case
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import random
from collections import defaultdict
from itertools import groupby
from flask_wtf import FlaskForm

from mi_app import db
from mi_app.models import Convocatoria, Bloque, Tema, Pregunta, Respuesta, ResultadoTest, RespuestaUsuario, Usuario 
from mi_app.forms import ObjetivoForm, FiltroCuentaForm, DashboardPreferencesForm, ObjetivoFechaForm
from mi_app.rag_agent import get_rag_response
# --- FIN IMPORTACIONES ---

# Definición de coste
RAG_COST_PER_QUERY = 100

main_bp = Blueprint('main', __name__)

# --- CONFIGURACIÓN DE VERTEX AI (NUEVA VERSIÓN) ---
SECRET_FILE_PATH = "/etc/secrets/gcp_service_account_key.json"
credentials = None
try:
    print("--- INICIANDO CONFIGURACIÓN DE VERTEX AI ---")
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    GCP_REGION = 'us-central1' # Usamos la región correcta

    if os.path.exists(SECRET_FILE_PATH):
        credentials = service_account.Credentials.from_service_account_file(SECRET_FILE_PATH)
        print("✅ Credenciales cargadas desde Secret File para las rutas.")
    elif os.getenv('GOOGLE_CREDS_JSON'):
        creds_info = json.loads(os.getenv('GOOGLE_CREDS_JSON'))
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        print("✅ Credenciales cargadas desde variable de entorno para las rutas.")
    
    if credentials and GCP_PROJECT_ID:
        vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION, credentials=credentials)
        print("✅ Vertex AI inicializado con éxito.")
    else:
        print("❌ ERROR: No se encontraron credenciales o PROJECT_ID para inicializar Vertex AI.")
except Exception as e:
    print(f"🔥 Error catastrófico al inicializar Vertex AI: {e}")


# --- FUNCIONES DE AYUDA ---
def obtener_preguntas_recursivas(tema):
    preguntas = []
    preguntas.extend(tema.preguntas)
    for subtema in tema.subtemas:
        preguntas.extend(obtener_preguntas_recursivas(subtema))
    return preguntas

def analizar_rendimiento_usuario(usuario):
    stats_temas = db.session.query(
        Tema.nombre,
        (func.sum(case((RespuestaUsuario.es_correcta, 1), else_=0)) * 100.0 / func.count(RespuestaUsuario.id)).label('porcentaje')
    ).select_from(RespuestaUsuario).join(Pregunta, RespuestaUsuario.pregunta_id == Pregunta.id).join(Tema, Pregunta.tema_id == Tema.id).filter(
        RespuestaUsuario.usuario_id == usuario.id
    ).group_by(Tema.id).having(func.count(RespuestaUsuario.id) >= 10).order_by('porcentaje').limit(3).all()

    stats_bloque = db.session.query(
        Bloque.nombre,
        (func.sum(case((RespuestaUsuario.es_correcta, 1), else_=0)) * 100.0 / func.count(RespuestaUsuario.id)).label('porcentaje')
    ).select_from(RespuestaUsuario).join(Pregunta, RespuestaUsuario.pregunta_id == Pregunta.id).join(Tema, Pregunta.tema_id == Tema.id).join(Bloque, Tema.bloque_id == Bloque.id).filter(
        RespuestaUsuario.usuario_id == usuario.id
    ).group_by(Bloque.id).having(func.count(RespuestaUsuario.id) >= 15).order_by('porcentaje').first()

    informe = {
        "temas_debiles": [f"{nombre} ({int(porcentaje)}% aciertos)" for nombre, porcentaje in stats_temas],
        "bloque_debil": f"{stats_bloque.nombre} ({int(stats_bloque.porcentaje)}% aciertos)" if stats_bloque else None
    }
    
    if not informe["temas_debiles"] and not informe["bloque_debil"]:
        return None

    return informe

# --- RUTAS PRINCIPALES DE LA APLICACIÓN ---

@main_bp.route('/')
@main_bp.route('/home')
def home():
    if not current_user.is_authenticated or current_user.es_admin:
        convocatorias = Convocatoria.query.order_by(Convocatoria.nombre).all()
        return render_template('home.html', convocatorias=convocatorias, modules={'datetime': datetime, 'hoy': date.today()})

    convocatorias = current_user.convocatorias_accesibles.all()
    ultimo_resultado = ResultadoTest.query.filter_by(autor=current_user).order_by(desc(ResultadoTest.fecha)).first()
    ultimas_favoritas = current_user.preguntas_favoritas.order_by(Pregunta.id.desc()).limit(3).all()

    hoy = date.today()
    inicio_periodo = (hoy - relativedelta(months=5)).replace(day=1)
    resultados = db.session.query(
        func.date_trunc('month', ResultadoTest.fecha).label('mes'),
        func.count(ResultadoTest.id).label('total')
    ).filter(
        ResultadoTest.usuario_id == current_user.id,
        ResultadoTest.fecha >= inicio_periodo
    ).group_by('mes').order_by('mes').all()

    datos_grafico = {r.mes.strftime('%b %y'): r.total for r in resultados}
    labels = []
    data = []
    for i in range(6):
        mes_actual = hoy - relativedelta(months=i)
        etiqueta = mes_actual.strftime('%b %y')
        labels.append(etiqueta)
        data.append(datos_grafico.get(etiqueta, 0))
    labels.reverse()
    data.reverse()
    stats_tests_mensual = {"labels": labels, "data": data}

    total_tests = ResultadoTest.query.filter_by(autor=current_user).count()
    total_preguntas_resp = RespuestaUsuario.query.filter_by(autor=current_user).count()
    nota_media_global = db.session.query(func.avg(ResultadoTest.nota)).filter_by(autor=current_user).scalar() or 0
    stats_clave = {
        "total_tests": total_tests,
        "total_preguntas": total_preguntas_resp,
        "nota_media": nota_media_global
    }
    
    progreso_objetivo = None
    if current_user.objetivo_fecha and hasattr(current_user, 'fecha_creacion') and current_user.fecha_creacion:
        hoy = date.today()
        fecha_inicio = current_user.fecha_creacion.date()
        
        if current_user.objetivo_fecha > fecha_inicio:
            total_dias = (current_user.objetivo_fecha - fecha_inicio).days
            dias_pasados = (hoy - fecha_inicio).days
            
            if total_dias > 0:
                porcentaje = max(0, min(100, (dias_pasados / total_dias) * 100))
                progreso_objetivo = {
                    "porcentaje": int(porcentaje),
                    "dias_pasados": dias_pasados,
                    "total_dias": total_dias
                }

    return render_template('home.html',
                           convocatorias=convocatorias,
                           ultimo_resultado=ultimo_resultado,
                           ultimas_favoritas=ultimas_favoritas,
                           stats_tests_mensual=stats_tests_mensual,
                           stats_clave=stats_clave,
                           progreso_objetivo=progreso_objetivo,
                           modules={'datetime': datetime, 'hoy': date.today()})

@main_bp.route('/convocatoria/<int:convocatoria_id>')
@login_required
def convocatoria_detalle(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    if not current_user.es_admin and convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    breadcrumbs = [('Inicio', url_for('main.home')), (convocatoria.nombre, None)]
    return render_template('convocatoria_detalle.html', convocatoria=convocatoria, breadcrumbs=breadcrumbs)

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
    return render_template('bloque_detalle.html', bloque=bloque, temas=temas, breadcrumbs=breadcrumbs)

@main_bp.route('/cuenta', methods=['GET', 'POST'])
@login_required
def cuenta():
    form = FiltroCuentaForm()
    objetivo_form = ObjetivoForm()
    dashboard_form = DashboardPreferencesForm()
    objetivo_fecha_form = ObjetivoFechaForm()
    
    if request.method == 'GET':
        if current_user.objetivo_fecha:
            objetivo_fecha_form.objetivo_fecha.data = current_user.objetivo_fecha
        if current_user.preferencias_dashboard:
            dashboard_form.mostrar_grafico_evolucion.data = current_user.preferencias_dashboard.get('mostrar_grafico_evolucion', True)
            dashboard_form.mostrar_rendimiento_bloque.data = current_user.preferencias_dashboard.get('mostrar_rendimiento_bloque', True)
            dashboard_form.mostrar_calendario_actividad.data = current_user.preferencias_dashboard.get('mostrar_calendario_actividad', True)
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
    total_preguntas_hechas = RespuestaUsuario.query.filter_by(autor=current_user).count()
    nota_media_global = db.session.query(func.avg(ResultadoTest.nota)).filter_by(autor=current_user).scalar() or 0
    stats_temas, stats_bloques = [], []
    query_stats_base = db.session.query(func.count(RespuestaUsuario.id).label('total'), func.sum(case((RespuestaUsuario.es_correcta, 1), else_=0)).label('aciertos')).select_from(RespuestaUsuario).join(Pregunta).filter(RespuestaUsuario.usuario_id == current_user.id)
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
    return render_template('cuenta.html', title='Mi Cuenta', form=form, objetivo_form=objetivo_form, dashboard_form=dashboard_form, objetivo_fecha_form=objetivo_fecha_form, resultados=resultados_tabla, labels_grafico=labels_grafico, datos_grafico=datos_grafico, total_preguntas_hechas=total_preguntas_hechas, nota_media_global=nota_media_global, stats_temas=stats_temas, stats_bloques=stats_bloques, active_tab=active_tab, iniciar_tour_automaticamente=iniciar_tour)

@main_bp.route('/cuenta/resetear', methods=['POST'])
@login_required
def resetear_estadisticas():
    RespuestaUsuario.query.filter_by(autor=current_user).delete()
    ResultadoTest.query.filter_by(autor=current_user).delete()
    db.session.commit()
    flash('¡Tus estadísticas han sido reseteadas con éxito!', 'success')
    return redirect(url_for('main.cuenta'))

@main_bp.route('/cuenta/guardar-fecha-objetivo', methods=['POST'])
@login_required
def guardar_objetivo_fecha():
    form = ObjetivoFechaForm()
    if form.validate_on_submit():
        current_user.objetivo_fecha = form.objetivo_fecha.data
        db.session.commit()
        flash('¡Tu fecha objetivo ha sido guardada!', 'success')
    else:
        flash('Hubo un error al guardar la fecha.', 'danger')
    return redirect(url_for('main.cuenta', tab='personalizar'))

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
    bloque, convocatoria = tema.bloque, tema.bloque.convocatoria
    breadcrumbs = [('Inicio', url_for('main.home')), (convocatoria.nombre, url_for('main.convocatoria_detalle', convocatoria_id=convocatoria.id)), (bloque.nombre, url_for('main.bloque_detalle', bloque_id=bloque.id)), (tema.nombre, None)]
    preguntas_test = obtener_preguntas_recursivas(tema)
    if not preguntas_test:
        flash('Este tema no contiene preguntas.', 'warning')
        return redirect(url_for('main.bloque_detalle', bloque_id=tema.bloque_id))
    random.shuffle(preguntas_test)
    for pregunta in preguntas_test:
        if pregunta.tipo_pregunta == 'opcion_multiple':
            lista_respuestas = list(pregunta.respuestas)
            random.shuffle(lista_respuestas)
            pregunta.respuestas_barajadas = lista_respuestas
    return render_template('hacer_test.html', title=f"Test de {tema.nombre}", tema=tema, preguntas=preguntas_test, form=form, is_personalizado=False, breadcrumbs=breadcrumbs)

@main_bp.route('/tema/<int:tema_id>/corregir', methods=['POST'])
@login_required
def corregir_test(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    if not current_user.es_admin and tema.bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    preguntas_en_test = obtener_preguntas_recursivas(tema)
    if not preguntas_en_test:
        flash('No se puede corregir un test sin preguntas.', 'warning')
        return redirect(url_for('main.home'))
    nuevo_resultado = ResultadoTest(nota=0, tema_id=tema.id, autor=current_user)
    db.session.add(nuevo_resultado)
    db.session.flush()
    aciertos = 0
    for pregunta in preguntas_en_test:
        es_correcta = False
        if pregunta.tipo_pregunta == 'opcion_multiple':
            id_respuesta_marcada = request.form.get(f'pregunta-{pregunta.id}')
            if id_respuesta_marcada:
                respuesta_seleccionada = Respuesta.query.get(id_respuesta_marcada)
                if respuesta_seleccionada and respuesta_seleccionada.es_correcta:
                    es_correcta = True
                db.session.add(RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta_id=pregunta.id, respuesta_seleccionada_id=int(id_respuesta_marcada), resultado_test=nuevo_resultado))
        elif pregunta.tipo_pregunta == 'respuesta_texto':
            respuesta_texto_usuario = request.form.get(f'pregunta-{pregunta.id}')
            if respuesta_texto_usuario and pregunta.respuesta_correcta_texto and respuesta_texto_usuario.strip().lower() == pregunta.respuesta_correcta_texto.strip().lower():
                es_correcta = True
            if respuesta_texto_usuario is not None:
                db.session.add(RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta_id=pregunta.id, respuesta_texto_usuario=respuesta_texto_usuario, resultado_test=nuevo_resultado))
        if es_correcta:
            aciertos += 1
    total_preguntas = len(preguntas_en_test)
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
            if respuesta_texto_usuario and pregunta.respuesta_correcta_texto and respuesta_texto_usuario.strip().lower() == pregunta.respuesta_correcta_texto.strip().lower():
                es_correcta = True
        if es_correcta:
            aciertos += 1
            respuestas_a_limpiar = RespuestaUsuario.query.filter_by(autor=current_user, pregunta_id=pregunta_id, es_correcta=False).all()
            for r in respuestas_a_limpiar:
                db.session.delete(r)
    db.session.commit()
    flash(f'¡Repaso finalizado! Has acertado {aciertos} de {len(ids_preguntas_enviadas)}.', 'success')
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
    return jsonify({'es_correcta': respuesta.es_correcta, 'retroalimentacion': respuesta.pregunta.retroalimentacion})

@main_bp.route('/pregunta/<int:pregunta_id>/toggle_favorito', methods=['POST'])
@login_required
def toggle_favorito(pregunta_id):
    pregunta = Pregunta.query.get_or_404(pregunta_id)
    es_favorita_ahora = False
    if current_user.es_favorita(pregunta):
        current_user.desmarcar_favorita(pregunta)
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
            try: num_preguntas = int(request.form.get(f'num_preguntas_{tema_id}', 10))
            except (ValueError, TypeError): num_preguntas = 10
            if num_preguntas == 0: continue
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
        flash('No hay un simulacro personalizado para empezar.', 'warning')
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
    return render_template('hacer_test.html', title="Simulacro Personalizado", tema=tema_dummy, preguntas=preguntas_test, is_personalizado=True, form=form)

@main_bp.route('/simulacro/corregir', methods=['POST'])
@login_required
def corregir_simulacro_personalizado():
    ids_preguntas_en_test = session.get('id_preguntas_simulacro', [])
    if not ids_preguntas_en_test:
        flash('La sesión de tu simulacro ha expirado.', 'danger')
        return redirect(url_for('main.generador_simulacro'))
    preguntas_en_test = db.session.query(Pregunta).filter(Pregunta.id.in_(ids_preguntas_en_test)).all()
    aciertos, total_preguntas = 0, len(preguntas_en_test)
    tema_simulacro_personalizado = Tema.query.filter_by(nombre="Simulacros Personalizados").first()
    if not tema_simulacro_personalizado:
        bloque_general = Bloque.query.filter_by(nombre="General").first()
        if not bloque_general:
            convo_general = Convocatoria.query.filter_by(nombre="General").first()
            if not convo_general:
                convo_general = Convocatoria(nombre="General"); db.session.add(convo_general); db.session.flush()
            bloque_general = Bloque(nombre="General", convocatoria_id=convo_general.id); db.session.add(bloque_general); db.session.flush()
        tema_simulacro_personalizado = Tema(nombre="Simulacros Personalizados", bloque_id=bloque_general.id, es_simulacro=True); db.session.add(tema_simulacro_personalizado); db.session.commit()
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
                db.session.add(RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta_id=pregunta.id, respuesta_seleccionada_id=int(id_respuesta_marcada), resultado_test=nuevo_resultado))
        elif pregunta.tipo_pregunta == 'respuesta_texto':
            respuesta_texto_usuario = request.form.get(f'pregunta-{pregunta.id}')
            if respuesta_texto_usuario and pregunta.respuesta_correcta_texto and respuesta_texto_usuario.strip().lower() == pregunta.respuesta_correcta_texto.strip().lower():
                es_correcta = True
            if respuesta_texto_usuario is not None:
                db.session.add(RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta_id=pregunta.id, respuesta_texto_usuario=respuesta_texto_usuario, resultado_test=nuevo_resultado))
        if es_correcta: aciertos += 1
    nota_final = (aciertos / total_preguntas) * 10 if total_preguntas > 0 else 0
    nuevo_resultado.nota = nota_final
    session.pop('id_preguntas_simulacro', None)
    db.session.commit()
    flash(f'¡Simulacro finalizado! Tu nota es: {nota_final:.2f}/10', 'success')
    return redirect(url_for('main.resultado_test', resultado_id=nuevo_resultado.id))

@main_bp.route('/guardar_preferencias', methods=['POST'])
@login_required
def guardar_preferencias():
    recibir_resumen = 'resumen_semanal' in request.form
    current_user.recibir_resumen_semanal = recibir_resumen
    db.session.commit()
    flash('Tus preferencias han sido guardadas.', 'success')
    return redirect(url_for('main.cuenta', tab='personalizar'))

@main_bp.route('/cuenta/cambiar-objetivo', methods=['POST'])
@login_required
def cambiar_objetivo():
    form = ObjetivoForm()
    if form.validate_on_submit():
        current_user.objetivo_principal = form.objetivo_principal.data
        db.session.commit()
        flash('¡Tu objetivo principal ha sido actualizado!', 'success')
    else:
        flash('Hubo un error al cambiar tu objetivo.', 'danger')
    return redirect(url_for('main.cuenta', tab='personalizar'))

@main_bp.route('/sw.js')
def sw():
    response = send_from_directory('static', 'sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@main_bp.route('/offline')
def offline():
    return render_template('offline.html')

# --- RUTAS DE API PARA GRÁFICOS ---
@main_bp.route('/api/evolucion-notas')
@login_required
def api_evolucion_notas():
    fecha_inicio = datetime.utcnow() - timedelta(days=30)
    resultados_periodo = ResultadoTest.query.filter(ResultadoTest.autor == current_user, ResultadoTest.fecha >= fecha_inicio).order_by(ResultadoTest.fecha.asc()).all()
    resultados_agrupados = defaultdict(list)
    for resultado in resultados_periodo:
        resultados_agrupados[resultado.fecha.date()].append(resultado.nota)
    notas_medias_por_dia = {fecha: sum(notas) / len(notas) for fecha, notas in resultados_agrupados.items()}
    dias_ordenados = sorted(notas_medias_por_dia.keys())
    labels_grafico = [dia.strftime('%d/%m') for dia in dias_ordenados]
    datos_grafico = [round(notas_medias_por_dia[dia], 2) for dia in dias_ordenados]
    return jsonify({'labels': labels_grafico, 'data': datos_grafico})

@main_bp.route('/api/rendimiento-temas')
@login_required
def api_rendimiento_temas():
    convocatoria_objetivo = current_user.objetivo_principal
    if not convocatoria_objetivo:
        return jsonify({'error': 'No se ha establecido un objetivo principal.'}), 400
    temas_ids = db.session.query(Tema.id).join(Bloque).filter(Bloque.convocatoria_id == convocatoria_objetivo.id).all()
    tema_ids_list = [id[0] for id in temas_ids]
    stats_temas = db.session.query(
        Tema.nombre,
        (func.sum(case((RespuestaUsuario.es_correcta, 1), else_=0)) * 100.0 / func.count(RespuestaUsuario.id)).label('porcentaje')
    ).select_from(Tema).join(Pregunta, Tema.id == Pregunta.tema_id).join(RespuestaUsuario, Pregunta.id == RespuestaUsuario.pregunta_id).filter(
        RespuestaUsuario.usuario_id == current_user.id,
        Tema.id.in_(tema_ids_list)
    ).group_by(Tema.id).having(func.count(RespuestaUsuario.id) > 0).all()
    stats_temas_sorted = sorted(stats_temas, key=lambda x: x.porcentaje)
    labels = [stat.nombre for stat in stats_temas_sorted]
    data = [round(stat.porcentaje) for stat in stats_temas_sorted]
    return jsonify({'labels': labels, 'data': data})

@main_bp.route('/api/calendario-actividad')
@login_required
def api_calendario_actividad():
    meses_a_mostrar = request.args.get('meses', 3, type=int)
    if meses_a_mostrar not in [3, 6, 12]: meses_a_mostrar = 3
    fecha_fin = datetime.utcnow().date()
    fecha_inicio = fecha_fin - relativedelta(months=meses_a_mostrar)
    resultados_por_dia = db.session.query(func.date(ResultadoTest.fecha).label('dia'), func.count(ResultadoTest.id).label('cantidad')).filter(
        ResultadoTest.usuario_id == current_user.id,
        func.date(ResultadoTest.fecha).between(fecha_inicio, fecha_fin)
    ).group_by('dia').all()
    return jsonify([{'date': r.dia.strftime('%Y-%m-%d'), 'value': r.cantidad} for r in resultados_por_dia])

# --- RUTAS DE IA ---

# --- RUTA DE API PARA CONSULTA RAG (MODIFICADA) ---
@main_bp.route('/api/consulta-rag', methods=['POST'])
@login_required
def api_consulta_rag():
    # 1. Verificación de acceso y tokens
    if not current_user.tiene_acceso_ia:
        return jsonify({'error': 'Acceso denegado. Función premium.'}), 403
    
    if current_user.rag_tokens_restantes <= 0:
        return jsonify({
            'error': 'Has agotado tus tokens de IA. Contacta con el administrador para recargar.',
            'remaining_tokens': 0
        }), 403

    data = request.get_json()
    user_message = data.get('message')
    response_mode = data.get('mode', 'formal')
    
    # --- ¡NUEVO! OBTENER LAS FUENTES SELECCIONADAS DEL FRONTEND ---
    selected_sources = data.get('selected_sources')

    if not user_message:
        return jsonify({'error': 'No se recibió ningún mensaje.'}), 400
    
    # 2. Llama a la función de consulta RAG, pasando las fuentes seleccionadas
    try:
        # --- ¡MODIFICADO! Se pasa el nuevo argumento 'selected_sources' ---
        response_data = get_rag_response(
            query=user_message, 
            mode=response_mode, 
            selected_sources=selected_sources
        )
        
        if "Error" in response_data['result']:
            return jsonify({'response': response_data['result'], 'sources': [], 'remaining_tokens': current_user.rag_tokens_restantes}), 500
        
        # 3. Descontar token si la consulta fue exitosa
        current_user.rag_tokens_restantes -= RAG_COST_PER_QUERY
        db.session.commit()

        # 4. Devolver la respuesta
        return jsonify({
            'response': response_data['result'],
            'sources': response_data['sources'],
            'remaining_tokens': current_user.rag_tokens_restantes
        })
        
    except Exception as e:
        print(f"Error al procesar la consulta RAG en Flask: {e}")
        return jsonify({'response': 'Error interno del servidor al consultar el agente.', 'sources': [], 'remaining_tokens': current_user.rag_tokens_restantes}), 500

# --- RUTA DE PÁGINA DEL AGENTE IA (MODIFICADA) ---
@main_bp.route('/agente-ia')
@login_required
def agente_ia_page():
    if not current_user.tiene_acceso_ia:
        flash('No tienes acceso a esta función premium en este momento.', 'warning')
        return redirect(url_for('main.home'))

    # --- ¡NUEVA LÓGICA PARA CARGAR LOS DOCUMENTOS DESDE GOOGLE CLOUD STORAGE! ---
    available_sources = []
    bucket_name = "silvatest-prod-temarios" # El nombre de tu bucket

    try:
        # Inicializa el cliente de Cloud Storage
        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs() # Obtiene todos los archivos del bucket

        for blob in blobs:
            # Nos aseguramos de que sean archivos PDF y no carpetas
            if blob.name.lower().endswith('.pdf'):
                # La ruta completa que necesita el filtro es gs://bucket/archivo.pdf
                full_gcs_path = f"gs://{bucket_name}/{blob.name}"

                file_name = blob.name.split('/')[-1]
                cleaned_name = re.sub(r'\.(pdf|txt)$', '', file_name, flags=re.IGNORECASE)
                cleaned_name = cleaned_name.replace('_', ' ').replace('.', ' ').strip().title()

                available_sources.append({
                    'name': cleaned_name,  # Nombre limpio para mostrar en la web
                    'path': full_gcs_path   # Ruta GCS completa que usará el filtro
                })

        # Ordena alfabéticamente la lista para una mejor visualización
        available_sources.sort(key=lambda x: x['name'])

    except Exception as e:
        print(f"ERROR: No se pudo conectar a Google Cloud Storage para listar los archivos: {e}")
        flash("Error al cargar los documentos del temario. Contacta con el administrador.", "danger")

    return render_template('agente_ia.html',
                           title="Asistente de Estudio IA",
                           rag_tokens_restantes=current_user.rag_tokens_restantes,
                           available_sources=available_sources) # <-- ¡LA VARIABLE CLAVE AHORA VIENE DE LA NUBE!

@main_bp.route('/explicar-respuesta', methods=['POST'])
@login_required
def explicar_respuesta_ia():
    if not current_user.tiene_acceso_ia: abort(403)

    data = request.get_json()
    pregunta_id = data.get('preguntaId')
    pregunta = Pregunta.query.get_or_404(pregunta_id)

    # Obtenemos el texto de la respuesta correcta
    respuesta_correcta_texto = ""
    for opcion in pregunta.respuestas:
        if opcion.es_correcta:
            respuesta_correcta_texto = opcion.texto
            break

    # 1. Creamos una pregunta específica para el agente RAG
    query = f"""
    Explica de forma didáctica y concisa por qué la respuesta correcta a la pregunta '{pregunta.texto}' es '{respuesta_correcta_texto}'.
    Basa tu explicación únicamente en el temario oficial.
    """

    try:
        # 2. Llamamos a la misma función RAG que usa el chatbot
        response_data = get_rag_response(query=query, mode="didactico")

        # 3. Devolvemos directamente la explicación generada
        return jsonify({'explicacion': response_data['result']})

    except Exception as e:
        print(f"Error al llamar al agente RAG para explicar respuesta: {e}")
        return jsonify({'error': 'Hubo un problema al generar la explicación.'}), 500

@main_bp.route('/api/generar-plan-ia', methods=['POST'])
@login_required
def generar_plan_ia():
    if not current_user.tiene_acceso_ia: abort(403)
    informe = analizar_rendimiento_usuario(current_user)
    if not informe: return jsonify({'error': 'Necesitas más tests para generar un plan.'}), 400
    resumen_rendimiento = f"Temas débiles: {', '.join(informe['temas_debiles'])}. " + (f"Bloque más débil: {informe['bloque_debil']}." if informe['bloque_debil'] else "")
    prompt_parts = [
        "Actúa como un preparador de oposiciones de élite llamado Silva. Eres motivador, directo y estratégico.",
        f"Un opositor llamado {current_user.nombre} te pide un plan. Su rendimiento es: {resumen_rendimiento}",
        "Crea un plan de estudio concreto para los próximos 3 días en Markdown con 3 puntos clave.",
        "Empieza con una frase de ánimo y termina con un objetivo numérico (ej: 'Tu objetivo es subir la media en el bloque X por encima del 6.0')."
    ]
    try:
        model = GenerativeModel("gemini-1.0-pro")
        response = model.generate_content("\n".join(prompt_parts))
        return jsonify({'plan': response.text})
    except Exception as e:
        print(f"Error al llamar a la API de Vertex AI: {e}")
        return jsonify({'error': 'Hubo un problema con el Entrenador IA.'}), 500

@main_bp.route('/api/agente-ia', methods=['POST'])
@login_required
def api_agente_ia():
    if not current_user.tiene_acceso_ia:
        abort(403)
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No se recibió ningún mensaje.'}), 400
    contexto_oposicion = ""
    if current_user.objetivo_principal:
        convocatoria_nombre = current_user.objetivo_principal.nombre
        contexto_oposicion = f"El opositor se está preparando para la oposición de {convocatoria_nombre}. Adapta tus respuestas a ese temario si es posible."
    prompt_parts = [
        "Eres Silva, un asistente de IA experto en oposiciones de Agente Medioambiental en España, especialmente de Castilla y León y Asturias. Eres amable, preciso y didáctico.",
        contexto_oposicion,
        "Responde a la pregunta del usuario de forma clara y concisa, como si fueras un preparador experto.",
        f"\nPregunta del usuario: {user_message}"
    ]
    prompt = "\n".join(prompt_parts)
    try:
        model = GenerativeModel("gemini-1.0-pro")
        response = model.generate_content(prompt)
        return jsonify({'response': response.text})
    except Exception as e:
        print(f"Error al llamar a la API de Vertex AI para el agente: {e}")
        return jsonify({'response': 'Lo siento, estoy teniendo problemas para conectar con mi cerebro digital. Inténtalo de nuevo en un momento.'}), 500

@main_bp.route('/cuenta/guardar-dashboard', methods=['POST'])
@login_required
def guardar_preferencias_dashboard():
    form = DashboardPreferencesForm()
    if form.validate_on_submit():
        preferencias = {
            'mostrar_grafico_evolucion': form.mostrar_grafico_evolucion.data,
            'mostrar_rendimiento_bloque': form.mostrar_rendimiento_bloque.data,
            'mostrar_calendario_actividad': form.mostrar_calendario_actividad.data,
        }
        current_user.preferencias_dashboard = preferencias
        db.session.commit()
        flash('¡Preferencias del panel actualizadas!', 'success')
    else:
        flash('Error al guardar tus preferencias.', 'danger')
    return redirect(url_for('main.cuenta', tab='personalizar'))

@main_bp.route('/api/rendimiento-bloques')
@login_required
def api_rendimiento_bloques():
    convocatoria_objetivo = current_user.objetivo_principal
    if not convocatoria_objetivo:
        return jsonify({'labels': [], 'data': []})
    bloques_ids = [b.id for b in convocatoria_objetivo.bloques]
    stats_bloques = db.session.query(
        Bloque.nombre,
        (func.sum(case((RespuestaUsuario.es_correcta, 1), else_=0)) * 100.0 / func.count(RespuestaUsuario.id)).label('porcentaje')
    ).join(Tema, Bloque.id == Tema.bloque_id).join(Pregunta, Tema.id == Pregunta.tema_id).join(RespuestaUsuario, Pregunta.id == RespuestaUsuario.pregunta_id).filter(
        RespuestaUsuario.usuario_id == current_user.id,
        Bloque.id.in_(bloques_ids)
    ).group_by(Bloque.id).having(func.count(RespuestaUsuario.id) > 0).all()
    stats_bloques_sorted = sorted(stats_bloques, key=lambda x: x.porcentaje)
    labels = [stat.nombre for stat in stats_bloques_sorted]
    data = [round(stat.porcentaje) for stat in stats_bloques_sorted]
    return jsonify({'labels': labels, 'data': data})