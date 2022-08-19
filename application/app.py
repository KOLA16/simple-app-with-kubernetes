import os
import logging
import psycopg2

from flask import Flask
from psycopg2.pool import ThreadedConnectionPool

DB_NAME = os.environ.get('DB_NAME')
DB_TABLE_NAME = os.environ.get('DB_TABLE_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT')

app = Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


def get_pools_and_connections(): # add return type

    threaded_pool = None
    conn = None
    try:
        threaded_pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host='localhost',
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )

        conn = threaded_pool.getconn()
    except psycopg2.DatabaseError as error:
        logger.info(f'Error while connecting to PostgreSQL: {error}')

    return (
        threaded_pool,
        conn
    )


@app.route('/api', methods=['GET', 'PUT'])
def interact():
    pool, conn = get_pools_and_connections()
    try:
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM {DB_TABLE_NAME}')
        records = cur.fetchmany(2)

        for row in records:
            logger.info(row)

        cur.close()
    except:
        logger.info('Query execution error')
    finally:
        pool.putconn(conn)
        if pool:
            pool.closeall()

    return "<p>INDEX</p>"


if __name__ == '__main__':
    app.run()
