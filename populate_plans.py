from mi_app import create_app, db
# --- LÍNEA CORREGIDA: Se añade RegistroEntrenamiento a la importación ---
from mi_app.models import PlanFisico, SemanaPlan, RegistroEntrenamiento

# --- DATOS DE LOS PLANES DIRECTAMENTE EN EL CÓDIGO ---

PLAN_BASE_DATA = [
    # Semana, Día 1, Día 2, Carga KM, Zona Ritmo, Progreso %
    (1, "3 km a 6:40 - 6:50 min/km", "6 x 400m a 6:20 min/km (Descanso 1:30 min)", 5.4, "Z3 - Umbral Aeróbico", 6.25),
    (2, "3.5 km a 6:40 min/km", "4 x 600m a 6:15 min/km (Descanso 1:30 min)", 5.9, "Z3 - Umbral Aeróbico", 12.50),
    (3, "4 km a 6:35 min/km", "3 x 800m a 6:10 min/km (Descanso 1:30 min)", 6.4, "Z3 - Umbral Aeróbico", 18.75),
    (4, "4.5 km a 6:30 min/km", "2 x 1000m a 6:10 min/km (Descanso 1:30 min)", 6.5, "Z3 - Umbral Aeróbico", 25.00),
    (5, "5 km a 6:25 min/km", "3 x 1000m a 6:05 min/km (Descanso 2 min)", 8.0, "Z3-Z4 - Umbral Aeróbico / Subumbral", 31.25),
    (6, "5.5 km a 6:20 min/km", "2 x 1500m a 6:00 min/km (Descanso 2 min)", 8.5, "Z3-Z4 - Umbral Aeróbico / Subumbral", 37.50),
    (7, "6 km a 6:15 min/km", "1 x 2000m a 6:00 min/km", 8.0, "Z3-Z4 - Umbral Aeróbico / Subumbral", 43.75),
    (8, "6 km a 6:10 min/km", "3 km progresivos (6:15 a 6:00 min/km)", 9.0, "Z3-Z4 - Umbral Aeróbico / Subumbral", 50.00),
    (9, "6 km a 6:05 min/km", "4 x 600m a 5:50 min/km (Descanso 1:30 min)", 8.4, "Z4 - Subumbral", 56.25),
    (10, "6 km a 6:00 min/km", "3 x 800m a 5:45 min/km (Descanso 2 min)", 8.4, "Z4 - Subumbral", 62.50),
    (11, "6 km a 5:55 min/km", "2 x 1000m a 5:40 min/km (Descanso 2 min)", 8.0, "Z4 - Subumbral", 68.75),
    (12, "6 km en menos de 35 min", "3 km rápidos a 5:50 min/km", 9.0, "Z4-Z5 - Subumbral / Umbral Anaeróbico", 75.00),
    (13, "6 km a 6:00 min/km", "4 x 400m a 5:30 min/km (Descanso 1:30 min)", 8.6, "Z4-Z5 - Subumbral / Umbral Anaeróbico", 81.25),
    (14, "6 km a 5:55 min/km", "3 x 600m a 5:30 min/km (Descanso 2 min)", 8.8, "Z4-Z5 - Subumbral / Umbral Anaeróbico", 87.50),
    (15, "6 km a 5:50 min/km", "2 x 800m a 5:30 min/km (Descanso 2 min)", 8.6, "Z4-Z5 - Subumbral / Umbral Anaeróbico", 93.75),
    (16, "6 km en menos de 35 min", "3 km rápidos a 5:30 min/km", 9.0, "Z5 - Umbral Anaeróbico", 100.00),
]

