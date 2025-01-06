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

    query_em_approv = (
        f"SELECT "
        f"ORDEM, MES_PLAN, DESCR_ORDEM, TIPO_ORDEM, STATUS_USUARIO, RESPONSAVEL, "
        f"STATUS_SISTEMA, CENTRAB, CENTRO_CUSTO, CUSTO, MES_ATUAL, CRIADOR "
        f"FROM {table_name2} t2 "
        f"WHERE STATUS <> 'APROVADO' AND STATUS <> 'REPROVADO' "
        f"AND (ID, ORDEM, CENTRO_CUSTO) IN ("
        f"SELECT MAX(ID), ORDEM, CENTRO_CUSTO "
        f"FROM {table_name2} "
        f"GROUP BY ORDEM, CENTRO_CUSTO)"
    )

    query_approv_rat = (
        f"SELECT "
        f"ORDEM, MES_PLAN, DESCR_ORDEM, TIPO_ORDEM, STATUS_USUARIO, RESPONSAVEL, "
        f"STATUS_SISTEMA, CENTRAB, CENTRO_CUSTO, CUSTO, CRIADOR "
        f"FROM {table_name3} t1 "
        f"WHERE STATUS = 'APROVADO SUPERVISOR' OR STATUS = 'EM APROVACAO GF' "
        f"AND (ID, ORDEM, CENTRO_CUSTO) IN ("
        f"SELECT MAX(ID), ORDEM, CENTRO_CUSTO "
        f"FROM {table_name3} "
        f"GROUP BY ORDEM, CENTRO_CUSTO)"
    )

    query_em_approv_rat = (
        f"SELECT "
        f"ORDEM, MES_PLAN, DESCR_ORDEM, TIPO_ORDEM, STATUS_USUARIO, RESPONSAVEL, "
        f"STATUS_SISTEMA, CENTRAB, CENTRO_CUSTO, CUSTO, CRIADOR "
        f"FROM {table_name3} t2 "
        f"WHERE STATUS <> 'APROVADO' AND STATUS <> 'REPROVADO' "
        f"AND (ID, ORDEM, CENTRO_CUSTO) IN ("
        f"SELECT MAX(ID), ORDEM, CENTRO_CUSTO "
        f"FROM {table_name3} "
        f"GROUP BY ORDEM, CENTRO_CUSTO)"
    )

    # Create DataFrame
    df_aprovada_hj = get_data_from_query(cursor, query_approv_direto)
    df_rat_aprovada_hj = get_data_from_query(cursor, query_approv_rat)
    df_em_aprovacao = get_data_from_query(cursor, query_em_approv)
    df_em_aprovacao['MES_ATUAL'] = None
    df_rat_em_aprovacao = get_data_from_query(cursor, query_em_approv_rat)
    df_rat_em_aprovacao['MES_ATUAL'] = None
    df_aprovada_hj.fillna(0, inplace=True)
    df_em_aprovacao.fillna(0, inplace=True)
    df_rat_aprovada_hj.fillna(0, inplace=True)
    df_rat_em_aprovacao.fillna(0, inplace=True)
    dfs_to_concat = [df for df in [df_aprovada_hj, df_em_aprovacao, df_rat_aprovada_hj, df_rat_em_aprovacao] if
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


def get_view_dados():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_ordens_colegiado'

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
        f"PORCENTAGEM as 'Porc' "
        f"FROM {table_name} "
        f"WHERE DT_ATUALIZACAO = CURDATE()  AND (`PORCENTAGEM` = 0 OR `PORCENTAGEM` = 100 "
        f"OR (CUSTO_REAL_TOTAL = 0 AND PORCENTAGEM > 0))"
    )

    df_info_approv, df_to_sum, df_to_sub = get_approv_info()
    # Create DataFrame
    df = get_data_from_query(cursor, query)

    df['Custo'] = df['Custo'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))

    def extract_month(status):
        match = re.search(r'E(\d+)H', status)
        if match and int(match.group(1)) <= 12:
            return int(match.group(1))
        else:
            return 16

    df['Mês'] = map_month(df['Stat. Usr.'].apply(extract_month), True)
    df['Mês'] = df['Mês'].replace('N/A', '')

    if user == "williamyamashita.gff" or user == "sagnaldo":
        pass
    else:
        df = pd.merge(df, df_user, on='Responsável', how='left')
        df = df[df['USUARIO'].isin(list_user)]
        df.drop(columns=['USUARIO'], inplace=True)

    try:
        df['Status'] = df.apply(lambda row:
                                "Sem Norma Aprop." if row['Porc'] == 0
                                else "Risco abaixo 18 sem Oport." if 18 > int(row['Risco']) > 0 and row['Oport.'] == ''
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
        if row['Risco'] == -1 and row['Tp. Ordem'] in ['PM05', 'PM03', 'PM04', 'PM11']:
            return 50
        else:
            return row['Risco']

    df['Risco_order'] = 0
    # Apply the function to update 'RISCO'
    df['Risco_order'] = df.apply(update_risco_order, axis=1)
    df['Risco'] = df.apply(update_risco, axis=1)
    df = df.sort_values(by='Risco_order', ascending=False)

    # Filter out the ones that were approved or are in the process
    if not df_info_approv.empty:
        df = df[~df['Nº Ordem'].isin(df_info_approv['Nº Ordem'])]
    # Filter out the ones in compromissado
    if not df_compr.empty:
        df = df[~df['Nº Ordem'].isin(df_compr['Nº Ordem'])]
    df.drop(columns=['Porc'], inplace=True)
    # Close cursor and connection
    cursor.close()
    conn.close()
    # Display DataFrame
    return df


def get_view_dados_rat():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_ordens_colegiado'
    table_rat_approv = 'tbl_aprovacao_rateado'
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
        f"PORCENTAGEM as 'Porcentagem', "
        f"RESPONSAVEL as 'Responsável' "
        f"FROM {table_name} "
        f"WHERE `PORCENTAGEM` <> 0 AND `PORCENTAGEM` < 100 AND DT_ATUALIZACAO = CURDATE() AND CUSTO_REAL_TOTAL > 0"
        # AND `CUSTO_REAL_TOTAL` <> 0
    )

    query_rat_em_approv = (
        f"SELECT "
        f"ORDEM as 'Nº Ordem', "
        f"MES_PLAN as 'Mês' "
        f"FROM {table_rat_approv} "
        f"WHERE `STATUS` = 'APROVADO SUPERVISOR'"
    )

    df_em_approv = get_data_from_query(cursor, query_rat_em_approv)
    df_info_approv, df_to_sum, df_to_sub = get_approv_info()
    # Create DataFrame
    df = get_data_from_query(cursor, query)

    df['Custo'] = df['Custo'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))

    # FAZ O FILTRO NO SCREEN_RAT NÃO AQUI, AQUI TEM QUE APARECER TODOS PARA FAZER O POP UP
    # if user == "williamyamashita.gf":
    #     pass
    # else:
    #     df = pd.merge(df, df_user, on='Responsável', how='left')
    #     df = df[df['USUARIO'] == "eallan"]  # MUDAR
    #     df.drop(columns=['USUARIO'], inplace=True)

    try:
        df['Status'] = df.apply(lambda row:
                                "Sem Norma de Apropriação e Risco abaixo 18 (Op.)" if row[
                                                                                          'Custo'] == "R$ nan" and 18 > int(
                                    row['Risco']) > 0 and row['Oport.'] == 0
                                else "Sem Norma de Apropriação e Risco abaixo 16 (PP)" if row[
                                                                                              'Custo'] == "R$ nan" and 16 >
                                                                                          int(row['Risco']) > 0 and row[
                                                                                              'Oport.'] == 2
                                else "Sem Norma de Apropriação" if row['Custo'] == "R$ nan"
                                else "Risco abaixo 18 sem Oport." if 18 > int(row['Risco']) > 0 and row['Oport.'] == ''
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
        if row['Risco'] == -1 and row['Tp. Ordem'] in ['PM05', 'PM03', 'PM04', 'PM11']:
            return 50
        else:
            return row['Risco']

    df['Risco_order'] = 0
    # Apply the function to update 'RISCO'
    df['Risco_order'] = df.apply(update_risco_order, axis=1)
    df['Risco'] = df.apply(update_risco, axis=1)
    df = df.sort_values(by='Risco_order', ascending=False)

    # Filter out the ones that were approved or are in the process
    if not df_info_approv.empty:
        df = df[~df['Nº Ordem'].isin(df_info_approv['Nº Ordem'])]
    # Filter out the ones in compromissado
    if not df_compr.empty:
        df = df[~df['Nº Ordem'].isin(df_compr['Nº Ordem'])]

    df = pd.merge(df, df_em_approv, on='Nº Ordem', how='left')

    df['Mês'] = pd.to_numeric(df['Mês'], errors='coerce')  # Convert to numeric safely
    df['Mês'] = map_month(df['Mês'], to_text=True)  # Convert month numbers to month names

    df_with_month = df.dropna(subset=['Mês'])
    df_table = df[df['Mês'].isna()]
    df_table.loc[df['Mês'].isna(), 'Mês'] = ''

    # Close cursor and connection
    cursor.close()
    conn.close()

    return df_table, df_with_month, df


def get_rat_n_aprovados(ordem):
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_aprovacao_rateado'

    # Execute the query
    query = (
        f"SELECT ORDEM, COUNT(*) AS N_APROVADO "
        f"FROM {table_name} "
        f"WHERE STATUS = 'APROVADO SUPERVISOR' "
        f"GROUP BY ORDEM"  # AND `CUSTO_REAL_TOTAL` <> 0
    )

    # Create DataFrame
    df = get_data_from_query(cursor, query)
    filtered_df = df[df['ORDEM'] == ordem]

    # Check if any rows exist after filtering
    if not filtered_df.empty:
        # Return the value of N_APROVADO from the first row
        return filtered_df['N_APROVADO'].iloc[0]
    else:
        # Return 0 if no rows exist
        return 0


def get_saldo(tipo, ano):
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
        df = pd.merge(df, df_user, on='Responsável', how='left')
        df = df[df['USUARIO'].isin(list_user)]
        df.drop(columns=['USUARIO'], inplace=True)

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

    if tipo == "rateado":
        return df
    else:
        return grouped_df


def get_compromissado():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_ordens_compromissado'

    # Execute the query
    query = (f"SELECT "
             f"ORDEM,"
             f"MES_PLAN,"
             f"DESCRICAO_ORDEM,"
             f"TIPO_ORDEM,"
             f"STATUS_USUARIO,"
             f"RESPONSAVEL,"
             f"STATUS_SISTEMA,"
             f"CENTRAB,"
             f"REVISAO, "
             f"CENTRO_CUSTO, "
             f"CUSTO "
             f"FROM {table_name} "
             f"WHERE `MES_PLAN` <> 16 AND `DT_ATUALIZACAO` = (SELECT MAX(`DT_ATUALIZACAO`) FROM {table_name})"
             )

    # Create DataFrame
    df = get_data_from_query(cursor, query)

    agg_dict = {
        'MES_PLAN': 'max',
        'DESCRICAO_ORDEM': 'max',
        'TIPO_ORDEM': 'max',
        'STATUS_USUARIO': 'max',
        'STATUS_SISTEMA': 'max',
        'CENTRAB': 'max',
        'REVISAO': 'max',
        'CENTRO_CUSTO': 'max',
        'CUSTO': 'sum'
    }

    df = df.groupby(['ORDEM', 'RESPONSAVEL']).agg(agg_dict).reset_index()

    df.rename(columns={
        "ORDEM": "Nº Ordem",
        "DESCRICAO_ORDEM": "Descr. Ordem",
        "MES_PLAN": "Mês Atual",
        "REVISAO": "Revisão",
        "TIPO_ORDEM": "Tp. Ordem",
        "OPORTUNIDADE": "Oport.",
        "CUSTO": "Custo",
        "RESPONSAVEL": "Responsável",
        "CENTRAB": "Centrab",
        "CENTRO_CUSTO": "Centro de Custo",
        "STATUS_USUARIO": "Stat. Usr.",
        "STATUS_SISTEMA": "Stat. Sist."
    }, inplace=True)

    df_info_approv, df_to_sum, df_to_sub = get_approv_info()

    if user == "williamyamashita.gff" or user == "sagnaldo":
        pass
    else:
        df = pd.merge(df, df_user, on='Responsável', how='left')
        df = df[df['USUARIO'].isin(list_user)]
        df.drop(columns=['USUARIO'], inplace=True)

    df = df[df['Mês Atual'] >= datetime.today().month]
    df['Mês Novo'] = ''

    df = df.sort_values(by=['Mês Atual', 'Custo'], ascending=[True, False])

    # Define a dictionary mapping month numbers to month names
    if not df_info_approv.empty:
        df = df[~df['Nº Ordem'].isin(df_info_approv['Nº Ordem'])]

    # df = pd.concat([df, df_info_approv], ignore_index=True)  PORQUE??????

    df['Custo'] = df['Custo'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))

    # df_info_approv['Mês Atual'] = map_month(df_info_approv['Mês Atual'], True)  PORQUE??????
    df['Mês Atual'] = map_month(df['Mês Atual'], True)
    # Close cursor and connection
    cursor.close()
    conn.close()

    # Display DataFrame
    return df


