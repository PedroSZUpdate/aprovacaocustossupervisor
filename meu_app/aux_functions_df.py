import mysql.connector
import pandas as pd
import re
import getpass
from datetime import datetime


def to_number(number_str):
    # Remove the currency symbol and spaces
    number_str = number_str.replace("R$", "").strip()
    # Replace the thousands separator and decimal separator
    number_str = number_str.replace('.', '').replace(',', '.')
    # Convert to float
    return float(number_str)


def to_string(number):
    # Check if the input is a string and replace the comma with a period
    if isinstance(number, str):
        number = number.replace(',', '.')
    # Convert the input to a float
    number = float(number)
    # Format the number with two decimal places
    number_str = f"{number:,.2f}"
    # Replace commas with periods for the thousands separator
    number_str = number_str.replace(',', 'temp').replace('.', ',').replace('temp', '.')
    # Add the currency symbol and space
    return "R$ " + number_str


def format_column(df, column_name):
    df[column_name] = df[column_name].apply(to_string)
    return df


def format_column_number(df, column_name):
    df[column_name] = df[column_name].apply(to_number)
    return df


def connect_db():
    host = 'ddelc7n35g3'
    db_user = 'all'
    password = 'senhafraca123@A'
    database = 'db_app_custo'

    # Connect to the database
    conn = mysql.connector.connect(
        user=db_user,
        password=password,
        host=host,
        database=database
    )
    return conn


def get_data_from_query(cursor, query):
    cursor.execute(query)

    # Fetch all rows from the result set
    rows = cursor.fetchall()

    # Get column names
    columns = [col[0] for col in cursor.description]

    # Create DataFrame
    df = pd.DataFrame(rows, columns=columns)

    return df


def map_month(column, to_text):
    # Define a dictionary mapping month names to month numbers
    month_mapping = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
        5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
        9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez', 16: 'N/A'
    }
    # Strip whitespace if the type is string
    column = column.apply(lambda x: x.strip() if isinstance(x, str) else x)
    # Define a dictionary mapping month numbers to month names
    month_mapping_inverse = {v: k for k, v in month_mapping.items()}

    if not to_text:
        # Map month numbers to month names
        return column.map(month_mapping_inverse)
    else:
        # Map month names to month numbers
        return column.map(month_mapping)


def map_month_one(value, to_text):
    # Define a dictionary mapping month names to month numbers
    month_mapping = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr',
        5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago',
        9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez', 16: 'N/A'
    }

    # Define a dictionary mapping month numbers to month names
    month_mapping_inverse = {v: k for k, v in month_mapping.items()}

    if not to_text:
        # Map month numbers to month names
        return month_mapping_inverse.get(value, 'Invalid month')
    else:
        # Map month names to month numbers
        return month_mapping.get(value, 'Invalid month')


