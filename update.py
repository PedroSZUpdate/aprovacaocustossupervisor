import os
import requests
import zipfile
import shutil
import tempfile
import tkinter as tk
from tkinter import Tk, ttk
import threading

# Configurações do repositório
GITHUB_OWNER = "PedroSZUpdate"
GITHUB_REPO = "aprovacaocustossupervisor"
BRANCH = "main"
LOCAL_DIR = "./meu_app"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits/{BRANCH}"
ZIP_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/refs/heads/{BRANCH}.zip"


def get_latest_commit_hash():
    """Obtém o hash do último commit do branch."""
    response = requests.get(GITHUB_API_URL)
    if response.status_code == 200:
        return response.json()["sha"]
    else:
        print("Erro ao acessar a API do GitHub:", response.status_code)
        return None


def download_and_extract_zip(url, extract_to):
    """Baixa e extrai o ZIP do repositório."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "repo.zip")
            with open(zip_path, "wb") as file:
                file.write(response.content)
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)
    else:
        print("Erro ao baixar o ZIP:", response.status_code)


def update_app(progress_bar, root, update_button, status_label):
    """Verifica e atualiza o app, se necessário."""
    latest_commit = get_latest_commit_hash()
    if not latest_commit:
        status_label.config(text="Erro ao obter o commit mais recente.")
        update_button.config(state="normal")
        return

    # Verifica se há um commit salvo
    commit_file = os.path.join(LOCAL_DIR, "commit.txt")
    if os.path.exists(commit_file):
        with open(commit_file, "r") as file:
            saved_commit = file.read().strip()
    else:
        saved_commit = None

    # Compara os commits
    if latest_commit != saved_commit:
        status_label.config(text="Nova atualização encontrada! Atualizando...")
        root.update_idletasks()  # Atualiza a interface

        # Baixa e substitui os arquivos do app
        with tempfile.TemporaryDirectory() as temp_dir:
            download_and_extract_zip(ZIP_URL, temp_dir)

            repo_dir = os.path.join(temp_dir, f"{GITHUB_REPO}-{BRANCH}")
            if os.path.exists(LOCAL_DIR):
                shutil.rmtree(LOCAL_DIR)
            shutil.move(repo_dir, LOCAL_DIR)

            # Salva o hash do último commit
            with open(commit_file, "w") as file:
                file.write(latest_commit)

        status_label.config(text="Atualização concluída com sucesso!")
    else:
        status_label.config(text="Nenhuma atualização disponível.")

    # Atualiza a barra de progresso
    progress_bar["value"] = 100

    # Desativa o botão e sugere ao usuário fechar a janela
    update_button.config(state="disabled")
    status_label.config(text=status_label.cget("text") + " Feche a janela para continuar.")


def start_update(progress_bar, root, update_button, status_label):
    """Inicia a atualização em uma nova thread."""
    update_button.config(state="disabled")  # Desativa o botão durante a execução
    threading.Thread(target=update_app, args=(progress_bar, root, update_button, status_label), daemon=True).start()


# Interface Tkinter
def create_interface():
    root = Tk()
    root.title("Atualizador de App")

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
    progress_bar.grid(row=0, column=0, pady=10)

    update_button = ttk.Button(frame, text="Atualizar App", command=lambda: start_update(progress_bar, root, update_button, status_label))
    update_button.grid(row=1, column=0, pady=5)

    status_label = ttk.Label(frame, text="")
    status_label.grid(row=2, column=0, pady=10)

    root.mainloop()


if __name__ == "__main__":
    create_interface()