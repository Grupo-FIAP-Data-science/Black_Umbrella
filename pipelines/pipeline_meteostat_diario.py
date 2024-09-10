import boto3
import pandas as pd
from meteostat import Point, Hourly, Daily
from datetime import datetime, timedelta
from io import BytesIO, StringIO

# Função para baixar o CSV do S3
def acessar_csv_s3(bucket_name, object_key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=object_key)

    csv_content = response['Body'].read()
    df = pd.read_csv(BytesIO(csv_content))

    return df

# Função para enviar o CSV atualizado de volta ao S3
def upload_csv_s3(bucket_name, object_key, local_file_name):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=object_key, Body=local_file_name.getvalue())

    print(f"Arquivo {object_key} enviado para o bucket {bucket_name}")

# Função para buscar dados do dia anterior usando a API Meteostat - Dados por hora
def novos_registros_hora(df_coord):
    # Data de ontem
    start_date = datetime.now().replace(hour=1, minute=0, second=0, microsecond=0) - timedelta(days=1)
    end_date = start_date + timedelta(days=1, hours=-1)

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

    final_data.reset_index(inplace=True)

    return final_data

# Função para buscar os dados da API da Meteostat - Dados diários
def dados_historicos_diario(df_coord):
    
    # Data de ontem
    start_date = datetime.now() - timedelta(days=1)
    end_date = start_date + timedelta(days=1)

    all_data = []

    for index, row in df_coord.iterrows():
        latitude = row['Latitude']
        longitude = row['Longitude']
        location = Point(latitude, longitude)
        
        # Obter dados diários do Meteostat
        data = Daily(location, start_date, end_date).fetch()
        
        # Adicionar uma coluna com o nome do distrito
        data['Distrito'] = row['Distrito']
        
        # Adicionar os dados à lista
        all_data.append(data)
    
    final_data = pd.concat(all_data)

    final_data.reset_index(inplace=True)

    # Salva o DataFrame em um buffer
    csv_buffer = StringIO()
    final_data.to_csv(csv_buffer, index=False)
    
    return csv_buffer

# Atualizar o CSV existente
def update_csv(df, new_data):
    # Carregar o CSV existente
    df_existing = df
    
    # Concatenar os dados novos
    df_updated = pd.concat([df_existing, new_data])
    
    return df_updated


# Função principal
def main():
    # Configurações do S3
    bucket_name = 'black-umbrella-fiap'
    object_key = 'bronze/meteostat/dados_historicos_2020_2024.csv' # Arquivo de dados históricos por hora

    bucket_name2 = 'black-umbrella-fiap'
    object_key2 = 'bronze/meteostat/dados_diarios_1950_2024.csv' # Arquivo de dados históricos diarios

    df_coord = pd.read_csv('./dados/distritos_lat_lon.csv')

    # Passos para atualizar o CSV
    df = acessar_csv_s3(bucket_name, object_key)  # Baixar o CSV existente
    new_data = novos_registros_hora(df_coord)  # Buscar novos dados
    df_final = update_csv(df, new_data)  # Atualizar o CSV
    csv_buffer = StringIO()
    df_final.to_csv(csv_buffer, index=False)
    upload_csv_s3(bucket_name, object_key, csv_buffer)  # Enviar o CSV atualizado de volta ao S3

    df2 = acessar_csv_s3(bucket_name2, object_key2)
    new_data2 = novos_registros_hora(df_coord)  # Buscar novos dados
    df_final2 = update_csv(df2, new_data2)  # Atualizar o CSV
    csv_buffer2 = StringIO()
    df_final2.to_csv(csv_buffer2, index=False)
    upload_csv_s3(bucket_name, object_key, csv_buffer2)

if __name__ == '__main__':
    main()