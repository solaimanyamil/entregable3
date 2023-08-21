import requests
import json
import pandas as pd
from sqlalchemy import create_engine


def get_data_from_api(url):

    '''Función que hace la solicitud a la API y devuelve
    los datos en formato JSON.'''
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        next_url = data.get('next')
        if next_url:
            return data['results'], next_url
        else:
            return data['results'], None
    else:
        raise Exception(f"Error en la solicitud. Código de estado: {response.status_code}") 
        
def transform_data(data):
    
    '''Función que recibe datos en formato JSON,
    los transforma en un DF y realiza algunos ajustes
    para adaptar el DF a la tabla creada en Redshift.'''
    
    df = pd.json_normalize(data)
    
    # Cambiar nombres de columnas del DF para adaptarlo a la tabla de Redshift:
    df.rename(columns={
        'age': 'player_age',
        'PTS': 'points',
        'AST': 'asists',
        'STL': 'stils',
        'BLK': 'blocks',
        'TOV': 'turnovers'
    }, inplace=True)

    # Eliminar las columnas no deseadas del DataFrame:
    columns_to_drop = [
        'games_started',
        'field_goals',
        'field_attempts',
        'field_percent',
        'three_fg',
        'three_attempts',
        'three_percent',
        'two_fg',
        'two_attempts',
        'two_percent',
        'effect_fg_percent',
        'ft',
        'fta',
        'ft_percent',
        'ORB',
        'DRB',
        'TRB',
        'PF'
    ]
    df = df.drop(columns=columns_to_drop, errors='ignore')

    # Cambiar los tipos de datos del DF para adaptarlo a la tabla de Redshift:
    df = df.astype({
        'id': int,
        'player_name': str,
        'player_age': int,
        'games': int,
        'minutes_played': float,
        'points': int,
        'asists': int,
        'stils': int,
        'blocks': int,
        'turnovers': int,
        'team': str,
        'season': int
    })

    return df

def load_data_to_redshift(df_final, table_name, schema_name, db_username, db_password, db_name, db_host, db_port):
    
    '''Función que configura la conexión con Redshift
    y carga el DataFrame en la tabla nba_players.'''
    
    # Objeto de conexión al motor de BD:
    engine = create_engine(f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}')

    # Obtener los IDs existentes en la tabla (armado de query + ejecución):
    existing_ids_query = f'SELECT id FROM {schema_name}.{table_name}'
    existing_ids = pd.read_sql_query(existing_ids_query, engine)['id']
    
    # Filtrar el DF para eliminar los registros que ya existen en la tabla:
    df_no_duplicates = df_final[~df_final['id'].isin(existing_ids)]
    
    # Comprobar si quedan datos después de eliminar los duplicados:
    if df_no_duplicates.empty:
        print("No hay nuevos datos para cargar.")
        return

    # Cargar los datos en la tabla de Redshift (solo los que no están duplicados):
    df_no_duplicates.to_sql(table_name, engine, schema=schema_name, if_exists='append', index=False)
    print("Los datos han sido cargados exitosamente en Redshift.")
