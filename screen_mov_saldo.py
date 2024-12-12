import tkinter as tk
import pandas as pd
import aux_functions_df
import aux_send_email
import aux_custom_classes
from aux_custom_classes import CustomSaldoCheckboxTreeview
from tkinter import ttk
from datetime import datetime
from tkinter import Canvas, Entry, font, Button, PhotoImage

# Set display options for pandas
pd.set_option('display.max_columns', None)


def update_status(table, df, email_responsavel, top, status):
    try:
        conn = aux_functions_df.connect_db()
        if conn.is_connected():
            cursor = conn.cursor()
            # Prepare the update query with placeholders %s
            update_query = f"""UPDATE {table}
                               SET STATUS = %s, DT_DECISAO = %s
                               WHERE REQUISITANTE = %s AND EMAIL_RESPONSAVEL = %s AND MES = %s 
                               AND ABS(VALOR - %s) < 3"""

            # Loop through the DataFrame and update each row
            for index, row in df.iterrows():
                # Apply transformation to the VALOR column
                transformed_valor = aux_functions_df.to_number(row["Valor Solic."])
                # Get the current datetime
                current_datetime = datetime.now()
                data = (
                    status, current_datetime, row['Responsável'], email_responsavel, row["Mês"], transformed_valor)
                #  row['Responsável'] é o requisitante
                print(data)
                cursor.execute(update_query, data)

            # Commit the transaction
            conn.commit()

    except:
        pass

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
        top.destroy()


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


