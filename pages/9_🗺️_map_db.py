import folium
import datetime
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import ast  # To parse Management_coords and coords_local stored as string
import time
from folium.plugins import MarkerCluster
from sqlalchemy import create_engine

st.set_page_config(page_title="Map", page_icon="🗺️")

# Initialize connection using SQLAlchemy and credentials from `secrets.toml`
def init_connection():
    connection_details = st.secrets["connections"]["apibd06"]
    connection_string = (
        f"{connection_details['dialect']}+{connection_details['driver']}://"
        f"{connection_details['username']}:{connection_details['password']}@"
        f"{connection_details['host']}:{connection_details['port']}/"
        f"{connection_details['database']}"
    )
    engine = create_engine(connection_string)
    return engine.connect()

# Establish the connection
conn = init_connection()

# Convert Streamlit date (YYYY-MM-DD) to DD/MM/YYYY format
def format_date_to_ddmmyyyy(date):
    return date.strftime('%d/%m/%Y')

# Fetch marker data
def get_marker_data():
    query = "SELECT management_id, Management_coords, Observer, Date FROM data_coralsol_management"
    df = pd.read_sql(query, conn)
    return df

# Fetch line data
def get_line_data():
    query = "SELECT locality_id, coords_local, name, date FROM data_locality"
    df = pd.read_sql(query, conn)
    return df

# Sidebar for date input
today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
start_date = st.sidebar.date_input('Data Inicial', datetime.date(2012, 1, 1))
end_date = st.sidebar.date_input('Data Final', tomorrow)
if start_date < end_date:
    st.sidebar.success(f'Start date: {start_date}\nEnd date: {end_date}')
else:
    st.sidebar.error('Error: Data Final deve ser após a Data inicial.')

# Convert dates to DD/MM/YYYY for comparison
start_date_str = format_date_to_ddmmyyyy(start_date)
end_date_str = format_date_to_ddmmyyyy(end_date)

# Checkbox options for markers and lines
show_markers = st.sidebar.checkbox("Show Markers", value=True)
show_lines = st.sidebar.checkbox("Show Lines", value=True)

# Initialize Folium map
m = folium.Map(location=[-13.003758, -38.533221], zoom_start=12, tiles="Esri.WorldImagery")

# Display markers if selected
if show_markers:
    # Fetch marker data
    data = get_marker_data()

    # Ensure Date column is a string before parsing
    data['Date'] = data['Date'].astype(str)

    # Manual date comparison to filter data
    filtered_data = data[
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    # Debugging - Check the filtered data
    st.write("Filtered Marker Data:")
    st.write(filtered_data)

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
                    popup=f"Observer: {row['Observer']}, Date: {row['Date']}",
                    tooltip=f"Management {row['management_id']}"
                ).add_to(marker_cluster)
            else:
                st.error(f"Invalid coordinates for Management ID {row['management_id']}: {spot_coords}")
        except Exception as e:
            st.error(f"Error adding marker for Management ID {row['management_id']}: {e}")

# Display lines if selected
if show_lines:
    # Fetch line data
    data = get_line_data()

    # Ensure Date column is a string before parsing
    data['date'] = data['date'].astype(str)

    # Manual date comparison to filter data
    filtered_data = data[
        (pd.to_datetime(data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    # Debugging - Check the filtered data
    st.write("Filtered Line Data:")
    st.write(filtered_data)

    # Add lines from the filtered data
    for index, row in filtered_data.iterrows():
        try:
            # Parse the coords_local from string to a list of lists
            coords_str = row['coords_local']
            line_coords = ast.literal_eval(coords_str)

            # Check if the parsed coordinates are valid
            if isinstance(line_coords, list) and len(line_coords) > 0:
                folium.PolyLine(
                    line_coords,
                    popup=f"Locality: {row['name']}, Date: {row['date']}",
                    tooltip=f"Locality {row['locality_id']}"
                ).add_to(m)
            else:
                st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {line_coords}")
        except Exception as e:
            st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")

# Render the Folium map in Streamlit
time.sleep(1)
st_data = st_folium(m, width=700)