def get_approv_info():
    conn = connect_db()
    cursor = conn.cursor()

    table_name1 = 'tbl_aprovacao_direto'
    table_name2 = 'tbl_aprovacao_fluxo'
    table_name3 = 'tbl_aprovacao_rateado'

    query_approv_direto = (
        f"SELECT "
        f"ORDEM, MES_PLAN, DESCR_ORDEM, TIPO_ORDEM, STATUS_USUARIO, RESPONSAVEL, "
        f"STATUS_SISTEMA, CENTRAB, CENTRO_CUSTO, CUSTO, MES_ATUAL, CRIADOR "
        f"FROM {table_name1} t1 "
        f"WHERE DT_ATUALIZACAO = CURDATE() "
        f"AND (ID, ORDEM, CENTRO_CUSTO) IN ("
        f"SELECT MAX(ID), ORDEM, CENTRO_CUSTO "
        f"FROM {table_name1} "
        f"GROUP BY ORDEM, CENTRO_CUSTO)"
    )

    query_em_approv = (  # Aprovadas Hoje pelo Gerente
        f"SELECT "
        f"ORDEM, MES_PLAN, DESCR_ORDEM, TIPO_ORDEM, STATUS_USUARIO, RESPONSAVEL, "
        f"STATUS_SISTEMA, CENTRAB, CENTRO_CUSTO, CUSTO, MES_ATUAL, CRIADOR "
        f"FROM {table_name2} t2 "
        f"WHERE STATUS = 'APROVADO' AND DATA_GF_APROVA > CURDATE() "
        f"AND (ID, ORDEM, CENTRO_CUSTO) IN ("
        f"SELECT MAX(ID), ORDEM, CENTRO_CUSTO "
        f"FROM {table_name2} "
        f"GROUP BY ORDEM, CENTRO_CUSTO)"
    )

    query_em_approv_rat = (
        f"SELECT "
        f"ORDEM, MES_PLAN, DESCR_ORDEM, TIPO_ORDEM, STATUS_USUARIO, RESPONSAVEL, "
        f"STATUS_SISTEMA, CENTRAB, CENTRO_CUSTO, CUSTO, CRIADOR "
        f"FROM {table_name3} t2 "
        f"WHERE STATUS = 'APROVADO' AND DATA_GF_APROVA > CURDATE() "  # MUDAR?
        f"AND (ID, ORDEM, CENTRO_CUSTO) IN ("
        f"SELECT MAX(ID), ORDEM, CENTRO_CUSTO "
        f"FROM {table_name3} "
        f"GROUP BY ORDEM, CENTRO_CUSTO)"
    )

    # Create DataFrame
    df_aprovada_hj = get_data_from_query(cursor, query_approv_direto)
    df_em_aprovacao = get_data_from_query(cursor, query_em_approv)
    df_em_aprovacao['MES_ATUAL'] = None
    df_rat_em_aprovacao = get_data_from_query(cursor, query_em_approv_rat)
    df_rat_em_aprovacao['MES_ATUAL'] = None
    df_aprovada_hj.fillna(0, inplace=True)
    df_em_aprovacao.fillna(0, inplace=True)
    df_rat_em_aprovacao.fillna(0, inplace=True)
    dfs_to_concat = [df for df in [df_aprovada_hj, df_em_aprovacao, df_rat_em_aprovacao] if
                     not df.empty]
    if dfs_to_concat:
        df = pd.concat(dfs_to_concat, ignore_index=True)
    else:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_all = df.copy()

    df = df[df['CRIADOR'].isin(list_user)]
    df.drop(columns=['CRIADOR'], inplace=True)
    # The ones approved today or in the process
    df_to_sum = df[['CUSTO', 'MES_ATUAL']].groupby('MES_ATUAL').sum().reset_index()
    total_custo_sum = df_to_sum['CUSTO'].sum()
    current_and_previous_custo_sum = df_to_sum.loc[df_to_sum['MES_ATUAL'].astype(int) <= current_month, 'CUSTO'].sum()

    total_row_sum = pd.DataFrame({'MES_ATUAL': [14], 'CUSTO': [total_custo_sum]})
    current_and_previous_row_sum = pd.DataFrame({'MES_ATUAL': [13], 'CUSTO': [current_and_previous_custo_sum]})
    df_to_sum = pd.concat([df_to_sum, current_and_previous_row_sum, total_row_sum], ignore_index=True)
    df_to_sum.rename(columns={'MES_ATUAL': 'MES', 'CUSTO': 'CUSTO_SUM'}, inplace=True)

    # The ones when changing the month that an order is currently planned to another
    df_to_subtract = df[['CUSTO', 'MES_PLAN']].groupby('MES_PLAN').sum().reset_index()
    total_custo_subtract = df_to_subtract['CUSTO'].sum()
    current_and_previous_custo_subtract = df_to_subtract.loc[
        df_to_subtract['MES_PLAN'].astype(int) <= current_month, 'CUSTO'].sum()

    total_row_subtract = pd.DataFrame({'MES_PLAN': [14], 'CUSTO': [total_custo_subtract]})
    current_and_previous_row_subtract = pd.DataFrame({'MES_PLAN': [13], 'CUSTO': [current_and_previous_custo_subtract]})
    df_to_subtract = pd.concat([df_to_subtract, current_and_previous_row_subtract, total_row_subtract],
                               ignore_index=True)
    df_to_subtract.rename(columns={'MES_PLAN': 'MES', 'CUSTO': 'CUSTO_SUB'}, inplace=True)

    df_all.rename(columns={
        "ORDEM": "Nº Ordem"
    }, inplace=True)

    df_all = df_all[["Nº Ordem"]]
    # Close cursor and connection
    cursor.close()
    conn.close()

    # Display DataFrame
    return df_all, df_to_sum, df_to_subtract


