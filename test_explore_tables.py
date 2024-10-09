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

        # Display the data
        if rows:
            print(f"\nData from table {data_coralsol_dafor}:")
            print(column_names)
            for row in rows:
                print(row)
        else:
            print(f"No data found in table {data_coralsol_dafor}.")

        # Close the cursor and connection
        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
