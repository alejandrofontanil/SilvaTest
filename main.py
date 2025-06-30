import os
import random
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, flash, redirect, url_for, abort, jsonify
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, RadioField, SelectField, BooleanField, IntegerField, SelectMultipleField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField

# =================================================================
# 1. CONFIGURACIÓN INICIAL
# =================================================================
app = Flask(__name__, template_folder='mi_app/templates', static_folder='mi_app/static')
app.config['SECRET_KEY'] = 'clave_secreta_super_larga_y_aleatoria_para_mi_app_12345'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'mi_app', 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
migrate = Migrate(app, db)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."

# =================================================================
# 2. MODELOS DE LA BASE DE DATOS
# =================================================================
accesos_usuario_convocatoria = db.Table('accesos_usuario_convocatoria',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('convocatoria_id', db.Integer, db.ForeignKey('convocatoria.id'), primary_key=True)
)
favoritos = db.Table('favoritos',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('pregunta_id', db.Integer, db.ForeignKey('pregunta.id'), primary_key=True)
)
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    es_admin = db.Column(db.Boolean, nullable=False, default=False)
    resultados = db.relationship('ResultadoTest', backref='autor', lazy=True)
    respuestas_dadas = db.relationship('RespuestaUsuario', backref='autor', lazy=True, cascade="all, delete-orphan")
    preguntas_favoritas = db.relationship('Pregunta', secondary=favoritos, backref='favorited_by_users', lazy='dynamic')
    convocatorias_accesibles = db.relationship('Convocatoria', secondary=accesos_usuario_convocatoria, backref='usuarios_con_acceso', lazy='dynamic')
    def es_favorita(self, pregunta):
        return self.preguntas_favoritas.filter(favoritos.c.pregunta_id == pregunta.id).count() > 0
    def marcar_favorita(self, pregunta):
        if not self.es_favorita(pregunta):
            self.preguntas_favoritas.append(pregunta)
    def desmarcar_favorita(self, pregunta):
        if self.es_favorita(pregunta):
            self.preguntas_favoritas.remove(pregunta)
class Convocatoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, unique=True)
    bloques = db.relationship('Bloque', backref='convocatoria', lazy=True, cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Convocatoria {self.nombre}>'
class Bloque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    convocatoria_id = db.Column(db.Integer, db.ForeignKey('convocatoria.id'), nullable=False)
    temas = db.relationship('Tema', backref='bloque', lazy='dynamic', foreign_keys='Tema.bloque_id', cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Bloque {self.nombre}>'
class Tema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=True)
    bloque_id = db.Column(db.Integer, db.ForeignKey('bloque.id'), nullable=True)
    es_simulacro = db.Column(db.Boolean, nullable=False, default=False)
    tiempo_limite_minutos = db.Column(db.Integer, nullable=True)
    subtemas = db.relationship('Tema', backref=db.backref('parent', remote_side=[id]), cascade="all, delete-orphan")
    preguntas = db.relationship('Pregunta', backref='tema', lazy=True, cascade="all, delete-orphan")
    resultados = db.relationship('ResultadoTest', backref='tema', lazy=True)
    notas = db.relationship('Nota', backref='tema', lazy=True, cascade="all, delete-orphan")
    @property
    def total_preguntas(self):
        return len(self.preguntas)
    def __repr__(self):
        return f'<Tema {self.nombre}>'
class Nota(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    tema_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
class Pregunta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    imagen_url = db.Column(db.String(300), nullable=True)
    retroalimentacion = db.Column(db.Text, nullable=True)
    dificultad = db.Column(db.String(50), nullable=False, default='Media')
    necesita_revision = db.Column(db.Boolean, default=False, nullable=False)
    tema_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=False)
    respuestas = db.relationship('Respuesta', backref='pregunta', lazy=True, cascade="all, delete-orphan")
    respuestas_usuarios = db.relationship('RespuestaUsuario', backref='pregunta', lazy=True, cascade="all, delete-orphan")
class Respuesta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.String(500), nullable=False)
    es_correcta = db.Column(db.Boolean, default=False, nullable=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('pregunta.id'), nullable=False)
    veces_seleccionada = db.relationship('RespuestaUsuario', backref='respuesta_seleccionada', lazy=True)
class ResultadoTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nota = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tema_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    desglose_respuestas = db.relationship('RespuestaUsuario', backref='resultado_test', lazy=True, cascade="all, delete-orphan")
class RespuestaUsuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    es_correcta = db.Column(db.Boolean, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey('pregunta.id'), nullable=False)
    respuesta_seleccionada_id = db.Column(db.Integer, db.ForeignKey('respuesta.id'), nullable=False)
    resultado_test_id = db.Column(db.Integer, db.ForeignKey('resultado_test.id'), nullable=False)

# =================================================================
# 3. FORMULARIOS
# =================================================================
class ConvocatoriaForm(FlaskForm):
    nombre = StringField('Nombre de la Convocatoria', validators=[DataRequired(), Length(min=5, max=200)])
    submit = SubmitField('Guardar Convocatoria')
class BloqueForm(FlaskForm):
    nombre = StringField('Nombre del Bloque', validators=[DataRequired(), Length(min=3, max=200)])
    submit = SubmitField('Guardar Bloque')
def bloques_query():
    return Bloque.query
def temas_query():
    return Tema.query
class TemaForm(FlaskForm):
    bloque = QuerySelectField('Bloque al que pertenece', query_factory=bloques_query, get_label='nombre', allow_blank=False, validators=[DataRequired()])
    nombre = StringField('Nombre del Tema/Subtema', validators=[DataRequired(), Length(min=3, max=200)])
    parent = QuerySelectField('Tema Padre (Opcional, para subtemas)', query_factory=temas_query, get_label='nombre', allow_blank=True, blank_text='-- Ninguno (Es un Tema Principal) --', validators=[Optional()])
    es_simulacro = BooleanField('¿Es un Simulacro de Examen?')
    tiempo_limite_minutos = IntegerField('Tiempo Límite (en minutos)', validators=[Optional()])
    submit = SubmitField('Guardar Tema')
class PermisosForm(FlaskForm):
    convocatorias = SelectMultipleField('Convocatorias con Acceso', coerce=int, widget=ListWidget(prefix_label=False), option_widget=CheckboxInput())
    submit = SubmitField('Guardar Permisos')
class RegistrationForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    submit = SubmitField('Crear Cuenta')
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')
class PreguntaForm(FlaskForm):
    texto = TextAreaField('Texto de la Pregunta', validators=[DataRequired()])
    dificultad = SelectField('Dificultad', choices=[('Fácil', 'Fácil'), ('Media', 'Media'), ('Difícil', 'Difícil')], validators=[DataRequired()])
    respuesta1_texto = StringField('Respuesta A', validators=[DataRequired(), Length(max=500)])
    respuesta2_texto = StringField('Respuesta B', validators=[DataRequired(), Length(max=500)])
    respuesta3_texto = StringField('Respuesta C', validators=[DataRequired(), Length(max=500)])
    respuesta4_texto = StringField('Respuesta D', validators=[DataRequired(), Length(max=500)])
    respuesta_correcta = RadioField('Marca la Respuesta Correcta', choices=[('1', 'A'), ('2', 'B'), ('3', 'C'), ('4', 'D')], validators=[DataRequired()])
    retroalimentacion = TextAreaField('Pista para el usuario (opcional)')
    submit = SubmitField('Guardar Pregunta')
class NotaForm(FlaskForm):
    texto = TextAreaField('Texto de la Nota', validators=[DataRequired()])
    submit_nota = SubmitField('Añadir Nota')

# =================================================================
# 4. RUTAS DE LA APLICACIÓN
# =================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/')
@app.route('/home')
def home():
    if current_user.is_authenticated and not current_user.es_admin:
        convocatorias = current_user.convocatorias_accesibles.all()
    else:
        convocatorias = Convocatoria.query.order_by(Convocatoria.nombre).all()
    return render_template('home.html', convocatorias=convocatorias)