def get_movement_info():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_mov_saldo'

    # Execute the query
    query = (
        f"SELECT "
        f"REQUISITANTE, "
        f"RESPONSAVEL, "
        f"MES, "
        f"ANO, "
        f"VALOR, "
        f"STATUS "
        f"FROM {table_name} "
        f"WHERE STATUS = 'APROVADO'"
    )

    # Create DataFrame
    df = get_data_from_query(cursor, query)
    df = df[df['ANO'] == current_year]
    df.rename(columns={'RESPONSAVEL': 'Responsável'}, inplace=True)
    pd.set_option('display.max_columns', None)
    df = pd.merge(df, df_email, left_on='REQUISITANTE', right_on='Responsável', how='left')
    df.rename(columns={'USUARIO': 'USR_REQ'}, inplace=True)
    df.drop(columns=['Responsável_y', 'EMAIL_USUARIO', 'EMAIL_GF', 'EMAIL_GE'], inplace=True)
    df = pd.merge(df, df_email, left_on='Responsável_x', right_on='Responsável', how='left')
    df.rename(columns={'USUARIO': 'USR_APROVADOR'}, inplace=True)
    df.drop(columns=['Responsável_x', 'EMAIL_USUARIO', 'EMAIL_GF', 'EMAIL_GE'], inplace=True)

    df_to_sum_mov = df[(df['USR_REQ'].isin(list_user))].copy()

    df_to_sum_mov.rename(columns={'VALOR': 'CUSTO_SUM_MOV'}, inplace=True)
    df_to_sum_mov = df_to_sum_mov[['CUSTO_SUM_MOV', 'MES']]
    df_to_sum_mov = df_to_sum_mov.groupby('MES').sum().reset_index()
    total_row_sum = pd.DataFrame({'MES': [14], 'CUSTO_SUM_MOV': [df_to_sum_mov['CUSTO_SUM_MOV'].sum()]})
    current_and_previous_row_sum = pd.DataFrame({'MES': [13],
                                                 'CUSTO_SUM_MOV': [df_to_sum_mov.loc[df_to_sum_mov['MES'].astype(int)
                                                                                     <= current_month, 'CUSTO_SUM_MOV'].sum()]})
    df_to_sum_mov = pd.concat([df_to_sum_mov, current_and_previous_row_sum], ignore_index=True)
    df_to_sum_mov = pd.concat([df_to_sum_mov, total_row_sum], ignore_index=True)

    df_to_sub_mov = df[(df['USR_APROVADOR'].isin(list_user))].copy()

    df_to_sub_mov.rename(columns={'VALOR': 'CUSTO_SUB_MOV'}, inplace=True)
    df_to_sub_mov = df_to_sub_mov[['CUSTO_SUB_MOV', 'MES']]
    df_to_sub_mov = df_to_sub_mov.groupby('MES').sum().reset_index()
    total_row_sum = pd.DataFrame({'MES': [14], 'CUSTO_SUB_MOV': [df_to_sub_mov['CUSTO_SUB_MOV'].sum()]})
    current_and_previous_row_sum = pd.DataFrame({'MES': [13],
                                                 'CUSTO_SUB_MOV': [df_to_sub_mov.loc[df_to_sub_mov['MES'].astype(int)
                                                                                     <= current_month, 'CUSTO_SUB_MOV'].sum()]})
    df_to_sub_mov = pd.concat([df_to_sub_mov, current_and_previous_row_sum], ignore_index=True)
    df_to_sub_mov = pd.concat([df_to_sub_mov, total_row_sum], ignore_index=True)

    return df, df_to_sum_mov, df_to_sub_mov


