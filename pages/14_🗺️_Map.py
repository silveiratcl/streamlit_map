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
import requests
import base64
from PIL import Image
from io import BytesIO
import json

st.set_page_config(page_title="Mapa", 
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
    df.columns = map(str.lower, df.columns) # Ensure column names are lowercase
    return df

# Fetch locality data
def get_locality_data():
    query = "SELECT locality_id, coords_local, name, date FROM data_coralsol_locality"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns) # Ensure column names are lowercase
    return df

def get_occ_data():
   query = "SELECT Occurrence_id, Spot_coords, Date, Depth, Superficie_photo FROM data_coralsol_occurrence WHERE Superficie_photo IS NOT NULL LIMIT 10"
   df = pd.read_sql(query, conn)  # Use pd.read_sql to fetch data
   df.columns = map(str.lower, df.columns)    # Ensure column names are lowercase
   return df

def get_dafor_data():
   query = "SELECT Dafor_id, Locality_id,  Dafor_coords, Date, Horizontal_visibility, Bathymetric_zone, Method, Dafor_value FROM data_coralsol_dafor"
   df = pd.read_sql(query, conn) # Use pd.read_sql to fetch data
   df.columns = map(str.lower, df.columns) # Ensure column names are lowercase
   return df

# Base URL test DB
base_url = "http://coralsol-api.kinghost.net/api"

# -- Sidebar for date input
today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
start_date = st.sidebar.date_input('Data Inicial', datetime.date(2012, 1, 1))
end_date = st.sidebar.date_input('Data Final', tomorrow)
if start_date < end_date:
    st.sidebar.success(f'Start date: {start_date} \nEnd date: {end_date}')
else:
    st.sidebar.error('Error: Data Final deve ser após a Data inicial.')

# -- Convert dates to DD/MM/YYYY for comparison
start_date_str = format_date_to_ddmmyyyy(start_date)
end_date_str = format_date_to_ddmmyyyy(end_date)

# -- Checkbox options to display Indicadores
with st.sidebar.expander("Indicadores", expanded=True):
    show_transects_suncoral = st.checkbox("Transectos com Coral-sol", value=True)

# -- Checkbox options to display data
with st.sidebar.expander("Camadas", expanded=True):
    show_management = st.checkbox("Manejos", value=True)
    show_locality = st.checkbox("Localidades", value=True)
    show_occ = st.checkbox("Ocorrências", value=True)
    show_dafor = st.checkbox("Monitoramento", value=True)

# -- Initialize Folium map
m = folium.Map(location=[-27.281798, -48.366133],
               width ="100%",
               height = "100%", 
               zoom_start = 13,
               tiles = "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2lsdmVpcmF0Y2wiLCJhIjoiY202MTRrN3N5MGt3MDJqb2xhc3R0empqZCJ9.YfjBqq5HbnacUNw9Tyiaew",
               attr="Mapbox attribution",
               max_zoom = 20,
               min_zoon = 1,
               #tiles="Esri.WorldImagery"
               )
#-48.366133,-27.281798

Fullscreen().add_to(m)

### Camadas ###

