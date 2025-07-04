from flask_login import UserMixin
from datetime import datetime
from . import db, bcrypt # Importamos bcrypt desde __init__.py

# =================================================================
# 2. MODELOS DE LA BASE DE DATOS
# =================================================================

# --- TABLAS DE ASOCIACIÓN ---
accesos_usuario_convocatoria = db.Table('accesos_usuario_convocatoria',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('convocatoria_id', db.Integer, db.ForeignKey('convocatoria.id'), primary_key=True)
)

favoritos = db.Table('favoritos',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('pregunta_id', db.Integer, db.ForeignKey('pregunta.id'), primary_key=True)
)

# --- CLASES DE LOS MODELOS ---
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

    # --- MÉTODOS DE CONTRASEÑA CORREGIDOS PARA USAR BCRYPT ---
    def set_password(self, password):
        """Crea un hash seguro de la contraseña usando bcrypt."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Comprueba el hash de la contraseña con bcrypt."""
        return bcrypt.check_password_hash(self.password_hash, password)
    # ----------------------------------------------------

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
        count = len(self.preguntas)
        for subtema in self.subtemas:
            count += subtema.total_preguntas
        return count
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
    tipo_pregunta = db.Column(db.String(50), nullable=False, default='opcion_multiple')
    respuesta_correcta_texto = db.Column(db.String(500), nullable=True)
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
    respuesta_seleccionada_id = db.Column(db.Integer, db.ForeignKey('respuesta.id'), nullable=True)
    respuesta_texto_usuario = db.Column(db.String(500), nullable=True)
    resultado_test_id = db.Column(db.Integer, db.ForeignKey('resultado_test.id'), nullable=False)