def get_saldo(ano):
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_saldo_colegiado'

    # Execute the query
    query = (
        f"SELECT "
        f"RESPONSAVEL as Responsável, "
        f"MES, "
        f"ANO, "
        f"SALDO_COLEGIADO "
        f"FROM {table_name} "
        f"WHERE DT_ATUALIZACAO = CURDATE() "
        f"AND ANO = {ano}"
    )
    df_info_approv, df_to_sum, df_to_sub = get_approv_info()
    df_info_mov, df_to_sum_mov, df_to_sub_mov = get_movement_info()

    # Create DataFrame
    df = get_data_from_query(cursor, query)

    if user == "williamyamashita.gff" or user == "sagnaldo":
        pass
    else:
        df = pd.merge(df, df_email.drop(columns=['USUARIO', 'EMAIL_GE', 'EMAIL_USUARIO']), on='Responsável',
                      how='left')
        df['EMAIL_GF'] = df['EMAIL_GF'].str.replace('@suzano.com.br', '')
        df = df.groupby(['EMAIL_GF', 'MES', 'ANO'])['SALDO_COLEGIADO'].sum().reset_index()
        df = pd.merge(df, df_user, left_on='EMAIL_GF', right_on='USUARIO', how='left')
        df = df[df['USUARIO'].isin(list_user)]
        df.drop(columns=['USUARIO', 'EMAIL_GF'], inplace=True)

    df = df.drop(columns=['ANO'])
    df['MES'] = df['MES'].astype(int)

    df = df.groupby(['MES', 'Responsável'])['SALDO_COLEGIADO'].sum().reset_index()

    # Group by MES and calculate the sum of SALDO_COLEGIADO
    grouped_df = df.groupby('MES')['SALDO_COLEGIADO'].sum().reset_index()

    # Add a new row for the sum of SALDO_COLEGIADO for all MES values
    total_row = pd.DataFrame({'MES': [14], 'SALDO_COLEGIADO': [grouped_df['SALDO_COLEGIADO'].sum()]})

    # Add a new row for the sum of SALDO_COLEGIADO for current month and previous months
    current_and_previous_row = pd.DataFrame({'MES': [13],
                                             'SALDO_COLEGIADO': [
                                                 grouped_df.loc[
                                                     grouped_df['MES'] <= current_month, 'SALDO_COLEGIADO'].sum()]})

    grouped_df = pd.concat([grouped_df, current_and_previous_row], ignore_index=True)
    grouped_df = pd.concat([grouped_df, total_row], ignore_index=True)

    if not df_to_sum.empty:
        grouped_df = pd.merge(grouped_df, df_to_sum, on='MES', how='left')
    else:
        grouped_df['CUSTO_SUM'] = 0
    if not df_to_sub.empty:
        grouped_df = pd.merge(grouped_df, df_to_sub, on='MES', how='left')
    else:
        grouped_df['CUSTO_SUB'] = 0
    if not df_to_sum_mov.empty:
        grouped_df = pd.merge(grouped_df, df_to_sum_mov, on='MES', how='left')
    else:
        grouped_df['CUSTO_SUM_MOV'] = 0
    if not df_to_sub_mov.empty:
        grouped_df = pd.merge(grouped_df, df_to_sub_mov, on='MES', how='left')
    else:
        grouped_df['CUSTO_SUB_MOV'] = 0
    grouped_df['SALDO_COLEGIADO'] = (grouped_df['SALDO_COLEGIADO'] - grouped_df['CUSTO_SUB'].fillna(0) -
                                     grouped_df['CUSTO_SUB_MOV'].fillna(0) + grouped_df['CUSTO_SUM'].fillna(0)
                                     + grouped_df['CUSTO_SUM_MOV'].fillna(0))
    grouped_df = grouped_df.drop(columns=['CUSTO_SUM', 'CUSTO_SUB', 'CUSTO_SUM_MOV', 'CUSTO_SUB_MOV'])

    grouped_df['SALDO_COLEGIADO'] = grouped_df['SALDO_COLEGIADO'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))

    return grouped_df


