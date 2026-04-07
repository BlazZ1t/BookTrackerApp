from src.backend.database.connection import get_connection, init_db
import sqlite3

'''
This class should be used to get database connection, so its persistent.
We don't want hundreds of database connections, so just:
from src.backend.api.initialize import service_connections
database = service_connections.get_connection()

It also initializes a database since it doesn't seem
like there are any initialization logic anywhere else
'''


class ServiceConnections:
    def __init__(self):
        self.database_connection = get_connection()
        init_db(self.database_connection)

    def get_connection(self) -> sqlite3.Connection:
        return self.database_connection


service_connections = ServiceConnections()
