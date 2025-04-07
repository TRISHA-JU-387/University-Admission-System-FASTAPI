import mysql.connector
from mysql.connector import Error


def get_connection():
    try:
        connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='mysql',
        database='university_admission_system'
        )

        return connection
    except Error as err:
        raise err