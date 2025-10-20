import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify
import psycopg2, math, psycopg2.extras

load_dotenv()

app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT')
}


def conectar():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<tipo>')
def ver_multimedia(tipo):
    tablas = {
        'libros': 'viewBook',
        'animes': 'animeView',
        'peliculas': 'viewMovie',
        'dramas': 'dramaView',
        'mangas': 'mangaView'
    }

    if tipo not in tablas:
        return f"No existe la categoría '{tipo}'", 404

    pagina = int(request.args.get('page', 1))
    busqueda = request.args.get('q', '')
    estado = request.args.get('estado', '')
    orden = request.args.get('orden', '')
    limite = 20
    offset = (pagina - 1) * limite

    conn = conectar()
    data = []
    total = 0
    conteos = {}

    if conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        tabla = tablas[tipo]

        cur.execute(f"SELECT status, COUNT(*) AS count FROM {tabla} GROUP BY status")
        conteos_raw = cur.fetchall()
        conteos = {fila['status']: fila['count'] for fila in conteos_raw}
        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        conteos['total'] = cur.fetchone()['count']

        condiciones = []
        parametros = []

        if busqueda:
            condiciones.append("title ILIKE %s")
            parametros.append(f"%{busqueda}%")

        if estado:
            condiciones.append("status = %s")
            parametros.append(estado)

        where_clause = "WHERE " + " AND ".join(condiciones) if condiciones else ""

        if orden == 'titulo':
            orden_sql = "ORDER BY title ASC"
        elif orden == 'titulo_desc':
            orden_sql = "ORDER BY title DESC"
        elif orden == 'puntuacion':
            orden_sql = "ORDER BY score DESC"
        else:
            orden_sql = "ORDER BY id DESC"

        query = f"SELECT * FROM {tabla} {where_clause} {orden_sql} LIMIT %s OFFSET %s"
        parametros.extend([limite, offset])
        cur.execute(query, tuple(parametros))
        data = cur.fetchall()

        cur.execute(f"SELECT COUNT(*) FROM {tabla} {where_clause}", tuple(parametros[:-2]))
        total = cur.fetchone()['count']

        cur.close()
        conn.close()

    total_paginas = math.ceil(total / limite)

    return render_template(
        'multimedia.html',
        data=data,
        tipo=tipo,
        pagina=pagina,
        total_paginas=total_paginas,
        busqueda=busqueda,
        estado=estado,
        orden=orden,
        conteos=conteos
    )

@app.route('/<tipo>/<int:item_id>')
def ver_detalle(tipo, item_id):
    tablas = {
        'libros': 'viewBook',
        'animes': 'animeView',
        'peliculas': 'viewMovie',
        'dramas': 'dramaView',
        'mangas': 'mangaView'
    }

    if tipo not in tablas:
        return f"No existe la categoría '{tipo}'", 404

    conn = conectar()
    item = None
    if conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT * FROM {tablas[tipo]} WHERE id = %s", (item_id,))
        item = cur.fetchone()
        cur.close()
        conn.close()

    return render_template('detalles.html', item=item, tipo=tipo)

@app.route('/agregar/<tipo>', methods=['GET', 'POST'])
def agregar(tipo):
    tablas = {
        'libros': 'books',
        'animes': 'anime',
        'peliculas': 'movies',
        'dramas': 'dramas',
        'mangas': 'manga'
    }
    
    if tipo not in tablas:
        return "Tipo no válido", 404
    
    if request.method == 'POST':
        title = request.form.get('titulo')
        status = request.form.get('status')
        score = request.form.get('score')
        year = request.form.get('year')
        tipo_id = request.form.get('type') if tipo in ['mangas', 'peliculas'] else None
        country = request.form.get('country') if tipo == 'dramas' else None
        
        conn = conectar()
        cur = conn.cursor()
        
        if tipo in ['mangas', 'peliculas']:
            cur.execute(
                f"INSERT INTO {tablas[tipo]} (title, id_status, score, year, id_type) VALUES (%s, %s, %s, %s, %s)",
                (title, status, score, year, tipo_id)
            )
        elif tipo == 'dramas':
            cur.execute(
                f"INSERT INTO {tablas[tipo]} (title, id_status, score, year, country) VALUES (%s, %s, %s, %s, %s)",
                (title, status, score, year, country)
            )
        else:
            cur.execute(
                f"INSERT INTO {tablas[tipo]} (title, id_status, score, year) VALUES (%s, %s, %s, %s)",
                (title, status, score, year)
            )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('ver_multimedia', tipo=tipo))
        
    return render_template('agregar.html', tipo=tipo)
    
