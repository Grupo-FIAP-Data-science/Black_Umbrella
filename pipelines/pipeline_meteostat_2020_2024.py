import pandas as pd
from meteostat import Point, Hourly
from datetime import datetime
import boto3
import os
from dotenv import load_dotenv
from io import StringIO
import warnings

warnings.filterwarnings("ignore")


# Função para buscar os dados da API da Meteostat
def dados_historicos_hora(df_coord, start_date, end_date):
    
    all_data = []

    for index, row in df_coord.iterrows():
        latitude = row['Latitude']
        longitude = row['Longitude']
        location = Point(latitude, longitude)
        
        # Obter dados diários do Meteostat
        data = Hourly(location, start_date, end_date).fetch()
        
        # Adicionar uma coluna com o nome do distrito
        data['Distrito'] = row['Distrito']
        data['Latitude'] = latitude
        data['Longitude'] = longitude
        
        # Adicionar os dados à lista
        all_data.append(data)
    
    final_data = pd.concat(all_data)

    final_data.reset_index(inplace=True)

    return final_data


# Função para enviar para o S3
def upload_to_s3(df):
    # Configurações do S3
    access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    s3 = boto3.client('s3',
                  aws_access_key_id=access_key_id,
                  aws_secret_access_key=secret_access_key,
                  region_name = 'sa-east-1')

    # Carregar o arquivo CSV para o S3
    s3.put_object(Bucket='black-umbrella-fiap',
                Key='bronze/meteostat_horario/horario_2020_2024.csv',
                Body=df.getvalue())
    
    print('Arquivo enviado para o S3 com sucesso!')


# Função principal
def main():
    # Datas de início e fim (pode ser ajustado para obter dados incrementais)
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 9, 9)
    
    df_coord = pd.read_csv('./dados/distritos_lat_lon.csv')

    # Coleta os dados da API
    df = dados_historicos_hora(df_coord, start_date, end_date)
  
    # Enviar os arquivos particionados para o S3
    upload_to_s3(df)

if __name__ == '__main__':
    main()