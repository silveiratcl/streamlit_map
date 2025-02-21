import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast
import datetime
from folium.plugins import MarkerCluster, Fullscreen
import requests
from branca.element import Template, MacroElement

# --- Page Configuration ---
st.set_page_config(page_title="Indicadores", page_icon="📊", layout="wide")
st.logo('./assets/logo_horiz.png', size="large")

# --- Initialize Connection ---
@st.cache_resource
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
        st.error(f"Database connection error: {e}")
        raise

conn = init_connection()

# --- Data Fetching Functions ---
@st.cache_data
def get_management_data():
    query = "SELECT management_id, management_coords, observer, managed_mass_kg, date FROM data_coralsol_management"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_locality_data():
    query = "SELECT locality_id, coords_local, name, date FROM data_coralsol_locality"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_occ_data():
    query = "SELECT Occurrence_id, Spot_coords, Date, Depth, Superficie_photo FROM data_coralsol_occurrence WHERE Superficie_photo IS NOT NULL LIMIT 10"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_dafor_data():
    query = "SELECT Dafor_id, Locality_id, Dafor_coords, Date, Horizontal_visibility, Bathymetric_zone, Method, Dafor_value FROM data_coralsol_dafor"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

base_url = "http://coralsol-api.kinghost.net/api"

# --- Sidebar Widgets ---
def render_sidebar():
    with st.sidebar:
        start_date = st.date_input('Data Inicial', datetime.date(2012, 1, 1))
        end_date = st.date_input('Data Final', datetime.date.today() + datetime.timedelta(days=1))

        indicator = st.radio("Indicadores", ["Transectos com Coral-sol", "Esforço de Monitoramento"])
        show_transects_suncoral = indicator == "Transectos com Coral-sol"
        show_effort = indicator == "Esforço de Monitoramento"

    return start_date, end_date, show_transects_suncoral, show_effort

# --- Legend Template ---

# Create the legend template as an HTML element
legend_template = """
{% macro html(this, kwargs) %}
<div id='maplegend' class='maplegend' 
    style='position: absolute; z-index: 9999; background-color: rgba(255, 255, 255, 0.5);
     border-radius: 6px; padding: 10px; font-size: 10.5px; right: 20px; top: 20px;'>     
<div class='legend-scale'>
  <ul class='legend-labels'>
    <li><span style='background: green; opacity: 0.75;'></span>Wind speed <= 55.21</li>
    <li><span style='background: yellow; opacity: 0.75;'></span>55.65 <= Wind speed <= 64.29</li>
    <li><span style='background: orange; opacity: 0.75;'></span>64.50 <= Wind speed <= 75.76</li>
    <li><span style='background: red; opacity: 0.75;'></span>75.90 <= Wind speed <= 90.56</li>
    <li><span style='background: purple; opacity: 0.75;'></span>Wind speed >= 91.07</li>
  </ul>
</div>
</div> 
<style type='text/css'>
  .maplegend .legend-scale ul {margin: 0; padding: 0; color: #0f0f0f;}
  .maplegend .legend-scale ul li {list-style: none; line-height: 18px; margin-bottom: 1.5px;}
  .maplegend ul.legend-labels li span {float: left; height: 16px; width: 16px; margin-right: 4.5px;}
</style>
{% endmacro %}
"""


# --- Persist Map State ---
def get_map():
    """Creates a folium map while preserving zoom and center."""
    if "map_center" not in st.session_state:
        st.session_state.map_center = [-27.281798, -48.366133]
    if "map_zoom" not in st.session_state:
        st.session_state.map_zoom = 13
    if "map_key" not in st.session_state:
        st.session_state.map_key = 0  # 🔥 Forces re-render when changed

    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom,
        tiles="https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2lsdmVpcmF0Y2wiLCJhIjoiY202MTRrN3N5MGt3MDJqb2xhc3R0empqZCJ9.YfjBqq5HbnacUNw9Tyiaew",
        attr="Mapbox attribution",
        max_zoom=20,
        min_zoom=1
    )
    Fullscreen().add_to(m)

    return m

