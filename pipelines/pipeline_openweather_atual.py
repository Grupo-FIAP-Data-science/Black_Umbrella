import boto3
import pandas as pd
import requests
from io import StringIO

# Função para enviar o CSV atualizado de volta ao S3
def upload_csv_s3(bucket_name, object_key, local_file_name):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=object_key, Body=local_file_name.getvalue())

    print(f"Arquivo {object_key} enviado para o bucket {bucket_name}")

# Função para buscar dados dos proximos 5 dias usando a API OpenWeather
def dados_previsao(df_coord):
    lista = []

    for index, row in df_coord.iterrows():
        # URL da API
        URL = "http://api.openweathermap.org/data/2.5/weather"
        latitude = row['Latitude']
        longitude = row['Longitude']

        # Parâmetros da solicitação
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': 'eb27e58eb68d175624e79e4efed521eb',
            'units': 'metric',  # Use 'imperial' para Fahrenheit
            'lang': 'pt'  # Idioma dos detalhes (opcional)
        }

        # Fazer a solicitação para a API
        response = requests.get(URL, params=params)
        weather_data = response.json()

        # Verificar se a solicitação foi bem-sucedida
        if response.status_code == 200:
            # Extrair os dados necessários
            detalhes = {
            'Temperatura Atual (°C)': weather_data['main'].get('temp', 'N/A'),
            'Sensação Térmica (°C)': weather_data['main'].get('feels_like', 'N/A'),
            'Temperatura Mínima': weather_data['main'].get('temp_min', 'Não disponível'),
            'Temperatura Máxima': weather_data['main'].get('temp_max', 'Não disponível'),
            'Umidade': weather_data['main'].get('humidity', 'Não disponível'),
            'Pressão': weather_data['main'].get('pressure', 'Não disponível'),
            'Condições': weather_data['weather'][0].get('description', 'Não disponível'),
            'Velocidade do Vento': weather_data['wind'].get('speed', 'Não disponível'),
            'Direção do Vento': weather_data['wind'].get('deg', 'Não disponível'),
            'Precipitação': weather_data.get('rain', {}).get('1h', 'N/A'),
            'Nuvens': weather_data['clouds'].get('all', 'N/A'),
            'Nascer do Sol': pd.to_datetime(weather_data['sys'].get('sunrise', 0), unit='s'),
            'Pôr do Sol': pd.to_datetime(weather_data['sys'].get('sunset', 0), unit='s'),
            'Visibilidade': weather_data.get('visibility', 'N/A'),
            'Distrito': row['Distrito'],
            'Latitude': latitude,
            'Longitude': longitude
            }
            lista.append(detalhes)

        else:
            print(f"Erro ao obter dados: {weather_data.get('message', 'Desconhecido')}")

    # Criar um DataFrame com os dados
    df = pd.DataFrame(lista)

    return df

# Função principal
def main():
    # Configurações do S3
    bucket_name = 'black-umbrella-fiap'
    object_key = 'bronze/meteorologia_atual/dados_atuais_meteorologicos.csv'
    df_coord = pd.read_csv('./dados/distritos_lat_lon.csv')

    # Passos para atualizar o CSV
    previsoes = dados_previsao(df_coord)  # Buscar novos dados
    csv_buffer = StringIO()
    previsoes.to_csv(csv_buffer, index=False)
    upload_csv_s3(bucket_name, object_key, csv_buffer)  # Enviar o CSV para o S3

if __name__ == '__main__':
    main()