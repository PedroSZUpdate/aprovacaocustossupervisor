import getpass
import numpy as np
import tkinter as tk
import pandas as pd
import aux_functions_df
import aux_send_email
import aux_custom_classes
import aux_sap
from tkinter import ttk
from datetime import datetime
from tkinter import Canvas, Entry, font, Button, PhotoImage

# Set display options for pandas
pd.set_option('display.max_columns', None)


def insert_info(df, table_name, top):
    conn = aux_functions_df.connect_db()
    # Define the insert query

    cursor = conn.cursor()

    for index, row in df.iterrows():
        # Replace NaN values with None
        row_values = [None if pd.isna(value) else value for value in row]

        # Define the insert query
        insert_query = f"""
        INSERT INTO {table_name}
        ({", ".join(df.columns)})
        VALUES ({", ".join(["%s"] * len(df.columns))})
        """

        cursor.execute(insert_query, row_values)
        conn.commit()

    # Close cursor and connection
    cursor.close()
    conn.close()

    top.destroy()


def update_status(table, ordem, column, new_value):
    conn = aux_functions_df.connect_db()
    cursor = conn.cursor()
    # Prepare the update query with placeholders %s
    update_query = (f"UPDATE {table} "
                    f"SET {column} = '{new_value}' "
                    f"WHERE ORDEM = {ordem} AND STATUS = 'EM APROVACAO GF'")
    cursor.execute(update_query)
    conn.commit()
    cursor.close()
    conn.close()


def format_responsavel(name):
    # Capitalize each word
    name = name.title()
    # Split the name into words
    words = name.split()
    # Initialize the formatted name with the first word
    formatted_name = words[0]
    # Add the initials of the next words, if they exist
    for word in words[1:]:
        formatted_name += f" {word[0]}."
    return formatted_name


