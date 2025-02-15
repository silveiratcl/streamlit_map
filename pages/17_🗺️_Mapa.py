import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast
import datetime
from folium.plugins import MarkerCluster, Fullscreen
import requests

# --- Page Configuration ---
st.set_page_config(page_title="Mapa_17", page_icon="🗺️", layout="wide")
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
    except KeyError as e:
        st.error(f"KeyError: {e}. Check your secrets.toml structure or Streamlit Cloud settings.")
        raise
    except Exception as e:
        st.error(f"An error occurred while connecting to the database: {e}")
        raise

conn = init_connection()

# --- Data Fetching Functions ---
@st.cache_data
def get_management_data():
    query = "SELECT management_id, Management_coords, Observer, Managed_mass_kg, Date FROM data_coralsol_management"
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

# Base URL test DB
base_url = "http://coralsol-api.kinghost.net/api"

# --- Sidebar Widgets ---

def render_sidebar():
    with st.sidebar:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        start_date = st.date_input('Data Inicial', datetime.date(2012, 1, 1))
        end_date = st.date_input('Data Final', tomorrow)
        if start_date < end_date:
            st.success(f'Start date: {start_date} \nEnd date: {end_date}')
        else:
            st.error('Error: Data Final deve ser após a Data inicial.')

        with st.expander("Indicadores", expanded=True):
            show_transects_suncoral = st.checkbox("Transectos com Coral-sol", value=True)

        with st.expander("Camadas", expanded=False):
            show_management = st.checkbox("Manejos", value=False)
            show_locality = st.checkbox("Localidades", value=False)
            show_occ = st.checkbox("Ocorrências", value=False)
            show_dafor = st.checkbox("Monitoramento", value=False)

    return start_date, end_date, show_transects_suncoral, show_management, show_locality, show_occ, show_dafor

