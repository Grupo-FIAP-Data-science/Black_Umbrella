import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import folium
import geopandas as gpd # type: ignore
import json

from meteostat import Point, Daily
from datetime import datetime
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Configuração da página
st.set_page_config(
    page_title="BlackUmbrella",
    page_icon="🌦️",
    layout="wide")

# Carregar dados dos distritos
df_distritos = pd.read_csv('/home/ryanrodr/FIAP/Black_Umbrella/dados/distritos_lat_lon.csv')

# Adicionar filtro de distrito na barra lateral
st.sidebar.title("Navegação")
page = st.sidebar.radio("Escolha a Página", ["Dados Diários", "Dados Históricos", "Dados de Localização", "Dados Densidade Populacional"])

# Adicionar filtro de distrito global
st.sidebar.subheader("Filtro de Distrito")
distrito_selecionado = st.sidebar.selectbox("Escolha um Distrito", df_distritos['Distrito'].unique())

def dados_diarios():
    latitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Latitude'].values[0]
    longitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Longitude'].values[0]

    api_key = "eb27e58eb68d175624e79e4efed521eb"
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric&lang=pt_br"
    response = requests.get(url)
    weather_data = response.json()

    weather_info = {
        "Distrito": distrito_selecionado,  # Adiciona o nome do distrito
        "Latitude": weather_data['coord'].get('lat', 'Não disponível'),
        "Longitude": weather_data['coord'].get('lon', 'Não disponível'),
        "Temperatura (°C)": weather_data['main'].get('temp', 'Não disponível'),
        "Sensação Térmica (°C)": weather_data['main'].get('feels_like', 'Não disponível'),
        "Temperatura Mínima (°C)": weather_data['main'].get('temp_min', 'Não disponível'),
        "Temperatura Máxima (°C)": weather_data['main'].get('temp_max', 'Não disponível'),
        "Pressão (hPa)": weather_data['main'].get('pressure', 'Não disponível'),
        "Umidade (%)": weather_data['main'].get('humidity', 'Não disponível'),
        "Visibilidade (m)": weather_data.get('visibility', 'Não disponível'),
        "Velocidade do Vento (m/s)": weather_data['wind'].get('speed', 'Não disponível'),
        "Direção do Vento (°)": weather_data['wind'].get('deg', 'Não disponível'),
        "Cobertura de Nuvens (%)": weather_data['clouds'].get('all', 'Não disponível'),
        "Descrição do Clima": weather_data['weather'][0].get('description', 'Não disponível'),
        "Ícone do Clima": weather_data['weather'][0].get('icon', 'Não disponível'),
        "Sunrise": pd.to_datetime(weather_data['sys'].get('sunrise', 0), unit='s'),
        "Sunset": pd.to_datetime(weather_data['sys'].get('sunset', 0), unit='s'),
        "Timezone (s)": weather_data.get('timezone', 'Não disponível'),
        "Código de Resposta": weather_data.get('cod', 'Não disponível'),
        "Precipitação (última 1h)": weather_data.get('rain', {}).get('1h', 'Não disponível')
    }

    # Adicionar título à página
    st.title(f"Dados Diários - {distrito_selecionado}")

    # Exibir informações meteorológicas
    st.subheader("Informações Meteorológicas Atuais")
    st.write(weather_info)

