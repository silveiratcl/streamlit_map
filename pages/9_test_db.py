import streamlit as st
from sqlalchemy import create_engine
import pandas as pd

# Retrieve connection details from secrets
connection_details = st.secrets["connections"]["apibd06"]
db_dialect = connection_details["dialect"]
db_driver = connection_details["driver"]
db_host = connection_details["host"]
db_port = connection_details["port"]
db_name = connection_details["database"]
db_username = connection_details["username"]
db_password = connection_details["password"]

# Create the connection string
connection_string = f"{db_dialect}+{db_driver}://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"

# Create the engine
engine = create_engine(connection_string)

# Establish the connection
try:
    conn = engine.connect()
    st.success("Connected to the database successfully!")
    
    # Example query
    query = "SELECT * FROM your_table"
    df = pd.read_sql(query, conn)
    
    # Display the data in the Streamlit app
    st.dataframe(df)

except Exception as e:
    st.error(f"An error occurred: {e}")
finally:
    conn.close()