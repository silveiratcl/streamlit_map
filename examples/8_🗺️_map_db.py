import folium
import datetime
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import ast  # To parse Management_coords and coords_local stored as string
import time
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Map", page_icon="🗺️")

# Initialize connection using the credentials from `secrets.toml`
conn = st.connection('apibd06', type='sql')

# Convert Streamlit date (YYYY-MM-DD) to DD/MM/YYYY format
def format_date_to_ddmmyyyy(date):
    return date.strftime('%d/%m/%Y')

# Fetch management data
def get_management_data():
    query = "SELECT management_id, Management_coords, Observer, Date FROM data_coralsol_management"
    df = conn.query(query, ttl=600)
    return df

# Fetch locality data
def get_locality_data():
    query = "SELECT locality_id, coords_local, name, date FROM data_locality"
    df = conn.query(query, ttl=600)
    return df

# Fetch occurence data
def get_occurrence_data():
    query = "SELECT Occurrence_id, Spot_coords, Date FROM data_coralsol_occurrence"
    df = conn.query(query, ttl=600)
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
show_management = st.sidebar.checkbox("Manejos", value = True)
show_locality = st.sidebar.checkbox("Localidades", value = True)
show_occurrence_data = st.sidebar.checkbox("Ocorrências", value = True)

# Initialize Folium map
m = folium.Map(location=[-13.003758, -38.533221], zoom_start=12, tiles="Esri.WorldImagery")

# Display manejos if selected
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

    # Debugging - Check the filtered data
    st.write("Filtered Management Data:")
    st.write(filtered_data)

    # Add managemente from the filtered data
    management_cluster = MarkerCluster().add_to(m)
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
                ).add_to(management_cluster)
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

    # Debugging - Check the filtered data
    st.write("Filtered locality Data:")
    st.write(filtered_data)

    # Add lines from the filtered data
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
################################################### review here, but i th front end has a problem to save it, seens ok
# Display occurrence if selected
if show_occurrence_data:
    # Fetch occurrence data
    data = get_occurrence_data()

    # Ensure Date column is a string before parsing
    data['Date'] = data['Date'].astype(str)

    # Manual date comparison to filter data
    filtered_data = data[
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
        (pd.to_datetime(data['Date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
    ]

    # Debugging - Check the filtered data
    st.write("Filtered Occurrence Data:")
    st.write(filtered_data)

    # Add occurrences from the filtered data
    occurrence_cluster = MarkerCluster().add_to(m)
    for index, row in filtered_data.iterrows():
        try:
            # Parse the Spot_coords from string to a list of lists
            coords_str = row['Spot_coords']
            occurrence_coords = ast.literal_eval(coords_str)

            # Check if the parsed coordinates are valid
            if isinstance(occurrence_coords, list) and len(occurrence_coords) > 0:
                lat, lon = occurrence_coords[0]  # Extract latitude and longitude
                folium.Marker(
                    [lat, lon],
                    popup=f"Occurrence ID: {row['Occurrence_id']}, Date: {row['Date']}",
                    tooltip=f"Occurrence {row['Occurrence_id']}"
                ).add_to(occurrence_cluster)
            else:
                st.error(f"Invalid coordinates for Occurrence ID {row['Occurrence_id']}: {occurrence_coords}")
        except Exception as e:
            st.error(f"Error adding marker for Occurrence ID {row['Occurrence_id']}: {e}")

    
####################################################        



# Render the Folium map in Streamlit
time.sleep(1)
st_data = st_folium(m, width=700)