# Display management  if selected
if show_management:
    # Fetch management data
    data = get_management_data()

    # Ensure Date column is a string before parsing
    data['date'] = data['date'].astype(str)

    # Manual date comparison to filter data
    filtered_data = data[
        (pd.to_datetime(data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    # Add markers from the filtered data
    marker_cluster = MarkerCluster(disableClusteringAtZoom = 6).add_to(m)
    for index, row in filtered_data.iterrows():
        try:
            # Parse the Management_coords from string to a list of lists
            coords_str = row['management_coords']
            spot_coords = ast.literal_eval(coords_str)

            # Check if the parsed coordinates are valid
            if isinstance(spot_coords, list) and len(spot_coords) > 0:
                lat, lon = spot_coords[0]  # Extract latitude and longitude
                folium.Marker(
                    [lat, lon],
                    popup=f"Observer: {row['observer']}, Date: {row['date']}, Mass(kg): {row['managed_mass_kg']}",
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

# if show_occ:
if show_occ:
    data = get_occ_data()

    if data is None or data.empty:
        st.warning("No occurrence data found matching the criteria.")
    else:
        # Ensure Date column is a string before parsing
        data['date'] = data['date'].astype(str)

        # Manual date comparison to filter data
        filtered_data = data[
            (pd.to_datetime(data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
            (pd.to_datetime(data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
        ]

        # Add markers from the filtered data
        marker_cluster = MarkerCluster(disableClusteringAtZoom = 6).add_to(m)
        for index, row in filtered_data.iterrows():
            try:
                coords_str = row['spot_coords']
                spot_coords = ast.literal_eval(coords_str)

                if isinstance(spot_coords, list) and len(spot_coords) > 0:
                    lat, lon = spot_coords[0]

                    # Construct the photo URL
                    occurrence_id = row['occurrence_id']
                    file_name = row['superficie_photo']
                    photo_url = f"{base_url}/Upload/UploadImageCoralSol/{occurrence_id}/{file_name}"

                    response = requests.get(photo_url)
                    if response.status_code == 200:
                        base64_image = response.text
                        popup_html = f"""
                        <b>Date:</b> {row['date']}<br>
                        <b>Depth (m):</b> {row['depth']}<br>
                        <b>Photo:</b><br>
                        <img src="data:image/png;base64,{base64_image}" width="300"/>
                        """
                    else:
                        popup_html = f"""
                        <b>Date:</b> {row['date']}<br>
                        <b>Depth (m):</b> {row['depth']}<br>
                        <b>Photo:</b> <i>Image not available (Error {response.status_code})</i>
                        """

                    folium.Marker(
                        [lat, lon],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"Ocorrência {row['occurrence_id']}"
                    ).add_to(marker_cluster)
                else:
                    st.error(f"Invalid coordinates for Occurrence ID {row['occurrence_id']}: {spot_coords}")
            except Exception as e:
                st.error(f"Error adding marker for Occurrence ID {row['occurrence_id']}: {e}")

# Display lines if selected
if show_dafor:
    # Fetch line data
    data = get_dafor_data()

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
            # Parse the dafor_coords from string to a list of lists
            coords_str = row['dafor_coords']
            try:
                dafor_coords = ast.literal_eval(coords_str)
            except (ValueError, SyntaxError) as e:
                st.error(f"Error parsing coordinates for Locality ID {row['locality_id']}: {e}")
                continue

            # Check if the parsed coordinates are valid
            if isinstance(dafor_coords, list) and len(dafor_coords) > 0:
                folium.PolyLine(
                    dafor_coords,
                    popup=f"Locality: {row['locality_id']}, Date: {row['date']}",
                    tooltip=f"Locality {row['locality_id']}"
                ).add_to(m)
            else:
                st.error(f"Invalid coordinates for Locality ID {row['dafor_id']}: {dafor_coords}")
        except Exception as e:
            st.error(f"Error adding line for Locality ID {row['dafor_id']}: {e}")

### Indicadores ###

if show_transects_suncoral:
    # Get locality data to get the locality lines
    locality_data = get_locality_data()

    # Ensure Date column is a string before parsing
    locality_data['date'] = locality_data['date'].astype(str)

    # Manual date comparison to filter data
    filtered_locality_data = locality_data[
        (pd.to_datetime(locality_data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(locality_data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    # Get dafor data
    dafor_data = get_dafor_data()

    # Ensure Date column is a string before parsing
    dafor_data['date'] = dafor_data['date'].astype(str)

    # Convert dafor_value to numeric
    dafor_data['dafor_value'] = pd.to_numeric(dafor_data['dafor_value'], errors='coerce')

    # Manual date comparison to filter data
    filtered_dafor_data = dafor_data[
        (pd.to_datetime(dafor_data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(dafor_data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    # Count the number of Dafor_value entries greater than 0 for each locality
    dafor_counts = filtered_dafor_data[filtered_dafor_data['dafor_value'] > 0].groupby('locality_id').size().reset_index(name='dafor_count')

    # Merge the counts with the locality data
    merged_data = filtered_locality_data.merge(dafor_counts, on='locality_id', how='left').fillna({'dafor_count': 0})

    # Display the table with dafor counts
    st.write("Dafor Counts by Locality")
    st.dataframe(merged_data[['locality_id', 'dafor_count']])

    # Add locality from the merged data
    for index, row in merged_data.iterrows():
        try:
            # Parse the coords_local from string to a list of lists
            coords_str = row['coords_local']
            try:
                coords_local = ast.literal_eval(coords_str)
            except (ValueError, SyntaxError) as e:
                st.error(f"Error parsing coordinates for Locality ID {row['locality_id']}: {e}")
                continue

            # Check if the parsed coordinates are valid
            if isinstance(coords_local, list) and len(coords_local) > 0:
                # Determine the color based on the dafor_count
                dafor_count = row['dafor_count']
                if dafor_count > 10:
                    color = 'red'
                elif dafor_count > 5:
                    color = 'orange'
                else:
                    color = 'green'

                folium.PolyLine(
                    coords_local,
                    color=color,
                    popup=f"Locality: {row['locality_id']}, Date: {row['date']}, Dafor Count: {dafor_count}",
                    tooltip=f"Locality {row['locality_id']}"
                ).add_to(m)
            else:
                st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {coords_local}")
        except Exception as e:
            st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")

# Render the Folium map in Streamlit
time.sleep(1)
st_data = st_folium(m, width= '100%', height='600')