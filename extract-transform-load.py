import pandas as pd
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.operators.redshift import RedshiftSQLOperator
from airflow.operators.python_operator import PythonOperator
from funciones import get_data_from_api, transform_data, load_data_to_redshift


#               ************* FUNCIONES *************

def extract():
    # Lista de temporadas consultadas:
    seasons = [2023, 2011]
    
    # Lista para almacenar los DataFrames de todas las temporadas:
    all_dfs = []
    
    for season in seasons:
        url = f'https://nba-stats-db.herokuapp.com/api/playerdata/topscorers/playoffs/{season}/'
        all_results = []
        while url:
            data, url = get_data_from_api(url)
            all_results.extend(data)
            if url is None:
                break  
            
        # Transformar los datos y obtener el DataFrame resultante:
        df = transform_data(all_results)
        # Agregar el DataFrame al listado de DataFrames:
        all_dfs.append(df)

    # Combinar todos los DataFrames en uno solo:
    df_final = pd.concat(all_dfs, ignore_index=True)
    
    # Retorna el DataFrame final:
    return df_final


def transform(df_final):
    return transform_data(df_final)


def load(df_transformed):

    # Configurar la conexión con Amazon Redshift:
    db_username = 'solaimanyamil_coderhouse'
    db_password = 'NbOb637sCW'
    db_name = 'data-engineer-database'
    db_host = 'data-engineer-cluster.cyhh5bfevlmn.us-east-1.redshift.amazonaws.com'
    db_port = '5439'

    # Cargar los datos en la tabla de Redshift:
    table_name = 'nba_players'
    schema_name = 'solaimanyamil_coderhouse'
    load_data_to_redshift(df_transformed, table_name, schema_name, db_username, db_password, db_name, db_host, db_port)


#               ************* PARÁMETROS Y DEFINICIÓN DEL DAG *************


default_args={
    'owner': 'Yamil',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)}

BC_dag = DAG(
    default_args=default_args,
    dag_id='entregable3',
    description='DAG para extracción, transformación y carga de datos',
    start_date=datetime(2023,8,21),
    schedule_interval="@daily",
    catchup=False)


#                   ************* DEFINICIÓN DE LAS TAREAS *************


# 1. Extracción:
task_1 = PythonOperator(
    task_id='extract_data',
    python_callable=extract,
    #op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=BC_dag)

# 2. Transformación:
task_2 = PythonOperator(
    task_id='transform_data',
    python_callable=transform,
    #op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=BC_dag)

# 3. Conexión a Redshift:
task_3= PythonOperator(
    task_id="load_data_to_redshift",
    python_callable=load,
    #op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=BC_dag)


#               ************* ORDEN DE LAS TAREAS *************


task_1 >> task_2 >> task_3
