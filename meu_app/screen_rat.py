import getpass
import numpy as np
import tkinter as tk
import pandas as pd
import aux_functions_df
import aux_send_email
import aux_custom_classes
from tkinter import ttk
from datetime import datetime
from aux_custom_classes import CustomRateadoCheckboxTreeview
from tkinter import Canvas, Entry, font, Button, PhotoImage

# Set display options for pandas
pd.set_option('display.max_columns', None)


def update_status(table, ordem, column, status):
    conn = aux_functions_df.connect_db()
    cursor = conn.cursor()
    # Prepare the update query with placeholders %s
    update_query = (f"UPDATE {table} "
                    f"SET {column} = '{status}' "
                    f"WHERE ORDEM = {ordem} AND STATUS <> 'REPROVADO' ")
    cursor.execute(update_query)

    conn.commit()
    cursor.close()
    conn.close()


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


class ScreenRateado(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.user = aux_functions_df.user
        self.is_expanded = tk.BooleanVar(value=False)

        '''
        Pegar df ordens
        '''
        self.df_ordens, self.df_with_month, self.df_ordens_popup = aux_functions_df.get_view_dados_rat()

        # Pegar dados para o Popup com as informações das ordens
        self.df_ordens_popup = self.df_ordens_popup[['Nº Ordem', 'Descr. Ordem',
                                               "Responsável", 'Centro de Custo', 'Risco', 'Oport.', 'Custo', 'Mês', 'Revisão']]

        if self.user == "williamyamashita.gff":
            pass
        else:
            self.df_ordens = pd.merge(self.df_ordens, aux_functions_df.df_user, on='Responsável', how='left')
            self.df_ordens = self.df_ordens[self.df_ordens['USUARIO'].isin(aux_functions_df.list_user)]
            self.df_ordens.drop(columns=['USUARIO'], inplace=True)
            
            self.df_with_month = pd.merge(self.df_with_month, aux_functions_df.df_user, on='Responsável', how='left')
            self.df_with_month = self.df_with_month[self.df_with_month['USUARIO'].isin(aux_functions_df.list_user)]
            self.df_with_month.drop(columns=['USUARIO'], inplace=True)

        # Pegar os dados para a tabela de ordens a aprovar
        self.df_ordens_table = self.df_ordens[['Nº Ordem', "Centrab", 'Risco', 'Oport.', 'Custo', 'Mês', "Status",
                                               "Revisão"]]

        self.df_centrab = np.sort(self.df_ordens['Centrab'].unique())
        self.df_revisao = np.sort(self.df_ordens['Revisão'].unique())

        '''
        Pegar dados de saldo
        '''
        self.df_saldo_todos = aux_functions_df.get_saldo("rateado", aux_functions_df.current_year)
        df_saldo_current = aux_functions_df.get_saldo("", aux_functions_df.current_year)

        df_saldo_future = aux_functions_df.get_saldo("", aux_functions_df.current_year + 1)

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
        Pegar dados aprovação reteado
        """

        self.df_with_month_table = self.df_with_month[['Nº Ordem', "Centrab", 'Risco', 'Oport.', 'Custo', 'Mês',
                                                       "Revisão"]]

        self.df_n_approv = self.df_ordens_popup.groupby('Nº Ordem').size().reset_index(name='N_APROVADORES')
        self.df_all_info = aux_functions_df.get_orders_all(self.df_ordens, self.df_with_month)  # MUDAR
        self.df_all_info = pd.merge(self.df_all_info, self.df_n_approv, on='Nº Ordem', how='left')
        self.df_email = aux_functions_df.df_email.copy()
        self.df_email.drop(columns=['USUARIO', 'EMAIL_USUARIO'], inplace=True)

        # Store image references
        self.images = {}
        self.create_widgets()

    def filter_saldo(self, event=None):

        # Obtém o texto digitado nos filtros
        filter_ano_text = self.combobox_ano.get()
        self.tree_orders_to_approve.ano = filter_ano_text
        self.tree_orders_to_approve.uncheck_all()
        self.tree_orders_to_approve.checked_ordens.clear()
        self.tree_orders_to_approve.checked_mes.clear()
        self.tree_orders_to_approve.checked_cost.clear()
        self.toaprove_entry.config(state="normal")
        self.toaprove_entry.delete("1.0", tk.END)
        self.toaprove_entry.config(state="disabled")

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
        entry_widgets = {
            "Jan": self.tree_orders_to_approve.jan_values, "Fev": self.tree_orders_to_approve.fev_values,
            "Mar": self.tree_orders_to_approve.mar_values, "Abr": self.tree_orders_to_approve.abr_values,
            "Mai": self.tree_orders_to_approve.mai_values, "Jun": self.tree_orders_to_approve.jun_values,
            "Jul": self.tree_orders_to_approve.jul_values, "Ago": self.tree_orders_to_approve.ago_values,
            "Set": self.tree_orders_to_approve.set_values, "Out": self.tree_orders_to_approve.out_values,
            "Nov": self.tree_orders_to_approve.nov_values, "Dez": self.tree_orders_to_approve.dez_values,
        }

        # Obtém o texto digitado nos filtros
        filter_order_text = self.filter_order_1.get()
        filter_centrab_text = self.combobox_centrab.get()
        filter_mes_text = self.combobox_month.get()
        filter_revisao_text = self.combobox_revisao.get()

        # Remove quaisquer filtros anteriores
        self.tree_orders_to_approve.delete(*self.tree_orders_to_approve.get_children())
        checked_values_ordem = self.tree_orders_to_approve.get_checked_values("Ordem")
        checked_values_mes = self.tree_orders_to_approve.get_checked_values("Mês")

        # Filtra as ordens com base nos filtros selecionados
        filtered_orders = self.df_ordens_table[
            self.df_ordens_table['Nº Ordem'].astype(str).str.contains(filter_order_text, case=False) &
            self.df_ordens_table['Centrab'].astype(str).str.contains(filter_centrab_text, case=False) &
            self.df_ordens_table['Mês'].astype(str).str.contains(filter_mes_text, case=False) &
            self.df_ordens_table['Revisão'].astype(str).str.contains(filter_revisao_text, case=False)
            ]

        # Preenche a treeview com as ordens filtradas
        inserted_items = []

        for index, row in filtered_orders.iterrows():
            values = [row[col] for col in filtered_orders.columns]
            status = str(row["Status"])
            ordem = str(row['Nº Ordem'])
            # Check if status is not "OK" and change background color accordingly
            if status != "OK":
                item = self.tree_orders_to_approve.insert("", tk.END, values=values, tags=("gray_background",))
                inserted_items.append(item)
            else:
                if ordem in checked_values_ordem:
                    mes_index = checked_values_ordem.index(ordem)
                    mes = checked_values_mes[mes_index]
                    entry_widget = entry_widgets.get(mes)
                    values[filtered_orders.columns.get_loc('Mês')] = mes
                    balance = float(
                        entry_widget.get().replace('R$', '').replace('.', '').replace(',', '.'))  # Valor do saldo atual
                    if balance < 0:
                        item = self.tree_orders_to_approve.insert("", tk.END, values=values, tags=("red_background",))
                        inserted_items.append(item)
                    else:
                        item = self.tree_orders_to_approve.insert("", tk.END, values=values)
                        inserted_items.append(item)
                    self.tree_orders_to_approve._check_ancestor(item)
                    self.tree_orders_to_approve._check_descendant(item)
                else:
                    item = self.tree_orders_to_approve.insert("", tk.END, values=values)
                    inserted_items.append(item)

        # Filtra as ordens com base nos filtros selecionados
        filtered_orders = self.df_with_month_table[
            self.df_with_month_table['Nº Ordem'].astype(str).str.contains(filter_order_text, case=False) &
            self.df_with_month_table['Centrab'].astype(str).str.contains(filter_centrab_text, case=False) &
            self.df_with_month_table['Mês'].astype(str).str.contains(filter_mes_text, case=False) &
            self.df_with_month_table['Revisão'].astype(str).str.contains(filter_revisao_text, case=False)
            ]

        # Remove quaisquer filtros anteriores
        self.tree_approval.delete(*self.tree_approval.get_children())
        checked_values_ordem = self.tree_approval.get_checked_values("Ordem")
        checked_values_mes = self.tree_approval.get_checked_values("Mês")
        checked_values_custo = self.tree_approval.get_checked_values("Custo")

        for index, row in filtered_orders.iterrows():
            values = [row[col] for col in filtered_orders.columns]
            ordem = str(row['Nº Ordem'])
            # Check if status is not "OK" and change background color accordingly
            if ordem in checked_values_ordem:
                mes_index = checked_values_ordem.index(ordem)
                mes = checked_values_mes[mes_index]
                custo = checked_values_custo[mes_index]
                entry_widget = entry_widgets.get(mes)
                values[filtered_orders.columns.get_loc('Mês')] = mes
                balance = float(
                    entry_widget.get().replace('R$', '').replace('.', '').replace(',', '.'))  # Valor do saldo atual
                if balance < 0 and custo != "R$ 0,00":
                    item = self.tree_approval.insert("", tk.END, values=values, tags=("red_background",))
                    inserted_items.append(item)
                else:
                    item = self.tree_approval.insert("", tk.END, values=values)
                    inserted_items.append(item)
                self.tree_approval._check_ancestor(item)
                self.tree_approval._check_descendant(item)
            else:
                item = self.tree_approval.insert("", tk.END, values=values)
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
            89.0,
            8.0,
            anchor="nw",
            text="APROVAÇÃO DE CUSTOS RATEADOS",
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

        # Banner Ordens A Aprovar
        self.images['image_2'] = PhotoImage(file=aux_custom_classes.relative_to_assets("image_2.png"))
        canvas.create_image(
            271.0 + navigate_area_width,
            124.0,
            image=self.images['image_2']
        )

        canvas.create_text(
            160.0 + navigate_area_width,
            112.0,
            anchor="nw",
            text="       ORDENS A APROVAR",
            fill="#FFFFFF",
            font=font.Font(family="Suzano Unicase XBold", size=13)
        )

        # Banner Compromissado
        self.images['image_3'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("image_3.png"))
        canvas.create_image(
            271.0 + navigate_area_width,
            381.0,
            image=self.images['image_3']
        )

        canvas.create_text(
            70.0 + navigate_area_width,
            368.0,
            anchor="nw",
            text="ORDENS JÁ APROVADAS POR OUTRO RESPONSÁVEL",
            fill="#FFFFFF",
            font=font.Font(family="Suzano Unicase XBold", size=13)
        )

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

        '''
        Tabela Colegiado Rateado
        '''

        # Define as dimensões da tabela
        table_orders_to_approve_width = 400
        table_orders_to_approve_height = 220

        # Define as fontes
        # custom_font_tree = font.Font(family="Suzano Unicase", size=8)
        custom_font_header = font.Font(family="Suzano Unicase Medium", size=8)

        # Define as cores
        style = ttk.Style()
        style.theme_use("alt")  # Use the "clam" theme as a base
        style.configure("Treeview", font=custom_font_header, background="#E6E6E6", foreground="black")
        style.configure("Treeview.Heading", font=custom_font_header,
                        background="black", foreground="white", hovercolor="black", justify="center")

        custom_font_to_change_tree = font.Font(family="Suzano Unicase", size=8)
        custom_font_to_change_header = font.Font(family="Suzano Unicase XBold", size=8)

        # Create a label for the checked values
        label_checked_values = tk.Label(self, text="À aprovar", font=custom_font_to_change_header, background="#E2E1DD")
        label_checked_values.place(x=table_orders_to_approve_width + 46 + navigate_area_width, y=143)

        # Create a Text widget to display checked values of orders to approve
        self.toaprove_entry = tk.Text(self, width=15, height=16, font=custom_font_to_change_tree, background="#E6E6E6",
                                      state=tk.DISABLED)
        self.toaprove_entry.place(x=table_orders_to_approve_width + 25 + navigate_area_width, y=163)

        # Define as dimensões da tabela
        table_orders_to_change_width = 400
        table_orders_to_change_height = 140

        # Create a Text widget to display checked values of orders to approve
        self.approval_entry = tk.Text(self, width=15, height=9, font=custom_font_to_change_tree, background="#E6E6E6",
                                      state=tk.DISABLED)
        self.approval_entry.place(x=table_orders_to_change_width + 25 + navigate_area_width, y=420)
        try:
            ano = self.combobox_ano.get()
        except:
            ano = aux_functions_df.current_year
        # Cria tabela com checkbox
        self.tree_orders_to_approve = (
            aux_custom_classes.CustomRateadoCheckboxTreeview(self, self.toaprove_entry, self.approval_entry,
                                                             self.jan_entry,
                                                             self.fev_entry, self.mar_entry, self.abr_entry,
                                                             self.mai_entry,
                                                             self.jun_entry, self.jul_entry, self.ago_entry,
                                                             self.set_entry,
                                                             self.out_entry, self.nov_entry, self.dez_entry,
                                                             self.acum_mes_entry,
                                                             self.acum_ano_entry, "tbl_a_aprovar", self.df_ordens_popup,
                                                             self.df_with_month_table, self.df_saldo_todos,
                                                             ano))

        # Adicionas as columns do df, excluindo a coluna "Status"
        columns = self.df_ordens_table.columns.tolist()
        columns.remove("Status")
        columns.remove("Revisão")
        self.tree_orders_to_approve["columns"] = columns

        # Define os headers das colunas
        for col in columns:
            self.tree_orders_to_approve.heading(col, text=col)

        # Insere as informações
        for index, row in self.df_ordens_table.iterrows():
            values = [row[col] for col in columns]
            status = row["Status"]
            # Check if status is not "OK" and change background color accordingly
            if status != "OK":
                self.tree_orders_to_approve.insert("", tk.END, values=values, tags=("gray_background",))
            else:
                self.tree_orders_to_approve.insert("", tk.END, values=values)

        # Define a cor de fundo cinza para as linhas com status diferente de "OK"
        style.configure("gray_background.Treeview", background="gray")

        # Aplica as tags para as linhas com status diferente de "OK"
        self.tree_orders_to_approve.tag_configure("gray_background", background="gray")
        self.tree_orders_to_approve.tag_configure("red_background", background="red")

        # Ajusta a largura das colunas
        self.tree_orders_to_approve.column("#0", width=30)
        self.tree_orders_to_approve.column("#1", width=55)
        self.tree_orders_to_approve.column("#2", width=48)
        self.tree_orders_to_approve.column("#3", width=30)
        self.tree_orders_to_approve.column("#4", width=40)
        self.tree_orders_to_approve.column("#5", width=80)
        self.tree_orders_to_approve.column("#6", width=50)

        # Posiciona a tabela
        self.tree_orders_to_approve.place(x=5 + navigate_area_width, y=143, width=table_orders_to_approve_width,
                                          height=table_orders_to_approve_height)

        # Adiciona um srollbar a tabela
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree_orders_to_approve.yview)
        scrollbar.place(x=2 + table_orders_to_approve_width + navigate_area_width, y=143,
                        height=table_orders_to_approve_height,
                        anchor="nw")

        self.tree_orders_to_approve.config(yscrollcommand=scrollbar.set)

        for col in columns:
            self.tree_orders_to_approve.column(col, anchor="center")

        '''
        EM APROVAÇÃO
        '''

        # Create a label for the checked values
        label_checked_values = tk.Label(self, text="À alterar", font=custom_font_to_change_header, background="#E2E1DD")
        label_checked_values.place(x=table_orders_to_change_width + 46 + navigate_area_width, y=399)

        # Cria tabela com checkbox
        self.tree_approval = CustomRateadoCheckboxTreeview(self, self.approval_entry, self.toaprove_entry,
                                                           self.jan_entry,
                                                           self.fev_entry, self.mar_entry, self.abr_entry,
                                                           self.mai_entry,
                                                           self.jun_entry, self.jul_entry, self.ago_entry,
                                                           self.set_entry,
                                                           self.out_entry, self.nov_entry, self.dez_entry,
                                                           self.acum_mes_entry, self.acum_ano_entry, "tbl_with_month",
                                                           self.df_ordens_popup, self.df_ordens_table, self.df_saldo_todos,
                                                           ano)  # MUDAR

        # Adicionas as columns do df, excluindo a coluna "Status"
        columns = self.df_with_month_table.columns.tolist()
        columns.remove("Revisão")
        self.tree_approval["columns"] = columns

        # Define os headers das colunas
        for col in columns:
            self.tree_approval.heading(col, text=col)

        # Insere as informações
        for index, row in self.df_with_month_table.iterrows():
            values = [row[col] for col in columns]
            self.tree_approval.insert("", tk.END, values=values)

        # Define a cor de fundo cinza para as linhas com status diferente de "OK"
        style.configure("red_background.Treeview", background="red")

        # Aplica as tags para as linhas com status diferente de "OK"
        self.tree_approval.tag_configure("red_background", background="red")

        # Ajusta a largura das colunas
        self.tree_approval.column("#0", width=30)
        self.tree_approval.column("#1", width=55)
        self.tree_approval.column("#2", width=48)
        self.tree_approval.column("#3", width=30)
        self.tree_approval.column("#4", width=40)
        self.tree_approval.column("#5", width=80)
        self.tree_approval.column("#6", width=50)

        # Posiciona a tabela
        self.tree_approval.place(x=5 + navigate_area_width, y=399, width=table_orders_to_change_width,
                                 height=table_orders_to_change_height)

        # Adiciona um srollbar a tabela
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree_approval.yview)
        scrollbar.place(x=2 + table_orders_to_change_width + navigate_area_width, y=399,
                        height=table_orders_to_change_height,
                        anchor="nw")

        self.tree_approval.config(yscrollcommand=scrollbar.set)

        for col in columns:
            self.tree_approval.column(col, anchor="center")

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

        self.filter_order_1 = Entry(
            self,
            bd=0,
            bg="#B7B1A9",
            fg="#000716",
            highlightthickness=0
        )
        self.filter_order_1.place(
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
        self.filter_order_1.bind("<Return>", self.filter_all)

        # Associa a função de filtragem ao evento de alteração no texto do campo de filtro
        self.filter_order_1.bind("<KeyRelease>", self.filter_all)

        # Combobox Centrab

        self.combobox_centrab = ttk.Combobox(
            self,
            values=[""] + list(self.df_centrab),
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_centrab['state'] = 'readonly'

        self.combobox_centrab.current(0)  # Set default selection
        self.combobox_centrab.place(x=190.0 + navigate_area_width, y=81.0, width=149.0, height=20.0)

        canvas.create_text(
            193.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Centrab",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de pressionar Enter no campo de filtro
        self.combobox_centrab.bind("<<ComboboxSelected>>", self.filter_all)

        # Combobox Mes

        self.combobox_month = ttk.Combobox(
            self,
            values=aux_custom_classes.months_from_current,
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_month['state'] = 'readonly'

        self.combobox_month.current(0)  # Set default selection
        self.combobox_month.place(x=370.0 + navigate_area_width, y=81.0, width=149.0, height=20.0)

        canvas.create_text(
            370.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Mes",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        self.combobox_month.bind("<<ComboboxSelected>>", self.filter_all)

        # Combobox Revisão

        if "" not in list(self.df_revisao):
            result = [""] + list(self.df_revisao)
        else:
            result = list(self.df_revisao)

        self.combobox_revisao = ttk.Combobox(
            self,
            values=result,
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_revisao['state'] = 'readonly'

        self.combobox_revisao.current(0)  # Set default selection
        self.combobox_revisao.place(x=545.0 + navigate_area_width, y=81.0, width=149.0, height=20.0)

        canvas.create_text(
            548.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Revisão",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de pressionar Enter no campo de filtro
        self.combobox_revisao.bind("<<ComboboxSelected>>", self.filter_all)


        '''
        Botão Aprovar/Requisitar
        '''

        def on_hover_approv(event):
            button_approv.config(image=self.images['image_button_approv_hover'])

        def on_leave_approv(event):
            button_approv.config(image=self.images['image_button_approv'])

        self.images['image_button_approv'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("screen_mov_button_approv.png"))

        self.images['image_button_approv_hover'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("screen_mov_button_approv_hover.png"))

        button_approv = Button(
            self,
            image=self.images['image_button_approv'],
            borderwidth=0,
            highlightthickness=0,
            command=self.button_request_click,
            relief="flat"
        )
        button_approv.place(
            x=580.0 + navigate_area_width,
            y=487.0,
            width=142.0,
            height=42.11713790893555
        )

        button_approv.bind("<Enter>", on_hover_approv)
        button_approv.bind("<Leave>", on_leave_approv)

        '''
        Botão Reprovar
        '''

        def on_hover_reprov(event):
            button_reprov.config(image=button_reprov_hover_img)

        def on_leave_reprov(event):
            button_reprov.config(image=button_reprov_img)

        button_reprov_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("screen_mov_button_reprov.png"))

        button_reprov_hover_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("screen_mov_button_reprov_hover.png"))

        button_reprov = Button(
            self,
            image=button_reprov_img,
            borderwidth=0,
            highlightthickness=0,
            command=self.button_reprov_click,
            relief="flat"
        )
        button_reprov.place(
            x=730.0 + navigate_area_width,
            y=487.0,
            width=142.0,
            height=42.11713790893555
        )

        button_reprov.bind("<Enter>", on_hover_reprov)
        button_reprov.bind("<Leave>", on_leave_reprov)

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
            button_go_approv.config(image=button_go_approv_hover_img)

        def on_leave_go_approv(event):
            button_go_approv.config(image=button_go_approv_img)

        button_go_approv_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_go_approv.png"))

        button_go_approv_hover_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_go_approv_hover.png"))

        button_go_approv = tk.Button(menu_space,
                                     image=button_go_approv_img,
                                     relief="flat",
                                     borderwidth=0,
                                     highlightthickness=0,
                                     command=self.go_to_screen_aprovar
                                     )
        button_go_approv.bind("<Enter>", on_hover_go_approv)
        button_go_approv.bind("<Leave>", on_leave_go_approv)

        def on_hover_go_mov_saldo(event):
            button_go_mov_saldo.config(image=button_go_mov_saldo_hover_img)

        def on_leave_go_mov_saldo(event):
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

        button_go_mov_saldo.bind("<Enter>", on_hover_go_mov_saldo)
        button_go_mov_saldo.bind("<Leave>", on_leave_go_mov_saldo)

        # Botão Tela Status
        def on_hover_go_rat(event):
            button_go_status.config(image=button_go_status_hover_img)

        def on_leave_go_rat(event):
            button_go_status.config(image=button_go_status_img)

        button_go_status_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_go_status.png"))

        button_go_status_hover_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_go_status_hover.png"))

        button_go_status = tk.Button(menu_space,
                                  image=button_go_status_img,
                                  relief="flat",
                                  borderwidth=0,
                                  highlightthickness=0,
                                  command=self.go_to_screen_status
                                  )

        button_go_status.bind("<Enter>", on_hover_go_rat)
        button_go_status.bind("<Leave>", on_leave_go_rat)

        button_go_approv.pack(pady=5)
        button_go_mov_saldo.pack(pady=5)
        button_go_status.pack(pady=5)

        self.filter_saldo()

    def go_to_screen_aprovar(self):
        self.master.show_screen("Aprovação de Custos")

    def go_to_screen_mov_saldo(self):
        self.master.show_screen("Movimentações de Saldo")

    def go_to_screen_status(self):
        self.master.show_screen("Status Ordens")

    def reset_and_go_to_current(self):
        self.master.reset_and_show_current_screen()

    def button_request_click(self):
        text1 = self.toaprove_entry.get("1.0", "end-1c")
        text2 = self.approval_entry.get("1.0", "end-1c")
        # Process text from torequest_entry
        if text1 != "":
            lines = text1.strip().split('\n')
            ordem = [line.split(') ')[1].strip().split('-')[0] for line in lines]
            mes = [line.split('-')[1].strip()[:-1] if line.strip().endswith("*") else line.split('-')[1].strip() for
                   line in
                   lines]
            processo = 'Aprovacao'  #['Aprovacao' if '*' in line else 'Direto' for line in lines]  # MUDAR SE VOLTAR AUTONOMIA
            df_to_approve = pd.DataFrame({'Nº Ordem': ordem, 'Mes': mes, 'Processo': processo})

        if text2 != "":
            lines = text2.strip().split('\n')
            ordem = [line.split(') ')[1].strip().split('-')[0] for line in lines]
            mes = [line.split('-')[1].strip()[:-1] if line.strip().endswith("*") else line.split('-')[1].strip() for
                   line in
                   lines]
            processo = 'Aprovacao'  #['Aprovacao' if '*' in line else 'Direto' for line in lines]  # MUDAR SE VOLTAR AUTONOMIA
            df_approval = pd.DataFrame({'Nº Ordem': ordem, 'Mes': mes, 'Processo': processo})

        # Concatenate both DataFrames
        if text1 != "" and text2 != "":
            df_combined = pd.concat([df_to_approve, df_approval], ignore_index=True)
        elif text1 != "":
            df_combined = df_to_approve
        elif text2 != "":
            df_combined = df_approval
        else:
            df_combined = pd.DataFrame()  # Empty DataFrame if both entry widgets are empty

        if not df_combined.empty:
            df_combined["Nº Ordem"] = df_combined["Nº Ordem"].astype(int)
            merged_df = pd.merge(df_combined, self.df_all_info, on="Nº Ordem", how="inner")
            merged_df = pd.merge(merged_df, self.df_email, on="Responsável", how="inner")
            merged_df["N_APROVADO"] = merged_df['Nº Ordem'].apply(aux_functions_df.get_rat_n_aprovados)
            merged_df['SAP'] = merged_df.apply(
                lambda row: "SIM" if row['N_APROVADO'] == (row['N_APROVADORES'] - 1) else "NAO", axis=1)
            #  MUDAR SE VOLTAR AUTONOMIA
            merged_df = merged_df.drop(columns=['Mês Atual', 'N_APROVADO'], inplace=False)
            self.df_concluido = merged_df[(merged_df['SAP'] == 'SIM')]  # CRIADO PARA SABER QUAIS MUDAR O STATUS E
            df_email = merged_df[(merged_df['Processo'] == 'Aprovacao')][
                ["Nº Ordem", "Mes", "Descr. Ordem", "Centrab", "Risco", "Oport.", "Custo"]]
            df_email["Mes Nº"] = aux_functions_df.map_month(df_email['Mes'], False)

            df_email['Saldo Antes'] = df_email['Mes Nº'].apply(self.get_saldo_antes)
            df_email['Saldo Depois'] = df_email['Mes'].apply(self.get_saldo_depois)
            if "Aprovacao" in merged_df['Processo'].values and "Direto" in merged_df['Processo'].values:
                approved = self.popup_aprovar(merged_df, "aprovacao", 2)
                if approved == "yes":
                    # try: MUDAR SE VOLTAR AUTONOMIA
                    #     aux_send_email.send_outlook_email(
                    #         "williamyamashita.gff@suzano.com.br", "aprovar", df_email)  # MUDAR
                    # except:
                    #     pass
                    self.popup_aprovar(merged_df, "direto", 2, "yes")

                else:
                    self.popup_aprovar(merged_df, "direto", 2)
            else:
                if "Direto" in merged_df['Processo'].values:
                    self.popup_aprovar(merged_df, "direto", 1)
                else:
                    approved = self.popup_aprovar(merged_df, "aprovacao", 1)
                    # if approved == "yes": MUDAR SE VOLTAR AUTONOMIA
                    #     try:
                    #         aux_send_email.send_outlook_email(
                    #             "williamyamashita.gff@suzano.com.br", "aprovar", df_email)
                    #     except:
                    #         pass

    def button_reprov_click(self):
        text2 = self.approval_entry.get("1.0", "end-1c")
        # Process text from toapprov_entry
        if text2 != "":
            lines = text2.strip().split('\n')
            ordem = [line.split(') ')[1].strip().split('-')[0] for line in lines]
            mes = [line.split('-')[1].strip()[:-1] if line.strip().endswith("*") else line.split('-')[1].strip() for
                   line in
                   lines]
            processo = 'Reprovacao'
            df_to_reprov = pd.DataFrame({'Nº Ordem': ordem, 'Mes': mes, 'Processo': processo})

        # Concatenate both DataFrames
        if text2 != "":
            df = df_to_reprov
        else:
            df = pd.DataFrame()  # Empty DataFrame if both entry widgets are empty

        if not df.empty:
            df["Nº Ordem"] = df["Nº Ordem"].astype(int)
            merged_df = pd.merge(df, self.df_all_info, on="Nº Ordem", how="inner")
            merged_df = pd.merge(merged_df, self.df_email, on="Responsável", how="inner")
            merged_df = merged_df.drop(columns=['Mês Atual'], inplace=False)
            self.df_reprov = merged_df
            self.popup_aprovar(merged_df, "reprovacao", 1)

    def popup_aprovar(self, df, processo, qtd_poup, popup1_approve='no'):
        top = tk.Toplevel()
        top.configure(bg="#E2E1DD")  # Set background color of the popup window
        top.grab_set()
        # Change the font size and style
        font_family_column = "Suzano Unicase XBold"
        font_family = "Suzano Text"
        font_size = 8
        global popup_approve
        popup_approve = None
        if processo == "aprovacao":
            df_table = df[df['Processo'] == 'Aprovacao'][['Nº Ordem', "Descr. Ordem", "Custo", 'Mes']]
            top.title(" FLUXO DE APROVAÇÃO ")
            text_intro = ("Caso todos os Supervisores envolvidos no custo realizarem a aprovação"
                         "\n a Ordem seguirá para aprovação do GF.")
            text_end = "Confirme abaixo a aprovação da/s ordem/ns."
            # text_end = ("Para realizar a aprovação dessas ordens será necessário passar pelo Fluxo de Aprovação."
            #             "\n Escolha abaixo se deseja iniciar o fluxo ou cancelar")
            text_button = "Aprovar"
            df_insert = df.loc[df['Processo'] == 'Aprovacao']
            df_insert["STATUS"] = "APROVADO SUPERVISOR"  # MUDAR SE VOLTAR AUTONOMIA

            if qtd_poup == 2:
                def on_click_aproval_flow():
                    global popup_approve
                    popup_approve = "yes"
                    insert_info(df_insert, "tbl_aprovacao_rateado", top)
                    for ordem in self.df_concluido["Nº Ordem"]:
                        update_status("tbl_aprovacao_rateado", ordem, "STATUS", "EM APROVACAO GF")
                        update_status("tbl_aprovacao_rateado", ordem, "TODOS_SUPERV", "SIM")
            else:
                def on_click_aproval_flow():
                    global popup_approve
                    popup_approve = "yes"
                    insert_info(df_insert, "tbl_aprovacao_rateado", top)
                    for ordem in self.df_concluido["Nº Ordem"]:
                        update_status("tbl_aprovacao_rateado", ordem, "STATUS", "EM APROVACAO GF")
                        update_status("tbl_aprovacao_rateado", ordem, "TODOS_SUPERV", "SIM")
                    self.reset_and_go_to_current()

            def on_click_cancel():
                global popup_approve
                popup_approve = "no"
                top.destroy()

            command_approve = on_click_aproval_flow
            command_cancel = on_click_cancel

        elif processo == "reprovacao":
            df_table = df[df['Processo'] == 'Reprovacao'][['Nº Ordem', "Descr. Ordem", "Custo", 'Mes']]
            top.title(" FLUXO DE APROVAÇÃO ")
            text_intro = "Deseja reprovar a/s Ordem/ns abaixo:"
            text_end = "Ao reprovar o processo de aprovação atual será finalizado."
            # text_end = ("Para realizar a aprovação dessas ordens será necessário passar pelo Fluxo de Aprovação."
            #             "\n Escolha abaixo se deseja iniciar o fluxo ou cancelar")
            text_button = "Reprovar"
            df_insert = df.loc[df['Processo'] == 'Reprovacao']
            df_insert["STATUS"] = "REPROVADO"

            def on_click_reproval_flow():
                global popup_approve
                print(df_insert)
                insert_info(df_insert, "tbl_aprovacao_rateado", top)
                for ordem in self.df_reprov["Nº Ordem"]:
                    update_status("tbl_aprovacao_rateado", ordem, "STATUS", "REPROVADO")
                self.reset_and_go_to_current()
            def on_click_cancel():
                global popup_approve
                top.destroy()

            command_approve = on_click_reproval_flow
            command_cancel = on_click_cancel

        elif processo == "direto":
            df_table = df[df['Processo'] != 'Aprovacao'][['Nº Ordem', "Descr. Ordem", "Custo", 'Mes']]
            top.title(" APROVAÇÃO DIRETA ")
            text_intro = "As seguintes ordens serão aprovadas:"
            text_end = "Ao confirmar a aprovação o SAP será aberto para realizar as modificações."
            text_button = "Confirmar Aprovação"
            df_insert = df.loc[df['Processo'] != 'Aprovacao']
            df_insert = df_insert.drop(columns=['EMAIL_GF', 'EMAIL_GE'])
            df_insert["STATUS"] = "APROVADO"

            def on_click_aprove():
                global popup_approve
                popup_approve = "no"
                insert_info(df_insert, "tbl_aprovacao_rateado", top)
                for ordem in self.df_concluido["Nº Ordem"]:
                    update_status("tbl_aprovacao_rateado", ordem, "STATUS", "EM APROVACAO GF")
                    update_status("tbl_aprovacao_rateado", ordem, "TODOS_SUPERV", "SIM")
                    # MUDAR - SAP AQUI, SÓ OCORRE QUANDO É DIRETO
                self.reset_and_go_to_current()

            command_approve = on_click_aprove
            if popup1_approve == "yes":
                def on_click_cancel():
                    self.reset_and_go_to_current()
            else:
                def on_click_cancel():
                    global popup_approve
                    popup_approve = "no"
                    top.destroy()

            command_cancel = on_click_cancel

        intro_label = tk.Label(top, text=text_intro,
                               font=(font_family_column, font_size), bg="#E2E1DD")
        intro_label.grid(row=0, column=0, columnspan=4, padx=10, pady=5)

        # Convert the DataFrame to a dictionary
        df_dict = df_table[['Nº Ordem', 'Descr. Ordem', 'Custo', 'Mes']].to_dict('records')

        df_insert = df_insert.drop(columns=['Processo'], inplace=False)  # MUDAR SE VOLTAR AUTONOMIA
        df_insert['DT_ATUALIZACAO'] = datetime.today().date()
        df_insert['CRIADOR'] = self.user
        df_insert['Mes'] = aux_functions_df.map_month(df_insert['Mes'], False)
        df_insert['Custo'] = df_insert['Custo'].str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.')
        df_insert = df_insert.where(pd.notnull(df_insert), None)
        pd.set_option('display.max_columns', None)
        df_insert.rename(columns={
            "Nº Ordem": "ORDEM",
            "Mes": "MES_PLAN",
            "Tp. Ordem": "TIPO_ORDEM",
            "Descr. Ordem": "DESCR_ORDEM",
            "Centrab": "CENTRAB",
            "Risco": "RISCO",
            "Oport.": "OPORTUNIDADE",
            "Custo": "CUSTO",
            "Stat. Usr.": "STATUS_USUARIO",
            "Stat. Sist.": "STATUS_SISTEMA",
            "Centro de Custo": "CENTRO_CUSTO",
            "Responsável": "RESPONSAVEL",
            "SAP": "TODOS_SUPERV",
            "Revisão": "REVISAO"
        }, inplace=True)
        try:
            df_insert['ANO'] = int(self.combobox_ano.get())
        except:
            df_insert['ANO'] = aux_functions_df.current_year
        # Create labels and entry widgets for each row in the DataFrame
        for i, data in enumerate(df_dict):
            # Font for the column name
            label_font = font.Font(family=font_family_column, size=font_size, weight="bold")
            # Labels for 'Ordem', 'Descr', 'Custo', and 'Mês'
            ordem_label = tk.Label(top, text=f'Ordem:', font=label_font, anchor="w", justify="left", bg="#E2E1DD")
            ordem_label.grid(row=i + 1, column=0, sticky="ew", padx=5, pady=1)
            descr_label = tk.Label(top, text=f'Descr:', font=label_font, anchor="w", justify="left", bg="#E2E1DD")
            descr_label.grid(row=i + 1, column=1, sticky="ew", padx=5, pady=1)
            custo_label = tk.Label(top, text=f'Custo:', font=label_font, anchor="w", justify="left", bg="#E2E1DD")
            custo_label.grid(row=i + 1, column=2, sticky="ew", padx=5, pady=1)
            mes_label = tk.Label(top, text=f'Mês:', font=label_font, anchor="w", justify="left", bg="#E2E1DD")
            mes_label.grid(row=i + 1, column=3, sticky="ew", padx=5, pady=1)
            # Entry widgets for 'Ordem', 'Descr', 'Custo', and 'Mês'
            ordem_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=10)
            ordem_entry.insert(0, data['Nº Ordem'])
            ordem_entry.grid(row=i + 1, column=0, sticky="ew", padx=5, pady=1)
            descr_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=40)
            descr_entry.insert(0, data['Descr. Ordem'])
            descr_entry.grid(row=i + 1, column=1, sticky="ew", padx=5, pady=1)
            custo_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=10)
            custo_entry.insert(0, data['Custo'])
            custo_entry.grid(row=i + 1, column=2, sticky="ew", padx=5, pady=1)
            mes_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=10)
            mes_entry.insert(0, data['Mes'])
            mes_entry.grid(row=i + 1, column=3, sticky="ew", padx=5, pady=1)

        outro_label = tk.Label(top, text=text_end, font=(font_family_column, font_size), bg="#E2E1DD")
        outro_label.grid(row=len(df_dict) + 1, column=0, columnspan=4, padx=10, pady=5)

        # Add buttons
        start_button = tk.Button(top, text=text_button, command=command_approve)
        start_button.grid(row=len(df_dict) + 2, column=1, padx=10, pady=5, sticky="ew")

        cancel_button = tk.Button(top, text="Cancelar", command=command_cancel)
        cancel_button.grid(row=len(df_dict) + 2, column=2, padx=10, pady=5, sticky="ew")

        # Centralize columns
        for i in range(4):
            top.grid_columnconfigure(i, weight=1)

        # Calculate the height of the window based on the number of rows
        total_rows = len(df_dict) + 4  # Number of rows in the DataFrame plus 4 (intro text, outro text, buttons)
        height = 50 + 20 * total_rows  # Initial height plus height per row
        top.geometry(f"700x{height}")  # Adjust the size as needed
        top.wait_window()

        if popup_approve is not None:
            return popup_approve

    def get_saldo_antes(self, mes):
        saldo_value = getattr(self, f'saldo_mes_{mes}', 0)
        return saldo_value

    def get_saldo_depois(self, mes):

        saldo_value = getattr(self, f'{mes.lower()}_entry', 0).get()
        return saldo_value
