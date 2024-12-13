import tkinter as tk
import aux_custom_classes
from update import update_app
from screen_gerentes import ScreenGerente
from screen_gerentes_mov_saldo import ScreenSaldo


class App(tk.Tk):
    update_app()
    
    def __init__(self, screen_name="Aprovação e Liberação de Ordens"):
        super().__init__()
        # self.title("My Tkinter App")
        # self.geometry("900x540")
        self.current_frame = None
        self.geometry(f"{900}x540+0+0")
        self.attributes("-topmost", True)
        self.update()  # Update the window to make sure it's displayed
        self.attributes("-topmost", False)  # Allow it to be moved behind other windows
        self.configure(bg="#FFFFFF")
        self.iconbitmap(aux_custom_classes.relative_to_assets("logo.ico"))
        self.resizable(False, False)
        self.screen_name = screen_name
        self.show_screen(screen_name)

    def show_screen(self, screen_name):
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.screen_name = screen_name
        if screen_name == "Aprovação e Liberação de Ordens":
            self.title("Aprovação e Liberação de Ordens")
            self.current_frame = ScreenGerente(self)
        if screen_name == "Movimentações de Saldo":
            self.title("Movimentações de Saldo")
            self.current_frame = ScreenSaldo(self)
        self.current_frame.pack(fill="both", expand=True)

    def reset_and_show_current_screen(self):
        # Restart the application by destroying and recreating the main window with the current screen
        current_screen = self.screen_name
        self.destroy()
        app = App(screen_name=current_screen)
        app.mainloop()


app = App()
app.mainloop()
