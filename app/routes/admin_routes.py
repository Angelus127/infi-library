from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from ..db import conectar, dict_cursor

admin_routes = Blueprint('admin_routes', __name__)

TABLAS = {
    'libros': 'books',
    'animes': 'anime',
    'peliculas': 'movies',
    'dramas': 'dramas',
    'mangas': 'manga'
}

VISTAS = {
    'libros': 'viewBook',
    'animes': 'animeView',
    'peliculas': 'viewMovie',
    'dramas': 'dramaView',
    'mangas': 'mangaView'
}


# -------------------------
#  AGREGAR NUEVO REGISTRO
# -------------------------
@admin_routes.route('/agregar/<tipo>', methods=['GET', 'POST'])
def agregar(tipo):
    if tipo not in TABLAS:
        return "Tipo no válido", 404

    if request.method == 'POST':
        title = request.form.get('titulo')
        status = request.form.get('status')
        score = request.form.get('score')
        year = request.form.get('year')
        tipo_id = request.form.get('type') if tipo in ['mangas', 'peliculas'] else None
        country = request.form.get('country') if tipo == 'dramas' else None

        conn = conectar()
        if not conn:
            return "Error de conexión", 500

        cur = conn.cursor()
        try:
            if tipo in ['mangas', 'peliculas']:
                cur.execute(
                    f"INSERT INTO {TABLAS[tipo]} (title, id_status, score, year, id_type) VALUES (%s, %s, %s, %s, %s)",
                    (title, status, score, year, tipo_id)
                )
            elif tipo == 'dramas':
                cur.execute(
                    f"INSERT INTO {TABLAS[tipo]} (title, id_status, score, year, country) VALUES (%s, %s, %s, %s, %s)",
                    (title, status, score, year, country)
                )
            else:
                cur.execute(
                    f"INSERT INTO {TABLAS[tipo]} (title, id_status, score, year) VALUES (%s, %s, %s, %s)",
                    (title, status, score, year)
                )

            conn.commit()
        except Exception as e:
            print("Error al insertar:", e)
            conn.rollback()
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('multimedia_routes.ver_multimedia', tipo=tipo))

    return render_template('agregar.html', tipo=tipo)


# -------------------------
#  BORRAR REGISTRO
# -------------------------
@admin_routes.route('/<tipo>/borrar/<int:item_id>', methods=['POST', 'GET'])
def borrar(tipo, item_id):
    if tipo not in TABLAS:
        return f"No existe la categoría '{tipo}'", 404

    conn = conectar()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute(f"DELETE FROM {TABLAS[tipo]} WHERE id_{TABLAS[tipo]} = %s", (item_id,))
            conn.commit()
        except Exception as e:
            print("Error al borrar:", e)
        finally:
            cur.close()
            conn.close()

    return redirect(url_for('multimedia_routes.ver_multimedia', tipo=tipo))


# -------------------------
#  EDITAR REGISTRO
# -------------------------
@admin_routes.route('/<tipo>/editar/<int:item_id>', methods=['GET', 'POST'])
def editar(tipo, item_id):
    if tipo not in TABLAS:
        return "Tipo no válido", 404

    conn = conectar()
    if not conn:
        return "Error de conexión", 500

    cur = dict_cursor(conn)
    cur.execute(f"SELECT * FROM {VISTAS[tipo]} WHERE id = %s", (item_id,))
    item = cur.fetchone()

    if not item:
        cur.close()
        conn.close()
        return "Elemento no encontrado", 404

    if request.method == 'POST':
        title = request.form.get('titulo')
        year = request.form.get('year')
        tipo_id = request.form.get('type') if tipo in ['mangas', 'peliculas'] else None
        country = request.form.get('country') if tipo == 'dramas' else None

        try:
            if tipo in ['mangas', 'peliculas']:
                cur.execute(
                    f"UPDATE {TABLAS[tipo]} SET title = %s, year = %s, id_type = %s WHERE id_{TABLAS[tipo]} = %s",
                    (title, year, tipo_id, item_id)
                )
            elif tipo == 'dramas':
                cur.execute(
                    f"UPDATE {TABLAS[tipo]} SET title = %s, year = %s, country = %s WHERE id_{TABLAS[tipo]} = %s",
                    (title, year, country, item_id)
                )
            else:
                cur.execute(
                    f"UPDATE {TABLAS[tipo]} SET title = %s, year = %s WHERE id_{TABLAS[tipo]} = %s",
                    (title, year, item_id)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            print("Error al actualizar:", e)
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('multimedia_routes.ver_detalle', tipo=tipo, item_id=item_id))

    cur.close()
    conn.close()
    return render_template('editar.html', tipo=tipo, item=item)


# -------------------------
#  ACTUALIZAR ESTADO
# -------------------------
@admin_routes.route('/<tipo>/estado/<int:item_id>/<int:nuevo_estado>', methods=['POST'])
def actualizar_estado(tipo, item_id, nuevo_estado):
    if tipo not in TABLAS:
        return "Tipo no válido", 404

    conn = conectar()
    if not conn:
        return "Error al conectar", 500

    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {TABLAS[tipo]} SET id_status = %s WHERE id_{TABLAS[tipo]} = %s",
            (nuevo_estado, item_id)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error al actualizar estado:", e)
        return "Error al actualizar estado", 500

    return redirect(url_for('multimedia_routes.ver_detalle', tipo=tipo, item_id=item_id))


# -------------------------
#  ACTUALIZAR PUNTUACIÓN
# -------------------------
@admin_routes.route('/<tipo>/actualizar_puntuacion/<int:item_id>', methods=['POST'])
def actualizar_puntuacion(tipo, item_id):
    if tipo not in TABLAS:
        return jsonify({'success': False, 'error': 'Tipo no válido'}), 400

    data = request.get_json(silent=True)
    if not data or 'score' not in data:
        return jsonify({'success': False, 'error': 'Payload inválido'}), 400

    try:
        score = float(data['score'])
        if score >= 10.0:
            return jsonify({'success': False, 'error': 'Score no permitido'}), 400
        score = round(score, 1)
    except Exception:
        return jsonify({'success': False, 'error': 'Score inválido'}), 400

    conn = conectar()
    if not conn:
        return jsonify({'success': False, 'error': 'Error de conexión'}), 500

    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {TABLAS[tipo]} SET score = %s WHERE id_{TABLAS[tipo]} = %s",
            (score, item_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'score': score})
    except Exception as e:
        print("Error al actualizar puntuación:", e)
        conn.rollback()
        try:
            cur.close()
            conn.close()
        except:
            pass
        return jsonify({'success': False, 'error': 'DB error'}), 500
