import pandas as pd
import numpy as np
import getpass
import pymysql
import subprocess
from datetime import datetime

user = getpass.getuser()
main_dir = f"C:\\Users\\{user}\\OneDrive - Suzano S A\\Dados Indicadores\\Dados App Custo"
dir_perm = f"C:\\Users\\{user}\\OneDrive - Suzano S A\\Dados Indicadores\\Dados Custo Compromissado\\Permite"
dir_aux_gpm = f"C:\\Users\\{user}\\OneDrive - Suzano S A\\IndicadoresManutencaoLimeira\\11.Auxiliares"
current_month = datetime.now().month
current_year = datetime.now().year
pd.set_option('display.max_columns', None)


def get_df(tipo):
    if tipo == "tbl_ordens_colegiado":
        """AUXILIARES"""
        df_custo = get_df("tbl_ordens_custo")
        df_custo = df_custo[['ORDEM', 'CUSTO_REAL_TOTAL']]
        df_custo['ORDEM'] = df_custo['ORDEM'].astype('int64', errors='ignore').dropna()
        df_norma = get_df("tbl_norma_apropriacao")
        df_norma = df_norma[['ORDEM', 'CENTRO_CUSTO', 'PORCENTAGEM']]
        df_resp = get_df("tbl_responsavel_cc")

        df_corretivas = pd.read_excel(main_dir + "\\Ordens Corretivas.xlsx")
        df_preventivas = pd.read_excel(main_dir + "\\Ordens Preventivas.xlsx")
        df_corretivas.columns = ["ORDEM", "SUPERVISOR"]
        df_preventivas.columns = ["ORDEM", "SUPERVISOR"]
        df_combined = pd.concat([df_corretivas, df_preventivas], ignore_index=True)
        df_combined = df_combined.drop_duplicates()
        df_combined["SUPERVISOR"] = df_combined["SUPERVISOR"].str.title()

        """INICIO"""
        df = pd.read_csv(main_dir + "\\ziw38.txt", sep='|', skiprows=[0, 1, 2, 4], encoding='1252', header=0,
                         on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
        df = df.iloc[:, 1:-1].dropna()
        df['Ordem'] = df['Ordem'].astype('int64', errors='ignore').dropna()
        df['DT_ATUALIZACAO'] = datetime.today().date()
        df.columns.values[0:20] = ['ORDEM', 'DESCRICAO_ORDEM', 'CENTRAB', 'LI', 'DESCRICAO_LI', 'REVISAO', 'DT_PLAN',
                                   'TIPO_ORDEM', 'RISCO', 'OPORTUNIDADE', 'GPM', 'STATUS_USUARIO', 'STATUS_SISTEMA',
                                   'CUSTO_PLAN', 'CUSTO_REAL', 'NOTA', 'DATA_NOTA', 'CRIADO_POR', 'PRIORIDADE',
                                   'DT_ATUALIZACAO']

        df = df.drop(['PRIORIDADE', 'CUSTO_PLAN', 'CUSTO_REAL'], axis=1)
        df = pd.merge(df, df_combined, on='ORDEM', how='left')

        # Define a function to update 'RISCO' based on conditions
        def update_risco(row):
            if row['RISCO'] == "" and row['TIPO_ORDEM'] in ['PM05', 'PM03', 'PM04', 'PM11']:
                return -1
            else:
                return row['RISCO']

        # Apply the function to update 'RISCO'
        df['RISCO'] = df.apply(update_risco, axis=1)

        df = pd.merge(df, df_custo, on='ORDEM', how='left')
        df = pd.merge(df, df_norma, on='ORDEM', how='left')
        df = pd.merge(df, df_resp, on='CENTRO_CUSTO', how='left')
        df = df.where(pd.notnull(df), None)

        df['RESPONSAVEL'] = df['RESPONSAVEL'].fillna("VAZIO")
        df = df.groupby(['ORDEM', 'RESPONSAVEL']).agg({
            'DESCRICAO_ORDEM': 'max',
            'CENTRAB': 'max',
            'LI': 'max',
            'DESCRICAO_LI': 'max',
            'REVISAO': 'max',
            'DT_PLAN': 'max',
            'TIPO_ORDEM': 'max',
            'RISCO': 'max',
            'OPORTUNIDADE': 'max',
            'GPM': 'max',
            'STATUS_USUARIO': 'max',
            'STATUS_SISTEMA': 'max',
            'NOTA': 'max',
            'DATA_NOTA': 'max',
            'CRIADO_POR': 'max',
            'DT_ATUALIZACAO': 'max',
            'CUSTO_REAL_TOTAL': 'sum',
            'CENTRO_CUSTO': 'max',
            'PORCENTAGEM': 'sum',
            'SUPERVISOR': 'max'
        }).reset_index()
        df['PORCENTAGEM'] = df['PORCENTAGEM'].clip(upper=100)
        df = df.fillna(np.nan).replace([np.nan], [None])
        df['CUSTO_REAL_TOTAL'] = (df['PORCENTAGEM'] * df['CUSTO_REAL_TOTAL']) / 100

    if tipo == "tbl_norma_apropriacao":
        df = pd.read_csv(main_dir + "\\sq01_07.txt", sep='|', skiprows=[0, 1, 2, 3, 5], encoding='1252', header=0,
                         on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
        df = df.iloc[:, 1:-1].dropna()
        df['Ordem'] = df['Ordem'].astype('int64')
        df['DT_ATUALIZACAO'] = datetime.today().date()
        df.columns.values[0:7] = ['ORDEM', 'CENTRO_CUSTO',
                                  'PORCENTAGEM', 'MES_DE', 'MES_ATE', 'ANO_DE', 'ANO_ATE']
        df['PORCENTAGEM'] = df['PORCENTAGEM'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

        def check_criteria(group):
            # Convert 'MES_ATE' and 'ANO_ATE' to integers, fill empty strings with 0
            group['MES_ATE'] = group['MES_ATE'].replace('', '0').astype(int)
            group['ANO_ATE'] = group['ANO_ATE'].replace('', '0').astype(int)

            # Filter rows where year matches current year and month is less than or equal to the current month
            valid_rows = group[(group['ANO_ATE'] == current_year) & (group['MES_ATE'] >= current_month)]
            if not valid_rows.empty:
                return valid_rows

            # Otherwise, return rows where 'MES_ATE' is '000' or empty
            return group[(group['MES_ATE'] == 0) & (group['ANO_ATE'] == 0)]

        df = df.groupby('ORDEM', group_keys=False)[['ORDEM', 'CENTRO_CUSTO', 'PORCENTAGEM', 'MES_DE', 'MES_ATE',
                                                    'ANO_DE', 'ANO_ATE']].apply(check_criteria).reset_index(drop=True)

    if tipo == "tbl_ordens_custo":
        df = pd.read_csv(main_dir + "\\zpm90.txt", sep='|',
                         skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11], encoding='1252', header=0, on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
        df = df.iloc[:, 1:-1].dropna()
        df.columns.values[0:12] = ['ORDEM', 'CUSTO_PLAN_MAT', 'CUSTO_PLAN_SERV', 'CUSTO_PLAN_MO', 'CUSTO_PLAN_OUTRO',
                                   'CUSTO_PLAN_TOTAL', 'CUSTO_REAL_MAT', 'CUSTO_REAL_SERV', 'CUSTO_REAL_MO',
                                   'CUSTO_REAL_OUTRO', 'CUSTO_REAL_TOTAL']
        # Columns to convert to Decimal
        columns_to_convert = ['CUSTO_PLAN_MAT', 'CUSTO_PLAN_SERV', 'CUSTO_PLAN_MO', 'CUSTO_PLAN_OUTRO',
                              'CUSTO_PLAN_TOTAL', 'CUSTO_REAL_MAT', 'CUSTO_REAL_SERV', 'CUSTO_REAL_MO',
                              'CUSTO_REAL_OUTRO', 'CUSTO_REAL_TOTAL']
        for col in columns_to_convert:
            df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

        df = df.groupby('ORDEM', as_index=False)[columns_to_convert].sum()
        df['DT_ATUALIZACAO'] = datetime.today().date()

    if tipo == "tbl_saldo_colegiado":
        df = pd.read_excel(main_dir + "\\Saldo Colegiado.xlsx")
        df.columns = df.columns.str.strip()
        df.rename(columns={
            'Centros de Custos[RESPONSÁVEL]': 'RESPONSAVEL',
            'Mês[num_mês]': 'MES',
            '[Saldo_Colegiado]': 'SALDO_COLEGIADO',
            'Centros de Custos[CCS]': 'CENTRO_CUSTO',
            'Ano[ano]': 'ANO'
        }, inplace=True)
        df['SALDO_COLEGIADO'] = df['SALDO_COLEGIADO'].astype(float)
        df = df[df['ANO'] > 2023]
        df['DT_ATUALIZACAO'] = datetime.today().date()

    if tipo == "tbl_responsavel_cc":
        df = pd.read_excel(main_dir + "\\Responsável CC.xlsx")
        df.columns = df.columns.str.strip()
        df = df.iloc[:, 3:]
        df = df.fillna(np.nan).replace([np.nan], [None])

    if tipo == "tbl_ordens_compromissado":
        df = pd.read_excel(main_dir + "\\Compromissado Colegiado.xlsx")
        df.columns = df.columns.str.strip()
        df.columns.values[0:11] = [
            'ORDEM', 'DESCRICAO_ORDEM', 'RESPONSAVEL', 'TIPO_ORDEM', 'STATUS_USUARIO',
            'STATUS_SISTEMA', 'REVISAO', 'CENTRAB', "CENTRO_CUSTO", 'CUSTO', 'MES_PLAN'
        ]

        df['CUSTO'] = df['CUSTO'].astype(float)
        df['DT_ATUALIZACAO'] = datetime.today().date()
        df = df.fillna(np.nan).replace([np.nan], [None])

    if tipo == "tbl_ordens_permite":
        """AUXILIAR"""
        df_zpm90 = pd.read_csv(main_dir + "\\permite_zpm90.txt", sep='|',
                               skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11], encoding='1252', header=0,
                               on_bad_lines='skip')
        df_zpm90.columns = df_zpm90.columns.str.strip()
        df_zpm90 = df_zpm90.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
        df_zpm90 = df_zpm90.iloc[:, 1:-1].dropna()
        df_zpm90.columns.values[0:12] = ['ORDEM', 'CUSTO_PLAN_MAT', 'CUSTO_PLAN_SERV', 'CUSTO_PLAN_MO',
                                         'CUSTO_PLAN_OUTRO',
                                         'CUSTO_PLAN_TOTAL', 'CUSTO_REAL_MAT', 'CUSTO_REAL_SERV', 'CUSTO_REAL_MO',
                                         'CUSTO_REAL_OUTRO', 'CUSTO_REAL_TOTAL']
        # Columns to convert to Decimal
        columns_to_convert = ['CUSTO_REAL_TOTAL']
        df_zpm90['CUSTO_REAL_TOTAL'] = df_zpm90['CUSTO_REAL_TOTAL'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
        df_zpm90 = df_zpm90.groupby('ORDEM', as_index=False)[columns_to_convert].sum()
        df_zpm90['ORDEM'] = df_zpm90['ORDEM'].astype('int64', errors='ignore').dropna()

        df_norma = pd.read_csv(main_dir + "\\permite_sq01_07.txt", sep='|', skiprows=[0, 1, 2, 3, 5], encoding='1252',
                               header=0, on_bad_lines='skip')
        df_norma.columns = df_norma.columns.str.strip()
        df_norma = df_norma.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
        df_norma = df_norma.iloc[:, 1:-1].dropna()
        df_norma['Ordem'] = df_norma['Ordem'].astype('int64')
        df_norma.columns.values[0:7] = ['ORDEM', 'CENTRO_CUSTO',
                                        'PORCENTAGEM', 'MES_DE', 'MES_ATE', 'ANO_DE', 'ANO_ATE']
        df_norma['PORCENTAGEM'] = df_norma['PORCENTAGEM'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)

        def check_criteria(group):
            # Convert 'MES_ATE' and 'ANO_ATE' to integers, fill empty strings with 0
            group['MES_ATE'] = group['MES_ATE'].replace('', '0').astype(int)
            group['ANO_ATE'] = group['ANO_ATE'].replace('', '0').astype(int)

            # Filter rows where year matches current year and month is less than or equal to the current month
            valid_rows = group[(group['ANO_ATE'] == current_year) & (group['MES_ATE'] >= current_month)]
            if not valid_rows.empty:
                return valid_rows

            # Otherwise, return rows where 'MES_ATE' is '000' or empty
            return group[(group['MES_ATE'] == 0) & (group['ANO_ATE'] == 0)]

        df_norma = df_norma.groupby('ORDEM', group_keys=False)[['ORDEM', 'CENTRO_CUSTO', 'PORCENTAGEM', 'MES_DE', 'MES_ATE',
             'ANO_DE', 'ANO_ATE']].apply(check_criteria, include_groups=True).reset_index(drop=True)

        df_resp = get_df("tbl_responsavel_cc")
        df_centrab = pd.read_excel(dir_aux_gpm + "\\Aux_GPM.xlsx", sheet_name="Planilha1")
        df_centrab = df_centrab[['Área GPM', 'CTR']]
        df_centrab = df_centrab.dropna(subset=['Área GPM', 'CTR'])
        df_centrab = df_centrab[~df_centrab['Área GPM'].str.contains('Expurg')]
        df_centrab = df_centrab[~df_centrab['CTR'].str.contains('_')]
        mapping_area = {
            'LMPDPP': 'Papel',
            'LMPDUR': 'Celulose',
            'LLUBPP': 'Papel',
            'LLUBUR': 'Celulose'
        }
        new_rows = pd.DataFrame({
            'CTR': ['LADMCM'],
            'Área GPM': ['CTM']
        })
        df_centrab = pd.concat([df_centrab, new_rows], ignore_index=True)
        df_centrab['Área GPM'] = df_centrab['CTR'].map(mapping_area).fillna(df_centrab['Área GPM'])
        mapping_aprovador = {
            'Papel': 'rcunha',
            'Celulose': 'rgiubbina',
            'CTM': 'lgustavo',
            'Confiabilidade': 'shortolan',
            'Fabricar': 'lgustavo'
        }
        df_centrab['APROVADOR1'] = df_centrab['Área GPM'].map(mapping_aprovador)
        df_centrab = df_centrab.drop(columns=['Área GPM'])

        """INICIO"""
        df = pd.read_csv(main_dir + "\\permite_ziw38.txt", sep='|', skiprows=[0, 1, 2, 4], encoding='1252', header=0)
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
        df = df.iloc[:, 1:-1].dropna()
        df['Ordem'] = df['Ordem'].astype('int64', errors='ignore').dropna()
        df['DT_ATUALIZACAO'] = datetime.today().date()
        df.columns.values[0:20] = ['ORDEM', 'DESCRICAO_ORDEM', 'CENTRAB', 'LI', 'DESCRICAO_LI', 'REVISAO', 'DT_PLAN',
                                   'TIPO_ORDEM', 'RISCO', 'OPORTUNIDADE', 'GPM', 'STATUS_USUARIO', 'STATUS_SISTEMA',
                                   'CUSTO_PLAN', 'CUSTO_REAL', 'NOTA', 'DATA_NOTA', 'CRIADO_POR', 'PRIORIDADE',
                                   'DT_ATUALIZACAO']

        df = df.drop(['PRIORIDADE', 'CUSTO_PLAN', 'CUSTO_REAL'], axis=1)

        # Define a function to update 'RISCO' based on conditions
        def update_risco(row):
            if row['RISCO'] == "" and row['TIPO_ORDEM'] in ['PM05', 'PM03', 'PM04', 'PM11']:
                return -1
            else:
                return row['RISCO']

        # Apply the function to update 'RISCO'
        df['RISCO'] = df.apply(update_risco, axis=1)

        df = pd.merge(df, df_zpm90, on='ORDEM', how='left')
        df = pd.merge(df, df_norma, on='ORDEM', how='left')
        df = pd.merge(df, df_resp, on='CENTRO_CUSTO', how='left')
        df = df.where(pd.notnull(df), None)
        df['RESPONSAVEL'] = df['RESPONSAVEL'].fillna("VAZIO")
        df = df.groupby(['ORDEM', 'RESPONSAVEL']).agg({
            'DESCRICAO_ORDEM': 'max',
            'CENTRAB': 'max',
            'LI': 'max',
            'DESCRICAO_LI': 'max',
            'REVISAO': 'max',
            'DT_PLAN': 'max',
            'TIPO_ORDEM': 'max',
            'RISCO': 'max',
            'OPORTUNIDADE': 'max',
            'GPM': 'max',
            'STATUS_USUARIO': 'max',
            'STATUS_SISTEMA': 'max',
            'NOTA': 'max',
            'DATA_NOTA': 'max',
            'CRIADO_POR': 'max',
            'DT_ATUALIZACAO': 'max',
            'CUSTO_REAL_TOTAL': 'sum',
            'CENTRO_CUSTO': 'max',
            'PORCENTAGEM': 'sum',
            'GERENCIA': 'max',
            'GF_APROVADOR': 'max'
        }).reset_index()
        df['CUSTO_REAL_TOTAL'] = (df['PORCENTAGEM'] * df['CUSTO_REAL_TOTAL']) / 100
        df = pd.merge(df, df_centrab, left_on='CENTRAB', right_on='CTR', how='left')
        df['APROVADOR'] = df.apply(lambda row:
                                   row['GF_APROVADOR'] if pd.notna(row['GF_APROVADOR']) else row['APROVADOR1'], axis=1)
        df = df.drop(['APROVADOR1', 'GF_APROVADOR', 'CTR'], axis=1)
        df = df.fillna(np.nan).replace([np.nan], [None])

    return df


# get_df('tbl_norma_apropriacao')

# get_df('tbl_ordens_colegiado')

# get_df("tbl_ordens_custo")

# get_df("tbl_saldo_colegiado")

# print(get_df("tbl_responsavel_cc"))

# print(get_df("tbl_ordens_compromissado"))

# print(get_df("tbl_ordens_permite"))


def insert_df_to_mariadb(df, table_name, host, db_user, password, database):
    # Establish a connection to the MariaDB database
    connection = pymysql.connect(
        host=host,
        user=db_user,
        password=password,
        database=database
    )

    # Create a cursor object using the connection
    cursor = connection.cursor()

    # Get today's date in the format matching DT_ATUALIZACAO column
    # today_date = datetime.now().strftime('%Y-%m-%d')

    delete_query = f"TRUNCATE {table_name}"
    cursor.execute(delete_query)

    # Prepare SQL query to insert DataFrame records into the database
    columns = ', '.join(df.columns)
    placeholders = ', '.join(['%s'] * len(df.columns))

    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    # Convert DataFrame rows to a list of tuples
    data = [tuple(row) for row in df.values]

    # Execute the insertion query
    cursor.executemany(insert_query, data)

    # Commit changes to the database
    connection.commit()
    print("Data inserted successfully!")

    if cursor:
        cursor.close()
    if connection:
        connection.close()


host = 'ddelc7n35g3'
db_user = 'all'
password = 'senhafraca123@A'
database = 'db_app_custo'

# insert_df_to_mariadb(
#     df=get_df('tbl_norma_apropriacao'), table_name='tbl_norma_apropiacao', host=host,
#     db_user=db_user, password=password, database=database)
#
# insert_df_to_mariadb(
#     df=get_df('tbl_ordens_custo'), table_name='tbl_ordens_custo', host=host,
#     db_user=db_user, password=password, database=database)

vbscript_path = main_dir + "\\Atualiza.vbs"
subprocess.call(['cscript', vbscript_path])

insert_df_to_mariadb(
    df=get_df('tbl_responsavel_cc'), table_name='tbl_responsavel_cc', host=host,
    db_user=db_user, password=password, database=database)

insert_df_to_mariadb(
    df=get_df('tbl_ordens_compromissado'), table_name='tbl_ordens_compromissado', host=host,
    db_user=db_user, password=password, database=database)

insert_df_to_mariadb(
    df=get_df('tbl_saldo_colegiado'), table_name='tbl_saldo_colegiado', host=host,
    db_user=db_user, password=password, database=database)

insert_df_to_mariadb(
    df=get_df('tbl_ordens_colegiado'), table_name='tbl_ordens_colegiado', host=host,
    db_user=db_user, password=password, database=database)

insert_df_to_mariadb(
    df=get_df('tbl_ordens_permite'), table_name='tbl_ordens_permite', host=host,
    db_user=db_user, password=password, database=database)

