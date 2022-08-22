import os
import json
import logging
import flask
import psycopg2

from psycopg2.pool import ThreadedConnectionPool

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT')
DB_TABLE_NAME = 'people'

app = flask.Flask(__name__)
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


def get_pools_and_connections():
    # TODO: Modify to return a list of pools and list of connections

    threaded_pool = None
    conn = None
    try:
        threaded_pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host='leader-followers-postgres-db-0.leader-followers-postgres-db-service.default.svc.cluster.local', # podname-i.dbservicename.namespace.svc.cluster.local
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
    table_creation_successful = create_table()
    if not table_creation_successful:
        return flask.jsonify({'create-table': 'FAILED'}), 500
    if flask.request.method == 'PUT':
        data = json.loads(flask.request.data)
        name = data.get('name')
        age = data.get('age')
        was_successful = add_new_person_to_table(name, age)
        if was_successful:
            return flask.jsonify({'write': 'successful'}), 200
        else:
            return flask.jsonify({'error': 'Write failed', 'name': name, 'age': age}), 500
    elif flask.request.method == 'GET':
        values, was_successful = read_personal_details()
        if was_successful:
            logger.info(values)
            return flask.jsonify({'read': 'successful'}), 200
        else:
            return flask.jsonify({'error': 'Read failed'}), 500


@app.route('/health/check', methods=['GET'])
def health_check():
    return {'healthy': True}, 200


@app.route('/readiness/check', methods=['GET'])
def readiness_check():
    # TODO: Implement real readiness check instead of the current dummy function.
    return {'ready': True}, 200


def write_to_database(command, variables):
    pool, conn = get_pools_and_connections()
    was_successful = True
    try:
        cur = conn.cursor()
        cur.execute(command, variables)
        logger.info('Successful write attempt.')
        conn.commit()

        cur.close()
    except Exception as err:
        logger.info(f'Query execution error: {err}')
        was_successful = False
    finally:
        pool.putconn(conn)
        if pool:
            pool.closeall()

    return was_successful


def read_from_database(command):
    pool, conn = get_pools_and_connections()
    was_successful = True
    try:
        cur = conn.cursor()
        values = []
        cur.execute(command)
        values.append(cur.fetchall())
        logger.info('Successful read attempt.')

        cur.close()
    except Exception as err:
        logger.info(f'Query execution error: {err}')
        was_successful = False
    finally:
        pool.putconn(conn)
        if pool:
            pool.closeall()

    return values, was_successful


def create_table():
    command = f"""
    CREATE TABLE IF NOT EXISTS {DB_TABLE_NAME} (
        name TEXT PRIMARY KEY NOT NULL,
        age integer NOT NULL
    );
    """
    variables = []
    return write_to_database(command, variables)


def add_new_person_to_table(name, age):
    command = f"INSERT INTO {DB_TABLE_NAME} (name, age) VALUES (%s, %s)"
    return write_to_database(command, (name, age))


def read_personal_details():
    command = f"SELECT * FROM {DB_TABLE_NAME}"
    return read_from_database(command)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
