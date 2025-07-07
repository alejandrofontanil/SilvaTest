from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from functools import wraps
import json
import gspread
from google.oauth2.service_account import Credentials
import os
import cloudinary
import cloudinary.uploader
from sqlalchemy.orm import selectinload
from flask_wtf import FlaskForm

from mi_app import db
from mi_app.models import (
    Pregunta, Respuesta, Tema, Convocatoria, Bloque, Usuario, Nota, 
    favoritos, RespuestaUsuario, ResultadoTest, AccesoConvocatoria
)
from mi_app.forms import (
    GoogleSheetImportForm, ConvocatoriaForm, BloqueForm, TemaForm, 
    PreguntaForm, NotaForm, PermisosForm
)

admin_bp = Blueprint('admin', __name__,
                     template_folder='../templates/admin',
                     url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE ADMINISTRACIÓN ---

    @admin_bp.route('/')
    @admin_required
    def admin_dashboard():
        preguntas_reportadas = Pregunta.query.filter_by(necesita_revision=True).count()
        return render_template('admin_dashboard.html', title="Panel de Administrador", preguntas_reportadas=preguntas_reportadas)

    @admin_bp.route('/preguntas_a_revisar')
    @admin_required
    def preguntas_a_revisar():
        preguntas = Pregunta.query.filter_by(necesita_revision=True).order_by(Pregunta.posicion).all()
        return render_template('preguntas_a_revisar.html', preguntas=preguntas)

    @admin_bp.route('/usuarios')
    @admin_required
    def admin_usuarios():
        usuarios = Usuario.query.options(
            selectinload(Usuario.accesos).selectinload(AccesoConvocatoria.convocatoria)
        ).filter(Usuario.es_admin == False).order_by(Usuario.nombre).all()
        return render_template('admin_usuarios.html', usuarios=usuarios, title="Gestionar Usuarios")

    @admin_bp.route('/usuario/<int:usuario_id>/permisos', methods=['GET', 'POST'])
    @admin_required
    def editar_permisos_usuario(usuario_id):
        usuario = Usuario.query.get_or_404(usuario_id)
        if usuario.es_admin:
            abort(403)
        form = PermisosForm()
        form.convocatorias.choices = [(c.id, c.nombre) for c in Convocatoria.query.order_by('nombre').all()]
        if form.validate_on_submit():
            AccesoConvocatoria.query.filter_by(usuario_id=usuario.id).delete()
            for id_convocatoria in form.convocatorias.data:
                nuevo_acceso = AccesoConvocatoria(
                    usuario_id=usuario.id,
                    convocatoria_id=id_convocatoria,
                    fecha_expiracion=form.fecha_expiracion.data
                )
                db.session.add(nuevo_acceso)
            db.session.commit()
            flash(f'Permisos actualizados para {usuario.nombre}.', 'success')
            return redirect(url_for('admin.admin_usuarios'))
        elif request.method == 'GET':
            accesos_actuales = usuario.accesos
            form.convocatorias.data = [acceso.convocatoria_id for acceso in accesos_actuales]
            if accesos_actuales and accesos_actuales[0].fecha_expiracion:
                form.fecha_expiracion.data = accesos_actuales[0].fecha_expiracion
        return render_template('editar_permisos.html', form=form, usuario=usuario)

    @admin_bp.route('/convocatorias')
    @admin_required
    def admin_convocatorias():
        convocatorias = Convocatoria.query.order_by(Convocatoria.nombre).all()
        return render_template('admin_convocatorias.html', title="Gestionar Convocatorias", convocatorias=convocatorias)

@admin_bp.route('/crear_convocatoria', methods=['GET', 'POST'])
@admin_required
def crear_convocatoria():
    form = ConvocatoriaForm()
    if form.validate_on_submit():
        nueva_convocatoria = Convocatoria(nombre=form.nombre.data)
        db.session.add(nueva_convocatoria)
        db.session.commit()
        flash('¡Convocatoria creada con éxito!', 'success')
        return redirect(url_for('admin.admin_convocatorias'))
    return render_template('crear_convocatoria.html', title="Crear Convocatoria", form=form)

@admin_bp.route('/convocatoria/<int:convocatoria_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_convocatoria(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    form = ConvocatoriaForm(obj=convocatoria)
    if form.validate_on_submit():
        convocatoria.nombre = form.nombre.data
        db.session.commit()
        flash('¡Convocatoria actualizada con éxito!', 'success')
        return redirect(url_for('admin.admin_convocatorias'))
    return render_template('editar_convocatoria.html', title="Editar Convocatoria", form=form, convocatoria=convocatoria)

@admin_bp.route('/convocatoria/<int:convocatoria_id>/eliminar', methods=['POST'])
@admin_required
def eliminar_convocatoria(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    try:
        bloque_ids = [bloque.id for bloque in convocatoria.bloques]
        tema_ids = [tema.id for tema in Tema.query.filter(Tema.bloque_id.in_(bloque_ids)).all()] if bloque_ids else []
        pregunta_ids = [pregunta.id for pregunta in Pregunta.query.filter(Pregunta.tema_id.in_(tema_ids)).all()] if tema_ids else []
        resultado_ids = [resultado.id for resultado in ResultadoTest.query.filter(ResultadoTest.tema_id.in_(tema_ids)).all()] if tema_ids else []
        if resultado_ids:
            db.session.execute(RespuestaUsuario.__table__.delete().where(RespuestaUsuario.resultado_test_id.in_(resultado_ids)))
        if pregunta_ids:
            db.session.execute(favoritos.delete().where(favoritos.c.pregunta_id.in_(pregunta_ids)))
            db.session.execute(Respuesta.__table__.delete().where(Respuesta.pregunta_id.in_(pregunta_ids)))
        if tema_ids:
            db.session.execute(ResultadoTest.__table__.delete().where(ResultadoTest.tema_id.in_(tema_ids)))
            db.session.execute(Nota.__table__.delete().where(Nota.tema_id.in_(tema_ids)))
        if pregunta_ids:
            db.session.execute(Pregunta.__table__.delete().where(Pregunta.id.in_(pregunta_ids)))
        if tema_ids:
            db.session.execute(Tema.__table__.delete().where(Tema.id.in_(tema_ids)))
        if bloque_ids:
             db.session.execute(Bloque.__table__.delete().where(Bloque.id.in_(bloque_ids)))
        db.session.delete(convocatoria)
        db.session.commit()
        flash('La convocatoria y todo su contenido han sido eliminados con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al borrar la convocatoria: {e}', 'danger')
    return redirect(url_for('admin.admin_convocatorias'))

@admin_bp.route('/convocatoria/<int:convocatoria_id>/bloques')
@admin_required
def admin_bloques(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    return render_template('admin_bloques.html', title=f"Bloques de {convocatoria.nombre}", convocatoria=convocatoria)

@admin_bp.route('/convocatoria/<int:convocatoria_id>/crear_bloque', methods=['GET', 'POST'])
@admin_required
def crear_bloque(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    form = BloqueForm()
    if form.validate_on_submit():
        max_pos = db.session.query(db.func.max(Bloque.posicion)).filter_by(convocatoria_id=convocatoria_id).scalar() or -1
        nuevo_bloque = Bloque(nombre=form.nombre.data, convocatoria_id=convocatoria.id, posicion=max_pos + 1)
        db.session.add(nuevo_bloque)
        db.session.commit()
        flash('¡Bloque creado con éxito!', 'success')
        return redirect(url_for('admin.admin_bloques', convocatoria_id=convocatoria.id))
    return render_template('crear_bloque.html', title="Crear Bloque", form=form, convocatoria=convocatoria)

@admin_bp.route('/bloque/<int:bloque_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_bloque(bloque_id):
    bloque = Bloque.query.get_or_404(bloque_id)
    form = BloqueForm(obj=bloque)
    if form.validate_on_submit():
        bloque.nombre = form.nombre.data
        db.session.commit()
        flash('¡Bloque actualizado con éxito!', 'success')
        return redirect(url_for('admin.admin_bloques', convocatoria_id=bloque.convocatoria_id))
    return render_template('editar_bloque.html', title="Editar Bloque", form=form, bloque=bloque)

@admin_bp.route('/bloque/<int:bloque_id>/eliminar', methods=['POST'])
@admin_required
def eliminar_bloque(bloque_id):
    bloque = Bloque.query.get_or_404(bloque_id)
    convocatoria_id = bloque.convocatoria_id
    try:
        tema_ids = [tema.id for tema in bloque.temas]
        pregunta_ids = [pregunta.id for pregunta in Pregunta.query.filter(Pregunta.tema_id.in_(tema_ids)).all()] if tema_ids else []
        resultado_ids = [resultado.id for resultado in ResultadoTest.query.filter(ResultadoTest.tema_id.in_(tema_ids)).all()] if tema_ids else []
        if resultado_ids:
            db.session.execute(RespuestaUsuario.__table__.delete().where(RespuestaUsuario.resultado_test_id.in_(resultado_ids)))
        if pregunta_ids:
            db.session.execute(favoritos.delete().where(favoritos.c.pregunta_id.in_(pregunta_ids)))
            db.session.execute(Respuesta.__table__.delete().where(Respuesta.pregunta_id.in_(pregunta_ids)))
        if tema_ids:
            db.session.execute(ResultadoTest.__table__.delete().where(ResultadoTest.tema_id.in_(tema_ids)))
            db.session.execute(Nota.__table__.delete().where(Nota.tema_id.in_(tema_ids)))
        if pregunta_ids:
            db.session.execute(Pregunta.__table__.delete().where(Pregunta.id.in_(pregunta_ids)))
        if tema_ids:
            db.session.execute(Tema.__table__.delete().where(Tema.id.in_(tema_ids)))
        db.session.delete(bloque)
        db.session.commit()
        flash('El bloque y todo su contenido han sido eliminados con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al borrar el bloque: {e}', 'danger')
    return redirect(url_for('admin.admin_bloques', convocatoria_id=convocatoria_id))

    @admin_bp.route('/temas')
    @admin_required
    def admin_temas():
        form = FlaskForm() 
        convocatorias = Convocatoria.query.order_by(Convocatoria.nombre).all()
        return render_template('admin_temas_general.html', title="Vista General de Temas", convocatorias=convocatorias, form=form)

@admin_bp.route('/crear_tema', methods=['GET', 'POST'])
@admin_required
def crear_tema():
    form = TemaForm()
    form.bloque.query = Bloque.query.order_by(Bloque.posicion)
    form.parent.query = Tema.query.order_by(Tema.posicion)
    if form.validate_on_submit():
        max_pos = db.session.query(db.func.max(Tema.posicion)).filter_by(bloque_id=form.bloque.data.id).scalar() or -1
        nuevo_tema = Tema(nombre=form.nombre.data, parent=form.parent.data, bloque=form.bloque.data, es_simulacro=form.es_simulacro.data, tiempo_limite_minutos=form.tiempo_limite_minutos.data, posicion=max_pos + 1)
        db.session.add(nuevo_tema)
        db.session.commit()
        flash('¡El tema ha sido creado con éxito!', 'success')
        return redirect(url_for('admin.admin_temas'))
    return render_template('crear_tema.html', title='Crear Tema', form=form)

@admin_bp.route('/tema/<int:tema_id>/detalle', methods=['GET', 'POST'])
@admin_required
def detalle_tema(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    form_pregunta = PreguntaForm(prefix='pregunta')
    form_nota = NotaForm(prefix='nota')
    if 'submit_pregunta' in request.form and form_pregunta.validate_on_submit():
        imagen_url_segura = None
        if form_pregunta.imagen.data:
            upload_result = cloudinary.uploader.upload(form_pregunta.imagen.data)
            imagen_url_segura = upload_result.get('secure_url')
        max_pos = db.session.query(db.func.max(Pregunta.posicion)).filter_by(tema_id=tema.id).scalar() or -1
        nueva_pregunta = Pregunta(
            texto=form_pregunta.texto.data, dificultad=form_pregunta.dificultad.data, retroalimentacion=form_pregunta.retroalimentacion.data, tema_id=tema.id, posicion=max_pos + 1,
            imagen_url=imagen_url_segura, tipo_pregunta=form_pregunta.tipo_pregunta.data, respuesta_correcta_texto=form_pregunta.respuesta_correcta_texto.data
        )
        db.session.add(nueva_pregunta)
        if form_pregunta.tipo_pregunta.data == 'opcion_multiple':
            respuestas_texto = [form_pregunta.respuesta1_texto.data, form_pregunta.respuesta2_texto.data, form_pregunta.respuesta3_texto.data, form_pregunta.respuesta4_texto.data]
            for i, texto_respuesta in enumerate(respuestas_texto, 1):
                if texto_respuesta:
                    es_correcta = (str(i) == form_pregunta.respuesta_correcta.data)
                    respuesta = Respuesta(texto=texto_respuesta, es_correcta=es_correcta, pregunta=nueva_pregunta)
                    db.session.add(respuesta)
        db.session.commit()
        flash('¡Pregunta añadida con éxito!', 'success')
        return redirect(url_for('admin.detalle_tema', tema_id=tema.id))
    if 'submit_nota' in request.form and form_nota.validate_on_submit():
        nueva_nota = Nota(texto=form_nota.texto.data, tema_id=tema.id)
        db.session.add(nueva_nota)
        db.session.commit()
        flash('¡Nota añadida con éxito!', 'success')
        return redirect(url_for('admin.detalle_tema', tema_id=tema.id))
    return render_template('detalle_tema.html', title=tema.nombre, tema=tema, form_pregunta=form_pregunta, form_nota=form_nota)

    @admin_bp.route('/tema/<int:tema_id>/editar', methods=['GET', 'POST'])
    @admin_required
    def editar_tema(tema_id):
        tema_a_editar = Tema.query.get_or_404(tema_id)
        form = TemaForm(obj=tema_a_editar) # Esta línea faltaba o era incorrecta
        form.bloque.query = Bloque.query.order_by(Bloque.nombre)
        form.parent.query = Tema.query.filter(Tema.id != tema_id).order_by(Tema.nombre)
        if form.validate_on_submit():
            if form.parent.data and form.parent.data == tema_a_editar:
                flash('Un tema no puede ser su propio padre.', 'danger')
                return redirect(url_for('admin.editar_tema', tema_id=tema_id))
            tema_a_editar.nombre = form.nombre.data
            tema_a_editar.parent = form.parent.data
            tema_a_editar.bloque = form.bloque.data
            tema_a_editar.es_simulacro = form.es_simulacro.data
            tema_a_editar.tiempo_limite_minutos = form.tiempo_limite_minutos.data
            db.session.commit()
            flash('¡Tema actualizado con éxito!', 'success')
            return redirect(url_for('admin.admin_temas'))
        return render_template('editar_tema.html', title="Editar Tema", form=form, tema=tema_a_editar)

@admin_bp.route('/tema/<int:tema_id>/eliminar', methods=['POST'])
@admin_required
def eliminar_tema(tema_id):
    # ... (código de borrado robusto) ...
    return redirect(url_for('admin.admin_temas'))

@admin_bp.route('/pregunta/<int:pregunta_id>/editar', methods=['GET', 'POST'])
@admin_required
def editar_pregunta(pregunta_id):
    # ... (código) ...
    return render_template('editar_pregunta.html', title="Editar Pregunta", form=form, pregunta=pregunta)

@admin_bp.route('/pregunta/<int:pregunta_id>/eliminar', methods=['POST'])
@admin_required
def eliminar_pregunta(pregunta_id):
    # ... (código de borrado robusto) ...
    return redirect(url_for('admin.detalle_tema', tema_id=tema_id))

@admin_bp.route('/nota/<int:nota_id>/eliminar', methods=['POST'])
@admin_required
def eliminar_nota(nota_id):
    # ... (código) ...
    return redirect(url_for('admin.detalle_tema', tema_id=nota.tema_id))

@admin_bp.route('/subir_sheets', methods=['GET', 'POST'])
@admin_required
def subir_sheets():
    # ... (código de importación) ...
    return render_template('subir_sheets.html', title="Importar desde Google Sheets", form=GoogleSheetImportForm())

@admin_bp.route('/tema/eliminar_preguntas_masivo', methods=['POST'])
@admin_required
def eliminar_preguntas_masivo():
    # ... (código de borrado masivo) ...
    pass

# --- NUEVAS RUTAS PARA GUARDAR EL ORDEN ---
@admin_bp.route('/reordenar-temas', methods=['POST'])
@admin_required
def reordenar_temas():
    nuevos_ids_ordenados = request.json.get('nuevos_ids_ordenados')
    if not nuevos_ids_ordenados:
        return jsonify({'error': 'No se recibieron datos de ordenación'}), 400
    try:
        for indice, tema_id in enumerate(nuevos_ids_ordenados):
            tema = Tema.query.get(int(tema_id))
            if tema:
                tema.posicion = indice
        db.session.commit()
        return jsonify({'success': True, 'message': '¡Orden de los temas actualizado!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/reordenar-preguntas', methods=['POST'])
@admin_required
def reordenar_preguntas():
    nuevos_ids_ordenados = request.json.get('nuevos_ids_ordenados')
    if not nuevos_ids_ordenados:
        return jsonify({'error': 'No se recibieron datos de ordenación'}), 400
    try:
        for indice, pregunta_id in enumerate(nuevos_ids_ordenados):
            pregunta = Pregunta.query.get(int(pregunta_id))
            if pregunta:
                pregunta.posicion = indice
        db.session.commit()
        return jsonify({'success': True, 'message': '¡Orden de las preguntas actualizado!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500