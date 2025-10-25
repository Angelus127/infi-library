from flask import Blueprint, render_template, request
import math
from ..db import conectar, dict_cursor

multimedia_routes = Blueprint('multimedia_routes', __name__)

TABLAS_VISTAS = {
    'libros': 'viewBook',
    'animes': 'animeView',
    'peliculas': 'viewMovie',
    'dramas': 'dramaView',
    'mangas': 'mangaView'
}

@multimedia_routes.route('/<tipo>')
def ver_multimedia(tipo):
    if tipo not in TABLAS_VISTAS:
        return f"No existe la categoría '{tipo}'", 404

    # Parámetros de consulta
    pagina = int(request.args.get('page', 1))
    busqueda = request.args.get('q', '')
    estado = request.args.get('estado', '')
    orden = request.args.get('orden', '')
    limite = 20
    offset = (pagina - 1) * limite

    conn = conectar()
    data, conteos, total = [], {}, 0

    if conn:
        cur = dict_cursor(conn)
        tabla = TABLAS_VISTAS[tipo]

        # Conteo de estados
        cur.execute(f"SELECT status, COUNT(*) AS count FROM {tabla} GROUP BY status")
        conteos_raw = cur.fetchall()
        conteos = {fila['status']: fila['count'] for fila in conteos_raw}

        cur.execute(f"SELECT COUNT(*) FROM {tabla}")
        conteos['total'] = cur.fetchone()['count']

        # Filtros dinámicos
        condiciones, parametros = [], []
        if busqueda:
            condiciones.append("title ILIKE %s")
            parametros.append(f"%{busqueda}%")
        if estado:
            condiciones.append("status = %s")
            parametros.append(estado)

        where_clause = "WHERE " + " AND ".join(condiciones) if condiciones else ""

        # Ordenamiento
        orden_sql = {
            'titulo': "ORDER BY title ASC",
            'titulo_desc': "ORDER BY title DESC",
            'puntuacion': "ORDER BY score DESC"
        }.get(orden, "ORDER BY id DESC")

        # Consulta principal
        query = f"SELECT * FROM {tabla} {where_clause} {orden_sql} LIMIT %s OFFSET %s"
        parametros.extend([limite, offset])
        cur.execute(query, tuple(parametros))
        data = cur.fetchall()

        # Conteo total para paginación
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

@multimedia_routes.route('/<tipo>/<int:item_id>')
def ver_detalle(tipo, item_id):
    if tipo not in TABLAS_VISTAS:
        return f"No existe la categoría '{tipo}'", 404

    conn = conectar()
    item = None

    if conn:
        cur = dict_cursor(conn)
        cur.execute(f"SELECT * FROM {TABLAS_VISTAS[tipo]} WHERE id = %s", (item_id,))
        item = cur.fetchone()
        cur.close()
        conn.close()

    if not item:
        return f"No se encontró el elemento con ID {item_id}", 404

    return render_template('detalles.html', item=item, tipo=tipo)
