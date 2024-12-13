import os
import requests
import zipfile
import shutil
import tkinter as tk
from tkinter import ttk
from threading import Thread

# Configurações do repositório
GITHUB_OWNER = "PedroSZUpdate"
GITHUB_REPO = "aprovacaocustogerente"
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
        with open("repo.zip", "wb") as file:
            file.write(response.content)
        with zipfile.ZipFile("repo.zip", "r") as zip_ref:
            zip_ref.extractall(extract_to)
        os.remove("repo.zip")
    else:
        print("Erro ao baixar o ZIP:", response.status_code)

def remove_readonly(func, path, excinfo):
    """Remove o atributo somente leitura de arquivos antes de apagar."""
    os.chmod(path, 0o777)  # Define permissões totais
    func(path)  # Tenta novamente

def update_app(progress, label):
    """Verifica e atualiza o app, se necessário."""
    label.config(text="Verificando atualizações...")
    latest_commit = get_latest_commit_hash()
    if not latest_commit:
        label.config(text="Erro ao verificar atualizações.")
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
        label.config(text="Nova atualização encontrada! Baixando...")

        # Animação da barrinha de progresso
        progress.start(10)  # Velocidade da animação

        # Baixa e substitui os arquivos do app
        temp_dir = "./temp_update"
        download_and_extract_zip(ZIP_URL, temp_dir)

        # Move os arquivos extraídos para o diretório do app
        repo_dir = os.path.join(temp_dir, f"{GITHUB_REPO}-{BRANCH}")
        if os.path.exists(LOCAL_DIR):
            shutil.rmtree(LOCAL_DIR, onerror=remove_readonly)
        shutil.move(repo_dir, LOCAL_DIR)
        shutil.rmtree(temp_dir)

        # Salva o hash do último commit
        with open(commit_file, "w") as file:
            file.write(latest_commit)

        # Para a animação após o download
        progress.stop()
        label.config(text="Atualização concluída!")
    else:
        label.config(text="Nenhuma atualização disponível.")

        # Para a animação caso não haja atualização
        progress.stop()

def start_update(progress, label):
    """Executa a função de atualização em uma thread separada."""
    thread = Thread(target=update_app, args=(progress, label))
    thread.start()

# Interface gráfica
def create_gui():
    """Cria a interface gráfica do aplicativo."""
    root = tk.Tk()
    root.title("Atualizador de App")

    # Label de status
    label = tk.Label(root, text="Clique no botão para verificar atualizações.")
    label.pack(pady=10)

    # Barra de progresso
    progress = ttk.Progressbar(root, mode="indeterminate")
    progress.pack(pady=10, fill=tk.X, padx=20)

    # Botão de atualização
    update_button = tk.Button(
        root, text="Atualizar App", command=lambda: start_update(progress, label)
    )
    update_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()