@app.route('/<tipo>/borrar/<int:item_id>', methods=['POST', 'GET'])
def borrar(tipo, item_id):
    tablas = {
        'libros': 'books',
        'animes': 'anime',
        'peliculas': 'movies',
        'dramas': 'dramas',
        'mangas': 'manga'
    }

    if tipo not in tablas:
        return f"No existe la categoría '{tipo}'", 404

    conn = conectar()
    if conn:
        cur = conn.cursor()
        try:
            cur.execute(f"DELETE FROM {tablas[tipo]} WHERE id_{tablas[tipo]} = %s", (item_id,))
            conn.commit()
        except Exception as e:
            print("Error al borrar:", e)
        finally:
            cur.close()
            conn.close()

    return redirect(url_for('ver_multimedia', tipo=tipo))

@app.route('/<tipo>/editar/<int:item_id>', methods=['GET', 'POST'])
def editar(tipo, item_id):
    tablas = {
        'libros': 'books',
        'animes': 'anime',
        'peliculas': 'movies',
        'dramas': 'dramas',
        'mangas': 'manga'
    }

    vistas = {
        'libros': 'viewBook',
        'animes': 'animeView',
        'peliculas': 'viewMovie',
        'dramas': 'dramaView',
        'mangas': 'mangaView'
    }

    if tipo not in tablas:
        return "Tipo no válido", 404

    conn = conectar()
    if not conn:
        return "Error de conexión", 500

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(f"SELECT * FROM {vistas[tipo]} WHERE id = %s", (item_id,))
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
                    f"UPDATE {tablas[tipo]} SET title = %s, year = %s, id_type = %s WHERE id_{tablas[tipo]} = %s",
                    (title, year, tipo_id, item_id)
                )
            elif tipo == 'dramas':
                cur.execute(
                    f"UPDATE {tablas[tipo]} SET title = %s, year = %s, country = %s WHERE id_{tablas[tipo]} = %s",
                    (title, year, country, item_id)
                )
            else:
                cur.execute(
                    f"UPDATE {tablas[tipo]} SET title = %s, year = %s WHERE id_{tablas[tipo]} = %s",
                    (title, year, item_id)
                )

            conn.commit()
        except Exception as e:
            conn.rollback()
            print("Error al actualizar:", e)
        finally:
            cur.close()
            conn.close()

        return redirect(url_for('ver_detalle', tipo=tipo, item_id=item_id))

    cur.close()
    conn.close()

    return render_template('editar.html', tipo=tipo, item=item)

@app.route('/<tipo>/estado/<int:item_id>/<int:nuevo_estado>', methods=['POST'])
def actualizar_estado(tipo, item_id, nuevo_estado):
    tablas = {
        'libros': 'books',
        'animes': 'anime',
        'peliculas': 'movies',
        'dramas': 'dramas',
        'mangas': 'manga'
    }

    if tipo not in tablas:
        return "Tipo no válido", 404

    conn = conectar()
    if not conn:
        return "Error al conectar", 500

    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {tablas[tipo]} SET id_status = %s WHERE id_{tablas[tipo]} = %s",
            (nuevo_estado, item_id)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error al actualizar estado:", e)
        return "Error al actualizar estado", 500

    return redirect(url_for('ver_detalle', tipo=tipo, item_id=item_id))

@app.route('/<tipo>/actualizar_puntuacion/<int:item_id>', methods=['POST'])
def actualizar_puntuacion(tipo, item_id):
    tablas = {
        'libros': 'books',
        'animes': 'anime',
        'peliculas': 'movies',
        'dramas': 'dramas',
        'mangas': 'manga'
    }

    if tipo not in tablas:
        return jsonify({'success': False, 'error': 'Tipo no válido'}), 400

    data = request.get_json(silent=True)
    if not data or 'score' not in data:
        return jsonify({'success': False, 'error': 'Payload inválido'}), 400

    try:
        score = float(data['score'])
        if score >= 10.0:
            return jsonify({'success': False, 'error': 'Score no permitido'}), 400
        score = round(score, 1)
    except Exception as e:
        return jsonify({'success': False, 'error': 'Score inválido'}), 400

    conn = conectar()
    if not conn:
        return jsonify({'success': False, 'error': 'Error de conexión'}), 500

    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {tablas[tipo]} SET score = %s WHERE id_{tablas[tipo]} = %s",
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

if __name__ == '__main__':
    app.run(debug=True)