class ScreenGerente(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.user = aux_functions_df.user
        self.is_expanded = tk.BooleanVar(value=False)

        '''
        Pegar df ordens
        '''
        self.df_permite = aux_functions_df.get_dados_permite()
        self.df_approv = aux_functions_df.get_em_aprov()

        # Filter out rows in self.df_permite where 'Ordem' exists in self.df_approv
        self.df_permite = self.df_permite[~self.df_permite['Nº Ordem'].isin(self.df_approv['Nº Ordem'])]
        # Pegar os dados para a tabela de ordens a aprovar
        self.df_permite_table = self.df_permite[['Nº Ordem', "Responsável", 'Risco', 'Oport.', 'Custo',
                                                 'Mês', "Status", "Saldo Disp.", "Revisão"]].copy()
        self.df_permite_table['Responsável'] = self.df_permite['Responsável'].apply(format_responsavel)

        self.num_rows_permite = len(self.df_permite_table)
        self.cost_permite = aux_functions_df.to_string(
            self.df_permite_table['Custo'].apply(aux_functions_df.to_number).sum())

        # Pegar dados para o Popup com as informações das ordens
        self.df_permite_popup = self.df_permite.drop(columns=['Risco_order'])

        """
        Pegar dados de saldo
        """
        df_saldo_current = aux_functions_df.get_saldo(aux_functions_df.current_year)

        df_saldo_future = aux_functions_df.get_saldo(aux_functions_df.current_year + 1)

        def get_saldo(df, mes):
            result = df.loc[df['MES'] == mes, 'SALDO_COLEGIADO']
            return result.values[0] if not result.empty else "R$ 0,00"

        self.saldo_mes_1 = get_saldo(df_saldo_current, 1)
        self.saldo_mes_2 = get_saldo(df_saldo_current, 2)
        self.saldo_mes_3 = get_saldo(df_saldo_current, 3)
        self.saldo_mes_4 = get_saldo(df_saldo_current, 4)
        self.saldo_mes_5 = get_saldo(df_saldo_current, 5)
        self.saldo_mes_6 = get_saldo(df_saldo_current, 6)
        self.saldo_mes_7 = get_saldo(df_saldo_current, 7)
        self.saldo_mes_8 = get_saldo(df_saldo_current, 8)
        self.saldo_mes_9 = get_saldo(df_saldo_current, 9)
        self.saldo_mes_10 = get_saldo(df_saldo_current, 10)
        self.saldo_mes_11 = get_saldo(df_saldo_current, 11)
        self.saldo_mes_12 = get_saldo(df_saldo_current, 12)
        self.saldo_acum_atual = get_saldo(df_saldo_current, 13)
        self.saldo_acum_total = get_saldo(df_saldo_current, 14)

        self.saldo_mes_1_fut = get_saldo(df_saldo_future, 1)
        self.saldo_mes_2_fut = get_saldo(df_saldo_future, 2)
        self.saldo_mes_3_fut = get_saldo(df_saldo_future, 3)
        self.saldo_mes_4_fut = get_saldo(df_saldo_future, 4)
        self.saldo_mes_5_fut = get_saldo(df_saldo_future, 5)
        self.saldo_mes_6_fut = get_saldo(df_saldo_future, 6)
        self.saldo_mes_7_fut = get_saldo(df_saldo_future, 7)
        self.saldo_mes_8_fut = get_saldo(df_saldo_future, 8)
        self.saldo_mes_9_fut = get_saldo(df_saldo_future, 9)
        self.saldo_mes_10_fut = get_saldo(df_saldo_future, 10)
        self.saldo_mes_11_fut = get_saldo(df_saldo_future, 11)
        self.saldo_mes_12_fut = get_saldo(df_saldo_future, 12)
        self.saldo_acum_atual_fut = get_saldo(df_saldo_future, 13)
        self.saldo_acum_total_fut = get_saldo(df_saldo_future, 14)

        """
        Pegar dados Aprovados Supervisor
        """
        self.df_approv_table = self.df_approv[['Nº Ordem', "Responsável", 'Risco', 'Oport.',
                                               'Custo', 'Mês', 'Ano', 'Saldo Disp.', 'Revisão']].copy()
        self.df_approv_table['Responsável'] = self.df_approv_table['Responsável'].apply(format_responsavel)

        self.num_rows_approv = len(self.df_approv_table)
        self.cost_superv = aux_functions_df.to_string(
            self.df_approv_table['Custo'].apply(aux_functions_df.to_number).sum())

        if not self.df_approv.empty:
            self.df_all_info = aux_functions_df.get_orders_all_permite(self.df_permite, self.df_approv)
        else:
            common_columns = ["Nº Ordem", "Descr. Ordem", "Centrab", 'Risco', 'Oport.', 'Custo', "Tp. Ordem",
                              "Stat. Sist.", "Stat. Usr.", "Centro de Custo", "Responsável", "Mês Atual", "Saldo Disp."]
            self.df_all_info = self.df_permite.reindex(columns=common_columns)
        self.df_email = aux_functions_df.df_email.copy()
        self.df_email.drop(columns=['USUARIO', 'EMAIL_USUARIO'], inplace=True)

        # Get unique values from both tables
        unique_permite = self.df_permite_table['Responsável'].unique()
        unique_approv = self.df_approv_table['Responsável'].unique()

        # Combine the unique values from both tables
        combined_unique = np.unique(np.concatenate((unique_permite, unique_approv)))

        # Remove any empty values from combined_unique
        combined_unique = combined_unique[combined_unique != '']

        # Sort the combined unique values
        sorted_unique = np.sort(combined_unique)

        # Start with an empty value and then add the sorted unique values
        self.df_responsavel = np.concatenate(([''], sorted_unique))

        # Get unique values from both tables for the column "Revisão"
        unique_permite = self.df_permite_table['Revisão'].unique()
        unique_approv = self.df_approv_table['Revisão'].unique()

        # Combine the unique values from both tables
        combined_unique = np.unique(np.concatenate((unique_permite, unique_approv)))

        # Remove any empty values from combined_unique
        combined_unique = combined_unique[combined_unique != '']

        # Sort the combined unique values
        sorted_unique = np.sort(combined_unique)

        # Start with an empty value and then add the sorted unique values
        self.df_revisao = np.concatenate(([''], sorted_unique))

        # Store image references
        self.images = {}
        self.create_widgets()

    def filter_saldo(self, event=None):

        # Obtém o texto digitado nos filtros
        filter_ano_text = self.combobox_ano.get()

        # Filtra as tabelas
        filtered_approv_table = self.df_approv_table[
            self.df_approv_table['Ano'].astype(str).str.contains(filter_ano_text, case=False)
            ]

        self.num_approv.config(text=str(len(filtered_approv_table)))

        self.cost_superv_label.config(
            text=str(
                aux_functions_df.to_string(filtered_approv_table['Custo'].apply(aux_functions_df.to_number).sum())))

        #  Preenche a tabela de ordens aprovadas pelos supervisores
        self.tree_orders_superv.delete(*self.tree_orders_superv.get_children())
        checked_values_ordem = self.tree_orders_superv.get_checked_values("Ordem")
        inserted_items = []
        # First, insert the checked rows
        for index, row in filtered_approv_table.iterrows():
            values = [row[col] for col in filtered_approv_table.columns]
            ordem = str(row['Nº Ordem'])
            try:
                saldo_disp = aux_functions_df.to_number(row["Saldo Disp."])
                custo = aux_functions_df.to_number(row["Custo"])
            except:
                saldo_disp = 0
                custo = 0
            if ordem in checked_values_ordem:
                # Insert unchecked rows
                if custo > 0 > (saldo_disp - custo):
                    item = self.tree_orders_superv.insert("", tk.END, values=values, tags=("red_background",))
                else:
                    item = self.tree_orders_superv.insert("", tk.END, values=values)
                inserted_items.append(item)
                # Assuming _check_ancestor and _check_descendant are methods to check item
                self.tree_orders_superv._check_ancestor(item)
                self.tree_orders_superv._check_descendant(item)
        # Now, insert the rest (unchecked rows)
        for index, row in filtered_approv_table.iterrows():
            values = [row[col] for col in filtered_approv_table.columns]
            ordem = str(row['Nº Ordem'])
            try:
                saldo_disp = aux_functions_df.to_number(row["Saldo Disp."])
                custo = aux_functions_df.to_number(row["Custo"])
            except:
                saldo_disp = 0
                custo = 0
            if ordem not in checked_values_ordem:
                # Insert unchecked rows
                if custo > 0 > (saldo_disp - custo):
                    item = self.tree_orders_superv.insert("", tk.END, values=values, tags=("red_background",))
                else:
                    item = self.tree_orders_superv.insert("", tk.END, values=values)
                inserted_items.append(item)

        self.tree_orders_superv.uncheck_all()
        self.tree_orders_superv.checked_ordens.clear()
        self.tree_orders_superv.checked_mes.clear()
        self.tree_orders_superv.checked_cost.clear()
        self.to_approv_entry.config(state="normal")
        self.to_approv_entry.delete("1.0", tk.END)
        self.to_approv_entry.config(state="disabled")

        # Change Saldo value
        if filter_ano_text == str(aux_functions_df.current_year):
            months = [
                ('saldo_mes_1', 'jan_entry'),
                ('saldo_mes_2', 'fev_entry'),
                ('saldo_mes_3', 'mar_entry'),
                ('saldo_mes_4', 'abr_entry'),
                ('saldo_mes_5', 'mai_entry'),
                ('saldo_mes_6', 'jun_entry'),
                ('saldo_mes_7', 'jul_entry'),
                ('saldo_mes_8', 'ago_entry'),
                ('saldo_mes_9', 'set_entry'),
                ('saldo_mes_10', 'out_entry'),
                ('saldo_mes_11', 'nov_entry'),
                ('saldo_mes_12', 'dez_entry'),
                ('saldo_acum_atual', 'acum_mes_entry'),
                ('saldo_acum_total', 'acum_ano_entry')
            ]
            for saldo, entry in months:
                value = float(getattr(self, saldo).replace('R$', '').replace('.', '').replace(',', '.'))
                color = "black" if value > 0 else "red"
                getattr(self, entry).config(disabledforeground=color)
                getattr(self, entry).config(state="normal")
                getattr(self, entry).delete(0, tk.END)
                getattr(self, entry).insert(0, getattr(self, saldo))
                getattr(self, entry).config(state="disabled")
        else:
            months = [
                ('saldo_mes_1_fut', 'jan_entry'),
                ('saldo_mes_2_fut', 'fev_entry'),
                ('saldo_mes_3_fut', 'mar_entry'),
                ('saldo_mes_4_fut', 'abr_entry'),
                ('saldo_mes_5_fut', 'mai_entry'),
                ('saldo_mes_6_fut', 'jun_entry'),
                ('saldo_mes_7_fut', 'jul_entry'),
                ('saldo_mes_8_fut', 'ago_entry'),
                ('saldo_mes_9_fut', 'set_entry'),
                ('saldo_mes_10_fut', 'out_entry'),
                ('saldo_mes_11_fut', 'nov_entry'),
                ('saldo_mes_12_fut', 'dez_entry'),
                ('saldo_acum_atual_fut', 'acum_mes_entry'),
                ('saldo_acum_total_fut', 'acum_ano_entry')
            ]
            for saldo, entry in months:
                value = float(getattr(self, saldo).replace('R$', '').replace('.', '').replace(',', '.'))
                color = "black" if value > 0 else "red"
                getattr(self, entry).config(disabledforeground=color)
                getattr(self, entry).config(state="normal")
                getattr(self, entry).delete(0, tk.END)
                getattr(self, entry).insert(0, getattr(self, saldo))
                getattr(self, entry).config(state="disabled")

    def filter_all(self, event=None):

        # Obtém o texto digitado nos filtros
        filter_order_text = self.filter_order.get()
        filter_resp_text = self.combobox_responsavel.get()
        filter_month_text = self.combobox_month.get()
        filter_revisao_text = self.combobox_revisao.get()
        if self.combobox_custo.get() == "Sem Custo":
            custo_cond_ordens = (self.df_permite_table['Custo'].str.replace('R$ ', '').str.replace('.', '')
                                 .str.replace(',', '.').astype(float) == 0)
            custo_cond_approv = (self.df_approv_table['Custo'].str.replace('R$ ', '').str.replace('.', '')
                                 .str.replace(',', '.').astype(float) == 0)
        elif self.combobox_custo.get() == "Com Custo":
            custo_cond_ordens = (self.df_permite_table['Custo'].str.replace('R$ ', '').str.replace('.', '')
                                 .str.replace(',', '.').astype(float) > 0)
            custo_cond_approv = (self.df_approv_table['Custo'].str.replace('R$ ', '').str.replace('.', '')
                                 .str.replace(',', '.').astype(float) > 0)
        elif self.combobox_custo.get() == "Sem Saldo Disp.":
            custo_cond_ordens = ((self.df_permite_table['Custo'].str.replace('R$ ', '').str.replace('.', '')
                                  .str.replace(',', '.').astype(float) > 0) &
                                 (self.df_permite_table['Saldo Disp.'].str.replace('R$ ', '').str.replace('.', '')
                                  .str.replace(',', '.').astype(float) < 0) &
                                 (self.df_permite_table['Saldo Disp.'].notna())
                                 )
            custo_cond_approv = ((self.df_approv_table['Custo'].str.replace('R$ ', '').str.replace('.', '')
                                  .str.replace(',', '.').astype(float) > 0) &
                                 (self.df_approv_table['Saldo Disp.'].str.replace('R$ ', '').str.replace('.', '')
                                  .str.replace(',', '.').astype(float) < 0)
                                 )
        else:
            custo_cond_ordens = True
            custo_cond_approv = True

        # Filtra as tabelas
        if filter_resp_text != "":
            filtered_permite_table = self.df_permite_table[
                self.df_permite_table['Nº Ordem'].astype(str).str.contains(filter_order_text, case=False) &
                (self.df_permite_table['Responsável'].astype(str).str.strip() == filter_resp_text.strip()) &
                self.df_permite_table['Mês'].astype(str).str.contains(filter_month_text, case=False) &
                self.df_permite_table['Revisão'].astype(str).str.contains(filter_revisao_text, case=False) &
                custo_cond_ordens
                ]
            filtered_approv_table = self.df_approv_table[
                self.df_approv_table['Nº Ordem'].astype(str).str.contains(filter_order_text, case=False) &
                (self.df_approv_table['Responsável'].astype(str).str.strip() == filter_resp_text.strip()) &
                self.df_approv_table['Mês'].astype(str).str.contains(filter_month_text, case=False) &
                self.df_approv_table['Revisão'].astype(str).str.contains(filter_revisao_text, case=False) &
                custo_cond_approv
                ]
        else:
            filtered_permite_table = self.df_permite_table[
                self.df_permite_table['Nº Ordem'].astype(str).str.contains(filter_order_text, case=False) &
                self.df_permite_table['Mês'].astype(str).str.contains(filter_month_text, case=False) &
                self.df_permite_table['Revisão'].astype(str).str.contains(filter_revisao_text, case=False) &
                custo_cond_ordens
                ]
            filtered_approv_table = self.df_approv_table[
                self.df_approv_table['Nº Ordem'].astype(str).str.contains(filter_order_text, case=False) &
                self.df_approv_table['Mês'].astype(str).str.contains(filter_month_text, case=False) &
                self.df_approv_table['Revisão'].astype(str).str.contains(filter_revisao_text, case=False) &
                custo_cond_approv
                ]

        self.num_permite.config(text=str(len(filtered_permite_table)))

        self.num_approv.config(text=str(len(filtered_approv_table)))

        self.cost_superv_label.config(
            text=str(
                aux_functions_df.to_string(filtered_approv_table['Custo'].apply(aux_functions_df.to_number).sum())))
        self.cost_permite_label.config(
            text=str(
                aux_functions_df.to_string(filtered_permite_table['Custo'].apply(aux_functions_df.to_number).sum())))

        #  Preenche a tabela de permite
        self.tree_orders_permite.delete(*self.tree_orders_permite.get_children())
        checked_values_ordem = self.tree_orders_permite.get_checked_values("Ordem")

        inserted_items = []
        # First, insert the checked rows
        for index, row in filtered_permite_table.iterrows():
            values = [row[col] for col in filtered_permite_table.columns]
            ordem = str(row['Nº Ordem'])
            try:
                saldo_disp = aux_functions_df.to_number(row["Saldo Disp."])
                custo = aux_functions_df.to_number(row["Custo"])
            except:
                saldo_disp = 0
                custo = 0
            if ordem in checked_values_ordem:
                status = str(row["Status"])
                # Insert unchecked rows
                if status != "OK":
                    item = self.tree_orders_permite.insert("", tk.END, values=values, tags=("gray_background",))
                elif custo > 0 > (saldo_disp - custo):
                    item = self.tree_orders_permite.insert("", tk.END, values=values, tags=("red_background",))
                else:
                    item = self.tree_orders_permite.insert("", tk.END, values=values)
                inserted_items.append(item)
                # Assuming _check_ancestor and _check_descendant are methods to check item
                self.tree_orders_permite._check_ancestor(item)
                self.tree_orders_permite._check_descendant(item)
        # Now, insert the rest (unchecked rows)
        for index, row in filtered_permite_table.iterrows():
            values = [row[col] for col in filtered_permite_table.columns]
            ordem = str(row['Nº Ordem'])
            try:
                saldo_disp = aux_functions_df.to_number(row["Saldo Disp."])
                custo = aux_functions_df.to_number(row["Custo"])
            except:
                saldo_disp = 0
                custo = 0
            if ordem not in checked_values_ordem:
                status = str(row["Status"])
                # Insert unchecked rows
                if status != "OK":
                    item = self.tree_orders_permite.insert("", tk.END, values=values, tags=("gray_background",))
                elif custo > 0 > (saldo_disp - custo):
                    item = self.tree_orders_permite.insert("", tk.END, values=values, tags=("red_background",))
                else:
                    item = self.tree_orders_permite.insert("", tk.END, values=values)
                inserted_items.append(item)

        #  Preenche a tabela de ordens aprovadas pelos supervisores
        self.tree_orders_superv.delete(*self.tree_orders_superv.get_children())
        checked_values_ordem = self.tree_orders_superv.get_checked_values("Ordem")

        inserted_items = []
        # First, insert the checked rows
        for index, row in filtered_approv_table.iterrows():
            values = [row[col] for col in filtered_approv_table.columns]
            ordem = str(row['Nº Ordem'])
            try:
                saldo_disp = aux_functions_df.to_number(row["Saldo Disp."])
                custo = aux_functions_df.to_number(row["Custo"])
            except:
                saldo_disp = 0
                custo = 0
            if ordem in checked_values_ordem:
                # Insert unchecked rows
                if custo > 0 > (saldo_disp - custo):
                    item = self.tree_orders_superv.insert("", tk.END, values=values, tags=("red_background",))
                else:
                    item = self.tree_orders_superv.insert("", tk.END, values=values)
                inserted_items.append(item)
                # Assuming _check_ancestor and _check_descendant are methods to check item
                self.tree_orders_superv._check_ancestor(item)
                self.tree_orders_superv._check_descendant(item)
        # Now, insert the rest (unchecked rows)
        for index, row in filtered_approv_table.iterrows():
            values = [row[col] for col in filtered_approv_table.columns]
            ordem = str(row['Nº Ordem'])
            try:
                saldo_disp = aux_functions_df.to_number(row["Saldo Disp."])
                custo = aux_functions_df.to_number(row["Custo"])
            except:
                saldo_disp = 0
                custo = 0
            if ordem not in checked_values_ordem:
                # Insert unchecked rows
                if custo > 0 > (saldo_disp - custo):
                    item = self.tree_orders_superv.insert("", tk.END, values=values, tags=("red_background",))
                else:
                    item = self.tree_orders_superv.insert("", tk.END, values=values)
                inserted_items.append(item)

    def create_widgets(self):
        """"
        Inicío da GUI
        """
        navigate_area_width = 0
        aux_custom_classes.add_font()
        canvas = Canvas(
            self,
            bg="#FFFFFF",
            height=540,
            width=900 + navigate_area_width,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )

        canvas.place(x=0, y=0)

        # Background
        canvas.create_rectangle(
            0.0,
            0.0,
            900 + navigate_area_width,
            540.0,
            fill="#E2E1DD",
            outline="")

        # Banner
        canvas.create_rectangle(
            0.0,
            0.0,
            900 + navigate_area_width,
            51.0,
            fill="#0046AD",
            outline="")

        canvas.create_text(
            60.0,
            8.0,
            anchor="nw",
            text="  APROVAÇÃO E LIBERAÇÃO DE ORDENS",
            fill="#FFFFFF",
            font=font.Font(family="Suzano Unicase XBold", size=24)
        )

        # Logo Suzano
        self.images['image_1'] = PhotoImage(file=aux_custom_classes.relative_to_assets("image_1.png"))
        canvas.create_image(
            796.0 + navigate_area_width,
            25.0,
            image=self.images['image_1']
        )

        # Vertical line
        canvas.create_rectangle(
            543.0 + navigate_area_width,
            119.0,
            545.0 + navigate_area_width,
            533.0,
            fill="#8F6F4D",
            outline="")

        # Horizontal line
        canvas.create_rectangle(
            569.9322021484375 + navigate_area_width,
            473.1270989647767,
            883.8034339763303 + navigate_area_width,
            474.8729553222656,
            fill="#8F6F4D",
            outline="")

        # Banner Superv
        self.images['image_3'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_3.png"))
        canvas.create_image(
            271.0 + navigate_area_width,
            124,
            image=self.images['image_3']
        )

        canvas.create_text(
            70.0 + navigate_area_width,
            112.0,
            anchor="nw",
            text="ORDENS APROVADAS PELOS SUPERVISORES",
            fill="#FFFFFF",
            font=font.Font(family="Suzano Unicase XBold", size=12)
        )

        # Create a label to display the number
        self.num_approv = tk.Label(self, text=self.num_rows_approv,
                                   font=font.Font(family="Suzano Unicase XBold", size=11),
                                   fg="white", bg='#0046AD')
        self.num_approv.place(x=35, y=109)

        # Create a label to display the cost number
        self.cost_superv_label = tk.Label(self, text=self.cost_superv,
                                          font=font.Font(family="Suzano Unicase XBold", size=11),
                                          fg="white", bg='#0046AD')
        self.cost_superv_label.place(x=425, y=109)

        # Banner Ordens Sem Permite
        self.images['image_2'] = PhotoImage(file=aux_custom_classes.relative_to_assets("image_2.png"))
        canvas.create_image(
            271.0 + navigate_area_width,
            381.0,
            image=self.images['image_2']
        )
        canvas.create_text(
            140.0 + navigate_area_width,
            368.0,
            anchor="nw",
            text="        ORDENS SEM PERMITE",
            fill="#FFFFFF",
            font=font.Font(family="Suzano Unicase XBold", size=13)
        )
        # Create a label to display the number
        self.num_permite = tk.Label(self, text=str(self.num_rows_permite),
                                    font=font.Font(family="Suzano Unicase XBold", size=12),
                                    fg="white", bg='#0046AD')
        self.num_permite.place(x=75, y=366)

        # Create a label to display the cost number
        self.cost_permite_label = tk.Label(self, text=self.cost_permite,
                                           font=font.Font(family="Suzano Unicase XBold", size=11),
                                           fg="white", bg='#0046AD')
        self.cost_permite_label.place(x=410, y=366)

        # Banner Saldo
        self.images['image_4'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_4.png"))
        image_4 = canvas.create_image(
            726.0 + navigate_area_width,
            124.0,
            image=self.images['image_4']
        )

        canvas.create_text(
            696.0 + navigate_area_width,
            112.0,
            anchor="nw",
            text="SALDO",
            fill="#FFFFFF",
            font=font.Font(family="Suzano Unicase XBold", size=13)
        )

        # # Botão voltar
        # image_image_5 = PhotoImage(
        #     file=relative_to_assets("image_5.png"))
        # image_5 = canvas.create_image(
        #     856.875,
        #     82.44000244140625,
        #     image=image_image_5
        # )

        '''
        Saldo dos meses
        '''

        jan_text = canvas.create_text(
            570.0 + navigate_area_width,
            142.0,
            anchor="nw",
            text="Jan.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_jan'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            642.0 + navigate_area_width,
            168.0,
            image=self.images['image_jan']
        )

        if float(self.saldo_mes_1.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.jan_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.jan_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575.0 + navigate_area_width, 162.0, anchor="nw", window=self.jan_entry)
        self.jan_entry.insert(0, self.saldo_mes_1)
        self.jan_entry.config(state="disabled")

        fev_text = canvas.create_text(
            738.0 + navigate_area_width,
            142.0,
            anchor="nw",
            text="Fev.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_fev'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            810.0 + navigate_area_width,
            168.0,
            image=self.images['image_fev']
        )

        if float(self.saldo_mes_2.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.fev_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.fev_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742.0 + navigate_area_width, 162.0, anchor="nw", window=self.fev_entry)
        self.fev_entry.insert(0, self.saldo_mes_2)
        self.fev_entry.config(state="disabled")

        mar_text = canvas.create_text(
            570.0 + navigate_area_width,
            187.0,
            anchor="nw",
            text="Mar.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_mar'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            642.0 + navigate_area_width,
            213.0,
            image=self.images['image_mar']
        )

        if float(self.saldo_mes_3.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.mar_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.mar_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575.0 + navigate_area_width, 206.0, anchor="nw", window=self.mar_entry)
        self.mar_entry.insert(0, self.saldo_mes_3)
        self.mar_entry.config(state="disabled")

        abr_text = canvas.create_text(
            738.0 + navigate_area_width,
            187.0,
            anchor="nw",
            text="Abr.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_abr'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        image_9 = canvas.create_image(
            810.0 + navigate_area_width,
            213.0,
            image=self.images['image_abr']
        )

        if float(self.saldo_mes_4.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.abr_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.abr_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742.0 + navigate_area_width, 206.0, anchor="nw", window=self.abr_entry)
        self.abr_entry.insert(0, self.saldo_mes_4)  # saldo_mes_4
        self.abr_entry.config(state="disabled")

        mai_text = canvas.create_text(
            570.0 + navigate_area_width,
            232.0,
            anchor="nw",
            text="Mai.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_mai'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            642.0 + navigate_area_width,
            258.0,
            image=self.images['image_mai']
        )

        if float(self.saldo_mes_5.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.mai_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.mai_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 251.0, anchor="nw", window=self.mai_entry)
        self.mai_entry.insert(0, self.saldo_mes_5)  # saldo_mes_5
        self.mai_entry.config(state="disabled")

        jun_text = canvas.create_text(
            738.0 + navigate_area_width,
            232.0,
            anchor="nw",
            text="Jun.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_jun'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            810.0 + navigate_area_width,
            258.0,
            image=self.images['image_jun']
        )

        if float(self.saldo_mes_6.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.jun_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.jun_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 251.0, anchor="nw", window=self.jun_entry)
        self.jun_entry.insert(0, self.saldo_mes_6)  # saldo_mes_6
        self.jun_entry.config(state="disabled")

        jul_text = canvas.create_text(
            570.0 + navigate_area_width,
            275.0,
            anchor="nw",
            text="Jul.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_jul'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            642.0 + navigate_area_width,
            303.0,
            image=self.images['image_jul']
        )

        if float(self.saldo_mes_7.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.jul_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.jul_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 296.0, anchor="nw", window=self.jul_entry)
        self.jul_entry.insert(0, self.saldo_mes_7)
        self.jul_entry.config(state="disabled")

        ago_text = canvas.create_text(
            738.0 + navigate_area_width,
            276.0,
            anchor="nw",
            text="Ago.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_ago'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            810.0 + navigate_area_width,
            303.0,
            image=self.images['image_ago']
        )

        if float(self.saldo_mes_8.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.ago_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.ago_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 296.0, anchor="nw", window=self.ago_entry)
        self.ago_entry.insert(0, self.saldo_mes_8)
        self.ago_entry.config(state="disabled")

        set_text = canvas.create_text(
            570.0 + navigate_area_width,
            324.0,
            anchor="nw",
            text="Set.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_set'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            642.0 + navigate_area_width,
            349.0,
            image=self.images['image_set']
        )

        canvas.create_text(
            575.0 + navigate_area_width,
            341.0,
            anchor="nw",
            text="R$ 1.000,00",
            fill="#000000",
            font=("Noto Sans", 13 * -1)
        )

        if float(self.saldo_mes_9.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.set_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.set_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 341.0, anchor="nw", window=self.set_entry)
        self.set_entry.insert(0, self.saldo_mes_9)
        self.set_entry.config(state="disabled")

        outtext = canvas.create_text(
            738.0 + navigate_area_width,
            324.0,
            anchor="nw",
            text="Out.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_out'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            810.0 + navigate_area_width,
            349.0,
            image=self.images['image_out']
        )

        if float(self.saldo_mes_10.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.out_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.out_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 341.0, anchor="nw", window=self.out_entry)
        self.out_entry.insert(0, self.saldo_mes_10)
        self.out_entry.config(state="disabled")

        nov_text = canvas.create_text(
            570.0 + navigate_area_width,
            368.0,
            anchor="nw",
            text="Nov.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_nov'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            642.0 + navigate_area_width,
            393.0,
            image=self.images['image_nov']
        )

        if float(self.saldo_mes_11.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.nov_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.nov_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 386.0, anchor="nw", window=self.nov_entry)
        self.nov_entry.insert(0, self.saldo_mes_11)
        self.nov_entry.config(state="disabled")

        dez_text = canvas.create_text(
            738.0 + navigate_area_width,
            368.0,
            anchor="nw",
            text="Dez.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_dez'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        image_17 = canvas.create_image(
            810.0 + navigate_area_width,
            393.0,
            image=self.images['image_dez']
        )

        if float(self.saldo_mes_12.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.dez_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.dez_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 386.0, anchor="nw", window=self.dez_entry)
        self.dez_entry.insert(0, self.saldo_mes_12)
        self.dez_entry.config(state="disabled")

        acum_mes_text = canvas.create_text(
            570.0 + navigate_area_width,
            421.0,
            anchor="nw",
            text="Acumulado Mês Atual",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_acum_mes'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            642.0 + navigate_area_width,
            448.0,
            image=self.images['image_acum_mes']
        )

        if float(self.saldo_acum_atual.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.acum_mes_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.acum_mes_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 441.0, anchor="nw", window=self.acum_mes_entry)
        self.acum_mes_entry.insert(0, self.saldo_acum_atual)
        self.acum_mes_entry.config(state="disabled")

        acum_ano_text = canvas.create_text(
            737.0 + navigate_area_width,
            421.0,
            anchor="nw",
            text="Acumulado Anual",
            fill="#000000",
            font=font.Font(family="Suzano Unicase Bold", size=8)
        )

        self.images['image_acum_ano'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_6.png"))
        canvas.create_image(
            810.0 + navigate_area_width,
            448.0,
            image=self.images['image_acum_ano']
        )

        if float(self.saldo_acum_total.replace('R$', '').replace('.', '').replace(',', '.')) > 0:
            self.acum_ano_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            self.acum_ano_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 441.0, anchor="nw", window=self.acum_ano_entry)
        self.acum_ano_entry.insert(0, self.saldo_acum_total)
        self.acum_ano_entry.config(state="disabled")

        '''
        Tabela Permite
        '''

        # Define as dimensões da tabela
        table_permite_width = 400
        table_permite_height = 120

        # Define as dimensões da tabela
        table_superv_width = 400
        table_superv_height = 220

        # Define as fontes
        # custom_font_tree = font.Font(family="Suzano Unicase", size=8)
        custom_font_header = font.Font(family="Suzano Unicase Medium", size=8)

        # Define as cores
        style = ttk.Style()
        style.theme_use("alt")  # Use the "clam" theme as a base
        style.configure("Treeview", font=custom_font_header, background="#E6E6E6", foreground="black")
        style.configure("Treeview.Heading", font=custom_font_header,
                        background="black", foreground="white", hovercolor="black", justify="center")

        custom_font_to_change_tree = font.Font(family="Suzano Unicase", size=7)
        custom_font_to_change_header = font.Font(family="Suzano Unicase XBold", size=7)

        # Create a label for the checked values
        label_checked_values = tk.Label(self, text="À aprovar", font=custom_font_to_change_header, background="#E2E1DD")
        label_checked_values.place(x=table_superv_width + 20 + navigate_area_width, y=399)

        cost_permit_checked_values = tk.Label(self, text="R$ 0,00", font=custom_font_to_change_header,
                                              background="#E2E1DD")
        cost_permit_checked_values.place(x=table_superv_width + 78 + navigate_area_width, y=399)

        # Create a Text widget to display checked values of orders to approve
        self.permite_entry = tk.Text(self, width=21, height=10, font=custom_font_to_change_tree, background="#E6E6E6",
                                     state=tk.DISABLED)
        self.permite_entry.place(x=table_permite_width + 25 + navigate_area_width, y=420)

        # Create a Text widget to display checked values of orders to approve
        self.to_approv_entry = tk.Text(self, width=21, height=18, font=custom_font_to_change_tree, background="#E6E6E6",
                                       state=tk.DISABLED)
        self.to_approv_entry.place(x=table_superv_width + 25 + navigate_area_width, y=163)

        # Cria tabela com checkbox
        self.tree_orders_permite = (
            aux_custom_classes.CustomGerenteAprovarCheckboxTreeview(self, self.permite_entry, self.to_approv_entry,
                                                                    self.jan_entry,
                                                                    self.fev_entry, self.mar_entry, self.abr_entry,
                                                                    self.mai_entry,
                                                                    self.jun_entry, self.jul_entry, self.ago_entry,
                                                                    self.set_entry,
                                                                    self.out_entry, self.nov_entry, self.dez_entry,
                                                                    self.acum_mes_entry, self.acum_ano_entry,
                                                                    "tbl_a_aprovar", self.df_permite_popup,
                                                                    self.df_approv_table, cost_permit_checked_values))
        # self.tree_orders_permite = (
        #     aux_custom_classes.CustomGerentePermiteCheckboxTreeview(self, self.permite_entry, self.df_permite_popup))

        # Adicionas as columns do df, excluindo a coluna "Status"
        columns = self.df_permite_table.columns.tolist()
        columns.remove("Status")
        columns.remove("Saldo Disp.")
        columns.remove("Revisão")
        self.tree_orders_permite["columns"] = columns

        # Define os headers das colunas
        for col in columns:
            self.tree_orders_permite.heading(col, text=col)

        # Insere as informações
        for index, row in self.df_permite_table.iterrows():
            values = [row[col] for col in columns]
            status = row["Status"]
            try:
                saldo_disp = aux_functions_df.to_number(row["Saldo Disp."])
                custo = aux_functions_df.to_number(row["Custo"])
            except:
                saldo_disp = 0
                custo = 0
            # Check if status is not "OK" and change background color accordingly
            if status != "OK":
                self.tree_orders_permite.insert("", tk.END, values=values, tags=("gray_background",))
            elif custo > 0 > (saldo_disp - custo):
                self.tree_orders_permite.insert("", tk.END, values=values, tags=("red_background",))
            else:
                self.tree_orders_permite.insert("", tk.END, values=values)

        # Define a cor de fundo cinza para as linhas com status diferente de "OK"
        style.configure("gray_background.Treeview", background="gray")

        # Aplica as tags para as linhas com status diferente de "OK"
        self.tree_orders_permite.tag_configure("gray_background", background="gray")
        self.tree_orders_permite.tag_configure("red_background", background="red")

        # Ajusta a largura das colunas
        self.tree_orders_permite.column("#0", width=30)
        self.tree_orders_permite.column("#1", width=55)
        self.tree_orders_permite.column("#2", width=80)
        self.tree_orders_permite.column("#3", width=35)
        self.tree_orders_permite.column("#4", width=35)
        self.tree_orders_permite.column("#5", width=65)
        self.tree_orders_permite.column("#6", width=40)

        self.checkbox_permite = aux_custom_classes.CustomCheckbox(self,
                                                                  self.tree_orders_permite.toggle_all_checkboxes,
                                                                  width=8, height=8)
        self.checkbox_permite.place(x=22, y=401)

        # Posiciona a tabela
        self.tree_orders_permite.place(x=5 + navigate_area_width, y=399, width=table_permite_width,
                                       height=table_permite_height)

        # Adiciona um srollbar a tabela
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree_orders_permite.yview)
        scrollbar.place(x=2 + table_permite_width + navigate_area_width, y=399,
                        height=table_permite_height,
                        anchor="nw")

        self.tree_orders_permite.config(yscrollcommand=scrollbar.set)

        for col in columns:
            self.tree_orders_permite.column(col, anchor="center")

        '''
        Tabela Aprovar as já aprovadas pelos Supervisores
        '''

        # Create a label for the checked values
        label_checked_values = tk.Label(self, text="À aprovar", font=custom_font_to_change_header, background="#E2E1DD")
        label_checked_values.place(x=table_permite_width + 20 + navigate_area_width, y=143)

        cost_order_checked_values = tk.Label(self, text="R$ 0,00", font=custom_font_to_change_header,
                                             background="#E2E1DD")
        cost_order_checked_values.place(x=table_permite_width + 77 + navigate_area_width, y=143)

        # Cria tabela com checkbox
        self.tree_orders_superv = (
            aux_custom_classes.CustomGerenteAprovarCheckboxTreeview(self, self.to_approv_entry, self.permite_entry,
                                                                    self.jan_entry,
                                                                    self.fev_entry, self.mar_entry, self.abr_entry,
                                                                    self.mai_entry,
                                                                    self.jun_entry, self.jul_entry, self.ago_entry,
                                                                    self.set_entry,
                                                                    self.out_entry, self.nov_entry, self.dez_entry,
                                                                    self.acum_mes_entry,
                                                                    self.acum_ano_entry, "tbl_a_aprovar", self.df_approv,
                                                                    self.df_permite_table, cost_order_checked_values))

        # Adicionas as columns do df, excluindo a coluna "Status"
        columns = self.df_approv_table.columns.tolist()
        columns.remove('Saldo Disp.')
        columns.remove('Revisão')
        if aux_functions_df.current_month != 11 and aux_functions_df.current_month != 12:
            columns.remove('Ano')
        self.tree_orders_superv["columns"] = columns

        # Define os headers das colunas
        for col in columns:
            self.tree_orders_superv.heading(col, text=col)

        # Insere as informações
        for index, row in self.df_approv_table.iterrows():
            values = [row[col] for col in columns]
            try:
                saldo_disp = aux_functions_df.to_number(row["Saldo Disp."])
                custo = aux_functions_df.to_number(row["Custo"])
            except:
                saldo_disp = 0
                custo = 0
            if custo > 0 > (saldo_disp - custo):
                self.tree_orders_superv.insert("", tk.END, values=values, tags=("red_background",))
            else:
                self.tree_orders_superv.insert("", tk.END, values=values)

        # Define a cor de fundo cinza para as linhas com status diferente de "OK"
        style.configure("red_background.Treeview", background="red")

        # Aplica as tags para as linhas com status diferente de "OK"
        self.tree_orders_superv.tag_configure("red_background", background="red")

        # Ajusta a largura das colunas

        self.tree_orders_superv.column("#0", width=30)
        self.tree_orders_superv.column("#1", width=55)
        self.tree_orders_superv.column("#2", width=80)
        self.tree_orders_superv.column("#3", width=35)
        self.tree_orders_superv.column("#4", width=35)
        self.tree_orders_superv.column("#5", width=65)
        self.tree_orders_superv.column("#6", width=35)
        if aux_functions_df.current_month == 11 or aux_functions_df.current_month == 12:
            self.tree_orders_superv.column("#7", width=35)

        self.checkbox_superv = aux_custom_classes.CustomCheckbox(self,
                                                                 self.tree_orders_superv.toggle_all_checkboxes,
                                                                 width=8, height=8)
        self.checkbox_superv.place(x=22, y=147)

        # Posiciona a tabela
        self.tree_orders_superv.place(x=5 + navigate_area_width, y=143, width=table_superv_width,
                                      height=table_superv_height)

        # Adiciona um srollbar a tabela
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree_orders_superv.yview)
        scrollbar.place(x=2 + table_superv_width + navigate_area_width, y=143,
                        height=table_superv_height,
                        anchor="nw")

        self.tree_orders_superv.config(yscrollcommand=scrollbar.set)

        for col in columns:
            self.tree_orders_superv.column(col, anchor="center")

        '''
        Filtros
        '''

        # Filto Order Tabl to approve

        entry_image = PhotoImage(
            file=aux_custom_classes.relative_to_assets("entry_1.png"))

        filter_order_bg = canvas.create_image(
            86.5 + navigate_area_width,
            92,
            image=entry_image
        )

        self.filter_order = Entry(
            self,
            bd=0,
            bg="#B7B1A9",
            fg="#000716",
            highlightthickness=0
        )
        self.filter_order.place(
            x=11.0 + navigate_area_width,
            y=83.0,
            width=151.0,
            height=17.0
        )

        canvas.create_text(
            14.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Nº Ordem",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de pressionar Enter no campo de filtro
        self.filter_order.bind("<Return>", self.filter_all)

        # Associa a função de filtragem ao evento de alteração no texto do campo de filtro
        self.filter_order.bind("<KeyRelease>", self.filter_all)

        # Combobox Centrab

        self.combobox_responsavel = ttk.Combobox(
            self,
            values=list(self.df_responsavel),
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_responsavel['state'] = 'readonly'

        self.combobox_responsavel.current(0)  # Set default selection
        self.combobox_responsavel.place(x=190.0 + navigate_area_width, y=83.0, width=149.0, height=20.0)

        canvas.create_text(
            193.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Responsável",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de pressionar Enter no campo de filtro
        self.combobox_responsavel.bind("<<ComboboxSelected>>", self.filter_all)

        # Combobox Mes

        self.combobox_month = ttk.Combobox(
            self,
            values=[""] + aux_custom_classes.months + ["N/A"],
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_month['state'] = 'readonly'

        self.combobox_month.current(0)  # Set default selection
        self.combobox_month.place(x=365.0 + navigate_area_width, y=83.0, width=149.0, height=20.0)

        canvas.create_text(
            368.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Mês Plan.",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        self.combobox_month.bind("<<ComboboxSelected>>", self.filter_all)

        self.combobox_custo = ttk.Combobox(
            self,
            values=["", "Sem Custo", "Com Custo", "Sem Saldo Disp."],
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_custo['state'] = 'readonly'

        self.combobox_custo.current(0)  # Set default selection
        self.combobox_custo.place(x=540.0 + navigate_area_width, y=83.0, width=149.0, height=20.0)

        canvas.create_text(
            543.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Custo",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        self.combobox_custo.bind("<<ComboboxSelected>>", self.filter_all)

        # Combobox Revisão

        self.combobox_revisao = ttk.Combobox(
            self,
            values=list(self.df_revisao),
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_revisao['state'] = 'readonly'

        self.combobox_revisao.current(0)  # Set default selection
        self.combobox_revisao.place(x=710.0 + navigate_area_width, y=83.0, width=149.0, height=20.0)

        canvas.create_text(
            713.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Revisão",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de pressionar Enter no campo de filtro
        self.combobox_revisao.bind("<<ComboboxSelected>>", self.filter_all)


        # Combobox Ano
        if aux_functions_df.current_month == 11 or aux_functions_df.current_month == 12:
            self.combobox_ano = ttk.Combobox(
                self,
                values=[aux_functions_df.current_year, aux_functions_df.current_year + 1],
                background="#0046AD",
                foreground="#000716",
                state='readonly'
            )
            self.combobox_ano.set(aux_functions_df.current_year)
            self.combobox_ano.place(x=785.0 + navigate_area_width, y=110.0, width=50.0, height=20.0)
            self.combobox_ano.bind("<<ComboboxSelected>>", self.filter_saldo)
            self.filter_saldo()

        '''
        Botão Aprovar/Requisitar
        '''

        def on_hover_approv(event):
            button_approv.config(image=button_approv_hover_img)

        def on_leave_approv(event):
            button_approv.config(image=button_approv_img)

        button_approv_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("screen_gerente_button_approv.png"))

        button_approv_hover_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("screen_gerente_button_approv_hover.png"))

        button_approv = Button(
            self,
            image=button_approv_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.button_click,
            relief="flat"
        )
        button_approv.place(
            x=640.0 + navigate_area_width,
            y=487.0,
            width=172.0,
            height=42.11713790893555
        )

        button_approv.bind("<Enter>", on_hover_approv)
        button_approv.bind("<Leave>", on_leave_approv)

        '''
        Menu
        '''

        def toggle_menu():
            if self.is_expanded.get():
                # Collapse the menu
                menu_space.place_forget()
                self.is_expanded.set(False)
            else:
                # Expand the menu
                menu_space.place(x=0, y=50)
                menu_space.tkraise()  # Bring the menu to the front
                self.is_expanded.set(True)

        def on_hover_menu(event):
            button_menu.config(image=self.images['image_button_menu_hover'])

        def on_leave_menu(event):
            button_menu.config(image=self.images['image_button_menu'])

        self.images['image_button_menu'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_menu.png"))

        self.images['image_button_menu_hover'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_menu_hover.png"))

        button_menu = tk.Button(self,
                                image=self.images['image_button_menu'],
                                text="Expand",
                                command=toggle_menu,
                                relief="flat",
                                borderwidth=0,
                                highlightthickness=0,
                                )

        button_menu.place(x=0, y=0)
        button_menu.bind("<Enter>", on_hover_menu)
        button_menu.bind("<Leave>", on_leave_menu)

        menu_space = tk.Frame(self, bd=5, relief='raised', width=150, height=400, bg='lightgrey')

        def on_hover_go_approv(event):
            button_go_mov_saldo.config(image=button_go_mov_saldo_hover_img)

        def on_leave_go_approv(event):
            button_go_mov_saldo.config(image=button_go_mov_saldo_img)

        button_go_mov_saldo_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_go_mov_saldo.png"))

        button_go_mov_saldo_hover_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_go_mov_saldo_hover.png"))

        button_go_mov_saldo = tk.Button(menu_space,
                                        image=button_go_mov_saldo_img,
                                        relief="flat",
                                        borderwidth=0,
                                        highlightthickness=0,
                                        command=self.go_to_screen_mov_saldo
                                        )
        button_go_mov_saldo.bind("<Enter>", on_hover_go_approv)
        button_go_mov_saldo.bind("<Leave>", on_leave_go_approv)

        button_go_mov_saldo.pack(pady=5)

    def go_to_screen_mov_saldo(self):
        self.master.show_screen("Movimentações de Saldo")

    def reset_and_go_to_current(self):
        self.master.reset_and_show_current_screen()

    def button_click(self):
        text1 = self.permite_entry.get("1.0", "end-1c")
        text2 = self.to_approv_entry.get("1.0", "end-1c")
        # Process text from toaprove_entry
        if text1 != "":
            lines = text1.strip().split('\n')
            ordem = [line.split(') ')[1].strip().split('-')[0] for line in lines]
            mes = [line.split('-')[1].strip()[:-1] if line.strip().endswith("*") else line.split('-')[1].strip() for
                   line in
                   lines]
            processo = 'Permite'
            df_toaprove = pd.DataFrame({'Nº Ordem': ordem, 'Mes': mes, 'Processo': processo})

        # Process text from tochange_entry
        if text2 != "":
            lines = text2.strip().split('\n')
            ordem = [line.split(') ')[1].strip().split('-')[0] for line in lines]
            mes = [line.split('-')[1].strip()[:-1] if line.strip().endswith("*") else line.split('-')[1].strip() for
                   line in
                   lines]
            processo = ['Aviso' if '*' in line else 'Aprovacao' for line in lines]
            df_tochange = pd.DataFrame({'Nº Ordem': ordem, 'Mes': mes, 'Processo': processo})

        # Concatenate both DataFrames
        if text1 != "" and text2 != "":
            df_combined = pd.concat([df_toaprove, df_tochange], ignore_index=True)
        elif text1 != "":
            df_combined = df_toaprove
        elif text2 != "":
            df_combined = df_tochange
        else:
            df_combined = pd.DataFrame()  # Empty DataFrame if both entry widgets are empty

        if not df_combined.empty:
            df_combined["Nº Ordem"] = df_combined["Nº Ordem"].astype(int)
            merged_df = pd.merge(df_combined, self.df_all_info, on="Nº Ordem", how="inner")
            merged_df = pd.merge(merged_df, self.df_email, on="Responsável", how="left")
            self.df_sap = merged_df
            df_email = merged_df[(merged_df['Processo'] == 'Aprovacao')][
                ["Nº Ordem", "Mes", "Descr. Ordem", "Centrab", "Risco", "Oport.", "Custo"]]
            df_email["Mes Nº"] = aux_functions_df.map_month(df_email['Mes'], False)

            df_email['Saldo Antes'] = df_email['Mes Nº'].apply(self.get_saldo_antes)
            df_email['Saldo Depois'] = df_email['Mes'].apply(self.get_saldo_depois)

            if "Aprovacao" in merged_df['Processo'].values and "Permite" in merged_df['Processo'].values:
                approved = self.popup_aprovar(merged_df, "aprovacao", 2)
                if approved == "yes":
                    # try:
                    #     aux_send_email.send_outlook_email(
                    #         "williamyamashita.gff@suzano.com.br", "aprovar", df_email)  # MUDAR
                    # except:
                    #     pass
                    self.popup_aprovar(merged_df, "permite", 2, "yes")
                else:
                    self.popup_aprovar(merged_df, "permite", 2)
            else:
                if "Permite" in merged_df['Processo'].values:
                    self.popup_aprovar(merged_df, "permite", 1)

                else:
                    approved = self.popup_aprovar(merged_df, "aprovacao", 1)
                    # if approved == "yes":
                    #     try:
                    #         aux_send_email.send_outlook_email(
                    #             "williamyamashita.gff@suzano.com.br", "aprovar", df_email)  # MUDAR
                    #     except:
                    #         pass

    def popup_aprovar(self, df, tipo, qtd_poup, popup1_approve='no'):
        top = tk.Toplevel()
        top.configure(bg="#E2E1DD")  # Set background color of the popup window
        top.grab_set()
        # Change the font size and style
        font_family_column = "Suzano Unicase XBold"
        font_family = "Suzano Text"
        font_size = 8
        global popup_approve
        popup_approve = None
        if tipo == "aprovacao":
            df_table = df[df['Processo'] != 'Permite'][
                ['Nº Ordem', "Descr. Ordem", "Custo", 'Mes', 'Responsável', 'Saldo Disp.']]
            top.title(" APROVAÇÃO ")
            if "Aviso" in df['Processo'].values:
                text_intro = "Há uma ou mais ordens com custo e sem saldo disponível:"
                text_end = ("Em caso de aprovação um e-mail será enviado ao GE notificando-o sobre"
                            "\no estouro do saldo para o mês em questão."
                            "\nApós o envio o SAP será reiniciado/aberto para realizar a liberação e permite.")
            else:
                text_intro = "Deseja aprovar ou reavaliar as ordens?"
                text_end = "Em caso de aprovação o SAP será reiniciado/aberto para realizar a liberação e permite."
            text_button = "Aprovar"
            text_cancel = "Reavaliar"

            if qtd_poup == 2:
                def on_click_aproval_flow():
                    global popup_approve
                    popup_approve = "yes"
                    for ordem, saldo_disp in zip(df_table['Nº Ordem'], df_table['Saldo Disp.']):
                        update_status("tbl_aprovacao_fluxo", ordem, "DATA_GF_APROVA", datetime.today())
                        if not pd.isna(saldo_disp):
                            update_status("tbl_aprovacao_fluxo", ordem,
                                          "SALDO_QND_GF_APROV", aux_functions_df.to_number(saldo_disp))
                        update_status("tbl_aprovacao_fluxo", ordem, "STATUS", "APROVADO")

                        update_status("tbl_aprovacao_rateado", ordem, "DATA_GF_APROVA", datetime.today())
                        if not pd.isna(saldo_disp):
                            update_status("tbl_aprovacao_rateado", ordem,
                                          "SALDO_QND_GF_APROV", aux_functions_df.to_number(saldo_disp))
                        update_status("tbl_aprovacao_rateado", ordem, "STATUS", "APROVADO")
                    if "Aviso" in df['Processo'].values:
                        """MUDAR"""
                        df_email = df[df['Processo'] == 'Aviso']
                        df_email = df_email[['Nº Ordem', "Descr. Ordem", "Custo", 'Mes', 'Responsável', 'Saldo Disp.']]
                        aux_send_email.send_outlook_email("williamyamashita.gff@suzano.com.br", "ge", df_email)
                    df_change_sap = self.df_sap[self.df_sap['Processo'] != "Permite"]
                    aux_sap.permite_e_liberar(df_change_sap)
                    top.destroy()

                def on_click_cancel():  # Botão de Reprovar
                    global popup_approve
                    popup_approve = "no"
                    for ordem, saldo_disp in zip(df_table['Nº Ordem'], df_table['Saldo Disp.']):
                        update_status("tbl_aprovacao_fluxo", ordem, "DATA_GF_APROVA", datetime.today())
                        if not pd.isna(saldo_disp):
                            update_status("tbl_aprovacao_fluxo", ordem,
                                          "SALDO_QND_GF_APROV", aux_functions_df.to_number(saldo_disp))
                        update_status("tbl_aprovacao_fluxo", ordem, "STATUS", "REPROVADO")
                        update_status("tbl_aprovacao_rateado", ordem, "DATA_GF_APROVA", datetime.today())
                        if not pd.isna(saldo_disp):
                            update_status("tbl_aprovacao_rateado", ordem,
                                          "SALDO_QND_GF_APROV", aux_functions_df.to_number(saldo_disp))
                        update_status("tbl_aprovacao_rateado", ordem, "STATUS", "REPROVADO")
                    top.destroy()
            else:
                def on_click_aproval_flow():
                    global popup_approve
                    popup_approve = "no"
                    for ordem, saldo_disp in zip(df_table['Nº Ordem'], df_table['Saldo Disp.']):
                        update_status("tbl_aprovacao_fluxo", ordem, "DATA_GF_APROVA", datetime.today())
                        if not pd.isna(saldo_disp):
                            update_status("tbl_aprovacao_fluxo", ordem,
                                          "SALDO_QND_GF_APROV", aux_functions_df.to_number(saldo_disp))
                        update_status("tbl_aprovacao_fluxo", ordem, "STATUS", "APROVADO")
                        update_status("tbl_aprovacao_rateado", ordem, "DATA_GF_APROVA", datetime.today())
                        if not pd.isna(saldo_disp):
                            update_status("tbl_aprovacao_rateado", ordem,
                                          "SALDO_QND_GF_APROV", aux_functions_df.to_number(saldo_disp))
                        update_status("tbl_aprovacao_rateado", ordem, "STATUS", "APROVADO")
                    if "Aviso" in df['Processo'].values:
                        """MUDAR"""
                        df_email = df[df['Processo'] == 'Aviso']
                        df_email = df_email[['Nº Ordem', "Descr. Ordem", "Custo", 'Mes', 'Responsável', 'Saldo Disp.']]
                        aux_send_email.send_outlook_email("williamyamashita.gff@suzano.com.br", "ge", df_email)
                    """
                    MACRO SAP AQUI USANDO self.df_sap
                    """
                    aux_sap.permite_e_liberar(self.df_sap)
                    self.reset_and_go_to_current()

                def on_click_cancel():
                    global popup_approve
                    popup_approve = "no"
                    for ordem, saldo_disp in zip(df_table['Nº Ordem'], df_table['Saldo Disp.']):
                        update_status("tbl_aprovacao_fluxo", ordem, "DATA_GF_APROVA", datetime.today())
                        if not pd.isna(saldo_disp):
                            update_status("tbl_aprovacao_fluxo", ordem,
                                          "SALDO_QND_GF_APROV", aux_functions_df.to_number(saldo_disp))
                        update_status("tbl_aprovacao_fluxo", ordem, "STATUS", "REPROVADO")
                        update_status("tbl_aprovacao_rateado", ordem, "DATA_GF_APROVA", datetime.today())
                        if not pd.isna(saldo_disp):
                            update_status("tbl_aprovacao_rateado", ordem,
                                          "SALDO_QND_GF_APROV", aux_functions_df.to_number(saldo_disp))
                        update_status("tbl_aprovacao_rateado", ordem, "STATUS", "REPROVADO")
                    self.reset_and_go_to_current()

            command_approve = on_click_aproval_flow
            command_cancel = on_click_cancel
        elif tipo == "permite":
            df_table = df[df['Processo'] != 'Aprovacao'][
                ['Nº Ordem', "Descr. Ordem", "Custo", 'Mes', 'Responsável', 'Saldo Disp.']]
            top.title(" APROVAÇÃO ")
            text_intro = "Deseja realizar a aprovação e liberação das ordens?"
            text_end = "Após a aprovação o SAP será aberto para realizar a liberação e permite para as ordens."
            text_button = "Aprovar"
            text_cancel = "Cancelar"
            df_insert = df.loc[df['Processo'] != 'Aprovacao']
            df_insert = df_insert.drop(columns=['EMAIL_GF', 'EMAIL_GE', 'Mês Atual', 'Processo'])
            # df_insert = df_insert.drop(columns=['Processo'], inplace=False)
            df_insert['DT_ATUALIZACAO'] = datetime.today().date()
            df_insert['DATA_GF_APROVA'] = datetime.today()
            df_insert['APROVADOR'] = self.user
            df_insert['Mes'] = aux_functions_df.map_month(df_insert['Mes'], False)
            df_insert['Custo'] = df_insert['Custo'].str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.')
            df_insert['Saldo Disp.'] = df_insert['Saldo Disp.'].str.replace('R$ ', '').str.replace('.', '').str.replace(
                ',', '.')
            df_insert = df_insert.where(pd.notnull(df_insert), None)
            pd.set_option('display.max_columns', None)
            df_insert.rename(columns={
                "Nº Ordem": "ORDEM",
                "Descr. Ordem": "DESCR_ORDEM",
                "Centrab": "CENTRAB",
                "Mes": "MES_PLAN",
                "Custo": "CUSTO",
                "Centro de Custo": "CENTRO_CUSTO",
                "Responsável": "RESPONSAVEL",
                "Tp. Ordem": "TIPO_ORDEM",
                "Risco": "RISCO",
                "Oport.": "OPORTUNIDADE",
                "Mês Atual": "MES_ATUAL",
                "Tipo": "TIPO_PROCESSO",
                "Saldo Disp.": "SALDO_QND_GF_APROV",
                'Stat. Usr.': "STATUS_USUARIO",
                'Stat. Sist.': "STATUS_SISTEMA"
            }, inplace=True)

            if popup1_approve == "yes":  # Se teve 2 Pop Ups e aprovou o 1º
                def on_click_aprove():
                    global popup_approve
                    popup_approve = "no"
                    insert_info(df_insert, "tbl_aprovado_permite", top)
                    """
                    MACRO SAP AQUI USANDO self.df_sap
                    """
                    df_change_sap = self.df_sap[self.df_sap['Processo'] == "Permite"]
                    aux_sap.permite_e_liberar(df_change_sap)
                    self.reset_and_go_to_current()

                def on_click_cancel():
                    global popup_approve
                    popup_approve = "no"
                    self.reset_and_go_to_current()
            else:
                def on_click_aprove():  # Teve 2 pop up e o 1º foi reprovado/cancelado ou só 1 pop up
                    global popup_approve
                    popup_approve = "no"
                    insert_info(df_insert, "tbl_aprovado_permite", top)
                    """
                    MACRO SAP AQUI USANDO self.df_sap
                    """
                    df_change_sap = self.df_sap[self.df_sap['Processo'] == "Permite"]
                    aux_sap.permite_e_liberar(df_change_sap)
                    self.reset_and_go_to_current()

                if qtd_poup == 2:
                    def on_click_cancel():
                        global popup_approve
                        popup_approve = "no"
                        self.reset_and_go_to_current()
                else:
                    def on_click_cancel():
                        global popup_approve
                        popup_approve = "no"
                        top.destroy()
            command_approve = on_click_aprove
            command_cancel = on_click_cancel

        if len(df_table) <= 25:
            intro_label = tk.Label(top, text=text_intro,
                                   font=(font_family_column, font_size), bg="#E2E1DD")
            intro_label.grid(row=0, column=0, columnspan=6, padx=10, pady=5)

            # Convert the DataFrame to a dictionary
            df_dict = df_table[['Nº Ordem', 'Descr. Ordem', 'Custo', 'Mes', 'Responsável', 'Saldo Disp.']].to_dict(
                'records')

            # Add column headers
            header_font = font.Font(family=font_family_column, size=font_size, weight="bold")
            headers = ['Ordem', 'Descr', 'Custo', 'Mês', 'Responsável', 'Saldo Disp.']
            for col, header in enumerate(headers):
                header_label = tk.Label(top, text=header, font=header_font, bg="#E2E1DD")
                header_label.grid(row=1, column=col, sticky="ew", padx=5, pady=1)

            # Create labels and entry widgets for each row in the DataFrame
            for i, data in enumerate(df_dict):
                # Entry widgets for 'Ordem', 'Descr', 'Custo', 'Mês', and 'Saldo Disp.'
                ordem_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=10)
                ordem_entry.insert(0, data['Nº Ordem'])
                ordem_entry.grid(row=i + 2, column=0, sticky="ew", padx=5, pady=1)
                descr_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=30)
                descr_entry.insert(0, data['Descr. Ordem'])
                descr_entry.grid(row=i + 2, column=1, sticky="ew", padx=5, pady=1)
                custo_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=15)
                custo_entry.insert(0, data['Custo'])
                custo_entry.grid(row=i + 2, column=2, sticky="ew", padx=5, pady=1)
                mes_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=15)
                mes_entry.insert(0, data['Mes'])
                mes_entry.grid(row=i + 2, column=3, sticky="ew", padx=5, pady=1)
                resp_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=18)
                resp_entry.insert(0, data['Responsável'])
                resp_entry.grid(row=i + 2, column=4, sticky="ew", padx=5, pady=1)
                saldo_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=15)
                saldo_entry.insert(0, data['Saldo Disp.'])
                saldo_entry.grid(row=i + 2, column=5, sticky="ew", padx=5, pady=1)

            outro_label = tk.Label(top, text=text_end, font=(font_family_column, font_size), bg="#E2E1DD")
            outro_label.grid(row=len(df_dict) + 2, column=0, columnspan=6, padx=10, pady=5)

            # Add buttons
            start_button = tk.Button(top, text=text_button, command=command_approve)
            start_button.grid(row=len(df_dict) + 3, column=2, padx=10, pady=5, sticky="ew")

            cancel_button = tk.Button(top, text=text_cancel, command=command_cancel)
            cancel_button.grid(row=len(df_dict) + 3, column=3, padx=10, pady=5, sticky="ew")

            # Centralize columns
            for i in range(4):
                top.grid_columnconfigure(i, weight=1)

            # Calculate the height of the window based on the number of rows
            total_rows = len(df_dict) + 4  # Number of rows in the DataFrame plus 4 (intro text, outro text, buttons)
            height = 50 + 20 * total_rows  # Initial height plus height per row
            width = 700

        else:
            intro_label = tk.Label(top, text=text_intro,
                                   font=(font_family_column, font_size), bg="#E2E1DD")
            intro_label.grid(row=0, column=0, columnspan=6, padx=10, pady=5)
            outro_label = tk.Label(top, text=text_end, font=(font_family_column, font_size), bg="#E2E1DD")
            outro_label.grid(row=2, column=0, columnspan=6, padx=10, pady=5)

            # Add buttons
            start_button = tk.Button(top, text=text_button, command=command_approve)
            start_button.grid(row=3, column=2, padx=10, pady=5, sticky="ew")

            cancel_button = tk.Button(top, text=text_cancel, command=command_cancel)
            cancel_button.grid(row=3, column=3, padx=10, pady=5, sticky="ew")
            height = 100  # Initial height plus height per row
            width = 600

        top.geometry(f"{width}x{height}")  # Adjust the size as needed
        top.wait_window()

        if popup_approve is not None:
            return popup_approve

    def get_saldo_antes(self, mes):
        saldo_value = getattr(self, f'saldo_mes_{mes}', 0)
        return saldo_value

    def get_saldo_depois(self, mes):

        saldo_value = getattr(self, f'{mes.lower()}_entry', 0).get()
        return saldo_value
