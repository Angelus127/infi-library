import psycopg2
from psycopg2 import extras
from .config import Config

def conectar():
    try:
        return psycopg2.connect(**Config.DB_CONFIG)
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
        return None

def dict_cursor(conn):
    return conn.cursor(cursor_factory=extras.RealDictCursor)