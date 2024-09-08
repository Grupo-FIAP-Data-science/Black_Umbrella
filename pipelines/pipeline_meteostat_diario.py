import boto3
import pandas as pd
from meteostat import Point, Hourly
from datetime import datetime, timedelta
from io import StringIO

# Função para baixar o CSV do S3
def download_csv_from_s3(bucket_name, object_key, local_file_name):
    s3 = boto3.client('s3')
    s3.download_file(bucket_name, object_key, local_file_name)

# Função para enviar o CSV atualizado de volta ao S3
def upload_csv_to_s3(bucket_name, object_key, local_file_name):
    s3 = boto3.client('s3')
    s3.upload_file(local_file_name, bucket_name, object_key)

# Função para buscar dados do dia anterior usando a API Meteostat
def fetch_new_data(df_coord):
    # Data de ontem
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    start_date = end_date

    all_data = []

    for index, row in df_coord.iterrows():
        latitude = row['Latitude']
        longitude = row['Longitude']
        location = Point(latitude, longitude)
        
        # Obter dados diários do Meteostat
        data = Hourly(location, start_date, end_date).fetch()
        
        # Adicionar uma coluna com o nome do distrito
        data['Distrito'] = row['Distrito']
        
        # Adicionar os dados à lista
        all_data.append(data)
    
    final_data = pd.concat(all_data)
    
    # Adicionando colunas para ano, mês e dia para partições
    final_data['Ano'] = final_data.index.year
    final_data['Mes'] = final_data.index.month

    final_data.reset_index(inplace=True)

    # Salva o DataFrame em um buffer
    csv_buffer = StringIO()
    final_data.to_csv(csv_buffer, index=False)

    return csv_buffer

# Atualizar o CSV existente
def update_csv(local_file_name, new_data):
    # Carregar o CSV existente
    df_existing = pd.read_csv(local_file_name)
    
    # Concatenar os dados novos
    df_updated = pd.concat([df_existing, new_data])
    
    # Salvar o CSV atualizado
    df_updated.to_csv(local_file_name, index=False)


# Função principal
def main():
    # Configurações do S3
    bucket_name = 'black-umbrella-fiap'
    object_key = 'bronze/meteostat/dados_diarios_2024.csv'
    local_file_name = 'dados_diarios_2024.csv'

    df_coord = pd.read_csv('dados/distritos_lat_lon.csv')

    # Passos para atualizar o CSV
    download_csv_from_s3(bucket_name, object_key, local_file_name)  # Baixar o CSV existente
    new_data = fetch_new_data(df_coord)  # Buscar novos dados
    update_csv(local_file_name, new_data)  # Atualizar o CSV
    upload_csv_to_s3(bucket_name, object_key, local_file_name)  # Enviar o CSV atualizado de volta ao S3

if __name__ == '__main__':
    main()