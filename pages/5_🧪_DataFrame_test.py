import streamlit as st
from etl.extract import explore_table

# Fetch the data from the table
data = explore_table('data_coralsol_dafor')

# Check if data is fetched successfully
if data is not None:
    st.write("Data from the table:")
    st.dataframe(data)  # Display the DataFrame in the Streamlit app
else:
    st.write("No data available or there was an error fetching the data.")

    #1_🗺️_map.py