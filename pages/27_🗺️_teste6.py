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
st.set_page_config(page_title="Mapa", page_icon="🗺️", layout="wide")
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

        with st.expander("Indicadores", expanded=True):
            show_transects_suncoral = st.checkbox("Transectos com Coral-sol", value=True)


        with st.expander("Camadas", expanded=True):
            show_management = st.checkbox("Manejos", value=st.session_state.get("show_management", False), key="show_management")
            show_locality = st.checkbox("Localidades", value=st.session_state.get("show_locality", False), key="show_locality")
            show_occ = st.checkbox("Ocorrências", value=st.session_state.get("show_occ", False), key="show_occ")
            show_dafor = st.checkbox("Monitoramento", value=st.session_state.get("show_dafor", False), key="show_dafor")


    return start_date, end_date, show_management, show_locality, show_occ, show_dafor, show_transects_suncoral

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
def render_map(m, start_date, end_date, show_management, show_locality, show_occ, show_dafor, show_transects_suncoral):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # --- Indicadores ---
    if show_transects_suncoral:
       
        layer = folium.FeatureGroup(name="Transectos com Coral-sol").add_to(m)
       
        st.write("Debug: Transectos com Coral-sol checkbox is checked.")
        locality_data = get_locality_data()
        locality_data['date'] = pd.to_datetime(locality_data['date']).dt.strftime('%Y-%m-%d')
        filtered_locality_data = locality_data[(locality_data['date'] >= start_date_str) & (locality_data['date'] <= end_date_str)]
        st.write("Debug: Filtered locality data", filtered_locality_data)
        
        dafor_data = get_dafor_data()
        dafor_data['date'] = pd.to_datetime(dafor_data['date']).dt.strftime('%Y-%m-%d')
        
        filtered_dafor_data = dafor_data[(dafor_data['date'] >= start_date_str) & (dafor_data['date'] <= end_date_str)]
        st.write("Debug: Filtered Dafor data", filtered_dafor_data)
        
        dafor_counts = filtered_dafor_data[filtered_dafor_data['dafor_value'] > 0].groupby('locality_id').size().reset_index(name='dafor_count')
        st.write("Debug: Dafor counts", dafor_counts)
        merged_data = filtered_locality_data.merge(dafor_counts, on='locality_id', how='left').fillna({'dafor_count': 0})
        st.write("Debug: Merged data", merged_data)
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
                            f"Locality: {row['locality_id']}<br>"
                            f"Name: {row['name']}<br>"
                            f"Date: {row['date']}<br>"
                            f"Dafor Count: {dafor_count}"
                        ),
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(layer)
                else:
                    st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {coords_local}")
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")
    

    #chargpt solution
# if show_transects_suncoral:
       
#     layer = folium.FeatureGroup(name="Transectos com Coral-sol").add_to(m)
   
#     st.write("Debug: Transectos com Coral-sol checkbox is checked.")
#     locality_data = get_locality_data()
#     locality_data['date'] = pd.to_datetime(locality_data['date']).dt.strftime('%Y-%m-%d')
#     filtered_locality_data = locality_data[(locality_data['date'] >= start_date_str) & (locality_data['date'] <= end_date_str)]
#     st.write("Debug: Filtered locality data", filtered_locality_data)
    
#     dafor_data = get_dafor_data()
#     dafor_data['date'] = pd.to_datetime(dafor_data['date']).dt.strftime('%Y-%m-%d')
    
#     # ✅ Convert 'dafor_value' to numeric, handling non-numeric values
#     dafor_data['dafor_value'] = pd.to_numeric(dafor_data['dafor_value'], errors='coerce')

#     # ✅ Ensure we filter out NaN values after conversion
#     filtered_dafor_data = dafor_data[
#         (dafor_data['date'] >= start_date_str) & 
#         (dafor_data['date'] <= end_date_str) & 
#         (dafor_data['dafor_value'].notna())  # Exclude NaN values
#     ]

#     st.write("Debug: Filtered Dafor data", filtered_dafor_data)
    
#     # ✅ Now, numeric comparisons are valid
#     dafor_counts = filtered_dafor_data[filtered_dafor_data['dafor_value'] > 0].groupby('locality_id').size().reset_index(name='dafor_count')
#     st.write("Debug: Dafor counts", dafor_counts)
    