def get_orders_all(df_to_approve, df_compr):
    common_columns = ["Nº Ordem", "Descr. Ordem", "Centrab", 'Risco', 'Oport.', 'Custo', "Tp. Ordem",
                      "Stat. Sist.", "Stat. Usr.", "Centro de Custo", "Responsável", "Mês Atual", "Revisão"]

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
                       'MES': "Mês",
                       'SALDO_COLEGIADO': "Saldo Disp."
                       }, inplace=True)

    if user == "williamyamashita.gff" or user == "sagnaldo":
        pass
    else:
        df = pd.merge(df, df_email, on='Responsável', how='left')
        try:
            email_gf = df[df['USUARIO'].isin(list_user)]['EMAIL_GF'].iloc[0]
        except IndexError:
            email_gf = None  # or any default value you prefer
        if email_gf is None:
            df = df[df['USUARIO'] != user]
        else:
            df = df[(df['USUARIO'] != user) & (df['EMAIL_GF'] == email_gf)]

        df.drop(columns=['USUARIO'], inplace=True)

    df = df[df['ANO'] == current_year]

    df = df[df['Mês'] >= current_month]
    df['Mês'] = df['Mês'].astype(int)

    # Get the values to sum or subtract
    df_to_sum_by_resp = df_info_mov.groupby(['REQUISITANTE', 'MES'])['VALOR'].sum().reset_index().copy()
    df_to_sum_by_resp.rename(columns={'REQUISITANTE': 'Responsável',
                                      'MES': "Mês",
                                      'VALOR': "VALOR_SUM"
                                      }, inplace=True)
    df_to_sub_by_resp = df_info_mov.groupby(['Responsável', 'MES'])['VALOR'].sum().reset_index().copy()
    df_to_sub_by_resp.rename(columns={'MES': "Mês",
                                      'VALOR': "VALOR_SUB"
                                      }, inplace=True)

    # Group by MES and calculate the sum of SALDO_COLEGIADO
    df = df.groupby(['Responsável', 'Mês'])['Saldo Disp.'].sum().reset_index()
    df = pd.merge(df, df_to_sum_by_resp, on=['Responsável', 'Mês'], how='left')
    df = pd.merge(df, df_to_sub_by_resp, on=['Responsável', 'Mês'], how='left')
    df['Saldo Disp.'] = df['Saldo Disp.'] + df['VALOR_SUM'].fillna(0) - df['VALOR_SUB'].fillna(0)
    df = df.drop(columns=['VALOR_SUM', 'VALOR_SUB'])

    df = df[df['Saldo Disp.'] > 0]
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


