import streamlit as st
import requests
import plotly.express as px
from meteostat import Point, Daily
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="BlackUmbrella",
    page_icon="🌦️",
    layout="wide")

def dados_diarios():
    # Definir localização (São Paulo)
    latitude = -23.5505
    longitude = -46.6333

    # OpenWeatherMap API Key
    api_key = "eb27e58eb68d175624e79e4efed521eb"

    # URL para obter dados meteorológicos atuais
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}&units=metric&lang=pt_br"

    # Solicitar dados
    response = requests.get(url)
    weather_data = response.json()

    # Extrair e formatar as informações
    weather_info = {
        "Temperatura": f"{weather_data['main']['temp']} °C",
        "Condição": weather_data['weather'][0]['description'].capitalize(),
        "Humidade": f"{weather_data['main']['humidity']}%",
        "Vento": f"{weather_data['wind']['speed']} m/s",
        "Direção do Vento": f"{weather_data['wind']['deg']}°",
        "Pressão": f"{weather_data['main']['pressure']} hPa",
        "Cobertura de Nuvens": f"{weather_data['clouds']['all']}%",
        "Precipitação": weather_data.get('rain', {}).get('1h', 'Não disponível')  # Precipitação nas últimas 1 hora
    }

    # Adicionar título à página
    st.title("Dados Diários do Estado de SP")

    # Exibir informações meteorológicas
    st.subheader("Informações Meteorológicas Atuais")
    st.write(weather_info)

def dados_historicos():
    # Definir localização (São Paulo)
    latitude = -23.5505
    longitude = -46.6333
    location = Point(latitude, longitude)

    # Definir datas diretamente no código
    start = datetime(2024, 8, 1)
    end = datetime(2024, 8, 31)

    # Obter dados diários do Meteostat
    data = Daily(location, start, end).fetch()

    # Verificar se há dados disponíveis para o período selecionado
    if data.empty:
        st.warning("Nenhum dado disponível para o período selecionado.")
    else:
        # Remover valores ausentes NaN (Not a Number)
        data = data.dropna(axis=1)
        data = data.reset_index()

        # Criar gráficos
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

        # Adicionar título à página
        st.title("Dados Históricos do Estado de SP")

        # Usar container para organizar a tabela e os gráficos
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

# Definir o menu de navegação
st.sidebar.title("Navegação")
page = st.sidebar.radio("Escolha a Página", ["Dados Diários", "Dados Históricos"])

# Carregar a página correspondente
if page == "Dados Diários":
    dados_diarios()
elif page == "Dados Históricos":
    dados_historicos()