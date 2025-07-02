import pandas as pd
import geopandas as gpd
import streamlit as st
from streamlit_folium import folium_static
import folium
from folium import GeoJson
import matplotlib.pyplot as plt
import numpy as np

csv_file_path = 'data.csv'
csv_data = pd.read_csv(csv_file_path)

geojson_file_path = 'up_districts.geojson'
geojson_data = gpd.read_file(geojson_file_path)

csv_data['District'] = csv_data['District'].str.lower().str.strip()
geojson_data['district'] = geojson_data['district'].str.lower().str.strip()

hazard_columns = csv_data.columns[2:]
selected_hazard = st.selectbox('Select Hazard Type', hazard_columns)

filtered_data = csv_data[['District', selected_hazard]].copy()
filtered_data.rename(columns={selected_hazard: 'Deaths'}, inplace=True)

merged_data = geojson_data.merge(filtered_data, left_on='district', right_on='District', how='left')

merged_data['Deaths'] = merged_data['Deaths'].fillna(0)

m = folium.Map(location=[merged_data.geometry.centroid.y.mean(), merged_data.geometry.centroid.x.mean()], zoom_start=7)

def color_scale(deaths):
    if deaths == 0:
        return '#CFBD99'
    elif deaths <= 20:
        return '#FFFF00'
    elif deaths <= 40:
        return '#FFA500'
    elif deaths <= 60:
        return '#FF0000'
    elif deaths <= 80:
        return '#800000'
    else:
        return '#0000FF'

GeoJson(
    merged_data,
    style_function=lambda feature: {
        'fillColor': color_scale(feature['properties']['Deaths']),
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.7,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['district', 'Deaths'],
        aliases=['District:', 'Deaths:'],
        localize=True,
        sticky=True
    )
).add_to(m)

legend_html = """
     <div style="position: fixed; 
     bottom: 50px; left: 50px; width: 150px; height: 150px; 
     border:2px solid grey; z-index:9999; font-size:14px;
     background-color:white; padding: 10px;">
     <strong>Legend</strong><br>
     <i style="background:#040273; width:18px; height:18px; float:left; margin-right:8px;"></i> 80+ Deaths<br
     <i style="background:#800000; width:18px; height:18px; float:left; margin-right:8px;"></i> 61-80 Deaths<br>
     <i style="background:#FF0000; width:18px; height:18px; float:left; margin-right:8px;"></i> 41-60 Deaths<br>
     <i style="background:#FFA500; width:18px; height:18px; float:left; margin-right:8px;"></i> 21-40 Deaths<br>
     <i style="background:#FFFF00; width:18px; height:18px; float:left; margin-right:8px;"></i> 1-20 Deaths<br>
     <i style="background:#CFBD99; width:18px; height:18px; float:left; margin-right:8px;"></i> 0 Deaths<br>
     </div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

st.title(f'District-Wise Deaths from 2018-19 till 2023-24 for {selected_hazard}')
folium_static(m)

st.subheader('Color Scale Used in the Map')
st.markdown("""
- <span style="color: #040273;">**Blue**</span>: 81+ Deaths
- <span style="color: #800000;">**Maroon**</span>: 61-80 Deaths
- <span style="color: #FF0000;">**Red**</span>: 41-60 Deaths
- <span style="color: #FFA500;">**Orange**</span>: 21-40 Deaths
- <span style="color: #FFFF00;">**Yellow**</span>: 1-20 Deaths
- <span style="color: #CFBD99;">**Pale Cream**</span>: 0 Deaths
""", unsafe_allow_html=True)

st.subheader("Overall Percentage Contribution of Each Hazard")

total_deaths_per_hazard = csv_data[hazard_columns].sum()

threshold = 2 
hazard_labels = total_deaths_per_hazard.index.tolist()
hazard_values = total_deaths_per_hazard.values

total_deaths = np.sum(hazard_values)

adjusted_labels = []
adjusted_values = []
others_total = 0  

for i, (label, value) in enumerate(zip(hazard_labels, hazard_values)):
    percentage = (value / total_deaths) * 100
    if percentage >= threshold:
        adjusted_labels.append(label)
        adjusted_values.append(value)
    else:
        others_total += value  

if others_total > 0:
    adjusted_labels.append('Others')
    adjusted_values.append(others_total)

plt.figure(figsize=(6, 6))
plt.pie(adjusted_values, labels=adjusted_labels, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
plt.title("Overall Percentage Contribution of Each Hazard")
st.pyplot(plt)

st.write("### Complete Data Table")
st.dataframe(csv_data)

st.subheader(f"Percentage Contribution of Each District in '{selected_hazard}'")
total_deaths_in_hazard = csv_data[selected_hazard].sum()
csv_data['Percentage Contribution'] = (csv_data[selected_hazard] / total_deaths_in_hazard) * 100

st.dataframe(csv_data[['District', selected_hazard, 'Percentage Contribution']])

st.subheader("State Insight")

district_most_deaths = csv_data.loc[csv_data[selected_hazard].idxmax()]
st.write(f"**District with Most Deaths**: {district_most_deaths['District'].title()} with {district_most_deaths[selected_hazard]} deaths")

district_least_deaths = csv_data.loc[csv_data[selected_hazard].idxmin()]
st.write(f"**District with Least Deaths**: {district_least_deaths['District'].title()} with {district_least_deaths[selected_hazard]} deaths")

selected_district = st.selectbox('Select District for Comparison', csv_data['District'].unique())
comparative_data = csv_data[csv_data['District'] == selected_district].set_index('District').T

mean_deaths = comparative_data.mean().values[0]
std_deviation = comparative_data.std().values[0]
min_deaths = comparative_data.min().values[0]
max_deaths = comparative_data.max().values[0]

st.subheader(f'Analysis of Death Data for {selected_district}')
st.dataframe(comparative_data.astype(int))  

st.write(f"**Mean Deaths**: {int(mean_deaths)}")  
st.write(f"**Standard Deviation**: {int(std_deviation)}")  
st.write(f"**Minimum Deaths**: {int(min_deaths)}")  
st.write(f"**Maximum Deaths**: {int(max_deaths)}")  

st.subheader(f'Distribution of Deaths Due to Multiple Casualties in {selected_district}')

hazard_death_values = csv_data[csv_data['District'] == selected_district][hazard_columns].values.flatten()

num_vars = len(hazard_columns)

angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()

hazard_death_values = np.concatenate((hazard_death_values, [hazard_death_values[0]]))
angles += angles[:1]

plt.figure(figsize=(6, 6))
ax = plt.subplot(111, polar=True)

ax.fill(angles, hazard_death_values, color='orange', alpha=0.25)
ax.plot(angles, hazard_death_values, color='orange', linewidth=2)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(hazard_columns, fontsize=10)

plt.title(f'Distribution of Deaths Due to Casualties in {selected_district.title()}', size=15)
ax.set_yticklabels([])

st.pyplot(plt)