# --- Update Layers Without Resetting Map ---
def render_map(m, start_date, end_date, show_transects_suncoral, show_effort):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    merged_data = pd.DataFrame()  # Initialize an empty DataFrame for merged_data
    merged_data_effort = pd.DataFrame()  # Initialize an empty DataFrame for merged_data_effort
   
    if show_transects_suncoral:
        layer = folium.FeatureGroup(name="Transectos com Coral-sol").add_to(m)

        locality_data = get_locality_data()
        locality_data['date'] = pd.to_datetime(locality_data['date'], errors='coerce', dayfirst=True)

        filtered_locality_data = locality_data[
            (locality_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (locality_data['date'] <= pd.to_datetime(end_date_str, errors='coerce'))
        ]

        dafor_data = get_dafor_data()
        dafor_data['date'] = pd.to_datetime(dafor_data['date'], errors='coerce', dayfirst=True)

        # Convert `dafor_value` to a list of numbers, handling errors
        dafor_data['dafor_value'] = dafor_data['dafor_value'].apply(lambda x: 
            [pd.to_numeric(i, errors='coerce') for i in str(x).split(',')]
        )

        dafor_data = dafor_data.explode('dafor_value')

        # Convert `dafor_value` column again to numeric
        dafor_data['dafor_value'] = pd.to_numeric(dafor_data['dafor_value'], errors='coerce')

        # Filter out NaN values after conversion
        filtered_dafor_data = dafor_data[
            (dafor_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (dafor_data['date'] <= pd.to_datetime(end_date_str, errors='coerce')) &
            (dafor_data['dafor_value'].notna())  # Remove NaNs
        ]

        dafor_counts = filtered_dafor_data[filtered_dafor_data['dafor_value'] > 0].groupby('locality_id').size().reset_index(name='dafor_count')

        # Merge filtered_locality_data with dafor_counts to include 'name' and other locality data
        merged_data = filtered_locality_data.merge(dafor_counts, on='locality_id', how='left').fillna({'dafor_count': 0})

        for _, row in merged_data.iterrows():
            try:
                coords_str = row['coords_local']
                try:
                    coords_local = ast.literal_eval(coords_str)
                except (ValueError, SyntaxError) as e:
                    st.error(f"Error parsing coordinates for Locality ID {row['locality_id']}: {e}")
                    continue

                if isinstance(coords_local, list) and len(coords_local) > 0:
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
                        popup=(
                            f"<b>Locality:</b> {row['locality_id']}<br>"
                            f"<b>Name:</b> {row['name']}<br>"
                            f"<b>Date:</b> {row['date']}<br>"
                            f"<b>Dafor Count:</b> {dafor_count}"
                        ),
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(layer)
                else:
                    st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {coords_local}")
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")
        # Add the legend to the map
            macro = MacroElement()
            macro._template = Template(legend_template)
            m.get_root().add_child(macro)
        

    if show_effort:
        layer = folium.FeatureGroup(name="Esforço de Monitoramento").add_to(m)

        locality_data = get_locality_data()
        locality_data['date'] = pd.to_datetime(locality_data['date'], errors='coerce', dayfirst=True)

        filtered_locality_data = locality_data[
            (locality_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (locality_data['date'] <= pd.to_datetime(end_date_str, errors='coerce'))
        ]

        dafor_data = get_dafor_data()
        dafor_data['date'] = pd.to_datetime(dafor_data['date'], errors='coerce', dayfirst=True)

        # Convert `dafor_value` to a list of numbers, handling errors
        dafor_data['dafor_value'] = dafor_data['dafor_value'].apply(lambda x: 
            [pd.to_numeric(i, errors='coerce') for i in str(x).split(',')]
        )

        dafor_data = dafor_data.explode('dafor_value')

        # Convert `dafor_value` column again to numeric
        dafor_data['dafor_value'] = pd.to_numeric(dafor_data['dafor_value'], errors='coerce')

        # Filter out NaN values after conversion
        filtered_dafor_data = dafor_data[
            (dafor_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (dafor_data['date'] <= pd.to_datetime(end_date_str, errors='coerce')) &
            (dafor_data['dafor_value'].notna())  # Remove NaNs
        ]

        dafor_counts_effort = filtered_dafor_data[filtered_dafor_data['dafor_value'] >= 0].groupby('locality_id').size().reset_index(name='dafor_count')

        # Merge filtered_locality_data with dafor_counts_effort to include 'name' and other locality data
        merged_data_effort = filtered_locality_data.merge(dafor_counts_effort, on='locality_id', how='left').fillna({'dafor_count': 0})

        for _, row in merged_data_effort.iterrows():
            try:
                coords_str = row['coords_local']
                try:
                    coords_local = ast.literal_eval(coords_str)
                except (ValueError, SyntaxError) as e:
                    st.error(f"Error parsing coordinates for Locality ID {row['locality_id']}: {e}")
                    continue

                if isinstance(coords_local, list) and len(coords_local) > 0:
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
                        popup=(
                            f"<b>Locality:</b> {row['locality_id']}<br>"
                            f"<b>Name:</b> {row['name']}<br>"
                            f"<b>Date:</b> {row['date']}<br>"
                            f"<b>Dafor Count:</b> {dafor_count}"
                        ),
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(layer)
                else:
                    st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {coords_local}")
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")

    return m, merged_data, merged_data_effort  # Return the map and merged_data


# --- Main Logic ---
def main():
    start_date, end_date, show_transects_suncoral, show_effort = render_sidebar()
   
    # Load or create the map
    m = get_map()
    m, merged_data, merged_data_effort = render_map(m, start_date, end_date, show_transects_suncoral, show_effort)
    
    # Capture the previous zoom & center
    prev_zoom = st.session_state.map_zoom
    prev_center = st.session_state.map_center

    # ✅ Temporary storage for zoom & center
    if "temp_map_zoom" not in st.session_state:
        st.session_state.temp_map_zoom = st.session_state.map_zoom
    if "temp_map_center" not in st.session_state:
        st.session_state.temp_map_center = st.session_state.map_center

    # Create two columns
    col1, col2 = st.columns([2, 1], gap="medium")

    with col1:
        # Display the map but DO NOT update zoom yet
        st.write("### Indicadores do Monitoramento")
        st_data = st_folium(
            m,
            width="100%",
            height=700,
            returned_objects=["center", "zoom"],
            key=st.session_state["map_key"],  # 🔥 Forces reloading when changed
        )

        # Debugging info
        #st.write(f"Debug: Before update -> Zoom: {prev_zoom}, Center: {prev_center}")
        #st.write(f"Debug: st_folium returned -> {st_data}")

        # Only store zoom & center TEMPORARILY
        if st_data:
            if "center" in st_data and st_data["center"]:
                st.session_state.temp_map_center = [st_data["center"]["lat"], st_data["center"]["lng"]]
            if "zoom" in st_data and st_data["zoom"]:
                st.session_state.temp_map_zoom = st_data["zoom"]

        # ✅ Add a button to apply zoom & center updates
        if st.button("Update Map View"):
            if (
                st.session_state.temp_map_zoom != prev_zoom or
                st.session_state.temp_map_center != prev_center
            ):
                st.session_state.map_zoom = st.session_state.temp_map_zoom
                st.session_state.map_center = st.session_state.temp_map_center
                st.session_state["map_key"] += 1  # 🔥 Forces full re-render
                st.write(f"Debug: Applied map updates, new key = {st.session_state['map_key']}")

    with col2:
        if show_transects_suncoral:
            # Sort merged_data by dafor_count in descending order and select 'name' and 'dafor_count' columns
            sorted_merged_data = merged_data[['name', 'dafor_count']].sort_values(by='dafor_count', ascending=False).rename(columns={'name': 'Localidade', 'dafor_count': 'N. Detecções'})
            # Add 'id' column name
            sorted_merged_data.index.name = 'id'

            # Display the sorted table
            st.write("### Número de Transectos com Coral-sol")
            st.dataframe(sorted_merged_data)

        if show_effort:
            # Sort merged_data_effort by dafor_count in descending order and select 'name' and 'dafor_count' columns
            sorted_merged_data_effort = merged_data_effort[['name', 'dafor_count']].sort_values(by='dafor_count', ascending=False).rename(columns={'name': 'Localidade', 'dafor_count': 'Esforço (minutos)'})
            # Add 'id' column name
            sorted_merged_data_effort.index.name = 'id'

            # Display the sorted table
            st.write("### Esforço de Monitoramento")
            st.dataframe(sorted_merged_data_effort)

if __name__ == "__main__":
    main()