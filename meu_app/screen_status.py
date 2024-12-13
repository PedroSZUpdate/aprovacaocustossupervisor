import tkinter as tk
import pandas as pd
import numpy as np
import aux_functions_df
import aux_send_email
import aux_custom_classes
from tkinter import ttk
from datetime import datetime
from tkinter import Canvas, Entry, font, Button, PhotoImage, ttk

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


class ScreenStatus(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.user = aux_functions_df.user
        self.is_expanded = tk.BooleanVar(value=False)

        '''
        Pegar dados ordens
        '''
        # Pegar os dados para a tabela de ordens a aprovar
        self.df_status_ordens = aux_functions_df.get_status_ordens()

        self.num_rows = len(self.df_status_ordens)
        
        self.df_centrab = np.sort(self.df_status_ordens['Centrab'].unique())
        self.df_revisao = np.sort(self.df_status_ordens['Revisão'].unique())
        self.df_supervisor = np.sort(self.df_status_ordens['Supervisor'].unique())
        self.df_tp_ordem = np.sort(self.df_status_ordens['Tp.'].unique())
        
        # Store image references
        self.images = {}
        self.create_widgets()

    def filter_all(self, event=None):

        # Obtém o texto digitado nos filtros
        filter_order_text = self.filter_order.get()
        filter_supervisor_text = self.combobox_superv.get()
        filter_centrab_text = self.combobox_centrab.get()
        filter_tp_ordem_text = self.combobox_tp_ordem.get()
        filter_revisao_text = self.combobox_revisao.get()


        # Remove quaisquer filtros anteriores
        self.tree_status.delete(*self.tree_status.get_children())

        # Filtra as ordens com base nos filtros selecionados
        filtered_orders = self.df_status_ordens[
            self.df_status_ordens['Ordem'].astype(str).str.contains(filter_order_text, case=False) &
            self.df_status_ordens['Centrab'].astype(str).str.contains(filter_centrab_text, case=False) &
            self.df_status_ordens['Supervisor'].astype(str).str.contains(filter_supervisor_text, case=False) &
            self.df_status_ordens['Revisão'].astype(str).str.contains(filter_revisao_text, case=False) &
            self.df_status_ordens['Tp.'].astype(str).str.contains(filter_tp_ordem_text, case=False)
            ]

        self.num.config(text=str(len(filtered_orders)))

        self.df_centrab = np.insert(np.sort(filtered_orders['Centrab'].unique()), 0, "") \
            if "" not in filtered_orders['Centrab'].unique() else np.sort(filtered_orders['Centrab'].unique())
        # For 'Revisão' column
        self.df_revisao = np.insert(np.sort(filtered_orders['Revisão'].unique()), 0, "") if "" not in filtered_orders[
            'Revisão'].unique() else np.sort(filtered_orders['Revisão'].unique())

        # For 'Supervisor' column
        self.df_supervisor = np.insert(np.sort(filtered_orders['Supervisor'].unique()), 0, "") if "" not in \
                            filtered_orders['Supervisor'].unique() else np.sort(filtered_orders['Supervisor'].unique())
        # For 'Tp.' column
        self.df_tp_ordem = np.insert(np.sort(filtered_orders['Tp.'].unique()), 0, "") if "" not in filtered_orders[
            'Tp.'].unique() else np.sort(filtered_orders['Tp.'].unique())

        self.combobox_superv.config(values=list(self.df_supervisor))
        self.combobox_tp_ordem.config(values=list(self.df_tp_ordem))
        self.combobox_revisao.config(values=list(self.df_revisao))
        self.combobox_centrab.config(values=list(self.df_centrab))

        # Preenche a treeview com as ordens filtradas
        inserted_items = []

        for index, row in filtered_orders.iterrows():
            values = [row[col] for col in filtered_orders.columns]
            status = str(row["Condição"])
            # Check if status is not "OK" and change background color accordingly
            if status != "OK":
                item = self.tree_status.insert("", tk.END, values=values, tags=("gray_background",))
                inserted_items.append(item)
            else:
                item = self.tree_status.insert("", tk.END, values=values)
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
            85.0,
            8.0,
            anchor="nw",
            text="STATUS DAS ORDENS",
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

        # Banner Ordens A Aprovar
        self.images['image_7'] = PhotoImage(file=aux_custom_classes.relative_to_assets("image_7.png"))
        canvas.create_image(
            450.0 + navigate_area_width,
            124.0,
            image=self.images['image_7']
        )

        canvas.create_text(
            370.0 + navigate_area_width,
            112.0,
            anchor="nw",
            text="STATUS DAS ORDENS",
            fill="#FFFFFF",
            font=font.Font(family="Suzano Unicase XBold", size=13)
        )

        # Create a label to display the number
        self.num = tk.Label(self, text=self.num_rows,
                                  font=font.Font(family="Suzano Unicase XBold", size=11),
                                  fg="white", bg='#0046AD')
        self.num.place(x=320, y=110)

        '''
        Tabela Ordens 
        '''

        # Define as dimensões da tabela
        table_saldo_width = 880
        table_saldo_height = 380

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
        # custom_font_entry_header = font.Font(family="Suzano Unicase XBold", size=8)

        # Adicionas as columns do df, excluindo a coluna "Status"
        columns = self.df_status_ordens.columns.tolist()

        # Cria tabela com checkbox
        self.tree_status = ttk.Treeview(self, columns=columns, show='headings')

        # Define os headers das colunas
        for col in columns:
            self.tree_status.heading(col, text=col)


        # Insere as informações
        for index, row in self.df_status_ordens.iterrows():
            values = [row[col] for col in columns]
            status = row["Condição"]
            # Check if status is not "OK" and change background color accordingly
            if status != "OK":
                self.tree_status.insert("", tk.END, values=values, tags=("gray_background",))
            else:
                self.tree_status.insert("", tk.END, values=values)

        # Define a cor de fundo cinza para as linhas com status diferente de "OK"
        style.configure("gray_background.Treeview", background="gray")

        # Aplica as tags para as linhas com status diferente de "OK"
        self.tree_status.tag_configure("gray_background", background="gray")
        self.tree_status.tag_configure("red_background", background="red")

        # Ajusta a largura das colunas
        # self.tree_status.column("#0", width=1)
        self.tree_status.column("#1", width=48)   # Ordem
        self.tree_status.column("#2", width=114)  # Descrição
        self.tree_status.column("#3", width=45)   # Centrab
        self.tree_status.column("#4", width=52)   # Revisão
        self.tree_status.column("#5", width=26)   # TP.Ordem
        self.tree_status.column("#6", width=28)   # Risco
        self.tree_status.column("#7", width=15)   # OP.
        self.tree_status.column("#8", width=35)   # CC
        self.tree_status.column("#9", width=60)   # Custo
        self.tree_status.column("#10", width=85)  # Responsável
        self.tree_status.column("#11", width=85)  # Supervisor
        self.tree_status.column("#12", width=88)  # Status
        self.tree_status.column("#13", width=70)  # Condição


        # Posiciona a tabela
        self.tree_status.place(x=3 + navigate_area_width, y=143, width=table_saldo_width,
                              height=table_saldo_height)

        # Adiciona um srollbar a tabela
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree_status.yview)
        scrollbar.place(x=2 + table_saldo_width + navigate_area_width, y=143, height=table_saldo_height,
                        anchor="nw")

        self.tree_status.config(yscrollcommand=scrollbar.set)

        for col in columns:
            self.tree_status.column(col, anchor="center")

        def copy_to_clipboard(event):
            selected_items = self.tree_status.selection()
            selected_values = []
            for item in selected_items:
                item_values = self.tree_status.item(item, 'values')
                if item_values:
                    # Copy only the value from the "Name" column (index 0)
                    selected_values.append(item_values[0])

            if selected_values:
                self.clipboard_clear()
                self.clipboard_append('\n'.join(selected_values))

        self.tree_status.bind('<Control-c>', copy_to_clipboard)

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
            y=82.0,
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

        # Combobox 1 - Supervisor

        if "" not in list(self.df_supervisor):
            result = [""] + list(self.df_supervisor)
        else:
            result = list(self.df_supervisor)

        self.combobox_superv = ttk.Combobox(
            self,
            values=result,
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_superv['state'] = 'readonly'

        self.combobox_superv.current(0)  # Set default selection
        self.combobox_superv.place(x=185.0 + navigate_area_width, y=81.0, width=149.0, height=20.0)

        canvas.create_text(
            188.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Supervisor Centrab",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de pressionar Enter no campo de filtro
        self.combobox_superv.bind("<<ComboboxSelected>>", self.filter_all)

        # Combobox 2 - Centrab
        self.combobox_centrab = ttk.Combobox(
            self,
            values=[""] + list(self.df_centrab),
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_centrab['state'] = 'readonly'

        self.combobox_centrab.current(0)  # Set default selection
        self.combobox_centrab.place(x=355.0 + navigate_area_width, y=81.0, width=149.0, height=20.0)

        canvas.create_text(
            358.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Centrab",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        self.combobox_centrab.bind("<<ComboboxSelected>>", self.filter_all)

        # Combobox 3 - Tp Ordem

        self.combobox_tp_ordem = ttk.Combobox(
            self,
            values=[""] + list(self.df_tp_ordem),
            background="#B7B1A9",
            foreground="#000716"
        )

        self.combobox_tp_ordem['state'] = 'readonly'

        self.combobox_tp_ordem.current(0)  # Set default selection
        self.combobox_tp_ordem.place(x=530.0 + navigate_area_width, y=81.0, width=149.0, height=20.0)

        canvas.create_text(
            533.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Tp. Ordem",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        self.combobox_tp_ordem.bind("<<ComboboxSelected>>", self.filter_all)

        # Combobox 4 - Revisão

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
        self.combobox_revisao.place(x=700.0 + navigate_area_width, y=81.0, width=149.0, height=20.0)

        canvas.create_text(
            703.0 + navigate_area_width,
            69.0,
            anchor="nw",
            text="Revisão",
            fill="#000000",
            font=font.Font(family="Suzano Unicase XBold", size=8)
        )

        # Associa a função de filtragem ao evento de pressionar Enter no campo de filtro
        self.combobox_revisao.bind("<<ComboboxSelected>>", self.filter_all)

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

        button_go_approv.pack(pady=5)
        button_go_mov_saldo.pack(pady=5)
        button_go_rat.pack(pady=5)

    def go_to_screen_aprovar(self):
        self.master.show_screen("Aprovação de Custos")

    def go_to_screen_mov_saldo(self):
        self.master.show_screen("Movimentações de Saldo")

    def go_to_screen_rat(self):
        self.master.show_screen("Aprovação Custos Rateados")

    def reset_and_go_to_current(self):
        self.master.reset_and_show_current_screen()