class ScreenSaldo(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.user = aux_functions_df.user
        self.is_expanded = tk.BooleanVar(value=False)

        '''
        Pegar dados ordens
        '''
        # Pegar os dados para a tabela de ordens a aprovar
        self.df_saldo_table = aux_functions_df.get_saldo_table()
        self.df_saldo_table = self.df_saldo_table.drop(columns=['Recebedor'])

        """
        Pegar dados de saldo
        """
        self.df_saldo = aux_functions_df.get_saldo("", aux_functions_df.current_year)

        def get_saldo(df, mes):
            result = df.loc[df['MES'] == mes, 'SALDO_COLEGIADO']
            return result.values[0] if not result.empty else "R$ 0,00"

        self.saldo_mes_1 = get_saldo(self.df_saldo, 1)
        self.saldo_mes_2 = get_saldo(self.df_saldo, 2)
        self.saldo_mes_3 = get_saldo(self.df_saldo, 3)
        self.saldo_mes_4 = get_saldo(self.df_saldo, 4)
        self.saldo_mes_5 = get_saldo(self.df_saldo, 5)
        self.saldo_mes_6 = get_saldo(self.df_saldo, 6)
        self.saldo_mes_7 = get_saldo(self.df_saldo, 7)
        self.saldo_mes_8 = get_saldo(self.df_saldo, 8)
        self.saldo_mes_9 = get_saldo(self.df_saldo, 9)
        self.saldo_mes_10 = get_saldo(self.df_saldo, 10)
        self.saldo_mes_11 = get_saldo(self.df_saldo, 11)
        self.saldo_mes_12 = get_saldo(self.df_saldo, 12)
        self.saldo_acum_atual = get_saldo(self.df_saldo, 13)
        self.saldo_acum_total = get_saldo(self.df_saldo, 14)


        """
        Pegar dados compromissado
        """
        self.df_approv_table = aux_functions_df.get_approv_mov_saldo()
        self.df_email = aux_functions_df.df_email.copy()
        self.df_email.drop(columns=['USUARIO', 'EMAIL_GF', 'EMAIL_GE'], inplace=True)

        # Store image references
        self.images = {}
        self.create_widgets()

    def filter_data(self, event=None):
        # Get the text typed in the filters
        filter_resp_text = self.entry_filter_resp.get()
        filter_mes_text = self.combobox_mes.get()

        # Remove previous filters
        self.tree_saldo.delete(*self.tree_saldo.get_children())
        checked_values_ordem = self.tree_saldo.get_checked_values("Ordem")
        checked_values_solic = self.tree_saldo.get_checked_values("Custo")

        # Filter orders based on selected filters
        filtered_orders = self.df_saldo_table[
            self.df_saldo_table['Responsável'].astype(str).str.contains(filter_resp_text, case=False) &
            self.df_saldo_table['Mês'].astype(str).str.contains(filter_mes_text, case=False)
            ]

        # Populate the treeview with filtered orders
        inserted_items = []

        for index, row in filtered_orders.iterrows():
            values = [row[col] for col in filtered_orders.columns]
            ordem = str(row['Responsável']) + str(row['Mês'])
            # Check if status is not "OK" and change background color accordingly
            if ordem in checked_values_ordem:
                ordem_index = checked_values_ordem.index(ordem)
                val_solic = checked_values_solic[ordem_index]
                values[filtered_orders.columns.get_loc('Valor Solic.')] = val_solic
                item = self.tree_saldo.insert("", tk.END, values=values)
                inserted_items.append(item)
                self.tree_saldo._check_ancestor(item)
                self.tree_saldo._check_descendant(item)

        for index, row in filtered_orders.iterrows():
            values = [row[col] for col in filtered_orders.columns]
            ordem = str(row['Responsável']) + str(row['Mês'])
            if ordem not in checked_values_ordem:
                item = self.tree_saldo.insert("", tk.END, values=values)
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
            text="MOVIMENTAÇÃO DE SALDO",
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
            text="REQUISITAR MOVIMENTAÇÕES",
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
            100.0 + navigate_area_width,
            368.0,
            anchor="nw",
            text="MOVIMENTAÇÕES PARA SUA APROVAÇÃO",
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
            jan_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            jan_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575.0 + navigate_area_width, 162.0, anchor="nw", window=jan_entry)
        jan_entry.insert(0, self.saldo_mes_1)
        jan_entry.config(state="disabled")

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
            fev_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            fev_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742.0 + navigate_area_width, 162.0, anchor="nw", window=fev_entry)
        fev_entry.insert(0, self.saldo_mes_2)
        fev_entry.config(state="disabled")

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
            mar_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            mar_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575.0 + navigate_area_width, 206.0, anchor="nw", window=mar_entry)
        mar_entry.insert(0, self.saldo_mes_3)
        mar_entry.config(state="disabled")

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
            abr_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            abr_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742.0 + navigate_area_width, 206.0, anchor="nw", window=abr_entry)
        abr_entry.insert(0, self.saldo_mes_4)  # saldo_mes_4
        abr_entry.config(state="disabled")

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
            mai_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            mai_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 251.0, anchor="nw", window=mai_entry)
        mai_entry.insert(0, self.saldo_mes_5)  # saldo_mes_5
        mai_entry.config(state="disabled")

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
            jun_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            jun_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 251.0, anchor="nw", window=jun_entry)
        jun_entry.insert(0, self.saldo_mes_6)  # saldo_mes_6
        jun_entry.config(state="disabled")

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
            jul_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            jul_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 296.0, anchor="nw", window=jul_entry)
        jul_entry.insert(0, self.saldo_mes_7)
        jul_entry.config(state="disabled")

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
            ago_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            ago_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 296.0, anchor="nw", window=ago_entry)
        ago_entry.insert(0, self.saldo_mes_8)
        ago_entry.config(state="disabled")

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
            set_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            set_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 341.0, anchor="nw", window=set_entry)
        set_entry.insert(0, self.saldo_mes_9)
        set_entry.config(state="disabled")

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
            out_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            out_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 341.0, anchor="nw", window=out_entry)
        out_entry.insert(0, self.saldo_mes_10)
        out_entry.config(state="disabled")

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
            nov_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            nov_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 386.0, anchor="nw", window=nov_entry)
        nov_entry.insert(0, self.saldo_mes_11)
        nov_entry.config(state="disabled")

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
            dez_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            dez_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                              width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 386.0, anchor="nw", window=dez_entry)
        dez_entry.insert(0, self.saldo_mes_12)
        dez_entry.config(state="disabled")

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
            acum_mes_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            acum_mes_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(575 + navigate_area_width, 441.0, anchor="nw", window=acum_mes_entry)
        acum_mes_entry.insert(0, self.saldo_acum_atual)
        acum_mes_entry.config(state="disabled")

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
            acum_ano_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="black")
        else:
            acum_ano_entry = Entry(canvas, bd=0, highlightthickness=0, font=font.Font(family="Suzano Text", size=10),
                                   width=17, disabledbackground="#b7b1a9", disabledforeground="red")
        canvas.create_window(742 + navigate_area_width, 441.0, anchor="nw", window=acum_ano_entry)
        acum_ano_entry.insert(0, self.saldo_acum_total)
        acum_ano_entry.config(state="disabled")

        '''
        Tabela Colegiado
        '''

        # Define as dimensões da tabela
        table_saldo_width = 400
        table_saldo_height = 220

        # Define as fontes
        # custom_font_tree = font.Font(family="Suzano Unicase Regular", size=7)
        custom_font_tree_header = font.Font(family="Suzano Unicase Medium", size=8)

        # Define as cores
        style = ttk.Style()
        style.theme_use("alt")  # Use the "clam" theme as a base
        style.configure("Treeview", font=custom_font_tree_header, background="#E6E6E6", foreground="black")
        style.configure("Treeview.Heading", font=custom_font_tree_header,
                        background="black", foreground="white", hovercolor="black", justify="center")

        # Define as fontes
        custom_font_entry = font.Font(family="Suzano Unicase", size=7)
        custom_font_entry_header = font.Font(family="Suzano Unicase XBold", size=8)

        # Create a label for the checked values
        label_checked_values = tk.Label(self, text="À requisitar", font=custom_font_entry_header,
                                        background="#E2E1DD")
        label_checked_values.place(x=table_saldo_width + 38 + navigate_area_width, y=143)

        # Create a Text widget to display checked values of orders to approve
        self.torequest_entry = tk.Text(self, width=21, height=18, font=custom_font_entry, background="#E6E6E6",
                                       state=tk.DISABLED)
        self.torequest_entry.place(x=table_saldo_width + 25 + navigate_area_width, y=163)

        # Define as dimensões da tabela
        table_approv_width = 400
        table_approv_height = 140

        # Create a Text widget to display checked values of orders to approve
        self.toapprov_entry = tk.Text(self, width=21, height=11, font=custom_font_entry, background="#E6E6E6",
                                      state=tk.DISABLED)
        self.toapprov_entry.place(x=table_approv_width + 25 + navigate_area_width, y=420)

        # Cria tabela com checkbox
        self.tree_saldo = CustomSaldoCheckboxTreeview(self, self.torequest_entry, self.toapprov_entry, jan_entry,
                                                      fev_entry,
                                                      mar_entry,
                                                      abr_entry,
                                                      mai_entry, jun_entry,
                                                      jul_entry, ago_entry, set_entry, out_entry, nov_entry, dez_entry,
                                                      acum_mes_entry, acum_ano_entry, "tbl_saldo")

        # Adicionas as columns do df, excluindo a coluna "Status"
        columns = self.df_saldo_table.columns.tolist()

        self.tree_saldo["columns"] = columns

        # Define os headers das colunas
        for col in columns:
            self.tree_saldo.heading(col, text=col)

        # Insere as informações
        for index, row in self.df_saldo_table.iterrows():
            values = [row[col] for col in columns]
            self.tree_saldo.insert("", tk.END, values=values)

        # Define a cor de fundo cinza para as linhas com status diferente de "OK"
        style.configure("gray_background.Treeview", background="gray")

        # Aplica as tags para as linhas com status diferente de "OK"
        self.tree_saldo.tag_configure("gray_background", background="gray")
        self.tree_saldo.tag_configure("red_background", background="red")

        # Ajusta a largura das colunas
        self.tree_saldo.column("#0", width=5)
        self.tree_saldo.column("#1", width=150)
        self.tree_saldo.column("#2", width=10)
        self.tree_saldo.column("#3", width=60)
        self.tree_saldo.column("#4", width=60)
        # tree_orders_to_approve.column("#5", width=80)
        # tree_orders_to_approve.column("#6", width=45)

        # Posiciona a tabela
        self.tree_saldo.place(x=5 + navigate_area_width, y=143, width=table_saldo_width,
                              height=table_saldo_height)

        # Adiciona um srollbar a tabela
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree_saldo.yview)
        scrollbar.place(x=2 + table_saldo_width + navigate_area_width, y=143, height=table_saldo_height,
                        anchor="nw")

        self.tree_saldo.config(yscrollcommand=scrollbar.set)

        for col in columns:
            self.tree_saldo.column(col, anchor="center")

        '''
        A Aprovar
        '''

        # Create a label for the checked values
        label_checked_values = tk.Label(self, text="À alterar", font=custom_font_entry_header, background="#E2E1DD")
        label_checked_values.place(x=table_approv_width + 46 + navigate_area_width, y=399)

        # Cria tabela com checkbox
        self.tree_approv = CustomSaldoCheckboxTreeview(self, self.toapprov_entry, self.torequest_entry, jan_entry,
                                                       fev_entry, mar_entry, abr_entry, mai_entry, jun_entry, jul_entry,
                                                       ago_entry, set_entry, out_entry, nov_entry, dez_entry,
                                                       acum_mes_entry, acum_ano_entry, "tbl_approv")

        # Adicionas as columns do df, excluindo a coluna "Status"
        columns = self.df_approv_table.columns.tolist()
        self.tree_approv["columns"] = columns

        # Define os headers das colunas
        for col in columns:
            self.tree_approv.heading(col, text=col)

        # Insere as informações
        for index, row in self.df_approv_table.iterrows():
            values = [row[col] for col in columns]
            self.tree_approv.insert("", tk.END, values=values)

        # Define a cor de fundo cinza para as linhas com status diferente de "OK"
        style.configure("red_background.Treeview", background="red")

        # Aplica as tags para as linhas com status diferente de "OK"
        self.tree_approv.tag_configure("red_background", background="red")

        # Ajusta a largura das colunas
        self.tree_approv.column("#0", width=5)
        self.tree_approv.column("#1", width=130)
        self.tree_approv.column("#2", width=30)
        self.tree_approv.column("#3", width=100)

        # Posiciona a tabela
        self.tree_approv.place(x=5 + navigate_area_width, y=399, width=table_approv_width,
                               height=table_approv_height)

        # Adiciona um srollbar a tabela
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree_approv.yview)
        scrollbar.place(x=2 + table_approv_width + navigate_area_width, y=399, height=table_approv_height,
                        anchor="nw")

        self.tree_approv.config(yscrollcommand=scrollbar.set)

        for col in columns:
            self.tree_approv.column(col, anchor="center")

        '''
        Filtros
        '''

        # Filtro Responsável
        # Create a container frame for other widgets

        self.images['image_filter_res'] = PhotoImage(
            file=aux_custom_classes.relative_to_assets("entry_1.png"))
        canvas.create_image(
            86.5 + navigate_area_width,
            92,
            image=self.images['image_filter_res']
        )

        self.entry_filter_resp = Entry(
            self,
            bd=0,
            bg="#B7B1A9",
            fg="#000716",
            highlightthickness=0
        )
        self.entry_filter_resp.place(
            x=11.0 + navigate_area_width,
            y=83.0,
            width=151.0,
            height=17.0
        )

        canvas.create_text(
            14.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="  Responsável",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de pressionar Enter no campo de filtro
        self.entry_filter_resp.bind("<Return>", self.filter_data)

        # Associa a função de filtragem ao evento de alteração no texto do campo de filtro
        self.entry_filter_resp.bind("<KeyRelease>", self.filter_data)

        ''' Combobox Mês'''

        self.combobox_mes = ttk.Combobox(
            self,
            values=aux_custom_classes.months_from_current,
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_mes['state'] = 'readonly'

        self.combobox_mes.current(0)  # Set default selection
        self.combobox_mes.place(x=190.0 + navigate_area_width, y=83.0, width=149.0, height=20.0)

        canvas.create_text(
            193.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="  Mês",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de seleção
        self.combobox_mes.bind("<<ComboboxSelected>>", self.filter_data)

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

        # Botão Tela Aprovar
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

        # Botão Tela Rateado
        def on_hover_go_rat(event):
            button_go_rat.config(image=button_go_rat_hover_img)

        def on_leave_go_rat(event):
            button_go_rat.config(image=button_go_rat_img)

        button_go_rat_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_go_rat.png"))

        button_go_rat_hover_img = PhotoImage(
            file=aux_custom_classes.relative_to_assets("button_go_rat_hover.png"))

        button_go_rat = tk.Button(menu_space,
                                  image=button_go_rat_img,
                                  relief="flat",
                                  borderwidth=0,
                                  highlightthickness=0,
                                  command=self.go_to_screen_rat
                                  )

        button_go_rat.bind("<Enter>", on_hover_go_rat)
        button_go_rat.bind("<Leave>", on_leave_go_rat)

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
        button_go_rat.pack(pady=5)
        button_go_status.pack(pady=5)

    def go_to_screen_aprovar(self):
        self.master.show_screen("Aprovação de Custos")

    def go_to_screen_rat(self):
        self.master.show_screen("Aprovação Custos Rateados")

    def go_to_screen_status(self):
        self.master.show_screen("Status Ordens")

    def reset_and_go_to_current(self):
        self.master.reset_and_show_current_screen()

    def button_request_click(self):
        text1 = self.torequest_entry.get("1.0", "end-1c")
        text2 = self.toapprov_entry.get("1.0", "end-1c")
        # Process text from torequest_entry
        if text1 != "":
            responsavel = self.tree_saldo.get_checked_values("Ordem")  # Ordem is actually the resp followed by month
            responsavel = [s[:-3] if len(s) > 3 else '' for s in responsavel]
            mes = self.tree_saldo.get_checked_values("Mês")
            valor = self.tree_saldo.get_checked_values("Custo")
            processo = ["Normal" for line in responsavel]
            tipo = ["Requisição" for line in responsavel]

            df_to_request = pd.DataFrame({'Responsável': responsavel, 'Mês': mes, "Valor Solic.": valor,
                                          "Tipo": tipo, "Processo": processo})

        # Process text from toapprov_entry
        if text2 != "":
            lines = text2.strip().split('\n')
            mes = [line.split(') ')[1].strip().split('-')[0] for line in lines]
            processo = ['Reprovar' if '*' in line else 'Normal' for line in lines]  # Check for asterisk
            responsavel = self.tree_approv.get_checked_values("Ordem")  # Ordem is actually the resp followed by month
            responsavel = [s[:-3] if len(s) > 3 else '' for s in responsavel]
            # mes = self.tree_approv.get_checked_values("Mês")
            valor = self.tree_approv.get_checked_values("Custo")
            tipo = ["Aprovar" for line in responsavel]

            df_to_approve = pd.DataFrame({'Responsável': responsavel, 'Mês': mes, "Valor Solic.": valor,
                                          "Tipo": tipo, "Processo": processo})

        # Concatenate both DataFrames
        if text1 != "" and text2 != "":
            df_combined = pd.concat([df_to_request, df_to_approve], ignore_index=True)
        elif text1 != "":
            df_combined = df_to_request
        elif text2 != "":
            df_combined = df_to_approve
        else:
            df_combined = pd.DataFrame()  # Empty DataFrame if both entry widgets are empty

        if not df_combined.empty:
            merged_df = pd.merge(df_combined, self.df_email, on="Responsável", how="inner")
            # Create the DataFrame with rows where 'Processo' is 'Reprovar'
            df_reprovar = merged_df[merged_df['Processo'] == 'Reprovar']
            # Create the DataFrame with the rest of the rows
            merged_df = merged_df[merged_df['Processo'] != 'Reprovar']

            if "Reprovar" in df_reprovar['Processo'].values:
                self.popup_reprovar()
                return

            if "Requisição" in merged_df['Tipo'].values and "Aprovar" in merged_df['Tipo'].values:
                self.popup_aprovar(merged_df, "requisicao", 2)
                self.popup_aprovar(merged_df, "aprovacao", 2)
            else:
                if "Requisição" in merged_df['Tipo'].values:
                    self.popup_aprovar(merged_df, "requisicao", 1)
                else:
                    self.popup_aprovar(merged_df, "aprovacao", 1)

    def button_reprov_click(self):
        text = self.toapprov_entry.get("1.0", "end-1c")
        # Process text from toapprov_entry
        if text != "":
            responsavel = self.tree_approv.get_checked_values("Ordem")  # Ordem is actually the resp followed by month
            responsavel = [s[:-3] if len(s) > 3 else '' for s in responsavel]
            mes = self.tree_approv.get_checked_values("Mês")
            valor = self.tree_approv.get_checked_values("Custo")
            tipo = ["Aprovar" for line in responsavel]

            df_to_reprov = pd.DataFrame({'Responsável': responsavel, 'Mês': mes, "Valor Solic.": valor, "Tipo": tipo})

        # Concatenate both DataFrames
        if text != "":
            df = df_to_reprov
        else:
            df = pd.DataFrame()  # Empty DataFrame if both entry widgets are empty

        if not df.empty:
            merged_df = pd.merge(df, self.df_email, on="Responsável", how="inner")

            self.popup_aprovar(merged_df, "reprovacao", 1)

    def popup_aprovar(self, df, tipo, qtd_poup):
        top = tk.Toplevel()
        top.configure(bg="#E2E1DD")  # Set background color of the popup window
        top.grab_set()

        # Change the font size and style
        font_family_column = "Suzano Unicase XBold"
        font_family = "Suzano Text"
        font_size = 8

        if tipo == "requisicao":
            df_table = df[df['Tipo'] != 'Aprovar'][['Responsável', "Mês", "Valor Solic."]]
            top.title(" REQUISIÇÕES ")
            text_intro = "Fazer a requisição das movimentações de saldo abaixo?"
            text_button = "Requisitar"
            df_insert = df[df['Tipo'] != 'Aprovar'].copy()
            df_insert.rename(columns={
                "Responsável": "RESPONSAVEL",
                "Mês": "MES",
                "Valor Solic.": "VALOR",
                "EMAIL_USUARIO": "EMAIL_RESPONSAVEL"
            }, inplace=True)
            df_insert['DT_ATUALIZACAO'] = datetime.today().date()
            df_insert['USUARIO'] = aux_functions_df.user  ################## MUDAR DEPOIS para user #####################
            df_user = aux_functions_df.df_user.copy()
            df_user.rename(columns={
                "Responsável": "REQUISITANTE"
            }, inplace=True)
            df_insert = pd.merge(df_insert, df_user, on="USUARIO", how="inner")
            df_insert['MES'] = aux_functions_df.map_month(df_insert['MES'], False)
            df_insert['VALOR'] = df_insert['VALOR'].str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.')
            df_insert['STATUS'] = "EM APROVACAO"
            df_insert['ANO'] = datetime.now().year
            df_insert = df_insert.drop(columns=['Tipo', 'USUARIO', 'Processo'], inplace=False)

            df_insert = df_insert.where(pd.notnull(df_insert), None)

            if qtd_poup == 2:  # wait for the second pop up
                def on_click_aproval_flow():
                    insert_info(df_insert, "tbl_mov_saldo", top)
                    emails = df[df['Tipo'] != 'Aprovar']['EMAIL_USUARIO'].unique()
                    try:
                        for email in emails:
                            df_email = df[(df['Tipo'] != 'Aprovar') & (df['EMAIL_USUARIO'] == email)][
                                ["Mês", "Valor Solic."]]
                            # Querying the DataFrame to get 'REQUISITANTE' where 'USUARIO' matches 'user'
                            result = aux_functions_df.df_user.loc[
                                aux_functions_df.df_user['USUARIO'] == self.user, 'Responsável']
                            # Check if the result is empty and set appropriate value
                            solicitante_value = result.values[0] if not result.empty else ''
                            # Setting the 'Solicitante' column in df_email
                            df_email['Solicitante'] = solicitante_value
                            '''MUDAR O EMAIL APÓS FAZER OS TESTES'''
                            aux_send_email.send_outlook_email(
                                email, "requisicao", df_email)
                    except:
                        pass
            else:  # also restart the program
                def on_click_aproval_flow():
                    insert_info(df_insert, "tbl_mov_saldo", top)
                    emails = df[df['Tipo'] != 'Aprovar']['EMAIL_USUARIO'].unique()
                    try:
                        for email in emails:
                            df_email = df[(df['Tipo'] != 'Aprovar') & (df['EMAIL_USUARIO'] == email)][
                                ["Mês", "Valor Solic."]]
                            # Querying the DataFrame to get 'REQUISITANTE' where 'USUARIO' matches 'user'
                            result = aux_functions_df.df_user.loc[
                                aux_functions_df.df_user['USUARIO'] == self.user, 'Responsável']
                            # Check if the result is empty and set appropriate value
                            solicitante_value = result.values[0] if not result.empty else ''
                            # Setting the 'Solicitante' column in df_email
                            df_email['Solicitante'] = solicitante_value
                            '''MUDAR O EMAIL APÓS FAZER OS TESTES'''
                            aux_send_email.send_outlook_email(
                                email, "requisicao", df_email)
                    except:
                        pass
                    self.reset_and_go_to_current()

            command = on_click_aproval_flow

        elif tipo == "aprovacao":
            df_table = df[df['Tipo'] == 'Aprovar'][['Responsável', "Mês", "Valor Solic."]]
            top.title(" APROVAR AS REQUISIÇÕES ")
            text_intro = "Realizar a aprovação das requisições de movimentação de saldo abaixo?"
            text_button = "Aprovar"
            df_approv = df.loc[df['Tipo'] == 'Aprovar'].copy()
            df_approv['Mês'] = aux_functions_df.map_month(df_approv['Mês'].str.strip(), False)
            def on_click_approve():  # MUDAR
                update_status("tbl_mov_saldo", df_approv, self.user + "@suzano.com.br", top, "APROVADO")
                emails = df[df['Tipo'] == 'Aprovar']['EMAIL_USUARIO'].unique()
                try:
                    for email in emails:
                        df_email = df[(df['Tipo'] == 'Aprovar') & (df['EMAIL_USUARIO'] == email)][
                            ["Mês", "Valor Solic."]]
                        # Querying the DataFrame to get 'REQUISITANTE' where 'USUARIO' matches 'user'
                        result = aux_functions_df.df_user.loc[aux_functions_df.df_user['USUARIO'] == self.user, 'Responsável']
                        # Check if the result is empty and set appropriate value
                        solicitante_value = result.values[0] if not result.empty else ''
                        # Setting the 'Solicitante' column in df_email
                        df_email['Aprovador'] = solicitante_value
                        '''MUDAR O EMAIL APÓS FAZER OS TESTES'''
                        aux_send_email.send_outlook_email(
                            email, "aprovacao", df_email)
                except:
                    pass
                self.reset_and_go_to_current()

            command = on_click_approve

        elif tipo == "reprovacao":
            df_table = df[df['Tipo'] == 'Aprovar'][['Responsável', "Mês", "Valor Solic."]]
            top.title(" REPROVAR AS REQUISIÇÕES ")
            text_intro = "Realizar a reprovação das requisições de movimentação de saldo abaixo?"
            text_button = "Reprovar"
            df_approv = df.loc[df['Tipo'] == 'Aprovar'].copy()
            df_approv['Mês'] = aux_functions_df.map_month(df_approv['Mês'], False)

            def on_click_reprove():
                update_status("tbl_mov_saldo", df_approv, self.user + "@suzano.com.br", top, "REPROVADO")
                emails = df[df['Tipo'] == 'Aprovar']['EMAIL_USUARIO'].unique()
                try:
                    for email in emails:
                        df_email = df[(df['Tipo'] == 'Aprovar') & (df['EMAIL_USUARIO'] == email)][
                            ["Mês", "Valor Solic."]]
                        # Querying the DataFrame to get 'REQUISITANTE' where 'USUARIO' matches 'user'
                        result = aux_functions_df.df_user.loc[aux_functions_df.df_user['USUARIO'] == self.user, 'Responsável']
                        # Check if the result is empty and set appropriate value
                        solicitante_value = result.values[0] if not result.empty else ''
                        # Setting the 'Solicitante' column in df_email
                        df_email['Aprovador'] = solicitante_value
                        '''MUDAR O EMAIL APÓS FAZER OS TESTES'''
                        aux_send_email.send_outlook_email(
                            email, "reprovacao", df_email)
                except:
                    pass
                self.reset_and_go_to_current()

            command = on_click_reprove

        intro_label = tk.Label(top, text=text_intro,
                               font=(font_family_column, font_size), bg="#E2E1DD")
        intro_label.grid(row=0, column=0, columnspan=4, padx=10, pady=5)

        # Convert the DataFrame to a dictionary
        df_dict = df_table[['Responsável', "Mês", "Valor Solic."]].to_dict('records')

        # Create labels and entry widgets for each row in the DataFrame
        for i, data in enumerate(df_dict):
            # Font for the column name
            label_font = font.Font(family=font_family_column, size=font_size, weight="bold")
            # Labels for 'Responsável', 'Mês', and 'Valor Solic.'
            responsavel_label = tk.Label(top, text=f'Responsável:', font=label_font, anchor="w", justify="left",
                                         bg="#E2E1DD")
            responsavel_label.grid(row=i + 1, column=0, sticky="ew", padx=5, pady=1)
            mes_label = tk.Label(top, text=f'Mês:', font=label_font, anchor="w", justify="left", bg="#E2E1DD")
            mes_label.grid(row=i + 1, column=1, sticky="ew", padx=5, pady=1)
            valor_solic_label = tk.Label(top, text=f'Valor Solic.:', font=label_font, anchor="w", justify="left",
                                         bg="#E2E1DD")
            valor_solic_label.grid(row=i + 1, column=2, sticky="ew", padx=5, pady=1)
            # Entry widgets for 'Responsável', 'Mês', and 'Valor Solic.'
            responsavel_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=10)
            responsavel_entry.insert(0, data['Responsável'])
            responsavel_entry.grid(row=i + 1, column=0, sticky="ew", padx=5, pady=1)
            mes_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=10)
            mes_entry.insert(0, data['Mês'])
            mes_entry.grid(row=i + 1, column=1, sticky="ew", padx=5, pady=1)
            valor_solic_entry = tk.Entry(top, font=(font_family, font_size), justify="center", bg="#E2E1DD", width=10)
            valor_solic_entry.insert(0, data['Valor Solic.'])
            valor_solic_entry.grid(row=i + 1, column=2, sticky="ew", padx=5, pady=1)

        # Add buttons
        start_button = tk.Button(top, text=text_button, command=command)
        start_button.grid(row=len(df_dict) + 2, column=1, padx=10, pady=5, sticky="ew")

        cancel_button = tk.Button(top, text="Cancelar", command=top.destroy)
        cancel_button.grid(row=len(df_dict) + 3, column=1, padx=10, pady=5, sticky="ew")

        # Centralize columns
        for i in range(3):
            top.grid_columnconfigure(i, weight=1)

        # Calculate the height of the window based on the number of rows
        total_rows = len(df_dict) + 3  # Number of rows in the DataFrame plus 4 (intro text, outro text, buttons)
        height = 50 + 20 * total_rows  # Initial height plus height per row
        top.geometry(f"700x{height}")  # Adjust the size as needed
        top.wait_window()

    def popup_reprovar(self):
        top = tk.Toplevel()
        top.title(" AVISO ")
        top.grab_set()

        # Change the icon
        icon = tk.PhotoImage(
            file=aux_custom_classes.relative_to_assets("logo.png"))  # Replace "your_icon_file.png" with the path to your icon file
        top.iconphoto(True, icon)

        # Change the font size and style
        message_text = ("Não há saldo suficiente para aprovar\n"
                        "uma da/s solicitações.\n"
                        "\n"
                        "Remova a solicitação para poder\n"
                        "poder aprovar/requisitar.")

        message_label = tk.Label(top, text=message_text, font=font.Font(family="Suzano Text", size=8), anchor="w",
                                 justify="left")
        message_label.pack(padx=5, pady=15)

        # OK button
        ok_button = tk.Button(top, text="OK", command=top.destroy, width=10, height=1)
        ok_button.pack(padx=5, pady=2)

        # Adjust the size of the window
        top.geometry("255x130")
        aux_custom_classes.center_window(top)
