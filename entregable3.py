import pandas as pd
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.operators.redshift import RedshiftSQLOperator
from airflow.operators.python_operator import PythonOperator
from funciones import load

#               ************* PARÁMETROS Y DEFINICIÓN DEL DAG *************

default_args={
    'owner': 'Yamil',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)}

BC_dag = DAG(
    default_args=default_args,
    dag_id='entregable3',
    description='DAG para extracción, transformación y carga de datos',
    start_date=datetime(2023,8,23),
    schedule_interval="@daily",
    catchup=False)

#               ************* DEFINICIÓN DE TAREAS *************

# 1. Extracción, Transformación y Carga:
load = PythonOperator(
    task_id='extract_and_transform_data',
    python_callable=load,
    #op_args=["{{ ds }} {{ execution_date.hour }}"],
    dag=BC_dag)


