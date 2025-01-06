import sys
import pyglet
import tkinter as tk
import pandas as pd
import os
import aux_functions_df
import aux_functions_df as functions_df
from tkinter import ttk
from pathlib import Path
from datetime import datetime
from tkinter import font, messagebox
from ttkwidgets import CheckboxTreeview

# Create a list of months
months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

# Get the current month
current_month_index = datetime.now().month

# Slice the months list to start from the current month onwards
months_from_current = [""] + months[current_month_index - 1:]
months_till_current = months[:current_month_index]

# Determine the base path based on whether running from a PyInstaller bundle
if hasattr(sys, '_MEIPASS'):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent

# Paths for assets and fonts
images_path = base_path / "assets" / "frame"
font_title = base_path / "font" / "SuzanoUnicase-XBold.ttf"
font_text = base_path / "font" / "SuzanoText-Regular.ttf"
font_month = base_path / "font" / "SuzanoUnicase-Bold.ttf"


def get_assets_directory():
    return os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "assets\\frame"))


IM_CHECKED = os.path.join(get_assets_directory(), "checked.png")
IM_UNCHECKED = os.path.join(get_assets_directory(), "unchecked.png")
IM_TRISTATE = os.path.join(get_assets_directory(), "tristate.png")


def add_font():
    pyglet.font.add_file(str(font_title))


# Function to resolve relative paths to assets
def relative_to_assets(path: str) -> Path:
    return images_path / Path(path)


def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry('{}x{}+{}+{}'.format(width, height, x, y))


def retrieve_widget_by_name(root, widget_name):
    for widget in root.winfo_children():
        if widget.winfo_name() == widget_name:
            return widget
    return None