def dados_historicos():
    latitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Latitude'].values[0]
    longitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Longitude'].values[0]
    location = Point(latitude, longitude)
    
    start = datetime(2024, 8, 1)
    end = datetime(2024, 8, 31)

    data = Daily(location, start, end).fetch()

    if data.empty:
        st.warning("Nenhum dado disponível para o período selecionado.")
    else:
        data = data.dropna(axis=1)
        data = data.reset_index()

        fig_line = px.line(data, x='time', y=['tavg', 'tmin', 'tmax'], labels={
            "value": "Temperatura (°C)",
            "variable": "Tipo de Temperatura"
        })
        fig_line.update_layout(autosize=True, margin=dict(l=0, r=0, t=0, b=0))

        fig_bar = px.bar(data, x='time', y=['tavg', 'tmin', 'tmax'], labels={
            "value": "Temperatura (°C)",
            "variable": "Tipo de Temperatura"
        })
        fig_bar.update_layout(autosize=True, margin=dict(l=0, r=0, t=0, b=0))

        fig_scatter = px.scatter(data, x='tmin', y='tmax', labels={
            "tmin": "Temperatura Mínima (°C)",
            "tmax": "Temperatura Máxima (°C)"
        })
        fig_scatter.update_layout(autosize=True, margin=dict(l=0, r=0, t=0, b=0))

        fig_box = px.box(data, y=['tavg', 'tmin', 'tmax'], labels={
            "value": "Temperatura (°C)",
            "variable": "Tipo de Temperatura"
        })
        fig_box.update_layout(autosize=True, margin=dict(l=0, r=0, t=0, b=0))

        fig_area = px.area(data, x='time', y=['tavg', 'tmin', 'tmax'], labels={
            "value": "Temperatura (°C)",
            "variable": "Tipo de Temperatura"
        })
        fig_area.update_layout(autosize=True, margin=dict(l=0, r=0, t=0, b=0))

        st.title(f"Dados Históricos - {distrito_selecionado}")

        with st.container():
            st.subheader("Tabela de Dados")
            st.dataframe(data, use_container_width=True)

            st.subheader("Gráfico de Linhas das Temperaturas")
            st.plotly_chart(fig_line, use_container_width=True)

            st.subheader("Gráfico de Barras das Temperaturas")
            st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("Gráfico de Dispersão das Temperaturas")
            st.plotly_chart(fig_scatter, use_container_width=True)

            st.subheader("Boxplot das Temperaturas")
            st.plotly_chart(fig_box, use_container_width=True)

            st.subheader("Gráfico de Área das Temperaturas")
            st.plotly_chart(fig_area, use_container_width=True)
    
def dados_localizacao():
    df_estacoes_metro = pd.read_csv('/home/ryanrodr/FIAP/Black_Umbrella/dados/localizacao_estacoes_metro.csv')
    
    latitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Latitude'].values[0]
    longitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Longitude'].values[0]

    map = folium.Map(location=[latitude, longitude], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(map)

    for index, row in df_estacoes_metro.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=row['name'],
            icon=folium.Icon(icon='train', prefix='fa')
        ).add_to(marker_cluster)

    st.title(f"Mapa Interativo para {distrito_selecionado}")
    st_folium(map, width=700, height=500)

def dados_densidade_populacional():
    # Carregar o shapefile
    df_densidade_pop = gpd.read_file('/home/ryanrodr/FIAP/Black_Umbrella/dados/densidade_demografica/SIRGAS_SHP_densidade_demografica_2010.shp')

    # Converter o CRS para EPSG:4326
    df_densidade_pop = df_densidade_pop.to_crs(epsg=4326)
        
    # Converter o GeoDataFrame para GeoJSON
    geojson_data = df_densidade_pop.to_json()
    
    # Criar um mapa base
    m = folium.Map(location=[-23.5505, -46.6333], zoom_start=12)
    
    # Adicionar o mapa coroplético
    folium.Choropleth(
        geo_data=geojson_data,
        data=df_densidade_pop,
        columns=['setor_cens', 'populacao'],
        key_on='feature.properties.setor_cens',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='População'
    ).add_to(m)
    
    # Exibir o mapa
    st.title(f"Mapa de Densidade Populacional")
    st_folium(m, width=700, height=500)

# Carregar a página correspondente
if page == "Dados Diários":
    dados_diarios()
elif page == "Dados Históricos":
    dados_historicos()
elif page == "Dados de Localização":
    dados_localizacao()
elif page == "Dados Densidade Populacional":
    dados_densidade_populacional()