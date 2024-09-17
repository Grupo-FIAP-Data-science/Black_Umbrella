import boto3
import pandas as pd
from io import BytesIO, StringIO
import warnings
import unidecode

warnings.filterwarnings("ignore")

# Função para baixar o CSV do S3
def acessar_csv_s3(bucket_name, object_key):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=f"bronze/{object_key}")

    csv_content = response['Body'].read()
    df = pd.read_csv(BytesIO(csv_content))

    return df

# Função para enviar o CSV atualizado de volta ao S3
def upload_csv_s3(bucket_name, object_key, local_file_name):
    s3 = boto3.client('s3')
    s3.put_object(Bucket=bucket_name, Key=f"silver/{object_key}", Body=local_file_name.getvalue())

    print(f"Arquivo {object_key} enviado para o bucket {bucket_name}")

# Função para buscar os dados da API da Meteostat - Dados diários
def normalizacao_dados(df, prefixo):
    
    if prefixo == 'meteostat_diario/historico_diario_1950_2024.csv':
        df = df.drop(columns=['snow', 'wpgt', 'tsun'])
        df = df.rename(columns={'index': 'data'})
        df['data'] = pd.to_datetime(df['data'], format='mixed')
        df['prcp'] = df['prcp'].fillna(0)
        df['wdir'] = df['wdir'].fillna(df['wdir'].mean())
        df['wspd'] = df['wspd'].fillna(df['wspd'].mean())
        df['tavg'] = df['tavg'].fillna(df['tavg'].mean())
        df['tmin'] = df['tmin'].fillna(df['tmin'].mean())
        df['tmax'] = df['tmax'].fillna(df['tmax'].mean())
        df['pres'] = df['pres'].fillna(df['pres'].mean())
    elif prefixo == 'meteostat_horario/horario_2020_2024.csv':
        df = df.drop(columns=['snow', 'wpgt', 'tsun'])
        df = df.rename(columns={'index': 'data'})
        df['data'] = pd.to_datetime(df['data'], format='mixed')
        df['prcp'] = df['prcp'].fillna(0)
        df['wdir'] = df['wdir'].fillna(df['wdir'].mean())
        df['wspd'] = df['wspd'].fillna(df['wspd'].mean())
        df['temp'] = df['temp'].fillna(df['temp'].mean())
        df['pres'] = df['pres'].fillna(df['pres'].mean())

        # Padronizar nomes das colunas: remover espaços, substituir por sublinhados e converter para minúsculas
    df.columns = [unidecode.unidecode(col.strip().replace(' ', '_').lower()) for col in df.columns]

    # Remover coluna 'unnamed:_0' se existir
    if 'unnamed:_0' in df.columns:
        df = df.drop(columns=['unnamed:_0'])

    # Normalizar texto em colunas de string: remover espaços em branco ao redor e padronizar para título
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip().str.title()

    # Remover acentuações dos dados de texto para padronização
    df = df.applymap(lambda x: unidecode.unidecode(x) if isinstance(x, str) else x)
    df.reset_index(inplace=True)

    return df


# Função principal
def main():
    # Configurações do S3

    prefixos = ['meteostat_diario/historico_diario_1950_2024.csv', 'meteostat_horario/horario_2020_2024.csv', 'densidade-demografica/densidade_demografica_2010.csv',
               'localizacoes/estacoes_metro.csv', 'localizacoes/localizacao_arborizacao_viaria.csv', 'localizacoes/localizacao_instituicoes_ensino.csv',
                'localizacoes/localizacao_servicos_saude_latlon.csv', 'ocorrencias/ocorrencias_com_distritos.csv', 'openweather/dados_previsao_meteorologica.csv']
    bucket_name = 'black-umbrella-fiap'


    for prefixo in prefixos:
        # Passos para atualizar o CSV
        df = acessar_csv_s3(bucket_name, prefixo)  # Baixar o CSV existente
        df_normalizado = normalizacao_dados(df, prefixo)  # Buscar novos dados
        csv_buffer = StringIO()
        df_normalizado.to_csv(csv_buffer, index=False)
        upload_csv_s3(bucket_name, prefixo, csv_buffer)  # Enviar o CSV atualizado de volta ao S3

if __name__ == '__main__':
    main()   