class CustomCheckbox(tk.Canvas):
    def __init__(self, master, func, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.checked = False
        self.image_checked = tk.PhotoImage(file=IM_CHECKED)
        self.image_unchecked = tk.PhotoImage(file=IM_UNCHECKED)
        self.create_image(0, 0, anchor=tk.NW, image=self.image_unchecked)
        self.bind("<Button-1>", self.toggle)
        self.func = func

    def toggle(self, event):
        self.func(self.checked)
        self.checked = not self.checked
        self.update_image()

    def update_image(self):
        self.delete("all")
        if self.checked:
            self.create_image(0, 0, anchor=tk.NW, image=self.image_checked)
        else:
            self.create_image(0, 0, anchor=tk.NW, image=self.image_unchecked)

    def toggle_checkbox(self):
        self.checked = False
        self.update_image()


class CustomCombobox(ttk.Combobox):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.bind("<FocusIn>", self.on_dropdown)
        self.bind("<<ComboboxSelected>>", self.on_select)
        self.dropdown_open = False

    def on_dropdown(self, event):
        self.dropdown_open = True
        self.grab_set()  # Grab the focus
        self.focus_set()  # Set focus on combobox

    def on_select(self, event):
        self.dropdown_open = False
        self.grab_release()  # Release the focus
        self.destroy()

    def intercept_interaction(self, event):
        if self.dropdown_open:
            return "break"


class CustomGerenteMovCheckboxTreeview(CheckboxTreeview):
    def __init__(self, master, list_resp, **kw):
        super().__init__(master, **kw)

        self.bind("<Double-1>", self.on_double_click)
        self.bind("<Button-1>", self._box_click)
        self.checked_resp = []
        self.checked_mes = []
        self.checked_recebedor = []
        self.checked_cost = []
        self.unchecked = ""
        self.list_resp = list_resp

    def get_checked_values(self, tipo):
        """Return a list of values from column index 0 for checked items."""
        if tipo == "Ordem":
            return self.checked_resp
        if tipo == "Mês":
            return self.checked_mes
        if tipo == "Custo":
            return self.checked_cost

    def on_double_click(self, event):
        region_clicked = self.identify_region(event.x, event.y)
        item = self.identify_row(event.y)
        values = self.item(item, 'values')
        limit_value_str = values[2]
        limit_value = functions_df.to_number(limit_value_str)

        if region_clicked not in "cell":
            return

        column = self.identify_column(event.x)
        # For example "#0" becomes -1
        column_index = int(column[1:]) - 1

        # Get the iid
        selected_iid = self.focus()

        # Get the value of the clicked cell
        selected_values = self.item(selected_iid).get("values")

        column_index_to_edit = 4
        column_index_receiver = 3
        if column_index == column_index_receiver:
            selected_value = selected_values[column_index_receiver]
            # Get the position and size of the cell
            column_box = self.bbox(selected_iid, column)
            # Create the editing cell
            combobox = CustomCombobox(self.master, values=self.list_resp, state="readonly")

            # Record the column index and item iid
            combobox.editing_column_index = column_index_receiver
            combobox.editing_item_iid = selected_iid

            # Show the previous value in the cell
            combobox.set(selected_value)

            combobox.bind("<<ComboboxSelected>>", lambda event, cbox=combobox: self.on_combobox_selected(event, cbox))

            combobox.config(postcommand=lambda: combobox.configure(height=15))

            ''' MUDAR AQUI PARA O COMBOBOX APARECER CERTO'''
            combobox.place(x=column_box[0] + 5,
                           y=column_box[1] + 143,
                           w=column_box[2],
                           h=column_box[3])

            combobox.focus_set()
            combobox.event_generate("<1>")

        if column_index == column_index_to_edit:

            def validate_entry(action, index, value_if_allowed, prior_value, text, validation_type, trigger_type,
                               widget_name):
                if action == '1':  # Insertion action
                    if text.isdigit() or text == ",":
                        try:
                            if value_if_allowed == "":
                                return True
                            elif float(value_if_allowed.replace(",", ".")) <= limit_value:
                                return True
                            else:
                                messagebox.showwarning("Valor Inválido",
                                                       f"O valor deve ser menor que {limit_value_str}")
                                return False
                        except ValueError:
                            return False
                    else:
                        messagebox.showwarning("Valor Inválido", "Precisa ser número.")
                        return False
                elif action == '0':  # Deletion action
                    return True  # Allow deletion
                return False

            vcmd = (self.master.register(validate_entry), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

            column_box = self.bbox(selected_iid, column)
            # Create the editing cell
            entry = tk.Entry(self.master, justify="center", bg="#E2E1DD", validate='key', validatecommand=vcmd)
            # Record the column index and item iid
            entry.editing_column_index = column_index
            entry.editing_item_iid = selected_iid

            entry.bind("<Return>", lambda event, cbox=entry: self.on_entry(event, cbox))
            entry.bind("<FocusOut>", lambda event, cbox=entry: self.on_entry(event, cbox))
            entry.bind("<Button-1>", lambda event, cbox=entry: self.on_entry(event, cbox))

            ''' MUDAR AQUI PARA O COMBOBOX APARECER CERTO'''
            entry.place(x=column_box[0] + 5,
                        y=column_box[1] + 143,
                        w=column_box[2],
                        h=column_box[3])

            entry.focus_set()
            entry.event_generate("<1>")

    def on_combobox_selected(self, event, combobox):
        self.bind_all("<Button-1>", lambda e: None)
        new_text = combobox.get()
        item = combobox.editing_item_iid
        column_index = combobox.editing_column_index
        selected_values = self.item(item)["values"]
        # Update the value in the treeview
        selected_values[column_index] = new_text
        self.item(item, values=selected_values)
        combobox.destroy()

    def show_message(self):
        top = tk.Toplevel()
        top.title("AVISO")
        top.grab_set()

        # Change the icon
        icon = tk.PhotoImage(file=relative_to_assets("logo.png"))
        top.iconphoto(True, icon)

        # Change the font size and style
        message_text = ("Adicione o Valor Solic e um Recebedor.\n"
                        "De um duplo clique na célula da coluna\n"
                        "Valor Solic. ou Recebedor para adicionar\n"
                        " o valor desejado.")

        message_label = tk.Label(top, text=message_text, font=font.Font(family="Suzano Text", size=8), anchor="w",
                                 justify="left")
        message_label.pack(padx=5, pady=15)

        # OK button
        ok_button = tk.Button(top, text="OK", command=top.destroy, width=10, height=1)
        ok_button.pack(padx=5, pady=2)

        # Adjust the size of the window
        top.geometry("255x120")
        center_window(top)

    def _box_click(self, event):
        """Check or uncheck box when clicked."""
        x, y = event.x, event.y
        elem = self.identify("element", x, y)
        if "image" in elem:
            # a box was clicked
            item = self.identify_row(y)

            values = self.item(item, 'values')

            resp_value = values[0]
            mes_value = values[1]
            recebedor_value = values[3]
            cost_value = values[4]
            if values[4] == "" or values[3] == "":
                self.show_message()
                return

            if self.tag_has("unchecked", item) or self.tag_has("tristate", item):  # is unchecked will check
                self.unchecked = "no"
                self._check_ancestor(item)
                self._check_descendant(item)

                self.checked_resp.append(resp_value)
                self.checked_mes.append(mes_value)
                self.checked_recebedor.append(recebedor_value)
                self.checked_cost.append(cost_value)

            else:  # is checked will uncheck
                self.unchecked = "yes"
                self._uncheck_descendant(item)
                self._uncheck_ancestor(item)
                data = {
                    'Respons.': self.checked_resp,
                    'Mês': self.checked_mes,
                    'Recebedor': self.checked_recebedor,
                    'Solic.': self.checked_cost
                }
                df = pd.DataFrame(data)
                print(df)
                try:
                    current_index = df.index.get_loc(df[(df['Respons.'] == values[0])
                                                        & (df['Mês'] == values[1])
                                                        & (df['Recebedor'] == values[3])
                                                        & (df['Solic.'] == values[4])
                                                     ].index[0])
                except ValueError:
                    current_index = None  # If the value is not found

                del self.checked_resp[int(current_index)]
                del self.checked_mes[int(current_index)]
                del self.checked_recebedor[int(current_index)]
                del self.checked_cost[int(current_index)]


    def on_entry(self, event, entry):  # Quando adiciona um valor solicitado
        self.bind_all("<Button-1>", lambda e: None)
        if entry.get() == '':
            new_text = ''
        else:
            new_text = functions_df.to_string(entry.get())
        item = entry.editing_item_iid
        column_index = entry.editing_column_index
        selected_values = self.item(item)["values"]
        # Update the value in the treeview
        selected_values[column_index] = new_text
        self.item(item, values=selected_values)
        entry.destroy()
        selected_values_updated = self.item(item, 'values')


class CustomGerenteAprovarCheckboxTreeview(CheckboxTreeview):
    def __init__(self, master, toaprove_entry, toaprove_entry_2, jan_entry, fev_entry, mar_entry, abr_entry, mai_entry,
                 jun_entry, jul_entry, ago_entry, set_entry, out_entry, nov_entry, dez_entry, acum_mes_entry,
                 acum_ano_entry, tbl, df_popup, df_other_tbl, checked_cost_label, **kw):
        super().__init__(master, **kw)

        # # Header checkbox variables
        # self.header_checked = False  # Track the state of the header checkbox
        #
        # # Load the checkbox images for the header (reuse the ones loaded for rows)
        # self.header_checked_image = self.im_checked
        # self.header_unchecked_image = self.im_unchecked
        #
        # # Create the header with a clickable checkbox for the checkbox column
        # self.heading('#0', text='', anchor='w', image=self.header_unchecked_image, command=self.toggle_all_checkboxes)

        self.bind("<Double-1>", self.on_double_click)
        self.bind("<Button-1>", self._box_click)
        self.checked_ordens = []
        self.checked_mes = []
        self.checked_cost = []
        self.entryto_aprove = toaprove_entry  # main entry
        self.entryto_aprove2 = toaprove_entry_2  # main entry
        self.unchecked = ""
        self.jan_values = jan_entry
        self.fev_values = fev_entry
        self.mar_values = mar_entry
        self.abr_values = abr_entry
        self.mai_values = mai_entry
        self.jun_values = jun_entry
        self.jul_values = jul_entry
        self.ago_values = ago_entry
        self.set_values = set_entry
        self.out_values = out_entry
        self.nov_values = nov_entry
        self.dez_values = dez_entry
        self.acum_mes = acum_mes_entry
        self.acum_ano = acum_ano_entry
        self.df_popup = df_popup
        self.df_other_tbl = df_other_tbl
        self.tbl = tbl
        self.checked_cost_label = checked_cost_label

    def get_checked_values(self, tipo):
        """Return a list of values from column index 0 for checked items."""
        if tipo == "Ordem":
            return self.checked_ordens
        if tipo == "Mês":
            return self.checked_mes
        if tipo == "Custo":
            return self.checked_cost

    def show_extra_info(self, row):
        top = tk.Toplevel()
        top.title(" DETALHES ")
        top.configure(bg="#E2E1DD")  # Set background color of the popup window
        top.grab_set()

        # Change the icon
        icon = tk.PhotoImage(file=relative_to_assets("logo.png"))  # Replace "logo.png" with the path to your icon file
        top.iconphoto(True, icon)

        # Change the font size and style
        font_family_column = "Suzano Unicase XBold"
        font_family = "Suzano Text"
        font_size = 8

        # Convert the row to a dictionary
        row_dict = row.to_dict()

        # Calculate the maximum width of the values
        max_value_width = max(len(str(value)) for value in row_dict.values()) + 5

        # Display the information from the filtered row
        for i, (column_name, value) in enumerate(row_dict.items()):
            # Font for the column name
            label_font = font.Font(family=font_family_column, size=font_size, weight="bold")
            column_label = tk.Label(top, text=column_name + ":", font=label_font, anchor="w", justify="left",
                                    bg="#E2E1DD")
            column_label.grid(row=i, column=0, sticky="ew", padx=10, pady=1)
            # Entry widget for the value (to enable copying)
            value_entry = tk.Entry(top, font=(font_family, font_size), justify="left", bg="#E2E1DD")
            # Insert value into the entry widget, insert an empty string if value is blank or NaN
            insert_value = "" if pd.isna(value) or value == "" or value == "R$ nan" else value
            value_entry.insert(0, insert_value)
            value_entry.grid(row=i, column=1, sticky="ew", padx=10, pady=1)
            # Set the width of the value column to match the maximum value width
            value_entry.config(width=max_value_width)

        # Add an OK button to close the window
        ok_button = tk.Button(top, text="OK", command=top.destroy, width=10)
        ok_button.grid(row=len(row_dict), column=0, columnspan=2, pady=2)

        # Centralize columns
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1)

        # Adjust the size of the window
        top.geometry("400x380")  # Adjust the size as needed
        center_window(top)

        top.focus_set()

    def on_double_click(self, event):
        region_clicked = self.identify_region(event.x, event.y)

        if region_clicked not in "cell":
            return

        # Get the iid
        selected_iid = self.focus()

        # Get the value of the clicked cell
        selected_values = self.item(selected_iid).get("values")

        ordem_value = selected_values[0]
        # Filter df_popup for the row that matches ordem_value in the "Nº Ordem" column
        filtered_row = self.df_popup[self.df_popup['Nº Ordem'] == ordem_value].iloc[
            0]  # Assuming there's only one matching row

        # Create the popup window
        self.show_extra_info(filtered_row)

    def calculate_total_cost(self, month, checked_values_mes, checked_values_cost, order):
        current_list_index = self.checked_ordens.index(order)  # get the index in the order list
        #  values[0] is the order number for the current item]

        mes = checked_values_mes[current_list_index]  # get the month for the current line
        cost_value = float(checked_values_cost[current_list_index].replace('R$', '').replace('.', '').replace(',',
                                                                                                              '.'))  # get the cost current line
        if mes == month:
            if self.unchecked == "yes":
                return -cost_value
            else:
                return cost_value
        else:
            return 0

    def update_balance_entry(self, entry_widget, month, order, type):

        total_cost = self.calculate_total_cost(month, self.get_checked_values("Mês"),
                                               self.get_checked_values("Custo"), order)
        current_balance = float(entry_widget.get().replace('R$', '').replace('.', '').replace(',', '.'))
        if type == "old":
            new_balance = current_balance + total_cost
        else:
            new_balance = current_balance - total_cost

        if new_balance < 0:
            entry_widget.config(disabledforeground="red")
        else:
            entry_widget.config(disabledforeground="black")
        new_balance = f"R$ {new_balance:,.2f}".replace('.', '_').replace(',', '.').replace('_', ',')
        entry_widget.config(state=tk.NORMAL)
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, new_balance)
        entry_widget.config(state=tk.DISABLED)

    def update_entry_to_approve(self):
        entry_widgets = {
            "Jan": self.jan_values, "Fev": self.fev_values,
            "Mar": self.mar_values, "Abr": self.abr_values,
            "Mai": self.mai_values, "Jun": self.jun_values,
            "Jul": self.jul_values, "Ago": self.ago_values,
            "Set": self.set_values, "Out": self.out_values,
            "Nov": self.nov_values, "Dez": self.dez_values,
            "N/A": self.acum_mes
        }

        checked_values_ordem = self.get_checked_values("Ordem")
        checked_values_mes = self.get_checked_values("Mês")
        # Display the DataFrame
        self.entryto_aprove.config(state=tk.NORMAL)
        self.entryto_aprove.delete("1.0", tk.END)
        table_width = 0  # Adjust this width as needed
        counter = 1
        for ordem, mes, custo in zip(checked_values_ordem, checked_values_mes, self.get_checked_values("Custo")):
            numbered_value = f"{counter})  {ordem} - {mes}"
            entry_widget = entry_widgets.get(mes)
            balance = float(
                entry_widget.get().replace('R$', '').replace('.', '').replace(',', '.'))  # Valor do saldo atual
            centered_value = numbered_value.center(table_width)
            if balance < 0 and custo != 'R$ 0,00':
                self.entryto_aprove.insert(tk.END,
                                           centered_value + "* \n")  # Insert centered value with a newline character
                self.entryto_aprove.tag_config("start", foreground="red")

                self.entryto_aprove.tag_add("start", str(counter) + ".4", str(counter) + ".19")
            else:
                self.entryto_aprove.insert(tk.END,
                                           centered_value + "\n")  # Insert centered value with a newline character
            counter += 1
        self.entryto_aprove.config(state=tk.DISABLED)

        text = self.entryto_aprove2.get("1.0", "end-1c")
        # Split the text by lines
        lines = text.strip().split('\n')
        if text != "":
            # Extracting data and creating lists for DataFrame
            ordem = []
            mes = []
            for line in lines:
                parts = line.split('-')
                ordem.append(parts[0].split(') ')[1].strip())
                mes_value = parts[1].strip()
                if mes_value.endswith('*'):
                    mes_value = mes_value[:-1]  # Remove the asterisk
                mes.append(mes_value)

            # Creating DataFrame
            df_to_insert = pd.DataFrame({
                'Ordem': ordem,
                'Mes': mes
            })

            df_to_filter = self.df_other_tbl

            # Display the DataFrame
            self.entryto_aprove2.config(state=tk.NORMAL)
            self.entryto_aprove2.delete("1.0", tk.END)
            table_width = 0  # Adjust this width as needed
            counter = 1
            for ordem, mes in zip(df_to_insert['Ordem'], df_to_insert['Mes']):
                numbered_value = f"{counter})  {ordem} - {mes}"
                entry_widget = entry_widgets.get(mes)
                balance = float(
                    entry_widget.get().replace('R$', '').replace('.', '').replace(',', '.'))  # Valor do saldo atual

                centered_value = numbered_value.center(table_width)
                filtered_df = df_to_filter[df_to_filter['Nº Ordem'] == int(ordem)]
                custo = filtered_df.iloc[0]['Custo']
                if balance < 0 and custo != 'R$ 0,00':
                    self.entryto_aprove2.insert(tk.END,
                                                centered_value + "* \n")  # Insert centered value with a newline character
                    self.entryto_aprove2.tag_config("start", foreground="red")

                    self.entryto_aprove2.tag_add("start", str(counter) + ".4", str(counter) + ".19")
                else:
                    self.entryto_aprove2.insert(tk.END,
                                                centered_value + "\n")  # Insert centered value with a newline character
                counter += 1
            self.entryto_aprove2.config(state=tk.DISABLED)

    def update_checked_values(self, order, month, month_old=None):
        entry_widgets = {
            "Jan": self.jan_values, "Fev": self.fev_values,
            "Mar": self.mar_values, "Abr": self.abr_values,
            "Mai": self.mai_values, "Jun": self.jun_values,
            "Jul": self.jul_values, "Ago": self.ago_values,
            "Set": self.set_values, "Out": self.out_values,
            "Nov": self.nov_values, "Dez": self.dez_values,
            "N/A": self.acum_mes
        }
        if month is not None:
            entry_widget = entry_widgets.get(month)
            self.update_balance_entry(entry_widget, month, order, "new")
            self.update_balance_entry(self.acum_ano, month, order, "new")
            if month in months_till_current:
                self.update_balance_entry(self.acum_mes, month, order, "new")

        if month_old is not None:
            entry_widget_old = entry_widgets.get(month_old)
            self.update_balance_entry(entry_widget_old, month, order, "old")
            self.update_balance_entry(self.acum_ano, month, order, "old")
            if month in months_till_current:
                self.update_balance_entry(self.acum_mes, month, order, "old")

    def toggle_all_checkboxes(self, checked):
        """
        Toggle the state of all checkboxes when the header checkbox is clicked.
        """
        if checked:
            # Uncheck all checkboxes
            # self.heading('#0', image=self.header_unchecked_image)
            self.uncheck_all()  # Uncheck all checkboxes
            for item in self.get_children(''):
                self._apply_transformation(item, action='uncheck')
        else:
            # self.heading('#0', image=self.header_checked_image)
            self.check_all()  # Check all checkboxes
            for item in self.get_children(''):
                self._apply_transformation(item, action='check')

    def _apply_transformation(self, item, action):
        """
        Apply transformations (entry update and balances) when checkboxes are toggled.
        The 'action' parameter specifies whether we are checking or unchecking.
        """
        values = self.item(item, 'values')
        column_index = 5  # month
        order_value = values[0]
        mes_value = values[column_index]

        if self.tbl == "tbl_a_aprovar":
            cost_value = values[4]
        else:
            cost_value = values[2]

        if action == 'check':  # When checking
            if order_value not in self.checked_ordens:  # Avoid duplicates
                self.unchecked = "no"
                self.checked_ordens.append(order_value)
                self.checked_mes.append(mes_value)
                self.checked_cost.append(cost_value)
                cost = [aux_functions_df.to_number(cost) for cost in self.checked_cost]
                self.checked_cost_label.config(text=aux_functions_df.to_string(sum(cost)))
                if values[column_index] != "":
                    if self.tbl == "tbl_a_aprovar":
                        self.update_checked_values(order_value, mes_value)
                        self.update_entry_to_approve()
                    else:
                        month_old = values[3]
                        self.update_checked_values(order_value, mes_value, month_old)
                        self.update_entry_to_approve()

        elif action == 'uncheck':  # When unchecking
            try:
                current_index = self.checked_ordens.index(order_value)
            except ValueError:
                current_index = None  # If the value is not found

            if current_index is not None:
                self.unchecked = "yes"
                # Only update and remove if the item is actually in the checked list
                if self.tbl == "tbl_a_aprovar":
                    self.update_checked_values(order_value, mes_value)
                else:
                    month_old = values[3]
                    self.update_checked_values(order_value, mes_value, month_old)

                self.checked_ordens.remove(order_value)
                del self.checked_mes[current_index]
                del self.checked_cost[current_index]
                cost = [aux_functions_df.to_number(cost) for cost in self.checked_cost]
                self.checked_cost_label.config(text=aux_functions_df.to_string(sum(cost)))
                self.update_entry_to_approve()

    def _box_click(self, event):
        """
        Check or uncheck box when clicked, and apply transformations.
        """
        x, y = event.x, event.y
        elem = self.identify("element", x, y)
        if "image" in elem:
            item = self.identify_row(y)
            values = self.item(item, 'values')
            column_index = 5  # month

            order_value = values[0]
            mes_value = values[column_index]
            if self.tbl == "tbl_a_aprovar":
                cost_value = values[4]
            else:
                cost_value = values[2]

            if self.tag_has("unchecked", item) or self.tag_has("tristate", item):  # is unchecked, will check
                self._check_ancestor(item)
                self._check_descendant(item)

                self._apply_transformation(item, action='check')

            else:  # is checked, will uncheck
                self._uncheck_descendant(item)
                self._uncheck_ancestor(item)

                self._apply_transformation(item, action='uncheck')

    # def _box_click(self, event):
    #     """Check or uncheck box when clicked."""
    #     x, y = event.x, event.y
    #     elem = self.identify("element", x, y)
    #     if "image" in elem:
    #         # a box was clicked
    #         item = self.identify_row(y)
    #
    #         values = self.item(item, 'values')
    #
    #         column_index = 5  # month
    #
    #         order_value = values[0]
    #         mes_value = values[column_index]
    #         if self.tbl == "tbl_a_aprovar":
    #             cost_value = values[4]
    #         else:
    #             cost_value = values[2]
    #
    #         if self.tag_has("unchecked", item) or self.tag_has("tristate", item):  # is unchecked will check
    #             self.unchecked = "no"
    #             self._check_ancestor(item)
    #             self._check_descendant(item)
    #
    #             self.checked_ordens.append(order_value)
    #             self.checked_mes.append(mes_value)
    #             self.checked_cost.append(cost_value)
    #             if values[column_index] != "":
    #                 if self.tbl == "tbl_a_aprovar":
    #                     self.update_checked_values(order_value, mes_value)  # Muda o valor do saldo
    #                     self.update_entry_to_approve()  # Adiciona ao aprovar/modificar
    #                 else:
    #                     month_old = values[3]
    #                     self.update_checked_values(order_value, mes_value, month_old)  # Muda o valor do saldo
    #                     self.update_entry_to_approve()  # Adiciona ao aprovar/modificar
    #
    #
    #         else:  # is checked will uncheck
    #             self.unchecked = "yes"
    #             self._uncheck_descendant(item)
    #             self._uncheck_ancestor(item)
    #             try:
    #                 current_index = self.checked_ordens.index(values[0])  # search the index in the order list
    #             except ValueError:
    #                 current_index = None  # If the value is not found
    #
    #             if self.tbl == "tbl_a_aprovar":
    #                 self.update_checked_values(order_value, mes_value)  # Muda o valor do saldo
    #             else:
    #                 month_old = values[3]
    #                 self.update_checked_values(order_value, mes_value,
    #                                            month_old)  # Muda o valor dos saldos (passa 2 meses)
    #
    #             self.checked_ordens.remove(values[0])
    #             del self.checked_mes[current_index]
    #             del self.checked_cost[current_index]
    #             self.update_entry_to_approve()  # Retira do ao aprovar/modificar