# --- Map Rendering ---
# --- Map Rendering ---
@st.fragment
def render_map(start_date, end_date, show_transects_suncoral, show_management, show_locality, show_occ, show_dafor):
    # ✅ 1. Initialize session state only if not set
    if "map_center" not in st.session_state:
        st.session_state.map_center = [-27.281798, -48.366133]  # Default center
    if "map_zoom" not in st.session_state:
        st.session_state.map_zoom = 13  # Default zoom level
    if "map_updated" not in st.session_state:
        st.session_state.map_updated = False  # Prevent unnecessary reruns

    # ✅ 2. Preserve zoom & center between reruns
    current_zoom = st.session_state.map_zoom
    current_center = st.session_state.map_center

    # Debugging: Show stored zoom before rendering
    st.write(f"Debug: Stored Zoom Before Map Render = {current_zoom}")

    # ✅ 3. Create the Folium map with stored zoom
    m = folium.Map(
        location=current_center,
        zoom_start=current_zoom,  # ✅ Use stored zoom
        tiles="https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2lsdmVpcmF0Y2wiLCJhIjoiY202MTRrN3N5MGt3MDJqb2xhc3R0empqZCJ9.YfjBqq5HbnacUNw9Tyiaew",
        attr="Mapbox attribution",
        max_zoom=20,
        min_zoom=1
    )
    Fullscreen().add_to(m)

    # Convert dates to DD/MM/YYYY for comparison
    start_date_str = start_date.strftime('%d/%m/%Y')
    end_date_str = end_date.strftime('%d/%m/%Y')

    # Display management if selected
    if show_management:
        data = get_management_data()
        data['date'] = data['date'].astype(str)
        filtered_data = data[
            (pd.to_datetime(data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
            (pd.to_datetime(data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
        ]
        marker_cluster = MarkerCluster(disableClusteringAtZoom=10).add_to(m)
        for index, row in filtered_data.iterrows():
            try:
                coords_str = row['management_coords']
                spot_coords = ast.literal_eval(coords_str)
                if isinstance(spot_coords, list) and len(spot_coords) > 0:
                    lat, lon = spot_coords[0]
                    folium.Marker(
                        [lat, lon],
                        popup=f"Observer: {row['observer']}, Date: {row['date']}, Mass(kg): {row['managed_mass_kg']}",
                        tooltip=f"Management {row['management_id']}"
                    ).add_to(marker_cluster)
            except Exception as e:
                st.error(f"Error adding marker for Management ID {row['management_id']}: {e}")

    # Display locality if selected
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

    # Display occurrences if selected
    if show_occ:
        data = get_occ_data()
        if data is None or data.empty:
            st.warning("No occurrence data found matching the criteria.")
        else:
            data['date'] = data['date'].astype(str)
            filtered_data = data[
                (pd.to_datetime(data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
                (pd.to_datetime(data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
            ]
            occurrence_layer = folium.FeatureGroup(name="Ocorrências").add_to(m)
            marker_cluster = MarkerCluster(disableClusteringAtZoom=5).add_to(occurrence_layer)
            for index, row in filtered_data.iterrows():
                try:
                    coords_str = row['spot_coords']
                    spot_coords = ast.literal_eval(coords_str)
                    if isinstance(spot_coords, list) and len(spot_coords) > 0:
                        lat, lon = spot_coords[0]
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
                except Exception as e:
                    st.error(f"Error adding marker for Occurrence ID {row['occurrence_id']}: {e}")

    # Display dafor if selected
    if show_dafor:
        data = get_dafor_data()
        data['date'] = data['date'].astype(str)
        filtered_data = data[
            (pd.to_datetime(data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
            (pd.to_datetime(data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
        ]
        dafor_layer = folium.FeatureGroup(name="Monitoramento").add_to(m)
        for index, row in filtered_data.iterrows():
            try:
                coords_str = row['dafor_coords']
                dafor_coords = ast.literal_eval(coords_str)
                if isinstance(dafor_coords, list) and len(dafor_coords) > 0:
                    folium.PolyLine(
                        dafor_coords,
                        popup=f"Locality: {row['locality_id']}, Date: {row['date']}",
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(dafor_layer)
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['dafor_id']}: {e}")
    
    
    ### Indicadores ###
    if show_transects_suncoral:
        st.write("Debug: Transectos com Coral-sol checkbox is checked.")
        locality_data = get_locality_data()
        locality_data['date'] = locality_data['date'].astype(str)
        filtered_locality_data = locality_data[
            (pd.to_datetime(locality_data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
            (pd.to_datetime(locality_data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
        ]
        st.write("Debug: Filtered locality data", filtered_locality_data)
        dafor_data = get_dafor_data()
        dafor_data['date'] = dafor_data['date'].astype(str)
        dafor_data['dafor_value'] = dafor_data['dafor_value'].apply(lambda x: [pd.to_numeric(i, errors='coerce') for i in str(x).split(',')])
        dafor_data = dafor_data.explode('dafor_value')
        filtered_dafor_data = dafor_data[
            (pd.to_datetime(dafor_data['date'], format='%d/%m/%Y') >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
            (pd.to_datetime(dafor_data['date'], format='%d/%m/%Y') <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
        ]
        st.write("Debug: Filtered Dafor data", filtered_dafor_data)
        dafor_counts = filtered_dafor_data[filtered_dafor_data['dafor_value'] > 0].groupby('locality_id').size().reset_index(name='dafor_count')
        st.write("Debug: Dafor counts", dafor_counts)
        merged_data = filtered_locality_data.merge(dafor_counts, on='locality_id', how='left').fillna({'dafor_count': 0})
        st.write("Debug: Merged data", merged_data)
        for index, row in merged_data.iterrows():
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
                            f"Locality: {row['locality_id']}<br>"
                            f"Name: {row['name']}<br>"
                            f"Date: {row['date']}<br>"
                            f"Dafor Count: {dafor_count}"
                        ),
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(m)
                else:
                    st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {coords_local}")
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")
            

  # ✅ 4. Render the map with folium
    st_data = st_folium(
        m,
        width="100%",
        height=600,
        returned_objects=["center", "zoom"]
    )

    # ✅ 5. Debugging: Print returned map state
    st.write(f"Debug: st_folium returned - {st_data}")

    # ✅ 6. Only update session state if values have changed
    rerun_needed = False

    if st_data:
        new_zoom = st_data.get("zoom", current_zoom)
        new_center = st_data.get("center", {"lat": current_center[0], "lng": current_center[1]})

        # ✅ If zoom changed, update session state but only rerun once
        if new_zoom != current_zoom:
            st.session_state.map_zoom = new_zoom
            if not st.session_state.map_updated:
                st.session_state.map_updated = True
                rerun_needed = True
            st.write(f"Debug: Updating Zoom to {new_zoom}")

        # ✅ If center changed, update session state
        if [new_center["lat"], new_center["lng"]] != current_center:
            st.session_state.map_center = [new_center["lat"], new_center["lng"]]
            if not st.session_state.map_updated:
                st.session_state.map_updated = True
                rerun_needed = True
            st.write(f"Debug: Updating Center to {st.session_state.map_center}")

    # ✅ 7. Prevent infinite reruns
    if rerun_needed:
        st.session_state.map_updated = False  # Reset update flag
        st.rerun()  # 🔥 Force rerun only when needed

# --- Main App Logic ---
def main():
    start_date, end_date, show_transects_suncoral, show_management, show_locality, show_occ, show_dafor = render_sidebar()
    render_map(start_date, end_date, show_transects_suncoral, show_management, show_locality, show_occ, show_dafor)

if __name__ == "__main__":
    main()