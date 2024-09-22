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
st.sidebar.subheader("Filtro de Distrito")
distrito_selecionado = st.sidebar.selectbox("Escolha um Distrito", df_distritos['Distrito'].unique())

# Adicionar opção de navegação na barra lateral
st.sidebar.title("Navegação")
page = st.sidebar.radio("Escolha a Página", ["Escolha entre os boletins", "Dados de Localização", "Dados Densidade Populacional", "Previsão de Ocorrências"])

# Função para exibir dados diários
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

    # Configurar layout com duas colunas
    col1, col2 = st.columns(2)

    with col1:
        st.image(icon_url, width=100)
        st.subheader(f"{weather_data['weather'][0].get('description', 'Não disponível').capitalize()}")
        st.metric("Temperatura Atual (°C)", weather_data['main'].get('temp', 'N/A'))
        st.metric("Sensação Térmica (°C)", weather_data['main'].get('feels_like', 'N/A'))
        st.metric("Temperatura Máxima (°C)", weather_data['main'].get('temp_max', 'Não disponível'))
        st.metric("Temperatura Mínima (°C)", weather_data['main'].get('temp_min', 'Não disponível'))

        st.write("### Horário Solar")
        st.write(f"**Nascer do Sol:** {pd.to_datetime(weather_data['sys'].get('sunrise', 0), unit='s').strftime('%H:%M:%S')}")
        st.write(f"**Pôr do Sol:** {pd.to_datetime(weather_data['sys'].get('sunset', 0), unit='s').strftime('%H:%M:%S')}")
        st.write(f"**Timezone:** {weather_data.get('timezone', 'Não disponível')} s")

    with col2:
        st.image(icon_url, width=100)
        st.write("### Informações Detalhadas")
        st.write(f"**Pressão Atmosférica:** {weather_data['main'].get('pressure', 'Não disponível')} hPa")
        st.write(f"**Umidade:** {weather_data['main'].get('humidity', 'Não disponível')}%")
        st.write(f"**Velocidade do Vento:** {weather_data['wind'].get('speed', 'Não disponível')} m/s")
        st.write(f"**Direção do Vento:** {weather_data['wind'].get('deg', 'Não disponível')}°")
        st.write("### Outras Informações")
        st.metric("Visibilidade (m)", weather_data.get('visibility', 'N/A'))
        st.metric("Cobertura de Nuvens (%)", weather_data['clouds'].get('all', 'N/A'))
        st.metric("Precipitação (última 1h)", weather_data.get('rain', {}).get('1h', 'N/A'))

import tempfile  # Importar a biblioteca para criar arquivos temporários
# Função para exibir dados históricos com filtro de data
def dados_historicos():
    latitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Latitude'].values[0]
    longitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Longitude'].values[0]
    location = Point(latitude, longitude)

    # Filtro de data para o usuário selecionar o período
    st.sidebar.subheader("Selecione o Período")
    start_date = st.sidebar.date_input("Data de Início", datetime(2024, 8, 1))
    end_date = st.sidebar.date_input("Data de Fim", datetime(2024, 8, 31))

    # Verifica se a data final é posterior à data inicial
    if start_date > end_date:
        st.error("A data final deve ser posterior à data inicial.")
    else:
        # Obter dados históricos para o período selecionado
        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.min.time())

        data = Daily(location, start, end).fetch()

        if data.empty:
            st.warning("Nenhum dado disponível para o período selecionado.")
        else:
            data = data.dropna(axis=1)
            data = data.reset_index()

            # Criar um botão de download
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar Dados Históricos (CSV)",
                data=csv,
                file_name=f'dados_historicos_{distrito_selecionado}.csv',
                mime='text/csv'
            )

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

# Função para exibir dados de localização
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

# Função para exibir dados de densidade populacional
def dados_densidade_populacional():
    df_densidade_pop = gpd.read_file('/home/ryanrodr/FIAP/Black_Umbrella/dados/densidade_demografica/SIRGAS_SHP_densidade_demografica_2010.shp')

    df_densidade_pop = df_densidade_pop.dropna()
    df_densidade_pop = df_densidade_pop.to_crs(epsg=4326)
    df_densidade_pop['centroid'] = df_densidade_pop.geometry.centroid

    heat_data = [[point.y, point.x, pop] for point, pop in zip(df_densidade_pop['centroid'], df_densidade_pop['populacao'])]

    m = folium.Map(location=[-23.5505, -46.6333], zoom_start=12)
    HeatMap(heat_data, radius=15, max_zoom=13).add_to(m)

    map_file = '/tmp/heatmap.html'
    m.save(map_file)

    with open(map_file, 'r') as file:
        map_data = file.read()

    map_data_base64 = base64.b64encode(map_data.encode()).decode()
    href = f'<a href="data:file/html;base64,{map_data_base64}" download="heatmap.html">Download do Mapa</a>'

    st.title("Mapa de Densidade Populacional (Heatmap)")
    st.write("Clique no link abaixo para baixar o mapa de calor:")
    st.markdown(href, unsafe_allow_html=True)

# Seleção da página para exibição
if page == "Escolha entre os boletins":
    st.sidebar.subheader("Selecione o Boletim")
    boletim = st.sidebar.radio("Escolha o tipo de boletim", ["Dados Diários", "Dados Históricos"])

    if boletim == "Dados Diários":
        dados_diarios()
    elif boletim == "Dados Históricos":
        dados_historicos()

elif page == "Dados de Localização":
    dados_localizacao()

elif page == "Dados Densidade Populacional":
    dados_densidade_populacional()

elif page == "Previsão de Ocorrências":
    st.write("Página de Previsão de Ocorrências ainda em desenvolvimento.")
