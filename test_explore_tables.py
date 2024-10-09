import mysql.connector
import pandas as pd
from config.db_config import db_config

def explore_table(data_coralsol_dafor):
    try:
        # Establish the connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Query to select data from the specified table (using one line or triple quotes)
        query = f"SELECT * FROM {data_coralsol_dafor} LIMIT 10;"
        cursor.execute(query)

        # Fetch the data
        rows = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]

        # Convert the result into a pandas DataFrame
        df = pd.DataFrame(rows, columns=column_names)

        # Close the cursor and connection
        cursor.close()
        connection.close()

        # Return the DataFrame
        return df

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