def get_orders_all_permite(df_to_approve, df_compr):
    common_columns = ["Nº Ordem", "Descr. Ordem", "Centrab", 'Risco', 'Oport.', 'Custo', "Tp. Ordem",
                      "Stat. Sist.", "Stat. Usr.", "Centro de Custo", "Responsável", "Mês Atual", "Saldo Disp.",
                      "Revisão"]

    # Select required columns and add missing columns in one step
    df_to_approve = df_to_approve.reindex(columns=common_columns)
    df_compr = df_compr.reindex(columns=common_columns)

    # Concatenate DataFrames
    df = pd.concat([df_to_approve, df_compr], ignore_index=True)

    # Ensure "Nº Ordem" is of integer type
    df["Nº Ordem"] = df["Nº Ordem"].astype(int)

    return df


def get_email():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_responsavel_cc'

    # Execute the query
    query = (f"SELECT "
             f"RESPONSAVEL,"
             f"EMAIL_USUARIO,"
             f"EMAIL_GF,"
             f"EMAIL_GE,"
             f"USUARIO "
             f"FROM {table_name}"
             )

    # Create DataFrame
    df = get_data_from_query(cursor, query)

    agg_dict = {
        'EMAIL_USUARIO': 'max',
        'EMAIL_GF': 'max',
        'EMAIL_GE': 'max',
        'USUARIO': 'max'
    }

    df = df.groupby(['RESPONSAVEL']).agg(agg_dict).reset_index()
    df.rename(columns={'RESPONSAVEL': 'Responsável'}, inplace=True)
    # Close cursor and connection
    cursor.close()
    conn.close()

    # Display DataFrame
    return df


def get_saldo_table():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_saldo_colegiado'

    # Execute the query
    query = (
        f"SELECT "
        f"RESPONSAVEL, "
        f"MES, "
        f"ANO, "
        f"CENTRO_CUSTO, "
        f"SALDO_COLEGIADO "
        f"FROM {table_name} "
        f"WHERE DT_ATUALIZACAO = CURDATE() "
    )

    df_info_mov, df_to_sum_mov, df_to_sub_mov = get_movement_info()

    # Create DataFrame
    df = get_data_from_query(cursor, query)

    df.rename(columns={'RESPONSAVEL': 'Responsável',
                       'ANO': "Ano",
                       'MES': "Mês",
                       'SALDO_COLEGIADO': "Saldo Disp."
                       }, inplace=True)
    if user == "williamyamashita.gff" or user == "sagnaldo":
        pass
    else:
        df = pd.merge(df, df_email, on='Responsável', how='left')
        df['EMAIL_GF'] = df['EMAIL_GF'].str.replace('@suzano.com.br', '')
        df = df[df['EMAIL_GF'].isin(list_user)]

    df['Mês'] = df['Mês'].astype(int)

    # Get the values to sum or subtract
    df_to_sum_by_resp = df_info_mov.groupby(['REQUISITANTE', 'MES'])['VALOR'].sum().reset_index().copy()
    df_to_sum_by_resp.rename(columns={'REQUISITANTE': 'Responsável',
                                      'MES': "Mês",
                                      'VALOR': "VALOR_SUM"
                                      }, inplace=True)
    df_to_sum_by_resp['Ano'] = current_year
    df_to_sub_by_resp = df_info_mov.groupby(['Responsável', 'MES'])['VALOR'].sum().reset_index().copy()
    df_to_sub_by_resp.rename(columns={'MES': "Mês",
                                      'VALOR': "VALOR_SUB"
                                      }, inplace=True)
    df_to_sub_by_resp['Ano'] = current_year

    # Group by MES and calculate the sum of SALDO_COLEGIADO
    df = df.groupby(['Responsável', 'Mês', 'Ano'])['Saldo Disp.'].sum().reset_index()
    df = pd.merge(df, df_to_sum_by_resp, on=['Responsável', 'Mês', 'Ano'], how='left')
    df = pd.merge(df, df_to_sub_by_resp, on=['Responsável', 'Mês', 'Ano'], how='left')
    df['Saldo Disp.'] = df['Saldo Disp.'] + df['VALOR_SUM'].fillna(0) - df['VALOR_SUB'].fillna(0)
    df = df.drop(columns=['VALOR_SUM', 'VALOR_SUB'])
    df['Saldo Disp.'] = df['Saldo Disp.'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))
    df['Recebedor'] = ''
    df['Valor Solic.'] = ''
    df['Mês'] = map_month(df['Mês'], True)

    return df


