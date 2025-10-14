import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import psycopg2, math

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
    limite = 20
    offset = (pagina - 1) * limite

    conn = conectar()
    data = []
    total = 0

    if conn:
        cur = conn.cursor()

        if busqueda:
            query = f"SELECT * FROM {tablas[tipo]} WHERE title ILIKE %s ORDER BY id LIMIT %s OFFSET %s"
            cur.execute(query, (f"%{busqueda}%", limite, offset))
            data = cur.fetchall()

            cur.execute(f"SELECT COUNT(*) FROM {tablas[tipo]} WHERE title ILIKE %s", (f"%{busqueda}%",))
            total = cur.fetchone()[0]
        else:
            query = f"SELECT * FROM {tablas[tipo]} ORDER BY id LIMIT %s OFFSET %s"
            cur.execute(query, (limite, offset))
            data = cur.fetchall()

            cur.execute(f"SELECT COUNT(*) FROM {tablas[tipo]}")
            total = cur.fetchone()[0]

        cur.close()
        conn.close()

    total_paginas = math.ceil(total / limite)

    return render_template(
        'multimedia.html',
        data=data,
        tipo=tipo,
        pagina=pagina,
        total_paginas=total_paginas,
        busqueda=busqueda
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
        cur = conn.cursor()
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

if __name__ == '__main__':
    app.run(debug=True)