def get_status_ordens():
    conn = connect_db()
    cursor = conn.cursor()

    table_name = 'tbl_ordens_colegiado'
    table_name1 = 'tbl_aprovacao_fluxo'
    table_name2 = 'tbl_aprovacao_rateado'

    # Execute the query
    query = (
        f"SELECT "
        f"ORDEM as 'Ordem', "
        f"DESCRICAO_ORDEM as 'Descr. Ordem', "
        f"CENTRAB as 'Centrab', "
        f"REVISAO as 'Revisão', "
        f"TIPO_ORDEM as 'Tp.', "
        f"RISCO as 'Risco', "
        f"OPORTUNIDADE as 'Op.', "
        f"CENTRO_CUSTO as 'CC', "
        f"CUSTO_REAL_TOTAL as 'Custo', "
        f"RESPONSAVEL as 'Responsável', "
        f"SUPERVISOR as 'Supervisor', "
        f"PORCENTAGEM as 'Porc' "
        f"FROM {table_name} "
        f"WHERE DT_ATUALIZACAO = CURDATE()"  # OR (`CUSTO_REAL_TOTAL` = 0 AND `PORCENTAGEM` > 0
    )

    query_em_approv = (
        f"SELECT "
        f"ORDEM as 'Ordem' , STATUS as 'Status' "
        f"FROM {table_name1} "
        f"WHERE STATUS = 'EM APROVACAO GF'")

    query_em_approv_rat = (
        f"SELECT "
        f"ORDEM as 'Ordem', MAX(STATUS) AS Status "
        f"FROM {table_name2} "
        f"WHERE STATUS = 'EM APROVACAO GF' "
        f"GROUP BY ORDEM"
    )

    df = get_data_from_query(cursor, query)
    df_em_aprovacao = get_data_from_query(cursor, query_em_approv)
    df_rat_em_aprovacao = get_data_from_query(cursor, query_em_approv_rat)
    df_em_approv = pd.concat([df_em_aprovacao, df_rat_em_aprovacao], ignore_index=True)

    df = pd.merge(df, df_em_approv, on='Ordem', how='left')
    df['Status'] = df['Status'].fillna('EM APROV. RESP.')
    df['Status'] = df['Status'].replace('EM APROVACAO GF', 'EM APROV. GF')

    df['Custo'] = df['Custo'].apply(
        lambda x: f"R$ {x:,.2f}".replace('.', '_').replace(',', '.').replace('_', ','))

    # Function to compare and choose the value
    def choose_value(row):
        supervisor_first_word = row['Supervisor'].split()[0].lower() if row['Supervisor'] else ''
        responsavel_first_word = row['Responsável'].split()[0].lower() if row['Responsável'] else ''

        if supervisor_first_word == responsavel_first_word:
            return row['Responsável']
        else:
            return row['Supervisor']

    # Apply the function to create a new column with the desired values
    df['Supervisor'] = df.apply(choose_value, axis=1)

    # Function to modify the Supervisor column
    def modify_supervisor(name):
        words = name.split()
        if len(words) >= 3:
            return f"{words[0]} {words[1]}"
        return name

    # Apply the function to the Supervisor column
    df['Supervisor'] = df['Supervisor'].apply(modify_supervisor).str.title()

    try:
        df['Condição'] = df.apply(lambda row:
                                  "Sem Norma" if row['Porc'] == 0
                                  else "Risco Baixo" if 18 > int(row['Risco']) > 0 and row['Op.'] == ''
                                  else "Risco Baixo" if 18 > int(row['Risco']) > 0 and int(row['Op.']) == 0
                                  else "Risco Baixo" if 16 > int(row['Risco']) > 0 and int(row['Op.']) == 2
                                  else "OK", axis=1)
    except:
        df['Condição'] = ''
    df['Risco'] = df['Risco'].replace(-1, 100)
    df = df.sort_values(by='Risco', ascending=False)
    df['Risco'] = df['Risco'].replace(100, 'PREV.')
    df.drop(columns=['Porc'], inplace=True)

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
df_compr = get_compromissado()

