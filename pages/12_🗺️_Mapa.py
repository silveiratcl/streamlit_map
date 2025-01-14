import streamlit as st
import base64
from sqlalchemy import create_engine
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast
import datetime
import os
from folium.plugins import MarkerCluster
from folium.plugins import Fullscreen

st.set_page_config(page_title="Map", 
                   page_icon="🗺️", 
                   layout="wide")
st.logo('./assets/logo_horiz.png', size="large")

# --- Initialize connection using SQLAlchemy and credentials from `secrets.toml` ---
def init_connection():
    try:
        connection_details = st.secrets["connections"]["apibd06"]
        connection_string = (
            f"{connection_details['dialect']}+{connection_details['driver']}://"
            f"{connection_details['username']}:{connection_details['password']}@"
            f"{connection_details['host']}:{connection_details['port']}/"
            f"{connection_details['database']}"
        )
        engine = create_engine(connection_string)
        return engine.connect()
    except Exception as e:
        st.error(f"An error occurred while connecting to the database: {e}")
        raise

# Establish the connection
conn = init_connection()

# Function to convert Streamlit date (YYYY-MM-DD) to DD/MM/YYYY format
def format_date_to_ddmmyyyy(date):
    return date.strftime('%d/%m/%Y')

# --- Get Data from DB ---
def get_management_data():
    query = "SELECT management_id, Management_coords, Observer, Managed_mass_kg, Date FROM data_coralsol_management"
    return pd.read_sql(query, conn)

def get_locality_data():
    query = "SELECT locality_id, coords_local, name, date FROM data_coralsol_locality"
    return pd.read_sql(query, conn)

def get_occ_data():
    query = "SELECT Occurrence_id, Locality_id, Spot_coords, Date, Depth, Superficie_photo FROM data_coralsol_occurrence"
    return pd.read_sql(query, conn)

# --- Sidebar for date input ---
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

# Checkbox options
show_management = st.sidebar.checkbox("Manejos", value=True)
show_locality = st.sidebar.checkbox("Localidades", value=True)
show_occ = st.sidebar.checkbox("Ocorrências", value=True)

# Initialize Folium map
m = folium.Map(location=[-27.281798, -48.366133], zoom_start=12, tiles="Esri.WorldImagery")
Fullscreen().add_to(m)

# Temporary directory for saving images
image_dir = "temp_images"
os.makedirs(image_dir, exist_ok=True)

# Display management layer
if show_management:
    data = get_management_data()
    data['Date'] = data['Date'].astype(str)

    filtered_data = data[
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    marker_cluster = MarkerCluster().add_to(m)
    for index, row in filtered_data.iterrows():
        try:
            coords_str = row['Management_coords']
            spot_coords = ast.literal_eval(coords_str)

            if isinstance(spot_coords, list) and len(spot_coords) > 0:
                lat, lon = spot_coords[0]
                folium.Marker(
                    [lat, lon],
                    popup=f"Observer: {row['Observer']}, Date: {row['Date']}, Mass(kg): {row['Managed_mass_kg']}",
                    tooltip=f"Management {row['management_id']}"
                ).add_to(marker_cluster)
            else:
                st.error(f"Invalid coordinates for Management ID {row['management_id']}: {spot_coords}")
        except Exception as e:
            st.error(f"Error adding marker for Management ID {row['management_id']}: {e}")

# Display locality layer
if show_locality:
    data = get_locality_data()
    data['date'] = data['date'].astype(str)

    filtered_data = data[
        (pd.to_datetime(data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    for index, row in filtered_data.iterrows():
        try:
            coords_str = row['coords_local']
            locality_coords = ast.literal_eval(coords_str)

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

# Display occurrence layer
import base64

if show_occ:
    data = get_occ_data()
    data['Date'] = data['Date'].astype(str)

    filtered_data = data[
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    marker_cluster = MarkerCluster().add_to(m)
    for index, row in filtered_data.iterrows():
        try:
            coords_str = row['Spot_coords']
            spot_coords = ast.literal_eval(coords_str)

            if isinstance(spot_coords, list) and len(spot_coords) > 0:
                lat, lon = spot_coords[0]

                # Handle binary data or URLs
                photo_html = ""
                if isinstance(row['Superficie_photo'], bytes):  # Binary data
                    # Encode the binary data to Base64
                    encoded_image = base64.b64encode(row['Superficie_photo']).decode('utf-8')
                    photo_html = f'<img src="data:image/png;base64,{encoded_image}" width="300"/>'
                elif isinstance(row['Superficie_photo'], str):  # URL
                    photo_html = f'<a href="{row["Superficie_photo"]}" target="_blank">View Photo</a>'

                # HTML for the popup
                popup_html = f"""
                <b>Date:</b> {row['Date']}<br>
                <b>Depth (m):</b> {row['Depth']}<br>
                <b>Photo:</b><br>{photo_html}
                """
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"Ocorrência {row['Occurrence_id']}"
                ).add_to(marker_cluster)
            else:
                st.error(f"Invalid coordinates for Occurrence ID {row['Occurrence_id']}: {spot_coords}")
        except Exception as e:
            st.error(f"Error adding marker for Occurrence ID {row['Occurrence_id']}: {e}")


# --- Debug if the picture exists on the database
# Sidebar option to test image retrieval
check_image = st.sidebar.checkbox("Check Image from DB")

if check_image:
    query = "SELECT Occurrence_id, Superficie_photo FROM data_coralsol_occurrence WHERE Superficie_photo IS NOT NULL LIMIT 1"
    result = pd.read_sql(query, conn)

    if not result.empty:
        row = result.iloc[0]  # Get the first row
        photo_data = row['Superficie_photo']

        if isinstance(photo_data, bytes):
            try:
                from PIL import Image
                from io import BytesIO
                
                img = Image.open(BytesIO(photo_data))  # Attempt to open the image
                st.image(img, caption=f"Occurrence ID: {row['Occurrence_id']}", use_column_width=True)
            except Exception as e:
                st.error(f"Invalid image data for Occurrence ID {row['Occurrence_id']}: {e}")
        elif isinstance(photo_data, str):  # Assume URL
            st.image(photo_data, caption=f"Occurrence ID: {row['Occurrence_id']}", use_column_width=True)
        else:
            st.error("Unexpected photo_data format.")
    else:
        st.warning("No image data found in the database.")




# Render the Folium map in Streamlit
st_data = st_folium(m, width='100%', height='600')