#     merged_data = filtered_locality_data.merge(dafor_counts, on='locality_id', how='left').fillna({'dafor_count': 0})
#     st.write("Debug: Merged data", merged_data)
    
#     for _, row in merged_data.iterrows():
#         try:
#             coords_str = row['coords_local']
#             try:
#                 coords_local = ast.literal_eval(coords_str)
#             except (ValueError, SyntaxError) as e:
#                 st.error(f"Error parsing coordinates for Locality ID {row['locality_id']}: {e}")
#                 continue
            
#             if isinstance(coords_local, list) and len(coords_local) > 0:
#                 dafor_count = row['dafor_count']
#                 if dafor_count > 10:
#                     color = 'red'
#                 elif dafor_count > 5:
#                     color = 'orange'
#                 else:
#                     color = 'green'
                    
#                 folium.PolyLine(
#                     coords_local,
#                     color=color,
#                     popup=(
#                         f"Locality: {row['locality_id']}<br>"
#                         f"Name: {row['name']}<br>"
#                         f"Date: {row['date']}<br>"
#                         f"Dafor Count: {dafor_count}"
#                     ),
#                     tooltip=f"Locality {row['locality_id']}"
#                 ).add_to(layer)
#             else:
#                 st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {coords_local}")
#         except Exception as e:
#             st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")






    # --- Camadas ---
    if show_management:
        data = get_management_data()
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
        filtered_data = data[(data['date'] >= start_date_str) & (data['date'] <= end_date_str)]

        marker_cluster = MarkerCluster().add_to(m)
        for _, row in filtered_data.iterrows():
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
                st.error(f"Error adding marker: {e}")


    if show_locality:
        layer = folium.FeatureGroup(name="Localidades").add_to(m)
        data = get_locality_data()
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
        filtered_data = data[(data['date'] >= start_date_str) & (data['date'] <= end_date_str)]

        for _, row in filtered_data.iterrows():
            try:
                coords_str = row['coords_local']
                locality_coords = ast.literal_eval(coords_str)
                if isinstance(locality_coords, list) and len(locality_coords) > 0:
                    folium.PolyLine(
                        locality_coords,
                        popup=f"Locality: {row['name']}, Date: {row['date']}",
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(layer)
                else:
                    st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {locality_coords}")
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")
    

    if show_occ:
        marker_cluster = MarkerCluster(disableClusteringAtZoom=5).add_to(m)
        data = get_occ_data()
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
        filtered_data = data[(data['date'] >= start_date_str) & (data['date'] <= end_date_str)]

        for _, row in filtered_data.iterrows():
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

    if show_dafor:
        layer = folium.FeatureGroup(name="Monitoramento").add_to(m)
        data = get_dafor_data()
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
        filtered_data = data[(data['date'] >= start_date_str) & (data['date'] <= end_date_str)]

        for _, row in filtered_data.iterrows():
            try:
                coords_str = row['dafor_coords']
                dafor_coords = ast.literal_eval(coords_str)
                if isinstance(dafor_coords, list) and len(dafor_coords) > 0:
                    folium.PolyLine(
                        dafor_coords,
                        popup=f"Locality: {row['locality_id']}, Date: {row['date']}",
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(layer)
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['dafor_id']}: {e}")

    return m
# --- Main Logic ---
def main():
    start_date, end_date, show_management, show_locality, show_occ, show_dafor, show_transects_suncoral = render_sidebar()

    # Load or create the map
    m = get_map()
    m = render_map(m, start_date, end_date, show_management, show_locality, show_occ, show_dafor, show_transects_suncoral)

    # Capture the previous zoom & center
    prev_zoom = st.session_state.map_zoom
    prev_center = st.session_state.map_center

    # ✅ Temporary storage for zoom & center
    if "temp_map_zoom" not in st.session_state:
        st.session_state.temp_map_zoom = st.session_state.map_zoom
    if "temp_map_center" not in st.session_state:
        st.session_state.temp_map_center = st.session_state.map_center

    # Display the map but DO NOT update zoom yet
    st_data = st_folium(
        m,
        width="100%",
        height= 700,
        returned_objects=["center", "zoom"],
        key=st.session_state["map_key"],  # 🔥 Forces reloading when changed
    )

    # Debugging info
    st.write(f"Debug: Before update -> Zoom: {prev_zoom}, Center: {prev_center}")
    st.write(f"Debug: st_folium returned -> {st_data}")

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

if __name__ == "__main__":
    main()
