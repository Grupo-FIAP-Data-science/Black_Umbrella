import pandas as pd

# Função de pré-processamento
def preprocessar_dados(df):
    # Converter 'data' para datetime
    df['data'] = pd.to_datetime(df['data'])

    # Preencher valores nulos em 'ocorrencia' com 'sem_ocorrencia' e padronizar texto
    df['ocorrencia'].fillna('sem_ocorrencia', inplace=True)
    df['ocorrencia'] = df['ocorrencia'].str.lower().str.replace(' ', '_', regex=False)

    # Imputar valores faltantes para latitude e longitude com a média
    df['latitude_distrito'].fillna(df['latitude_distrito'].mean(), inplace=True)
    df['longitude_distrito'].fillna(df['longitude_distrito'].mean(), inplace=True)
    df['latitude_ocorrencia'].fillna(df['latitude_ocorrencia'].mean(), inplace=True)
    df['longitude_ocorrencia'].fillna(df['longitude_ocorrencia'].mean(), inplace=True)

    # Criar a coluna target binária 'ocorrencia_target' (1 se houve ocorrência, 0 caso contrário)
    df['ocorrencia_target'] = df['ocorrencia'].apply(lambda x: 0 if x == 'sem_ocorrencia' else 1)

    # Imputar valores nulos em 'distrito' com 'Unknown' e transformar em categórica
    df['distrito'].fillna('Unknown', inplace=True)
    df['distrito'] = df['distrito'].astype('category')

    return df

# Exemplo de uso
# caminho_arquivo = '../Black_Umbrella/dados/integracao_ocorr_diario.csv'
# df = pd.read_csv(caminho_arquivo)
# df_preprocessado = preprocessar_dados(df)