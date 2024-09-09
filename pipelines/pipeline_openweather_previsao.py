import boto3
import pandas as pd
import requests
from io import StringIO

# Função para enviar o CSV atualizado de volta ao S3
def upload_csv_to_s3(bucket_name, object_key, local_file_name):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=object_key, Body=local_file_name.getvalue())

# Função para buscar dados dos proximos 5 dias usando a API OpenWeather
def fetch_new_data(df_coord):
    lista = []

    for index, row in df_coord.iterrows():
        # URL da API
        URL = 'https://api.openweathermap.org/data/2.5/forecast'
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
        data = response.json()

        # Verificar se a solicitação foi bem-sucedida
        if response.status_code == 200:
            # Extrair os dados necessários
            for item in data['list']:
                detalhes = {
                    'Data e Hora': item['dt_txt'],
                    'Temperatura': item['main']['temp'],
                    'Temperatura Mínima': item['main']['temp_min'],
                    'Temperatura Máxima': item['main']['temp_max'],
                    'Umidade': item['main']['humidity'],
                    'Pressão': item['main']['pressure'],
                    'Condições': item['weather'][0]['description'],
                    'Velocidade do Vento': item['wind']['speed'],
                    'Nuvens': item['clouds']['all'],
                    'Distrito': row['Distrito']
                }
                lista.append(detalhes)

        else:
            print(f"Erro ao obter dados: {data.get('message', 'Desconhecido')}")

    # Criar um DataFrame com os dados
    df = pd.DataFrame(lista)

    return df

# Função principal
def main():
    # Configurações do S3
    bucket_name = 'black-umbrella-fiap'
    object_key = 'bronze/openweather/dados_previsao_meteorologica.csv'
    df_coord = pd.read_csv('./dados/distritos_lat_lon.csv')

    # Passos para atualizar o CSV
    previsoes = fetch_new_data(df_coord)  # Buscar novos dados
    csv_buffer = StringIO()
    previsoes.to_csv(csv_buffer, index=False)
    upload_csv_to_s3(bucket_name, object_key, csv_buffer)  # Enviar o CSV para o S3

if __name__ == '__main__':
    main()