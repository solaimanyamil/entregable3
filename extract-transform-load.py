import pandas as pd
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.operators.redshift import RedshiftSQLOperator
from airflow.operators.python_operator import PythonOperator
from funciones import get_data_from_api, transform_data, load_data_to_redshift

#               ************* PARÁMETROS Y DEFINICIÓN DEL DAG *************

default_args={
    'owner': 'Yamil',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)}

BC_dag = DAG(
    default_args=default_args,
    dag_id='entregable3',
    description='DAG para extracción, transformación y carga de datos',
    start_date=datetime(2023,8,22),
    schedule_interval="@daily",
    catchup=False)

#               ************* FUNCIONES *************

def extract_and_transform():
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

def load():
    # Configurar la conexión con Amazon Redshift:
    df_transformed = df_final
    db_username = 'solaimanyamil_coderhouse'
    db_password = 'NbOb637sCW'
    db_name = 'data-engineer-database'
    db_host = 'data-engineer-cluster.cyhh5bfevlmn.us-east-1.redshift.amazonaws.com'
    db_port = '5439'

    # Cargar los datos en la tabla de Redshift:
    table_name = 'nba_players'
    schema_name = 'solaimanyamil_coderhouse'
    load_data_to_redshift(df_transformed, table_name, schema_name, db_username, db_password, db_name, db_host, db_port)


#                   ************* DEFINICIÓN DE LAS TAREAS *************


# 1. Extracción y transformación:
task_1 = PythonOperator(
    task_id='extract_and_transform_data',
    python_callable=extract_and_transform,
    #op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=BC_dag)

# 2. Conexión a Redshift:
task_2= PythonOperator(
    task_id="load_data_to_redshift",
    python_callable=load,
    #op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=BC_dag)


#                   ************* ORDEN DE LAS TAREAS *************


task_1 >> task_2
