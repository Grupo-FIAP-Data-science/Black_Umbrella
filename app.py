import pandas as pd
import streamlit as st
import requests
import plotly.express as px # type: ignore
import os
import folium
from meteostat import Point, Daily # type: ignore
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError
from streamlit_folium import folium_static # type: ignore
from datetime import datetime

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
# df_distritos = pd.read_csv("dados/distritos_lat_lon.csv")

# Exibir logo na sidebar
st.sidebar.image("black_umbrella.jpeg", width=300)

# Adicionar filtro de distrito na barra lateral
st.sidebar.subheader("Navegação")
# distrito_selecionado = st.sidebar.selectbox("Escolha um Distrito", df_distritos['Distrito'].unique())

# Adicionar a página "Avaliação" à barra lateral
page = st.sidebar.radio("Escolha a Página", ["Dashboard", "Reportar Ocorrência", "Avaliação do Usuário"])
            
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
    power_bi_url = "https://app.powerbi.com/view?r=eyJrIjoiMzMyNmE1ZjUtODRlZS00MjQ1LTg2MDUtZGFiYjI4YzA3YTEyIiwidCI6IjU4YjBjYWY5LWFkZjUtNDQxNC1hOThlLTQyM2JlYjEzZGRkZCJ9"

    # Use st.components.v1.iframe para incorporar o relatório no Streamlit
    st.components.v1.iframe(power_bi_url, width=800, height=600)

# Função para obter coordenadas de um endereço
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="my_geocoder_app")
        location = geolocator.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        return None
    except GeocoderServiceError as e:
        st.error(f"Erro ao acessar o serviço de geocodificação: {e}")
        return None

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

# Função para indicar ocorrência
def pagina_ocorrencia():
    st.title("Indicação de Ocorrência")

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

    # Endereço para geolocalização
    address = st.text_input("Digite o endereço (Rua, Cidade, Estado):")
    
    # Se o usuário fornecer um endereço
    if address:
        # Obtenha as coordenadas
        coordinates = get_coordinates(address)
        
        if coordinates:
            latitude, longitude = coordinates
            # Exibir coordenadas automaticamente
            st.write(f"**Coordenadas**: {latitude}, {longitude}")
            
            # Crie o mapa centrado nas coordenadas encontradas
            m = folium.Map(location=coordinates, zoom_start=15)
            # Adicione um marcador no endereço
            folium.Marker(coordinates, popup=address).add_to(m)
            # Renderize o mapa no Streamlit
            folium_static(m)
        else:
            st.error("Endereço não encontrado ou erro ao acessar o serviço.")
    
    # Upload de imagem (opcional)
    imagem = st.file_uploader("Anexar uma imagem (opcional)", type=["jpg", "jpeg", "png"])

    # Botão para enviar ocorrência
    if st.button("Enviar Ocorrência"):
        if coordinates:
            st.success("Ocorrência enviada com sucesso!")
            # Salvar ocorrência em um arquivo CSV
            salvar_ocorrencia(nome, email, data, latitude, longitude, categoria, descricao, imagem)
        else:
            st.error("Não foi possível enviar a ocorrência. Verifique o endereço.")

if page == "Dashboard":
    dashboard()

elif page == "Reportar Ocorrência":
    pagina_ocorrencia()

elif page == "Avaliação do Usuário":
    pagina_avaliacao()