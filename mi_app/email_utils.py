from datetime import datetime, timedelta
from .models import ResultadoTest

def get_stats_semanales(user):
    """
    Calcula las estadísticas de tests de un usuario en los últimos 7 días.
    Devuelve un diccionario con las estadísticas o None si no hay actividad.
    """
    hoy = datetime.utcnow()
    hace_7_dias = hoy - timedelta(days=7)
    
    # Busca todos los resultados de tests del usuario en la última semana
    resultados = ResultadoTest.query.filter(
        ResultadoTest.usuario_id == user.id,
        ResultadoTest.fecha >= hace_7_dias
    ).all()
    
    # Si no hay resultados, no hay nada que reportar
    if not resultados:
        return None

    # Calcula las estadísticas
    stats = {
        'tests_completados': len(resultados),
        'nota_media': round(sum(r.nota for r in resultados) / len(resultados), 2)
    }
    
    return stats