import os
import requests
import zipfile
import shutil

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
        with open("repo.zip", "wb") as file:
            file.write(response.content)
        with zipfile.ZipFile("repo.zip", "r") as zip_ref:
            zip_ref.extractall(extract_to)
        os.remove("repo.zip")
    else:
        print("Erro ao baixar o ZIP:", response.status_code)


def update_app():
    """Verifica e atualiza o app, se necessário."""
    latest_commit = get_latest_commit_hash()
    if not latest_commit:
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
        print("Nova atualização encontrada! Atualizando...")
        # Baixa e substitui os arquivos do app
        temp_dir = "./temp_update"
        download_and_extract_zip(ZIP_URL, temp_dir)
        # Move os arquivos extraídos para o diretório do app
        repo_dir = os.path.join(temp_dir, f"{GITHUB_REPO}-{BRANCH}")
        if os.path.exists(LOCAL_DIR):
            shutil.rmtree(LOCAL_DIR)
        shutil.move(repo_dir, LOCAL_DIR)
        shutil.rmtree(temp_dir)
        # Salva o hash do último commit
        with open(commit_file, "w") as file:
            file.write(latest_commit)
        print("Atualização concluída!")
    else:
        print("Nenhuma atualização disponível.")


if __name__ == "__main__":
    update_app()

