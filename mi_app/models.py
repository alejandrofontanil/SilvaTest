from flask_login import UserMixin
from datetime import datetime
from . import db, bcrypt
from werkzeug.utils import cached_property
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

class AccesoConvocatoria(db.Model):
    __tablename__ = 'accesos_usuario_convocatoria'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    convocatoria_id = db.Column(db.Integer, db.ForeignKey('convocatoria.id'), primary_key=True)
    fecha_expiracion = db.Column(db.DateTime, nullable=True)
    usuario = db.relationship("Usuario", back_populates="accesos")
    convocatoria = db.relationship("Convocatoria", back_populates="usuarios_con_acceso")

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
    recibir_resumen_semanal = db.Column(db.Boolean, nullable=False, default=False)
    
    objetivo_principal_id = db.Column(db.Integer, db.ForeignKey('convocatoria.id'), nullable=True)
    ha_visto_tour = db.Column(db.Boolean, nullable=False, server_default='false')
    tiene_acceso_ia = db.Column(db.Boolean, nullable=False, server_default='false')
    preferencias_dashboard = db.Column(db.JSON, nullable=True)
    
    # --- NUEVA COLUMNA PARA FECHA OBJETIVO ---
    objetivo_fecha = db.Column(db.Date, nullable=True)
    # --- FIN DE NUEVA COLUMNA ---
    
    objetivo_principal = db.relationship('Convocatoria', foreign_keys=[objetivo_principal_id])
    resultados = db.relationship('ResultadoTest', backref='autor', lazy=True, cascade="all, delete-orphan")
    respuestas_dadas = db.relationship('RespuestaUsuario', backref='autor', lazy=True, cascade="all, delete-orphan")
    preguntas_favoritas = db.relationship('Pregunta', secondary=favoritos, backref='favorited_by_users', lazy='dynamic')
    accesos = db.relationship('AccesoConvocatoria', back_populates='usuario', cascade="all, delete-orphan")

    @property 
    def convocatorias_accesibles(self):
        if self.es_admin:
            return Convocatoria.query.order_by(Convocatoria.nombre)
        return Convocatoria.query.join(AccesoConvocatoria).filter(
            AccesoConvocatoria.usuario_id == self.id,
            (AccesoConvocatoria.fecha_expiracion == None) | (AccesoConvocatoria.fecha_expiracion > datetime.utcnow())
        ).order_by(Convocatoria.nombre)

    def es_favorita(self, pregunta):
        return self.preguntas_favoritas.filter(favoritos.c.pregunta_id == pregunta.id).count() > 0

    def marcar_favorita(self, pregunta):
        if not self.es_favorita(pregunta):
            self.preguntas_favoritas.append(pregunta)

    def desmarcar_favorita(self, pregunta):
        if self.es_favorita(pregunta):
            self.preguntas_favoritas.remove(pregunta)

    @property
    def password(self):
        raise AttributeError('La contraseña no es un atributo legible.')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return Usuario.query.get(user_id)

class Convocatoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, unique=True)
    es_publica = db.Column(db.Boolean, nullable=False, default=True)
    es_premium = db.Column(db.Boolean, nullable=False, server_default='false')
    
    bloques = db.relationship('Bloque', backref='convocatoria', lazy=True, cascade="all, delete-orphan", order_by='Bloque.posicion')
    usuarios_con_acceso = db.relationship('AccesoConvocatoria', back_populates='convocatoria', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Convocatoria {self.nombre}>'

class Bloque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    posicion = db.Column(db.Integer, default=0, nullable=False)
    esta_oculto = db.Column(db.Boolean, nullable=False, default=False) 
    convocatoria_id = db.Column(db.Integer, db.ForeignKey('convocatoria.id'), nullable=False)
    contexto_ia = db.Column(db.String(250), nullable=True)
    
    temas = db.relationship('Tema', backref='bloque', lazy='dynamic', foreign_keys='Tema.bloque_id', cascade="all, delete-orphan", order_by='Tema.posicion')

    def __repr__(self):
        return f'<Bloque {self.nombre}>'

class Tema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    posicion = db.Column(db.Integer, default=0, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('tema.id'), nullable=True)
    bloque_id = db.Column(db.Integer, db.ForeignKey('bloque.id'), nullable=True)
    es_simulacro = db.Column(db.Boolean, nullable=False, default=False)
    tiempo_limite_minutos = db.Column(db.Integer, nullable=True)
    pdf_url = db.Column(db.String(300), nullable=True)
    ruta_documento_contexto = db.Column(db.String(300), nullable=True)

    subtemas = db.relationship('Tema', backref=db.backref('parent', remote_side=[id]), cascade="all, delete-orphan", order_by='Tema.posicion')
    preguntas = db.relationship('Pregunta', backref='tema', lazy=True, cascade="all, delete-orphan", order_by='Pregunta.posicion')
    resultados = db.relationship('ResultadoTest', backref='tema', lazy=True, cascade="all, delete-orphan")
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
    posicion = db.Column(db.Integer, default=0, nullable=False)
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
    texto = db.Column(db.Text, nullable=False)
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