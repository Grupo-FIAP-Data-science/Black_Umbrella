import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import folium
import geopandas as gpd  # type: ignore
import os
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
    .css-1d391kg {
        background-color: rgb(70, 70, 70); /* Cor da sidebar */
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
df_distritos = pd.read_csv("dados/distritos_lat_lon.csv")

# Exibir logo na sidebar
st.sidebar.image("black_umbrella.jpeg", width=300)

# Adicionar filtro de distrito na barra lateral
st.sidebar.subheader("Navegação")
distrito_selecionado = st.sidebar.selectbox("Escolha um Distrito", df_distritos['Distrito'].unique())

# Adicionar a página "Avaliação" à barra lateral
page = st.sidebar.radio("Escolha a Página", ["Informativo Meteorológico", "Dashboard", "Reportar Ocorrência", "Avaliação do Usuário"])

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

def pagina_avaliacao():
    st.title("Avaliação do Sistema")

    # Campos adicionais
    nome = st.text_input("Seu Nome (opcional)")
    email = st.text_input("Seu E-mail (opcional)")
    data = datetime.now().strftime("%Y-%m-%d")

    # Avaliação por múltiplos critérios
    facilidade = st.slider("Facilidade de Uso", 0, 5, 3)
    qualidade_informacao = st.slider("Qualidade da Informação", 0, 5, 3)
    velocidade_resposta = st.slider("Velocidade de Resposta", 0, 5, 3)
    design = st.slider("Design/UX", 0, 5, 3)

    comentario = st.text_area("Comentários adicionais", "")

    # Botão para enviar avaliação
    if st.button("Enviar Avaliação"):
        st.success("Avaliação enviada com sucesso!")

        # Salvar avaliação em um arquivo CSV
        salvar_avaliacao(nome, email, data, facilidade, qualidade_informacao, velocidade_resposta, design, comentario)

# Função para salvar avaliação em um arquivo CSV (modificada para incluir novos campos)
def salvar_avaliacao(nome, email, data, facilidade, qualidade_informacao, velocidade_resposta, design, comentario):
    arquivo_csv = 'avaliacoes.csv'

    # Verifica se o arquivo já existe
    if not os.path.isfile(arquivo_csv):
        with open(arquivo_csv, 'w') as f:
            f.write('Nome,E-mail,Data,Facilidade,Qualidade,Velocidade,Design,Comentário\n')

    # Adiciona a nova avaliação ao arquivo
    with open(arquivo_csv, 'a') as f:
        f.write(f'{nome},"{email}","{data}",{facilidade},{qualidade_informacao},{velocidade_resposta},{design},"{comentario}"\n')

def dashboard():
    st.title("Boletins")

    # URL do relatório do Power BI gerado na incorporação
    power_bi_url = "https://app.powerbi.com/view?r=eyJrIjoiZTIxZTRjYjUtNjhmZC00MDhhLWFlZjgtZmIxNWUwNzU4YmI4IiwidCI6IjU4YjBjYWY5LWFkZjUtNDQxNC1hOThlLTQyM2JlYjEzZGRkZCJ9&pageName=98eebda01d89b142dd10"

    # Use st.components.v1.iframe para incorporar o relatório no Streamlit
    st.components.v1.iframe(power_bi_url, width=800, height=600)

# Função para indicar ocorrência
def pagina_ocorrencia():
    st.title("Indicação de Ocorrência")

    # Obter latitude e longitude do distrito selecionado
    latitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Latitude'].values[0]
    longitude = df_distritos[df_distritos['Distrito'] == distrito_selecionado]['Longitude'].values[0]

    # Exibir o distrito e coordenadas automaticamente
    st.subheader(f"Você selecionou o Distrito: {distrito_selecionado}")
    st.write(f"**Coordenadas**: {latitude}, {longitude}")

    # Campos de entrada de texto
    nome = st.text_input("Seu Nome (opcional)")
    email = st.text_input("Seu E-mail (opcional)")
    data = datetime.now().strftime("%Y-%m-%d")

    # Categoria da ocorrência
    categoria = st.selectbox(
        "Categoria da Ocorrência",
        ["Queda de Árvore", "Alagamento", "Deslizamento", "Inundação", "Interrupção do Fornecimento de Energia", "Outros"]
    )

    # Descrição da ocorrência
    descricao = st.text_area("Descrição da Ocorrência")

    # Upload de imagem (opcional)
    imagem = st.file_uploader("Anexar uma imagem (opcional)", type=["jpg", "jpeg", "png"])

    # Botão para enviar ocorrência
    if st.button("Enviar Ocorrência"):
        st.success("Ocorrência enviada com sucesso!")

        # Salvar ocorrência em um arquivo CSV
        salvar_ocorrencia(nome, email, data, latitude, longitude, categoria, descricao, imagem)

# Função para salvar a ocorrência em um arquivo CSV (pode ser adaptada para banco de dados)
def salvar_ocorrencia(nome, email, data, latitude, longitude, categoria, descricao, imagem):
    arquivo_csv = 'ocorrencias.csv'

    # Verifica se o arquivo já existe
    if not os.path.isfile(arquivo_csv):
        with open(arquivo_csv, 'w') as f:
            f.write('Nome,E-mail,Data,Latitude,Longitude,Categoria,Descrição,Imagem\n')

    # Salva os dados no CSV
    with open(arquivo_csv, 'a') as f:
        f.write(f'{nome},{email},{data},{latitude},{longitude},{categoria},{descricao},{imagem}\n')

# Seleção da página para exibição
if page == "Informativo Meteorológico":
    # st.sidebar.subheader("Selecione o Boletim")
    boletim = st.sidebar.radio("Escolha o tipo de informativo", ["Diários", "Históricos"])

    if boletim == "Diários":
        dados_diarios()
    elif boletim == "Históricos":
        dados_historicos()

elif page == "Dashboard":
    dashboard()

elif page == "Reportar Ocorrência":
    pagina_ocorrencia()

elif page == "Avaliação do Usuário":
    pagina_avaliacao()
