from flask_login import UserMixin
from datetime import datetime, date # <-- AÑADIDO: 'date' para el nuevo modelo
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
    objetivo_fecha = db.Column(db.Date, nullable=True)
    
    rag_tokens_restantes = db.Column(db.Integer, default=50000) 
    
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # --- INICIO: NUEVOS CAMPOS PARA PLAN FÍSICO ---
    plan_fisico_actual_id = db.Column(db.Integer, db.ForeignKey('plan_fisico.id'), nullable=True)
    plan_fisico_actual = db.relationship('PlanFisico', foreign_keys=[plan_fisico_actual_id])
    registros_entrenamiento = db.relationship('RegistroEntrenamiento', backref='usuario', lazy='dynamic', cascade="all, delete-orphan")
    # --- FIN: NUEVOS CAMPOS ---
    
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

# ... (Tus modelos Convocatoria, Bloque, Tema, Nota, Pregunta, Respuesta, ResultadoTest y RespuestaUsuario se mantienen igual) ...
class Convocatoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, unique=True)
    es_publica = db.Column(db.Boolean, nullable=False, default=True)
    es_premium = db.Column(db.Boolean, nullable=False, server_default='false')
    bloques = db.relationship('Bloque', backref='convocatoria', lazy=True, cascade="all, delete-orphan", order_by='Bloque.posicion')
    usuarios_con_acceso = db.relationship('AccesoConvocatoria', back_populates='convocatoria', cascade="all, delete-orphan")

class Bloque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    posicion = db.Column(db.Integer, default=0, nullable=False)
    esta_oculto = db.Column(db.Boolean, nullable=False, default=False) 
    convocatoria_id = db.Column(db.Integer, db.ForeignKey('convocatoria.id'), nullable=False)
    contexto_ia = db.Column(db.String(250), nullable=True)
    temas = db.relationship('Tema', backref='bloque', lazy='dynamic', foreign_keys='Tema.bloque_id', cascade="all, delete-orphan", order_by='Tema.posicion')

class Tema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    # ... resto de campos ...
    subtemas = db.relationship('Tema', backref=db.backref('parent', remote_side=[id]), cascade="all, delete-orphan", order_by='Tema.posicion')
    preguntas = db.relationship('Pregunta', backref='tema', lazy=True, cascade="all, delete-orphan", order_by='Pregunta.posicion')
    # ... resto de relaciones ...

class Nota(db.Model):
    # ... tu modelo Nota sin cambios ...
    pass

class Pregunta(db.Model):
    # ... tu modelo Pregunta sin cambios ...
    pass

class Respuesta(db.Model):
    # ... tu modelo Respuesta sin cambios ...
    pass

class ResultadoTest(db.Model):
    # ... tu modelo ResultadoTest sin cambios ...
    pass

class RespuestaUsuario(db.Model):
    # ... tu modelo RespuestaUsuario sin cambios ...
    pass


# --- INICIO: NUEVOS MODELOS PARA PREPARACIÓN FÍSICA ---

class PlanFisico(db.Model):
    __tablename__ = 'plan_fisico'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False) # ej: "Plan Base", "Plan Exigente"
    
    semanas = db.relationship('SemanaPlan', backref='plan', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<PlanFisico {self.nombre}>'

class SemanaPlan(db.Model):
    __tablename__ = 'semana_plan'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan_fisico.id'), nullable=False)
    numero_semana = db.Column(db.Integer, nullable=False)
    
    # Campos de tu Excel
    progreso_pct = db.Column(db.Float)
    dia1_desc = db.Column(db.String(200))
    dia2_desc = db.Column(db.String(200))
    sensacion = db.Column(db.String(200))
    carga_semanal_km = db.Column(db.Float)
    zona_ritmo = db.Column(db.String(100))

    registros = db.relationship('RegistroEntrenamiento', backref='semana', lazy=True)

    def __repr__(self):
        return f'<SemanaPlan {self.numero_semana} del Plan {self.plan.nombre}>'

class RegistroEntrenamiento(db.Model):
    __tablename__ = 'registro_entrenamiento'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    semana_id = db.Column(db.Integer, db.ForeignKey('semana_plan.id'), nullable=False)
    
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    dia_entreno = db.Column(db.Integer, nullable=False) # 1 para Día 1, 2 para Día 2
    km_realizados = db.Column(db.Float)
    sensacion_usuario = db.Column(db.String(200), nullable=True)
    notas_usuario = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Registro del Usuario {self.usuario_id} para la Semana {self.semana_id}>'

# --- FIN: NUEVOS MODELOS ---