PLAN_EXIGENTE_DATA = [
    # Semana, Día 1, Día 2, Carga KM, Zona Ritmo, Progreso %
    (1, "3 km a 6:00 min/km", "6 x 400m a 5:55 min/km (Descanso 1:30 min)", 5.4, "Z3-Z4 - Umbral Aeróbico / Subumbral", 6),
    (2, "3.5 km a 5:55 min/km", "4 x 600m a 5:45 min/km (Descanso 1:30 min)", 5.9, "Z4 - Subumbral", 13),
    (3, "4 km a 5:50 min/km", "2 x 1000m a 5:40 min/km (Descanso 1:30 min)", 6.4, "Z4 - Subumbral", 19),
    (4, "4.5 km a 5:45 min/km", "3 x 1000m a 5:35 min/km (Descanso 2 min)", 8.5, "Z4 - Subumbral", 25),
    (5, "5 km a 5:40 min/km", "2 x 1500m a 5:30 min/km (Descanso 2 min)", 8.0, "Z4-Z5 - Subumbral / Umbral Anaeróbico", 31),
    (6, "5.5 km a 5:35 min/km", "1 x 2000m a 5:30 min/km", 8.5, "Z4-Z5 - Subumbral / Umbral Anaeróbico", 38),
    (7, "6 km a 5:30 min/km", "3 km progresivos (5:40 a 5:20 min/km)", 9.0, "Z5 - Umbral Anaeróbico", 44),
    (8, "6 km a 5:25 min/km", "4 x 600m a 5:15 min/km (Descanso 1:30 min)", 8.4, "Z5 - Umbral Anaeróbico", 50),
    (9, "6 km a 5:20 min/km", "3 x 800m a 5:15 min/km (Descanso 2 min)", 8.4, "Z5 - Umbral Anaeróbico", 56),
    (10, "6 km a 5:15 min/km", "2 x 1000m a 5:10 min/km (Descanso 2 min)", 8.0, "Z5 - Umbral Anaeróbico", 63),
    (11, "6 km a 5:10 min/km", "3 km rápidos a 5:10 min/km", 9.0, "Z5 - Umbral Anaeróbico", 69),
    (12, "6 km en menos de 33 min", "4 x 400m a 5:00 min/km (Descanso 1:30 min)", 8.6, "Z5 - Umbral Anaeróbico", 75),
    (13, "6 km a 5:05 min/km", "3 x 600m a 5:00 min/km (Descanso 2 min)", 8.8, "Z5 - Umbral Anaeróbico", 81),
    (14, "6 km en menos de 33 min", "2 x 800m a 5:00 min/km (Descanso 2 min)", 8.6, "Z5 - Umbral Anaeróbico", 88),
    (15, "6 km a 5:00 min/km", "3 km rápidos a 5:00 min/km", 9.0, "Z5 - Umbral Anaeróbico", 94),
    (16, "6 km en menos de 32 min", "", 9.0, "Z5 - Umbral Anaeróbico", 100),
]

def poblar_plan(plan_nombre, plan_data):
    print(f"--- Procesando '{plan_nombre}' ---")
    
    nuevo_plan = PlanFisico(nombre=plan_nombre)
    db.session.add(nuevo_plan)
    
    for data_semana in plan_data:
        nueva_semana = SemanaPlan(
            plan=nuevo_plan,
            numero_semana=data_semana[0],
            dia1_desc=data_semana[1],
            dia2_desc=data_semana[2],
            carga_semanal_km=data_semana[3],
            zona_ritmo=data_semana[4],
            progreso_pct=data_semana[5]
        )
        db.session.add(nueva_semana)
        print(f"  -> Añadida semana {data_semana[0]} al plan '{plan_nombre}'")

    db.session.commit()
    print(f"✅ Plan '{plan_nombre}' guardado en la base de datos.")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("--- Limpiando datos de planes físicos existentes... ---")
        # --- CORREGIDO: Ahora el script sabe qué es RegistroEntrenamiento ---
        db.session.query(RegistroEntrenamiento).delete()
        db.session.query(SemanaPlan).delete()
        db.session.query(PlanFisico).delete()
        db.session.commit()
        print("--- Base de datos de planes físicos limpiada. ---")
        
        try:
            poblar_plan("Plan Base", PLAN_BASE_DATA)
            poblar_plan("Plan Exigente", PLAN_EXIGENTE_DATA)
            print("\n--- Proceso de población de datos finalizado con éxito ---")
        except Exception as e:
            print(f"❌ ERROR GENERAL durante la población: {e}")
            db.session.rollback()