def get_approv_mov_saldo():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_mov_saldo'

    # Execute the query
    query = (
        f"SELECT "
        f"REQUISITANTE, "
        f"RESPONSAVEL, "
        f"MES, "
        f"ANO, "
        f"VALOR, "
        f"STATUS "
        f"FROM {table_name}"
    )

    # Create DataFrame
    df = get_data_from_query(cursor, query)

    df.rename(columns={'RESPONSAVEL': 'Responsável',
                       'ANO': "Ano",
                       'MES': "Mês",
                       'VALOR': "Valor Solic."
                       }, inplace=True)

    if user == "williamyamashita.gff" or user == "sagnaldo":
        pass
    else:
        df = pd.merge(df, df_user, on='Responsável', how='left')
        df = df[(df['USUARIO'].isin(list_user))]
        # & (df['EMAIL_USUARIO'] != gf)
        df.drop(columns=['USUARIO'], inplace=True)

    df = df[(df['STATUS'] != 'APROVADO') & (df['STATUS'] != 'REPROVADO')]
    df['Mês'] = df['Mês'].astype(int)
    df.drop(columns=['Responsável', 'STATUS', 'ANO'], inplace=True)

    df['Valor Solic.'] = df['Valor Solic.'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))
    df['Mês'] = map_month(df['Mês'], True)
    return df


def get_dados_permite():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_ordens_permite'
    table_permite_approv = 'tbl_aprovado_permite'

    # Execute the query
    query = (
        f"SELECT "
        f"ORDEM as 'Nº Ordem', "
        f"DESCRICAO_ORDEM as 'Descr. Ordem', "
        f"CENTRAB as 'Centrab', "
        f"LI as 'LI', "
        f"DESCRICAO_LI as 'Descr. LI', "
        f"REVISAO as 'Revisão', "
        f"TIPO_ORDEM as 'Tp. Ordem', "
        f"RISCO as 'Risco', "
        f"OPORTUNIDADE as 'Oport.', "
        f"STATUS_SISTEMA as 'Stat. Sist.', "
        f"STATUS_USUARIO as 'Stat. Usr.', "
        f"CENTRO_CUSTO as 'Centro de Custo', "
        f"CUSTO_REAL_TOTAL as 'Custo', "
        f"RESPONSAVEL as 'Responsável', "
        f"APROVADOR as 'Aprovador' "
        f"FROM {table_name} "
        f"WHERE `PORCENTAGEM` = 100 AND DT_ATUALIZACAO = CURDATE() AND STATUS_SISTEMA NOT LIKE '%BLOQ%' "
        f"AND REVISAO NOT LIKE 'PG%'"
    )

    query_approv_today = (
        f"SELECT "
        f"ORDEM as 'Nº Ordem', APROVADOR "
        f"FROM {table_permite_approv} "
        f"WHERE `DT_ATUALIZACAO` = CURDATE()"
    )

    # Create DataFrame
    df_approv_today = get_data_from_query(cursor, query_approv_today)
    df = get_data_from_query(cursor, query)

    df = pd.merge(df, df_approv_today, on='Nº Ordem', how='left')
    df = df[df['APROVADOR'].isna()]
    df.drop(columns=['APROVADOR'], inplace=True)

    df['Custo'] = df['Custo'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))

    def extract_month(status):
        match = re.search(r'E(\d+)H', status)
        if match and int(match.group(1)) <= 12:
            return int(match.group(1))
        else:
            return 16

    df['Mês'] = map_month(df['Stat. Usr.'].apply(extract_month), True)

    if user == "williamyamashita.gff" or user == "sagnaldo":
        pass
    else:
        df = df[df['Aprovador'].isin(list_user)]
        df.drop(columns=['Aprovador'], inplace=True)

    try:
        df['Status'] = df.apply(lambda row:
                                "Risco abaixo 18 sem Oport." if 18 > int(row['Risco']) > 0 and row['Oport.'] == ''
                                else "Risco abaixo 18 (Op.)" if 18 > int(row['Risco']) > 0 and int(row['Oport.']) == 0
                                else "Risco abaixo 16 (PP)" if 16 > int(row['Risco']) > 0 and int(row['Oport.']) == 2
                                else "OK", axis=1)
    except:
        df['Status'] = ''

    def update_risco(row):
        if row['Risco'] == -1 and row['Tp. Ordem'] in ['PM05', 'PM03', 'PM04', 'PM11']:
            return "PREV"
        else:
            return row['Risco']

    def update_risco_order(row):
        if row['Status'] != "OK":
            return -100 + row['Risco']
        if row['Risco'] == -1 and row['Tp. Ordem'] in ['PM05', 'PM03', 'PM04', 'PM11'] and row['Mês'] == "N/A":
            return 40
        if row['Risco'] == -1 and row['Tp. Ordem'] in ['PM05', 'PM03', 'PM04', 'PM11'] and row['Mês'] != "N/A":
            return 50
        else:
            return row['Risco']

    df['Risco_order'] = 0
    # Apply the function to update 'RISCO'
    df['Risco_order'] = df.apply(update_risco_order, axis=1)
    df['Risco'] = df.apply(update_risco, axis=1)
    df = df.sort_values(by='Risco_order', ascending=False)
    if current_month == 12:
        df['Ano'] = current_year + 1
    else:
        df['Ano'] = current_year
    df_saldo = get_saldo_table()
    df_saldo.drop(columns=['Valor Solic.'], inplace=True)
    df = pd.merge(df, df_saldo, on=['Responsável', 'Mês', 'Ano'], how='left')
    df.drop(columns=['Ano'], inplace=True)
    # Close cursor and connection
    cursor.close()
    conn.close()

    # Display DataFrame
    return df


