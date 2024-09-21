import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import folium
import geopandas as gpd  # type: ignore
import json
import joblib
import base64

from meteostat import Point, Daily
from datetime import datetime
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

# Configuração da página
st.set_page_config(
    page_title="BlackUmbrella",
    page_icon="🌦️",
    layout="wide"
)


# Estilos personalizados
st.markdown(
    """
    <style>
    body {
        background-color: rgb(255, 255, 240); /* Branco */
    }
    h1, h2, h3 {
        color: rgb(0, 0, 204); /* Azul */
    }
    .metric {
        color: rgb(255, 215, 0); /* Amarelo */
    }
    .stButton>button {
        background-color: rgb(255, 215, 0); /* Amarelo */
        color: rgb(0, 0, 0); /* Preto */
    }
    .stDataFrame {
        color: rgb(70, 70, 70); /* Cinza */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Carregar dados dos distritos
df_distritos = pd.read_csv('dados/distritos_lat_lon.csv')

# Adicionar filtro de distrito na barra lateral
st.sidebar.title("Navegação")
page = st.sidebar.radio("Escolha a Página", ["Dados Diários", "Dados Históricos", "Dados de Localização", "Dados Densidade Populacional", "Previsão de Ocorrências"])

# Adicionar filtro de distrito global
st.sidebar.subheader("Filtro de Distrito")
distrito_selecionado = st.sidebar.selectbox("Escolha um Distrito", df_distritos['Distrito'].unique())

def dados_diarios():
    # Obter latitude e longitude do distrito selecionado
    latitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Latitude'].values[0]
    longitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Longitude'].values[0]

    # Requisição à API
    api_key = "eb27e58eb68d175624e79e4efed521eb"
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric&lang=pt_br"
    response = requests.get(url)
    weather_data = response.json()

    # Obter ícone do clima
    icon_url = f"http://openweathermap.org/img/wn/{weather_data['weather'][0].get('icon', '01d')}@2x.png"

    # Configurar layout com colunas
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(icon_url, width=100)  # Exibir ícone do clima
        st.subheader(f"{weather_data['weather'][0].get('description', 'Não disponível').capitalize()}")
        st.metric("Temperatura Atual (°C)", weather_data['main'].get('temp', 'N/A'))
        st.metric("Sensação Térmica (°C)", weather_data['main'].get('feels_like', 'N/A'))

    with col2:
        st.write("### Informações Detalhadas")
        st.write(f"**Temperatura Máxima:** {weather_data['main'].get('temp_max', 'Não disponível')} °C")
        st.write(f"**Temperatura Mínima:** {weather_data['main'].get('temp_min', 'Não disponível')} °C")
        st.write(f"**Pressão Atmosférica:** {weather_data['main'].get('pressure', 'Não disponível')} hPa")
        st.write(f"**Umidade:** {weather_data['main'].get('humidity', 'Não disponível')}%")
        st.write(f"**Velocidade do Vento:** {weather_data['wind'].get('speed', 'Não disponível')} m/s")
        st.write(f"**Direção do Vento:** {weather_data['wind'].get('deg', 'Não disponível')}°")

    # Exibir dados em formato de caixas
    st.write("### Outras Informações")
    col3, col4, col5 = st.columns(3)
    with col3:
        st.metric("Visibilidade (m)", weather_data.get('visibility', 'N/A'))
    with col4:
        st.metric("Cobertura de Nuvens (%)", weather_data['clouds'].get('all', 'N/A'))
    with col5:
        st.metric("Precipitação (última 1h)", weather_data.get('rain', {}).get('1h', 'N/A'))

    # Exibir informações sobre o nascer e pôr do sol
    st.write("### Horário Solar")
    col6, col7 = st.columns(2)
    with col6:
        st.write(f"**Nascer do Sol:** {pd.to_datetime(weather_data['sys'].get('sunrise', 0), unit='s').strftime('%H:%M:%S')}")
    with col7:
        st.write(f"**Pôr do Sol:** {pd.to_datetime(weather_data['sys'].get('sunset', 0), unit='s').strftime('%H:%M:%S')}")

    st.write(f"**Timezone:** {weather_data.get('timezone', 'Não disponível')} s")

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
    df_estacoes_metro = pd.read_csv('dados/localizacao_estacoes_metro.csv')
    
    latitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Latitude'].values[0]
    longitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Longitude'].values[0]

    map = folium.Map(location=[latitude, longitude], zoom_start=12)
    marker_cluster = MarkerCluster().add_to(map)

    for index, row in df_estacoes_metro.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=row['name2'],
            icon=folium.Icon(icon='train', prefix='fa')
        ).add_to(marker_cluster)

    st.title(f"Mapa Interativo para {distrito_selecionado}")
    st_folium(map, width=700)

def dados_densidade_populacional():
    # Carregar o shapefile usando geopandas
    df_densidade_pop = gpd.read_file('/home/ryanrodr/FIAP/Black_Umbrella/dados/densidade_demografica/SIRGAS_SHP_densidade_demografica_2010.shp')

    # Remover valores ausentes
    df_densidade_pop = df_densidade_pop.dropna()

    # Converter o CRS para EPSG:4326 (latitude/longitude)
    df_densidade_pop = df_densidade_pop.to_crs(epsg=4326)

    # Extrair os centroides dos polígonos para usar como pontos no heatmap
    df_densidade_pop['centroid'] = df_densidade_pop.geometry.centroid

    # Criar uma lista de pontos de calor (latitude, longitude, peso)
    heat_data = [[point.y, point.x, pop] for point, pop in zip(df_densidade_pop['centroid'], df_densidade_pop['populacao'])]

    # Criar um mapa base centralizado em São Paulo
    m = folium.Map(location=[-23.5505, -46.6333], zoom_start=12)

    # Adicionar o HeatMap ao mapa base
    HeatMap(heat_data, radius=15, max_zoom=13).add_to(m)

    # Salvar o mapa como arquivo HTML
    map_file = '/tmp/heatmap.html'
    m.save(map_file)

    # Ler o arquivo HTML e codificar em Base64
    with open(map_file, 'r') as file:
        map_data = file.read()
    
    map_data_base64 = base64.b64encode(map_data.encode()).decode()

    # Criar o link de download
    href = f'<a href="data:file/html;base64,{map_data_base64}" download="heatmap.html">Download do Mapa</a>'

    # Exibir o link de download no Streamlit
    st.title("Mapa de Densidade Populacional (Heatmap)")
    st.write("Clique no link abaixo para baixar o mapa de calor:")
    st.markdown(href, unsafe_allow_html=True)

# Selecionar a página ativa
if page == "Dados Diários":
    dados_diarios()
elif page == "Dados Históricos":
    dados_historicos()
elif page == "Dados de Localização":
    dados_localizacao()
elif page == "Dados Densidade Populacional":
    dados_densidade_populacional()