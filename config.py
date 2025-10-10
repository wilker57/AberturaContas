import psycopg2
from psycopg2 import sql


def get_conn():
    
    return psycopg2.connect(
        dbname='abertura_contas',
        user='postgres',
        password='wil874408',
        host='localhost',
        port='5432'
    )


def get_cursor():
    
    conn = get_conn()
    return conn.cursor()


def close_connection(conn):
   
    if conn:
        conn.close()