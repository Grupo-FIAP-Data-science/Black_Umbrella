import pandas as pd
import unidecode
import warnings

warnings.filterwarnings("ignore")

# Função para padronizar dados do DataFrame
def padronizar_dados(df):
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

    # Verificar e remover duplicatas
    df.drop_duplicates(inplace=True)

    # Verificar e remover valores ausentes NaN
    df.dropna(inplace=True)
    
    return df

# Exemplo de uso
arquivo = '/home/ryanrodr/FIAP/Black_Umbrella/dados/codigos_distritos_msp.csv'
df = pd.read_csv(arquivo, sep=';', encoding='latin1')
df_padronizado = padronizar_dados(df)
print(df_padronizado)