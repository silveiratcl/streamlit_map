import folium
import datetime
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import numpy as np


st.set_page_config(page_title="Plotting Demo", page_icon="🗺️")




today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
start_date = st.sidebar.date_input('Data Inicial', datetime.date(2012,1,1))
end_date = st.sidebar.date_input('Data Final', tomorrow)
if start_date < end_date:
    st.sidebar.success('Start date: `%s`\n\nEnd date:`%s`' % (start_date, end_date))
else:
    st.sidebar.error('Error: Data Final deve ser após a Data inicial.')


add_check_box = st.sidebar.radio("**Camadas**", ["Dias transcorridos desde o último monitoaramento",
                                                  "Detecções por hora", 
                                                  "Dias desde o último manejo ",
                                                  "Manejos"])




m = folium.Map(location=[-27.28878,-48.36812],
               zoom_start=12,
               tiles = "Esri.WorldImagery",
               width=1200,
               height=700,
               )
folium.Marker([-27.28878,-48.36812],
              popup="Teste", tooltip="Teste"
              ).add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(m, width=700)


