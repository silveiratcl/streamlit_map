import streamlit as st

st.set_page_config(page_title="Sobre", page_icon="📃")
st.logo('./assets/logo_horiz.png', size="large")

st.markdown(

"""    
## Overview
A dashboard is an incredibly valuable tool that empowers users to effortlessly 
visualize and make sense of complex data. By acting as a centralized hub, it presents
a wealth of essential metrics, trends, and insights in a visually captivating format. 
This makes it an ideal solution for environmental agencies seeking to acquire valuable
resources for the Early Detection - Quick Response (EDQR) of invasive species. In this
documentation, we will explore the pivotal components of data interpretation in the Sun 
Coral Monitoring Dashboard - PACS REBIO Arvoredo. 



## Monitoring Protocol
### Spatial reference
The monitoring data is obtained in localities, in the locality is defined a segment, and in the extension of a segment are obtained information linked to 1 minute transects recorded by the divers.

"""
)

st.image('./assets/about_local.png', caption='teste paste pic')




st.markdown(
"""    
### Active search
Snorkelling - Floatation In the depth range of zero to 2 meters of the sampling segment, monitoring will be carried out by a snorkelling diver. The diver will search within this depth range, covering the sampling segment and looking for possible occurrences of sun coral.
Autonomous Diving The active search technique for sun coral colonies will be employed in each sampling segment. Autonomous diving samples will be conducted by two pairs of divers. The operational area for each pair will be determined by depth ranges (e.g., from 0 to 8m and from 9 to 15m) along the rocky shore, aiming to cover the greatest vertical extension possible. The division of scanning depths between the pairs may vary depending on the bathymetric characteristics of each sampling segment.
Monitoring
Monitoring

### DAFOR
To classify the invasion levels in the sampled segments, we utilize a semi-quantitative scale of abundance known as the DAFOR scale (Sutherland, 2006), specifically adapted for assessing the abundance of sun coral (Creed & Fleury, 2009). The scale assigns values to each relative abundance class, which are described as follows:

Dominant: This category represents highly evident populations that form predominantly monospecific patches of at least 1m². These patches contain numerous isolated colonies and/or smaller patches scattered throughout the substrate.
Abundant: Clusters within this category form essentially monospecific patches ranging from 50 to 100 cm in diameter. Similar to the dominant category, isolated colonies and/or small scattered patches can be observed throughout the substrate.
Frequent: This class includes isolated colonies and/or small patches ranging from 10 to 50 cm in diameter, scattered across the substrate.
Occasional: Here, we have less than 10 colonies or small patches smaller than 10 cm in diameter, but with more than 5 scattered colonies throughout the substrate.
Rare: This category encompasses instances where between 1 and 5 colonies are sparsely scattered throughout the substrate.
Absent: In this class, no records of sun coral occurrences are found.
During the assessment process, divers move along transects delimited by 1 minute of sampling. Observations made on the DAFOR scale are then converted to a relative abundance index (RAI) using the following classification: 10 - dominant, 8 - abundant, 6 - frequent, 4 - occasional, 2 - rare; zero - absent.


## Data displayed on Map

### Indicators

Transects with Sun Coral (TWSC): Number of sun coral transects within the locality limits. This metric compensates for the low relative abundances assessed by DAFOR. Selecting a date controls the displayed data period on the map.
Habitat Suitability Index (HSI): Average HSI value calculated for the locality. Selecting a date controls the displayed data period on the map.
TWSC/1000m: Number of sun coral transects within the locality limits per 1000 meters of monitoring effort. Selecting a date controls the displayed data period on the map.
Number of Transects by Locality (NTL): Number of transects within the locality. Selecting a date controls the displayed data period on the map
Days since the last management: Computes days elapsed since last management.
Days since the last check: Computes days elapsed since last check.
Layers
Occurrence: Historical records of sun coral occurrences within REBIO Arvoredo Limits. The data is despaired with TWSC once the data using the DAFOR protocol started to be gathered in January/2023. Selecting a date controls the displayed data period on the map.
DAFOR: Raw data recorded during monitoring. Selecting a date controls the displayed data period on the map.
Geomorphology: Raw data recorded during monitoring. Selecting a date controls the displayed data period on the map.
Target Location: Locations in the PACS Arvoredo project.
Locality: Limits and nomenclature of the localities within REBIO Arvoredo.
REBIO Limits: Limits of the REBIO Arvoredo Conservation Unit.
Infoboxes
Monitored location: Number of localities monitored at REBIO and surroundings.

Number of segments: The segment is a line representing where the divers did the monitoring protocol, this box shows the count.

Transects with sun coral: Transect is part of segment obtained in one minute of active search. Here is showed the count of segments positive for sun coral occurrence.

Dive Time: Sun of dive time by all pair of divers in the monitoring data.



### References and useful links

CREED, J.C.; FLEURY, B.G. 2009. Monitoramento extensivo de coral-sol (Tubastraea coccinea e T. tagusensis): protocolo de semi-quantificação. Projeto Coral-Sol, Instituto Biodiversidade Marinha, Rio de Janeiro. p 1.

CREED JC; JUNQUEIRA ADOR, FLEURY BG, MANTELLATO MC, OIGMAN-PSZCZOL SS. 2017. The Sun-Coral Project: the first social-environmental initiative to manage the biological invasion of Tubastraea spp. in Brazil. Management of Biological Invasions 8(2): 181.

CREED JC, FENNER D, SAMMARCO P, CAIRNS S, CAPEL K., JUNQUEIRA AO, CRUZ I, MIRANDA RJ, CARLOS-JUNIORL, MANTELLATO MC, OIGMAN-PSZCZOL, S. 2017. The invasion of the azooxanthellate coral Tubastraea (Scleractinia: Dendrophylliidae) throughout the world: history, pathways and vectors. Biological Invasions 19: 283-305.

CRISP, DJ; SOUTHWARD, AJ. 1958. The distribution of intertidal organisms along the coasts of the English Channel. Journal of the Marine Biological Association UK 37: 157-208.

GRAINGER, S.; MAO, F.; BUYTAERT, W. 2016. Environmental data visualisation for non-scientific contexts: Literature review and design framework. Environmental Modelling & Software, 85, 299-318.

SILVEIRA, T.C.L.; CARVALHAL, A.; SEGAL, B. 2023. Protocolo Técnico de monitoramento de coral-sol na REBIO Arvoredo e entorno. In: Protocolos Técnicos de Campo. PACS Arvoredo. Projeto PACS Arvoredo. Florianópolis, 56 p.

SUTHERLAND, W. J. (Ed.). 2006. Ecological census techniques: a handbook. Cambridge university press.
"""
)