iadas)
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

# --- NUEVAS RUTAS PARA EL GENERADOR DE SIMULACROS ---

@main_bp.route('/generador-simulacro', methods=['GET', 'POST'])
@login_required
def generador_simulacro():
    if request.method == 'POST':
        preguntas_para_el_test_ids = []
        temas_seleccionados_ids = request.form.getlist('tema_seleccionado', type=int)

        # ✅ AÑADIDO: Capturar y guardar el tiempo límite en la sesión
        try:
            tiempo_limite = int(request.form.get('tiempo_limite', 30))
        except (ValueError, TypeError):
            tiempo_limite = 30
        session['tiempo_limite_simulacro'] = tiempo_limite


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
    return render_template('generador_simulacro.html', title="Generador de Simulacros", convocatorias=convocatorias_accesibles)

@main_bp.route('/simulacro/empezar')
@login_required
def simulacro_personalizado_test():
    form = FlaskForm() # ✅ CORREGIDO: Se crea el formulario
    ids_preguntas = session.get('id_preguntas_simulacro', [])
    if not ids_preguntas:
        flash('No hay un simulacro personalizado para empezar. Por favor, genera uno nuevo.', 'warning')
        return redirect(url_for('main.generador_simulacro'))

    preguntas_test = db.session.query(Pregunta).filter(Pregunta.id.in_(ids_preguntas)).order_by(sql_func.random()).all()

    for pregunta in preguntas_test:
        if pregunta.tipo_pregunta == 'opcion_multiple':
            lista_respuestas = list(pregunta.respuestas)
            random.shuffle(lista_respuestas)
            pregunta.respuestas_barajadas = lista_respuestas

    # ✅ CORREGIDO: Se lee el tiempo de la sesión y se pasa a la plantilla
    tiempo_limite = session.get('tiempo_limite_simulacro', 30) # 30 min por defecto
    tema_dummy = {'nombre': 'Simulacro Personalizado', 'es_simulacro': True, 'tiempo_limite_minutos': tiempo_limite}

    return render_template('hacer_test.html', 
                           title="Simulacro Personalizado", 
                           tema=tema_dummy, 
                           preguntas=preguntas_test, 
                           is_personalizado=True, 
                           form=form) # ✅ CORREGIDO: Se pasa el formulario

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
    session.pop('tiempo_limite_simulacro', None) # Limpiar también el tiempo

    db.session.commit()
    flash(f'¡Simulacro finalizado! Tu nota es: {nota_final:.2f}/10', 'success')
    return redirect(url_for('main.resultado_test', resultado_id=nuevo_resultado.id))