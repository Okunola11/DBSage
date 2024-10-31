import json
import psycopg2
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from typing import Dict, Optional

class PostgresManager:
    """A context manager for managing PostgreSQL database connections.

    This class provides a convenient way to establish a connection to a PostgreSQL database,
    execute SQL queries, retrieve table definitions, and automatically close the connection
    when the context is exited.

    Attributes:
        conn: A psycopg2 connection object.
        cur: A psycopg2 cursor object.
    """
    
    def __init__(self):
        """Initializes the DatabaseConnection object."""

        self.conn = None
        self.cur = None

    def __enter__(self):
        """Enters the context manager, returning the PostgresManager object.

        Returns:
            The PostgresManager object.
        """

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exits the context manager, closing the database connection if necessary.

        Args:
            exc_type: The type of exception that occurred, if any.
            exc_val: The exception object, if any.
            exc_tb: The traceback object, if any.
        """
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def connect_with_url(self, url):
        """Connects to a PostgreSQL database using the specified URL.

        Args:
            url: The URL of the PostgreSQL database to connect to.

        Raises:
            pscopg2 error: error during database connection.
        """

        try:
            self.conn = psycopg2.connect(url)
            self.cur = self.conn.cursor()
        except psycopg2.Error as e:
            error_message = f"Error connecting to database: {e}"
            print(error_message)
            raise HTTPException(status_code=500, detail={"message": error_message})

    def run_sql(self, sql) -> str:
        """Executes a SQL query and returns the results as a JSON string.

        Args:
            sql: The SQL query to execute.

        Returns:
            JSON: result of the query.
        """

        if not self.conn or not self.cur:
            raise HTTPException(status_code=400, detail="No active database connection")

        try:
            self.cur.execute(sql)
            columns = [desc[0] for desc in self.cur.description]
            res = self.cur.fetchall()

            list_of_dicts = [(dict(zip(columns, row))) for row in res]

            json_result = json.dumps(list_of_dicts, indent=4, default=self.datetime_handler)

            return json_result
        except Exception as e:
            print(f"Error executing SQL query: {e}")
            raise

    def datetime_handler(self, obj):
        """Handles datetime objects when serializing to JSON.

        Args:
            obj: The datetime object

        Returns:
            str: ISO format date as a string
        """

        if isinstance(obj, datetime):
            return obj.isoformat()
        return str(obj)

    def get_table_definitions(self, table_name):
        """Retrieves the CREATE TABLE statement for a given table in the 'public' schema.

        Args:
            self: An instance of the class containing this method.
            table_name: The name of the table to retrieve the definition for.

        Returns:
            A string representing the CREATE TABLE statement for the specified table.
        """

        get_def_stmt = """
        SELECT pg_class.relname as tablename,
            pg_attribute.attnum,
            pg_attribute.attname,
            format_type(atttypid, atttypmod)
        FROM pg_class
        JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
        JOIN pg_attribute ON pg_attribute.attrelid = pg_class.oid
        WHERE pg_attribute.attnum > 0
            AND pg_attribute.attisdropped = false
            AND pg_class.relname = %s
            AND pg_namespace.nspname = 'public' -- Assuming we are only interested in the public schema
        """
        self.cur.execute(get_def_stmt, (table_name,))
        rows = self.cur.fetchall()
        create_table_stmt = "CREATE TABLE {} (\n".format(table_name)
        for row in rows:
            create_table_stmt += "{} {},\n".format(row[2], row[3])
        create_table_stmt = create_table_stmt.rstrip(",\n") + "\n);"
        return create_table_stmt

    def get_all_table_names(self):
        """Retrieves a list of all table names in the 'public' schema.

        Args:
            self: An instance of the class containing this method.

        Returns:
            A list of table names.
        """

        get_all_tables_stmt = (
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
        )
        try:
            self.cur.execute(get_all_tables_stmt)
        except Exception as e:
            print(f"Error retrieving table names: {e}")
            raise
        return [row[0] for row in self.cur.fetchall()]

    def get_all_tables_and_columns(self):
        """
        Retrieves all tables in the public schema and their corresponding columns.
        
        Returns:
            A list of dictionaries, where each dictionary represents a table.
            The dictionary has two keys: 'table_name' and 'columns'.
            'columns' is a list of column names for that table.
        """
        query = """
        SELECT 
            table_name,
            array_agg(column_name::text) AS columns
        FROM 
            information_schema.columns
        WHERE 
            table_schema = 'public'
        GROUP BY 
            table_name
        ORDER BY 
            table_name;
        """
        
        try:
            self.cur.execute(query)
            results = self.cur.fetchall()
            
            tables_and_columns = [
                {
                    'table_name': table_name,
                    'columns': columns
                }
                for table_name, columns in results
            ]
            
            return tables_and_columns
        except psycopg2.Error as e:
            print(f"Error retrieving tables and columns: {e}")
            raise

    def get_table_definitions_for_prompt(self):
        """Retrieves the definitions of all tables in the 'public' schema as a formatted string.

        Args:
            self: An instance of the class containing this method.

        Returns:
            A string containing the definitions of all tables in the 'public' schema, separated by newline characters.
        """
        
        table_names = self.get_all_table_names()
        definitions = []
        for table_name in table_names:
            definitions.append(self.get_table_definitions(table_name))
        return "\n\n".join(definitions)

    def get_table_definition_map_for_embeddings(self):
        """Retrieves a mapping of table names to their definitions for use in embeddings.

        Returns:
            dict: A dictionary where keys are table names and values are their corresponding definitions.
        """
        table_names = self.get_all_table_names()
        definitions = {}
        for table_name in table_names:
            definitions[table_name] = self.get_table_definitions(table_name)
        return definitions

    def get_related_tables(self, table_list, n=2):
        """Retrieves a list of tables related to the given tables through foreign key references.

        This method queries the database to find tables that have foreign keys referencing the given tables,
        as well as tables that are referenced by the given tables. The results are combined and duplicates are removed.

        Args:
            table_list (list): A list of table names to find related tables for.
            n (int, optional): The maximum number of related tables to retrieve for each table. Defaults to 2.

        Returns:
            list: A list of unique table names related to the given tables through foreign key references.
        """

        related_tables_dict = {}

        for table in table_list:
            # Query to fetch tables that have foreign key referencing the given table
            self.cur.execute(
                """
                SELECT
                    a.relname AS table_name
                FROM
                    pg_constraint con
                    JOIN pg_class a ON a.oid = con.conrelid
                WHERE
                    confrelid = (SELECT oid FROM pg_class WHERE relname = %s)
                LIMIT %s;
                """,
                (table, n),
            )

            related_tables = [row[0] for row in self.cur.fetchall()]

            # Query to fetch tables that the given table references
            self.cur.execute(
                """
                SELECT
                    a.relname AS referenced_table_name
                FROM
                    pg_constraint con
                    JOIN pg_class a ON a.oid = con.confrelid
                WHERE
                    conrelid = (SELECT oid FROM pg_class WHERE relname = %s)
                LIMIT %s;
                """,
                (table, n),
            )

            related_tables += [row[0] for row in self.cur.fetchall()]

            related_tables_dict[table] = related_tables

        # convert the dict to list and remove dups
        related_tables_list = []
        for table, related_tables in related_tables_dict.items():
            related_tables_list += related_tables

        related_tables_list = list(set(related_tables_list))

        return related_tables_list

import threading

class DatabaseStateManager:
    """
    A singleton class for managing database connections for multiple users across the application.

    This class provides a centralized way to manage database connections on a per-user basis,
    ensuring proper isolation and resource management. It maintains separate connections for
    different users and includes automatic cleanup of inactive connections.

    Attributes:
        _connections (Dict[str, PostgresManager]): Dictionary mapping user IDs to their database connections.
        _urls (Dict[str, str]): Dictionary mapping user IDs to their database URLs.
        _last_used (Dict[str, datetime]): Dictionary tracking when each connection was last accessed.
        _cleanup_threshold (timedelta): Time after which inactive connections are cleaned up.

    Methods:
        set_connection(user_id: str, db_url: str) -> bool:
            Establishes a new database connection for a specific user.

        get_connection(user_id: str) -> Optional[PostgresManager]:
            Retrieves the database connection for a specific user.

        close_connection(user_id: str) -> None:
            Closes the database connection for a specific user.

        check_connection_health(user_id: str) -> bool:
            Checks if a user's database connection is alive and functioning.

        get_active_connections() -> Dict[str, dict]:
            Retrieves information about all active database connections.

        get_connection_status(user_id: str) -> dict:
            Gets detailed status information about a user's database connection.

        cleanup_inactive_connections() -> None:
            Cleans up connections that have been inactive for longer than the threshold.

    Note:
        This class uses a thread-safe singleton pattern to ensure that only one
        instance exists throughout the application lifecycle.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseStateManager, cls).__new__(cls)
                    cls._instance._connections: Dict[str, PostgresManager] = {}
                    cls._instance._urls: Dict[str, str] = {}
                    cls._instance._last_used: Dict[str, datetime] = {}
                    cls._instance._created_at: Dict[str, datetime] = {}
        return cls._instance

    def __init__(self):
        self._cleanup_threshold = timedelta(hours=1) 

    def set_connection(self, user_id: str, db_url: str) -> bool:
        """
        Establishes a new database connection for a specific user.

        This method attempts to create a new database connection using the provided URL
        and associates it with the specified user ID. If the user already has the maximum
        allowed connections, it will raise an HTTPException.

        Args:
            user_id (str): The ID of the user for whom to establish the connection.
            db_url (str): The URL of the database to connect to.

        Returns:
            bool: True if the connection was successfully established, False otherwise.

        Raises:
            HTTPException: If the user has reached the maximum allowed number of connections
                (HTTP 400) or if the connection attempt fails (HTTP 500).

        Note:
            If a previous connection exists for this user, it will be closed before
            attempting to establish a new one. There is a limit of one connection
            per user by default.
        """

        MAX_CONNECTIONS_PER_USER = 1
        if len([k for k in self._connections.keys() if k.startswith(user_id)]) >= MAX_CONNECTIONS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum number of connections reached for this user"
            )

        try:
            new_db = PostgresManager()
            new_db.connect_with_url(db_url)
            
            # Close existing connection if it exists
            self.close_connection(user_id)
            
            self._connections[user_id] = new_db
            self._urls[user_id] = db_url
            self._created_at[user_id] = datetime.now(timezone.utc)
            return True
        except Exception as e:
            print(f"Failed to establish database connection: {e}")
            return False

    def get_connection(self, user_id: str) -> Optional[PostgresManager]:
        """
        Retrieves the database connection for a specific user.

        This method returns the PostgresManager instance associated with the given user ID
        if one exists. It also updates the last usage timestamp for the connection.

        Args:
            user_id (str): The ID of the user whose connection to retrieve.

        Returns:
            Optional[PostgresManager]: The database connection manager for the specified user
            if one exists, None otherwise.

        Note:
            Each access to the connection updates the last_used timestamp, which is used
            for cleaning up inactive connections.
        """

        conn = self._connections.get(user_id)
        if conn:
            now_utc = datetime.now(timezone.utc)
            self._last_used[user_id] = now_utc.isoformat()

        return conn

    def close_connection(self, user_id: str):
        """
        Closes the database connection for a specific user.

        This method closes the database connection associated with the given user ID
        if one exists and removes it from the internal state tracking.

        Args:
            user_id (str): The ID of the user whose connection to close.

        Note:
            This method is safe to call even if no connection exists for the specified user.
            It will clean up all associated resources including the connection URL and
            last used timestamp.
        """

        if user_id in self._connections:
            self._connections[user_id].__exit__(None, None, None)
            del self._connections[user_id]
            del self._urls[user_id]

    def cleanup_inactive_connections(self):
        """
        Cleans up database connections that have been inactive for longer than the cleanup threshold.

        This method checks all connections and closes those that haven't been used
        for longer than the specified cleanup threshold (default: 1 hour).

        Note:
            This method is typically called periodically by the application's
            background task scheduler.
        """
        
        now = datetime.now(timezone.utc)
        for user_id, last_used in list(self._last_used.items()):
            last_used_time = datetime.fromisoformat(last_used)
            if now - last_used_time > self._cleanup_threshold:
                self.close_connection(user_id)

    def get_connection_status(self, user_id: str) -> dict:
        """
        Gets detailed status information about a specific user's database connection.

        Args:
            user_id (str): The ID of the user whose connection status to check.

        Returns:
            dict: A dictionary containing connection status information including:
                - has_connection: Whether an active connection exists
                - db_url: The URL of the database connection
                - last_used: Timestamp of last connection usage
                - connection_age: Time elapsed since the connection was set
        """

        connection = self._connections.get(user_id)
        url = self._urls.get(user_id)
        last_used_iso = self._last_used.get(user_id)
        created_at = self._created_at.get(user_id)

        if created_at:
            connection_age = str(datetime.now(timezone.utc) - created_at)
        else:
            connection_age = None
        
        return {
            "has_connection": connection is not None,
            "db_url": url,
            "last_used": last_used_iso,
            "connection_age": connection_age
        }

    def get_active_connections(self) -> Dict[str, dict]:
        """
        Retrieves information about all currently active database connections.

        Returns:
            Dict[str, dict]: A dictionary mapping user IDs to connection information,
            including database URLs and last usage timestamps.

        Note:
            This method is particularly useful for monitoring and administrative purposes.
        """

        return {
            user_id: {
                "db_url": self._urls[user_id],
                "last_used": self._last_used.get(user_id),
            }
            for user_id in self._connections.keys()
        }

    async def check_connection_health(self, user_id: str) -> bool:
        """
        Checks if a user's database connection is healthy and responsive.

        Args:
            user_id (str): The ID of the user whose connection to check.

        Returns:
            bool: True if the connection is healthy and responsive, False otherwise.

        Note:
            If the connection is found to be dead, it will be automatically closed
            and cleaned up.
        """

        connection = self._connections.get(user_id)
        if not connection:
            return False
        
        try:
            # Assuming PostgresManager has a method to test connection
            await connection.execute("SELECT 1")
            return True
        except Exception:
            # Connection is dead, clean it up
            self.close_connection(user_id)
            return False