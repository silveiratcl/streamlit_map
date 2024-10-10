import folium
import datetime
import streamlit as st
from streamlit_folium import st_folium
import ast  # To parse Spot_coords stored as string

st.set_page_config(page_title="Plotting Demo", page_icon="🗺️")

# Initialize connection using the credentials from `secrets.toml`
conn = st.connection('apibd06', type='sql')

# Fetch data from the database
def get_data_from_db(start_date, end_date):
    query = f"""
    SELECT Occurrence_id, Spot_coords, Observer, Date 
    FROM data_coralsol_occurrence 
    WHERE Date BETWEEN '{start_date}' AND '{end_date}'
    """
    df = conn.query(query, ttl=600)
    return df

# Sidebar for date input
today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
start_date = st.sidebar.date_input('Data Inicial', datetime.date(2012, 1, 1))
end_date = st.sidebar.date_input('Data Final', tomorrow)
if start_date < end_date:
    st.sidebar.success('Start date: `%s`\n\nEnd date: `%s`' % (start_date, end_date))
else:
    st.sidebar.error('Error: Data Final deve ser após a Data inicial.')

# Fetch data based on selected dates
data = get_data_from_db(start_date, end_date)

# Check the fetched data
st.write("Fetched Data from DB:")
st.write(data)

# Initialize Folium map
m = folium.Map(location=[-27.28878, -48.36812], zoom_start=12, tiles="Esri.WorldImagery")

# Add markers from database query
for index, row in data.iterrows():
    try:
        # Parse the Spot_coords from string to a list of lists
        spot_coords = ast.literal_eval(row['Spot_coords'])
        st.write(f"Parsed coordinates for Occurrence ID {row['Occurrence_id']}: {spot_coords}")
        
        # Ensure coordinates are valid
        if isinstance(spot_coords, list) and len(spot_coords) > 0:
            lat, lon = spot_coords[0]  # Extract latitude and longitude
            st.write(f"Adding marker for Occurrence ID {row['Occurrence_id']} at {lat}, {lon}")
            
            # Add marker to map
            folium.Marker(
                [lat, lon],
                popup=f"Observer: {row['Observer']}, Date: {row['Date']}",
                tooltip=f"Occurrence {row['Occurrence_id']}"
            ).add_to(m)
        else:
            st.error(f"Invalid coordinates for Occurrence ID {row['Occurrence_id']}: {spot_coords}")
    except Exception as e:
        st.error(f"Error parsing coordinates for Occurrence ID {row['Occurrence_id']}: {e}")

# Render the Folium map in Streamlit
st_data = st_folium(m, width=700)

