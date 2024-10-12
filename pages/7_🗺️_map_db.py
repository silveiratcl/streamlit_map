import folium
import datetime
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd  # Ensure pandas is imported
import ast  # To parse Management_coords stored as string
import time 
from folium.plugins import MarkerCluster



st.set_page_config(page_title="Plotting Demo", page_icon="🗺️")

# Initialize connection using the credentials from `secrets.toml`
conn = st.connection('apibd06', type='sql')

# Convert Streamlit date (YYYY-MM-DD) to DD/MM/YYYY format
def format_date_to_ddmmyyyy(date):
    return date.strftime('%d/%m/%Y')

# Fetch all data without date filtering for debugging purposes
def get_all_data():
    query = "SELECT management_id, Management_coords, Observer, Date FROM data_coralsol_management"
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

# Fetch all data for debugging
data = get_all_data()

# Debugging - Check the full data fetched without filtering
st.write("Fetched Data from DB (without filtering):")
st.write(data)

# Ensure Date column is a string before parsing
data['Date'] = data['Date'].astype(str)

# Manual date comparison to filter data
filtered_data = data[
    (pd.to_datetime(data['Date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
    (pd.to_datetime(data['Date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
]

# Debugging - Check the filtered data based on manual date comparison
st.write("Manually filtered data based on date comparison:")
st.write(filtered_data)

# Initialize Folium map
m = folium.Map(location=[-13.003758, -38.533221], zoom_start=12, tiles="Esri.WorldImagery")
marker_cluster = MarkerCluster().add_to(m)


# Add markers from the filtered data
for index, row in filtered_data.iterrows():
    try:
        # Parse the Management_coords from string to a list of lists
        coords_str = row['Management_coords']
        st.write(f"Raw coordinates for Management ID {row['management_id']}: {coords_str}")
        
        # Parse Management_coords safely
        try:
            spot_coords = ast.literal_eval(coords_str)
        except Exception as parse_err:
            st.error(f"Failed to parse coordinates for Management ID {row['management_id']}: {parse_err}")
            continue

        # Check if the parsed coordinates are valid
        if isinstance(spot_coords, list) and len(spot_coords) > 0:
            lat, lon = spot_coords[0]  # Extract latitude and longitude
            st.write(f"Adding marker for Management ID {row['management_id']} at {lat}, {lon}")
            
            # Add marker to map
            folium.Marker(
                [lat, lon],
                popup=f"Observer: {row['Observer']}, Date: {row['Date']}",
                tooltip=f"Management {row['management_id']}"
            ).add_to(marker_cluster)
        else:
            st.error(f"Invalid coordinates for Management ID {row['management_id']}: {spot_coords}")
    except Exception as e:
        st.error(f"Error adding marker for Management ID {row['management_id']}: {e}")

# Render the Folium map in Streamlit
time.sleep(1) 
st_data = st_folium(m, width=700)
