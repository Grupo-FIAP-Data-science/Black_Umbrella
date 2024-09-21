import pandas as pd
from feature_engine.encoding import OneHotEncoder

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

    # Criar a coluna target binária 'ocorrencia_target'
    df['ocorrencia_target'] = df['ocorrencia'].apply(lambda x: 0 if x == 'sem_ocorrencia' else 1)

    # Imputar valores nulos em 'distrito' com 'Unknown' e transformar em categórica
    df['distrito'].fillna('Unknown', inplace=True)
    df['distrito'] = df['distrito'].astype('category')

    # Target Encoding
    district_means = df.groupby('distrito')['ocorrencia_target'].mean()
    df['distrito_encoded'] = df['distrito'].map(district_means)

    # Extrair dia, mês e ano
    df['dia'] = df['data'].dt.day
    df['mes'] = df['data'].dt.month
    df['ano'] = df['data'].dt.year

    # Função para determinar a estação do ano
    def estacao_do_ano(data):
        mes = data.month
        dia = data.day
        if (mes == 12 and dia >= 21) or (mes in [1, 2]) or (mes == 3 and dia <= 20):
            return 'verao'
        elif (mes == 3 and dia >= 21) or (mes in [4, 5]) or (mes == 6 and dia <= 20):
            return 'outono'
        elif (mes == 6 and dia >= 21) or (mes in [7, 8]) or (mes == 9 and dia <= 22):
            return 'inverno'
        elif (mes == 9 and dia >= 23) or (mes in [10, 11]) or (mes == 12 and dia <= 20):
            return 'primavera'

    # Aplicar a função na coluna 'data' e criar a nova coluna 'estacao'
    df['estacao'] = df['data'].apply(estacao_do_ano)

    # Identificar e converter variáveis categóricas para 'category'
    cat_features = ['estacao']
    df[cat_features] = df[cat_features].astype('category')

    # Codificar variáveis categóricas usando OneHotEncoder
    onehot = OneHotEncoder(variables=cat_features)
    df = onehot.fit_transform(df)

    return df

# Exemplo de uso
# caminho_arquivo = '../Black_Umbrella/dados/integracao_ocorr_diario.csv'
# df = pd.read_csv(caminho_arquivo)
# df_preprocessado = preprocessar_dados(df)
# df_preprocessado.to_csv('../Black_Umbrella/dados/integracao_ocorr_diario_pre_processado.csv', index=False)