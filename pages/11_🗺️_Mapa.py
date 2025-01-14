import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import ast
import datetime
import time
from folium.plugins import MarkerCluster
from folium.plugins import Fullscreen

st.set_page_config(page_title="Map", 
                   page_icon="🗺️", 
                   layout = "wide")
st.logo('./assets/logo_horiz.png',
         size="large")



# --- Initialize connection using SQLAlchemy and credentials from `secrets.toml` ---
def init_connection():
    try:
        # Debugging: Show the structure of st.secrets
        #st.write(st.secrets)

        # Access connection details from secrets
        connection_details = st.secrets["connections"]["apibd06"]
        connection_string = (
            f"{connection_details['dialect']}+{connection_details['driver']}://"
            f"{connection_details['username']}:{connection_details['password']}@"
            f"{connection_details['host']}:{connection_details['port']}/"
            f"{connection_details['database']}"
        )
        # Create an SQLAlchemy engine
        engine = create_engine(connection_string)
        return engine.connect()
    except KeyError as e:
        st.error(f"KeyError: {e}. Check your secrets.toml structure or Streamlit Cloud settings.")
        raise
    except Exception as e:
        st.error(f"An error occurred while connecting to the database: {e}")
        raise


# Establish the connection
conn = init_connection()

# Function to convert Streamlit date (YYYY-MM-DD) to DD/MM/YYYY format
def format_date_to_ddmmyyyy(date):
    return date.strftime('%d/%m/%Y')

# --- Get Data from DB ---
# Fetch management data
def get_management_data():
    query = "SELECT management_id, Management_coords, Observer, Managed_mass_kg, Date FROM data_coralsol_management"
    df = pd.read_sql(query, conn)
    return df

# Fetch locality data
def get_locality_data():
    query = "SELECT locality_id, coords_local, name, date FROM data_coralsol_locality"
    df = pd.read_sql(query, conn)
    return df


# Sidebar for date input
today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
start_date = st.sidebar.date_input('Data Inicial', datetime.date(2012, 1, 1))
end_date = st.sidebar.date_input('Data Final', tomorrow)
if start_date < end_date:
    st.sidebar.success(f'Start date: {start_date} \nEnd date: {end_date}')
else:
    st.sidebar.error('Error: Data Final deve ser após a Data inicial.')

# Convert dates to DD/MM/YYYY for comparison
start_date_str = format_date_to_ddmmyyyy(start_date)
end_date_str = format_date_to_ddmmyyyy(end_date)


# Checkbox options to display data
show_management = st.sidebar.checkbox("Manejos", value=True)
show_locality = st.sidebar.checkbox("Localidades", value=True)

# Initialize Folium map
m = folium.Map(location=[-27.281798, -48.366133], zoom_start=12, tiles="Esri.WorldImagery")
#-48.366133,-27.281798

Fullscreen().add_to(m)

# Display management  if selected
if show_management:
    # Fetch management data
    data = get_management_data()

    # Ensure Date column is a string before parsing
    data['Date'] = data['Date'].astype(str)

    # Manual date comparison to filter data
    filtered_data = data[
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    # Add markers from the filtered data
    marker_cluster = MarkerCluster().add_to(m)
    for index, row in filtered_data.iterrows():
        try:
            # Parse the Management_coords from string to a list of lists
            coords_str = row['Management_coords']
            spot_coords = ast.literal_eval(coords_str)

            # Check if the parsed coordinates are valid
            if isinstance(spot_coords, list) and len(spot_coords) > 0:
                lat, lon = spot_coords[0]  # Extract latitude and longitude
                folium.Marker(
                    [lat, lon],
                    popup=f"Observer: {row['Observer']}, Date: {row['Date']}, Mass(kg): {row['Managed_mass_kg']}",
                    tooltip=f"Management {row['management_id']}"
                ).add_to(marker_cluster)
            else:
                st.error(f"Invalid coordinates for Management ID {row['management_id']}: {spot_coords}")
        except Exception as e:
            st.error(f"Error adding marker for Management ID {row['management_id']}: {e}")

# Display lines if selected
if show_locality:
    # Fetch line data
    data = get_locality_data()

    # Ensure Date column is a string before parsing
    data['date'] = data['date'].astype(str)

    # Manual date comparison to filter data
    filtered_data = data[
        (pd.to_datetime(data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    # Add locality from the filtered data
    for index, row in filtered_data.iterrows():
        try:
            # Parse the coords_local from string to a list of lists
            coords_str = row['coords_local']
            locality_coords = ast.literal_eval(coords_str)

            # Check if the parsed coordinates are valid
            if isinstance(locality_coords, list) and len(locality_coords) > 0:
                folium.PolyLine(
                    locality_coords,
                    popup=f"Locality: {row['name']}, Date: {row['date']}",
                    tooltip=f"Locality {row['locality_id']}"
                ).add_to(m)
            else:
                st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {locality_coords}")
        except Exception as e:
            st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")

# Render the Folium map in Streamlit

time.sleep(0.5)
st_data = st_folium(m, width= '100%', height='100%')