@app.route('/convocatoria/<int:convocatoria_id>')
@login_required
def convocatoria_detalle(convocatoria_id):
    convocatoria = Convocatoria.query.get_or_404(convocatoria_id)
    if not current_user.es_admin and convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    return render_template('convocatoria_detalle.html', convocatoria=convocatoria)

@app.route('/bloque/<int:bloque_id>')
@login_required
def bloque_detalle(bloque_id):
    bloque = Bloque.query.get_or_404(bloque_id)
    if not current_user.es_admin and bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    temas = bloque.temas.filter_by(parent_id=None).order_by(Tema.nombre).all()
    return render_template('bloque_detalle.html', bloque=bloque, temas=temas)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        nuevo_usuario = Usuario(nombre=form.nombre.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('¡Tu cuenta ha sido creada! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html', title='Registro', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('¡Has iniciado sesión con éxito!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Inicio de sesión fallido. Por favor, comprueba tu email y contraseña.', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado la sesión con éxito.', 'success')
    return redirect(url_for('home'))

@app.route('/cuenta')
@login_required
def cuenta():
    periodo = request.args.get('periodo', 'mes')

    # --- Consulta Corregida ---
    query_base = db.session.query(
        func.strftime('%d/%m/%Y', ResultadoTest.fecha).label('fecha_dia'), # Le pedimos a la BD la fecha ya formateada
        func.avg(ResultadoTest.nota).label('nota_media')
    ).filter(ResultadoTest.usuario_id == current_user.id)

    if periodo == 'mes':
        hoy = date.today()
        primer_dia_mes = hoy.replace(day=1)
        query_base = query_base.filter(ResultadoTest.fecha >= primer_dia_mes)

    resultados_agrupados = query_base.group_by(func.date(ResultadoTest.fecha)).order_by(func.date(ResultadoTest.fecha)).all()

    # Ahora la creación de las listas es más directa
    labels_grafico = [resultado.fecha_dia for resultado in resultados_agrupados]
    datos_grafico = [round(resultado.nota_media, 2) for resultado in resultados_agrupados]

    resultados_tabla = ResultadoTest.query.filter_by(autor=current_user).order_by(ResultadoTest.fecha.desc()).all()

    total_preguntas_hechas = RespuestaUsuario.query.filter_by(autor=current_user).count()
    if resultados_tabla:
        nota_media_global = sum([r.nota for r in resultados_tabla]) / len(resultados_tabla)
    else:
        nota_media_global = 0

    return render_template(
        'cuenta.html', 
        title='Mi Cuenta', 
        resultados=resultados_tabla,
        labels_grafico=labels_grafico,
        datos_grafico=datos_grafico,
        periodo_activo=periodo,
        total_preguntas_hechas=total_preguntas_hechas,
        nota_media_global=nota_media_global
    )

@app.route('/cuenta/favoritas')
@login_required
def preguntas_favoritas():
    preguntas = current_user.preguntas_favoritas.order_by(Pregunta.id.desc()).all()
    return render_template('favoritas.html', title="Mis Preguntas Favoritas", preguntas=preguntas)

@app.route('/tema/<int:tema_id>', methods=['GET', 'POST'])
@admin_required
def detalle_tema(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    form_pregunta = PreguntaForm(prefix='pregunta')
    form_nota = NotaForm(prefix='nota')
    if form_pregunta.submit.data and form_pregunta.validate_on_submit():
        nueva_pregunta = Pregunta(texto=form_pregunta.texto.data, dificultad=form_pregunta.dificultad.data, retroalimentacion=form_pregunta.retroalimentacion.data, tema_id=tema.id)
        db.session.add(nueva_pregunta)
        respuestas_texto = [form_pregunta.respuesta1_texto.data, form_pregunta.respuesta2_texto.data, form_pregunta.respuesta3_texto.data, form_pregunta.respuesta4_texto.data]
        for i, texto_respuesta in enumerate(respuestas_texto, 1):
            es_correcta = (str(i) == form_pregunta.respuesta_correcta.data)
            respuesta = Respuesta(texto=texto_respuesta, es_correcta=es_correcta, pregunta=nueva_pregunta)
            db.session.add(respuesta)
        db.session.commit()
        flash('¡Pregunta añadida con éxito!', 'success')
        return redirect(url_for('detalle_tema', tema_id=tema.id))
    if form_nota.submit_nota.data and form_nota.validate_on_submit():
        nueva_nota = Nota(texto=form_nota.texto.data, tema_id=tema.id)
        db.session.add(nueva_nota)
        db.session.commit()
        flash('¡Nota añadida con éxito!', 'success')
        return redirect(url_for('detalle_tema', tema_id=tema.id))
    return render_template('detalle_tema.html', title=tema.nombre, tema=tema, form_pregunta=form_pregunta, form_nota=form_nota)

@app.route('/tema/<int:tema_id>/test')
@login_required
def hacer_test(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    if not current_user.es_admin and tema.bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    preguntas_test = list(tema.preguntas)
    random.shuffle(preguntas_test)
    for pregunta in preguntas_test:
        respuestas_barajadas = list(pregunta.respuestas)
        random.shuffle(respuestas_barajadas)
        pregunta.respuestas_barajadas = respuestas_barajadas
    return render_template('hacer_test.html', title=f"Test de {tema.nombre}", tema=tema, preguntas=preguntas_test)

@app.route('/tema/<int:tema_id>/corregir', methods=['POST'])
@login_required
def corregir_test(tema_id):
    tema = Tema.query.get_or_404(tema_id)
    if not current_user.es_admin and tema.bloque.convocatoria not in current_user.convocatorias_accesibles.all():
        abort(403)
    aciertos = 0
    total_preguntas = 0
    nuevo_resultado = ResultadoTest(nota=0, tema_id=tema.id, autor=current_user)
    db.session.add(nuevo_resultado)
    db.session.flush()
    preguntas_en_test = Pregunta.query.join(Tema.preguntas).filter(Tema.id == tema_id).all()
    for pregunta in preguntas_en_test:
        total_preguntas += 1
        id_respuesta_marcada = request.form.get(f'pregunta-{pregunta.id}')
        if id_respuesta_marcada:
            respuesta_marcada = Respuesta.query.get(id_respuesta_marcada)
            es_correcta = respuesta_marcada and respuesta_marcada.es_correcta
            if es_correcta:
                aciertos += 1
            respuesta_usuario = RespuestaUsuario(es_correcta=es_correcta, autor=current_user, pregunta=pregunta, respuesta_seleccionada=respuesta_marcada, resultado_test=nuevo_resultado)
            db.session.add(respuesta_usuario)
    nota_final = (aciertos / total_preguntas) * 10 if total_preguntas > 0 else 0
    nuevo_resultado.nota = nota_final
    db.session.commit()
    flash(f'¡Test finalizado! Tu nota es: {nota_final:.2f}/10', 'success')
    return redirect(url_for('resultado_test', resultado_id=nuevo_resultado.id))

@app.route('/resultado/<int:resultado_id>')
@login_required
def resultado_test(resultado_id):
    resultado = ResultadoTest.query.get_or_404(resultado_id)
    if resultado.autor != current_user:
        abort(403)
    return render_template('resultado_test.html', title="Resultado del Test", resultado=resultado)

@app.route('/resultado/<int:resultado_id>/repaso')
@login_required
def repaso_test(resultado_id):
    resultado = ResultadoTest.query.get_or_404(resultado_id)
    if resultado.autor != current_user:
        abort(403)
    return render_template('repaso_test.html', resultado=resultado)

@app.route('/repaso_global')
@login_required
def repaso_global():
    respuestas_falladas = RespuestaUsuario.query.filter_by(autor=current_user, es_correcta=False).all()
    ids_preguntas_falladas = list({r.pregunta_id for r in respuestas_falladas})
    preguntas_a_repasar = Pregunta.query.filter(Pregunta.id.in_(ids_preguntas_falladas)).all()
    random.shuffle(preguntas_a_repasar)
    with db.session.no_autoflush:
        for pregunta in preguntas_a_repasar:
            respuestas_barajadas = list(pregunta.respuestas)
            random.shuffle(respuestas_barajadas)
            pregunta.respuestas_barajadas = respuestas_barajadas
    return render_template('repaso_global_test.html', preguntas=preguntas_a_repasar)

@app.route('/repaso_global/corregir', methods=['POST'])
@login_required
def corregir_repaso_global():
    aciertos = 0
    ids_preguntas_enviadas = [key.split('-')[1] for key in request.form if key.startswith('pregunta-')]
    total_preguntas = len(ids_preguntas_enviadas)
    for pregunta_id in ids_preguntas_enviadas:
        id_respuesta_marcada = request.form.get(f'pregunta-{pregunta_id}')
        if id_respuesta_marcada:
            respuesta_marcada = Respuesta.query.get(id_respuesta_marcada)
            if respuesta_marcada and respuesta_marcada.es_correcta:
                aciertos += 1
                respuestas_a_limpiar = RespuestaUsuario.query.filter_by(autor=current_user, pregunta_id=pregunta_id, es_correcta=False).all()
                for r in respuestas_a_limpiar:
                    db.session.delete(r)
    db.session.commit()
    nota_string = f"Has acertado {aciertos} de {total_preguntas}."
    flash(f'¡Repaso finalizado! {nota_string}', 'success')
    return redirect(url_for('cuenta'))

@app.route('/comprobar_respuesta', methods=['POST'])
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
        return jsonify({'es_correcta': True})
    else:
        return jsonify({'es_correcta': False, 'retroalimentacion': respuesta.pregunta.retroalimentacion})

@app.route('/pregunta/<int:pregunta_id>/toggle_favorito', methods=['POST'])
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

# --- RUTAS DE ADMINISTRACIÓN ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    preguntas_reportadas = Pregunta.query.filter_by(necesita_revision=True).count()
    return render_template('admin/admin_dashboard.html', title="Panel de Administrador", preguntas_reportadas=preguntas_reportadas)

@app.route('/admin/preguntas_a_revisar')
@admin_required
def preguntas_a_revisar():
    preguntas = Pregunta.query.filter_by(necesita_revision=True).order_by(Pregunta.id.desc()).all()
    return render_template('admin/preguntas_a_revisar.html', preguntas=preguntas)

@app.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    usuarios = Usuario.query.filter_by(es_admin=False).order_by(Usuario.nombre).all()
    return render_template('admin/admin_usuarios.html', usuarios=usuarios)

@app.route('/admin/usuario/<int:usuario_id>/permisos', methods=['GET', 'POST'])
@admin_required
def editar_permisos_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if usuario.es_admin:
        abort(403)
    form = PermisosForm()
    form.convocatorias.choices = [(c.id, c.nombre) for c in Convocatoria.query.order_by('nombre').all()]
    if request.method == 'POST':
        usuario.convocatorias_accesibles = []
        for id_convocatoria in form.convocatorias.data:
            convocatoria_a_dar_acceso = Convocatoria.query.get(id_convocatoria)
            usuario.convocatorias_accesibles.append(convocatoria_a_dar_acceso)
        db.session.commit()
        flash(f'Permisos actualizados para {usuario.nombre}.', 'success')
        return redirect(url_for('admin_usuarios'))
    form.convocatorias.data = [c.id for c in usuario.convocatorias_accesibles]
    return render_template('admin/editar_permisos.html', form=form, usuario=usuario)
# ... (El resto de las rutas de admin no cambian)
# =================================================================
# 5. ARRANQUE DEL SERVIDOR
# =================================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=8080, debug=True)