def get_em_aprov():
    conn = connect_db()
    cursor = conn.cursor()

    table_name1 = 'tbl_aprovacao_fluxo'
    table_name2 = 'tbl_aprovacao_rateado'
    table_desbloq = 'sap_desbloqueadas'

    query_em_approv = (
        f"SELECT "
        f"ORDEM, DESCR_ORDEM, MES_PLAN, ANO, CUSTO, RISCO, OPORTUNIDADE, RESPONSAVEL, EMAIL_GF, EMAIL_GE, "
        f"STATUS_USUARIO, STATUS_SISTEMA, CENTRAB, STATUS, REVISAO "
        f"FROM {table_name1} "
        f"WHERE STATUS = 'EM APROVACAO GF'")

    query_em_approv_rat = (
        f"SELECT "
        f"ORDEM, "
        f"MAX(DESCR_ORDEM) AS DESCR_ORDEM, MAX(MES_PLAN) AS MES_PLAN, MAX(ANO) AS ANO, SUM(CUSTO) AS CUSTO, "
        f"MAX(RISCO) AS RISCO, MAX(OPORTUNIDADE) AS OPORTUNIDADE, MAX(RESPONSAVEL) AS RESPONSAVEL, "
        f"MAX(EMAIL_GF) AS EMAIL_GF, MAX(EMAIL_GE) AS EMAIL_GE, MAX(STATUS_USUARIO) AS STATUS_USUARIO, "
        f"MAX(STATUS_SISTEMA) AS STATUS_SISTEMA, MAX(CENTRAB) AS CENTRAB, MAX(STATUS) AS STATUS,MAX(REVISAO) AS REVISAO "
        f"FROM {table_name2} "
        f"WHERE STATUS = 'EM APROVACAO GF' "
        f"GROUP BY ORDEM"
    )

    query_desbloq = (
        f"SELECT "
        f"ORDEM, DT_DESBLOQ "
        f"FROM {table_desbloq} "
        f"WHERE DT_DESBLOQ BETWEEN CURDATE() - INTERVAL 90 DAY AND CURDATE()")

    df_em_aprovacao = get_data_from_query(cursor, query_em_approv)
    df_rat_em_aprovacao = get_data_from_query(cursor, query_em_approv_rat)
    df_em_aprovacao.dropna(axis=1, how='all', inplace=True)
    df_rat_em_aprovacao.dropna(axis=1, how='all', inplace=True)
    df = pd.concat([df_em_aprovacao, df_rat_em_aprovacao], ignore_index=True)

    df_desbloq = get_data_from_query(cursor, query_desbloq)

    if df.empty:
        df = pd.DataFrame(columns=[
            'Nº Ordem', 'Descr. Ordem', 'Oport.', 'Custo', 'Risco', 'Responsável', 'Centrab', 'Stat. Usr.',
            'Stat. Sist.', 'Mês', 'Ano', 'Saldo Disp.', 'Revisão'
        ])
        return df

    if not df_desbloq.empty:
        df = pd.merge(df, df_desbloq, on='ORDEM', how='left')
        df = df[~(df['STATUS_SISTEMA'].str.contains('BLOQ') & df['DT_DESBLOQ'].isna())]
        df.drop(columns=['DT_DESBLOQ'], inplace=True)

    if user == "williamyamashita.gff" or user == "sagnaldo":
        pass
    else:
        if user in df.loc[df['ID'].idxmax()]['EMAIL_GE']:
            df = df[df['STATUS'].str.contains('GE', na=False)]
        else:
            df['EMAIL_GF'] = df['EMAIL_GF'].str.replace('@suzano.com.br', '')
            df = df[df['EMAIL_GF'].isin(list_user)]

    df.drop(columns=['EMAIL_GF', 'EMAIL_GE', 'STATUS'], inplace=True)

    df.rename(columns={
        "ORDEM": "Nº Ordem",
        "DESCR_ORDEM": "Descr. Ordem",
        "MES_PLAN": "Mês",
        "ANO": "Ano",
        "OPORTUNIDADE": "Oport.",
        "CUSTO": "Custo",
        "RISCO": "Risco",
        "RESPONSAVEL": "Responsável",
        "CENTRAB": "Centrab",
        "STATUS_USUARIO": "Stat. Usr.",
        "STATUS_SISTEMA": "Stat. Sist.",
        "REVISAO": "Revisão"
    }, inplace=True)

    df['Mês'] = map_month(df['Mês'], True)
    df['Custo'] = df['Custo'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))
    df[['Oport.', 'Risco']] = df[['Oport.', 'Risco']].replace({None: ''})
    df_saldo = get_saldo_table()
    df_saldo.drop(columns=['Valor Solic.', 'Recebedor'], inplace=True)
    df = pd.merge(df, df_saldo, on=['Responsável', 'Mês', 'Ano'], how='left')

    return df


def get_list_substituto():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_substituto'

    # Execute the query
    query = (f"SELECT "
             f"RESPONSAVEL,"
             f"SUBSTITUTO, "
             f"STATUS "
             f"FROM {table_name}"
             )

    # Create DataFrame
    df = get_data_from_query(cursor, query)

    df1 = df[df['RESPONSAVEL'] == user]
    df2 = df[(df['SUBSTITUTO'] == user) & (df['STATUS'] == "ATIVO")]

    list_return = df1['SUBSTITUTO'].tolist() + df2['RESPONSAVEL'].tolist()
    # Close cursor and connection
    cursor.close()
    conn.close()

    # Display DataFrame
    return list_return


user = getpass.getuser().lower()
list_user = [user] + get_list_substituto()

current_year = datetime.now().year
current_month = datetime.now().month

pd.set_option('display.max_columns', None)
pd.set_option('future.no_silent_downcasting', True)


df_email = get_email()
df_user = df_email.drop(columns=['EMAIL_GF', 'EMAIL_GE', 'EMAIL_USUARIO'])

