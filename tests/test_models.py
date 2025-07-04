# Contenido para tests/test_models.py

import sys
import os

# Añadimos la ruta principal al path para que Python pueda encontrar 'mi_app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mi_app.models import Usuario

def test_password_hashing():
    """
    GIVEN un nuevo objeto Usuario
    WHEN se le asigna una contraseña con el método set_password
    THEN el hash se almacena y el método check_password funciona correctamente.
    """
    # Creamos un usuario de prueba
    u = Usuario(nombre="alejandro", email="alejandro@test.com")

    # Le asignamos una contraseña
    u.set_password('mi_password_123')

    # ASEGURAMOS (assert) que la contraseña NO es el hash directamente
    assert u.password_hash != 'mi_password_123'

    # ASEGURAMOS que check_password devuelve True para la contraseña correcta
    assert u.check_password('mi_password_123') == True

    # ASEGURAMOS que check_password devuelve False para una contraseña incorrecta
    assert u.check_password('un_password_falso') == False