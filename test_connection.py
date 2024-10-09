import mysql.connector
from config.db_config import db_config

def list_tables():
    try:
        # Establish the connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Query to list all tables
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        # Print all table names
        if tables:
            print("Tables in the database:")
            for table in tables:
                print(table[0])
        else:
            print("No tables found in the database.")

        # Close the cursor and connection
        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == "__main__":
    list_tables()
