# scripts/deploy_updates.py (MODIFICADO para COPIAR desde dev a master, CON GitHubAPI INTEGRADA)
import os
import requests # Necesitamos requests para descargar desde GitHub API
import base64, json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GitHubAPI: # **CLASE GitHubAPI INTEGRADA DIRECTAMENTE AQUÍ**
    def __init__(self):
        self.token = os.getenv("GIT_TOKEN")
        if not self.token:
            raise ValueError("La variable de entorno GIT_TOKEN no está definida.")
        self.owner = os.getenv("GIT_OWNER")
        if not self.owner:
            raise ValueError("La variable de entorno GIT_OWNER no está definida.")
        self.repo = os.getenv("GIT_REPO")
        if not self.repo:
            raise ValueError("La variable de entorno GIT_REPO no está definida.")
        self.branch = os.getenv("GIT_BRANCH", "dev")
        if not self.branch:
            raise ValueError("La variable de entorno GIT_BRANCH no está definida.")
        self.push_mode = os.getenv("GIT_PUSH_MODE", "staged")
        self.folder_path = os.getenv("GIT_FOLDER_PATH", "price-lists-json").strip('/') # **MODIFICADO:  Carpeta 'price-lists-json' por defecto**
        self.api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }

    def _get_full_path(self, path): # **NUEVA FUNCIÓN INTERNA**
        """Construye la ruta completa incluyendo la carpeta si está definida."""
        print(f"folder_path: {self.folder_path}")
        if self.folder_path:
            return f"{self.folder_path}/{path}"
        return path


    def get_file_sha(self, path):
        full_path = self._get_full_path(path) # **Usar _get_full_path**
        url = f"{self.api_url}/{full_path}" # **Usar full_path**
        params = {"ref": self.branch}
        response = requests.get(url, headers=self._get_headers(), params=params)
        if response.status_code == 200:
            return response.json().get("sha")
        elif response.status_code == 404:
            # El archivo no existe, lo cual es normal para una creación
            print(f"Archivo {full_path} no encontrado; se procederá a crearlo.") # **Usar full_path en logs**
            return None
        else:
            print(f"Error al obtener el SHA de {full_path}: {response.status_code} {response.text}") # **Usar full_path en logs**
            print(self.token)
            print(self.owner)
            print(self.repo)
            print(self.branch)
            print(self.api_url)
            return None

    def create_or_update_file_binary(self, path, file_bytes, commit_message):
        full_path = self._get_full_path(path) # **Usar _get_full_path**
        url = f"{self.api_url}/{full_path}" # **Usar full_path**
        b64_content = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "message": commit_message,
            "content": b64_content,
            "branch": self.branch
        }
        sha = self.get_file_sha(path)
        if sha:
            payload["sha"] = sha
        response = requests.put(url, headers=self._get_headers(), json=payload)
        if response.status_code in [200, 201]:
            print(f"Archivo '{full_path}' creado/actualizado correctamente en GitHub.")  # **Usar full_path en logs**
            return True
        else:
            print(f"Error al crear/actualizar '{full_path}': {response.status_code} {response.text}")  # **Usar full_path en logs**
            return False

    def delete_file_by_pattern(self, pattern):
        full_folder_path = self._get_full_path('') # **Obtener ruta de la carpeta base**
        url = f"{self.api_url}{full_folder_path if full_folder_path else ''}" # **Usar ruta carpeta base en URL de listado**

        params = {"ref": self.branch}
        response = requests.get(url, headers=self._get_headers(), params=params)
        if response.status_code == 200:
            items = response.json()
            for item in items:
                full_item_path = self._get_full_path(item.get("name")) # **Usar _get_full_path para item name**
                if item.get("type") == "file" and item.get("name").endswith(pattern):
                    sha = item.get("sha")
                    delete_url = f"{self.api_url}/{full_item_path}" # **Usar full_item_path para delete_url**
                    payload = {
                        "message": f"Eliminar archivo antiguo {item.get('name')}",
                        "sha": sha,
                        "branch": self.branch
                    }
                    del_response = requests.delete(delete_url, headers=self._get_headers(), json=payload)
                    if del_response.status_code not in [200, 201]:
                        print(f"Error eliminando {item.get('name')}: {del_response.status_code} {del_response.text}")
            return True
        else:
            print(f"Error listando archivos: {response.status_code} {response.text}")
            return False

    def create_or_update_file_text(self, path, text_content, commit_message):
        full_path = self._get_full_path(path) # **Usar _get_full_path**
        url = f"{self.api_url}/{full_path}" # **Usar full_path**
        b64_content = base64.b64encode(text_content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": commit_message,
            "content": b64_content,
            "branch": self.branch
        }
        sha = self.get_file_sha(path)
        if sha:
            payload["sha"] = sha
        response = requests.put(url, headers=self._get_headers(), json=payload)
        if response.status_code in [200, 201]:
            print(f"Archivo de texto '{full_path}' creado/actualizado correctamente en GitHub.") # **Usar full_path en logs**
            return True
        else:
            print(f"Error al crear/actualizar archivo de texto '{full_path}': {response.status_code} {response.text}") # **Usar full_path en logs**
            return False

    def get_dynamic_file_name(self):
        """
        Genera el nombre del archivo con la fecha actual en formato DD-MM-YY.
        Ejemplo: list_price_27-07-24_json_compres.gz
        """
        now = datetime.now()
        date_str = now.strftime("%d-%m-%y")
        return f"list_price_{date_str}_json_compres.gz"

    def merge_branch(self, base, head, commit_message):
        """Fusiona la rama 'head' en la rama 'base' usando el endpoint de merges de GitHub."""

        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/merges"
        payload = {
            "base": base,
            "head": head,
            "commit_message": commit_message
        }
        response = requests.post(url, headers=self._get_headers(), json=payload)
        if response.status_code in [200, 201]:
            print(f"Fusión de {head} en {base} exitosa.")
            return True
        else:
            print(f"Error al fusionar {head} en {base}: {response.status_code} {response.text}")
            return False

    def get_file_text_content(self, path): # **NUEVA FUNCIÓN en GitHubAPI**
        """Obtiene el contenido de un archivo de texto desde GitHub."""
        full_path = self._get_full_path(path)
        url = f"{self.api_url}/{full_path}"
        params = {"ref": self.branch}
        response = requests.get(url, headers=self._get_headers(), params=params)
        if response.status_code == 200:
            return response.text
        elif response.status_code == 404:
            print(f"Archivo de texto '{full_path}' no encontrado en rama '{self.branch}'.")
            return None
        else:
            print(f"Error al obtener archivo de texto '{full_path}' en rama '{self.branch}': {response.status_code} {response.text}")
            return None

    def download_file_binary(self, path): # **NUEVA FUNCIÓN en GitHubAPI**
        """Descarga el contenido binario de un archivo desde GitHub."""
        full_path = self._get_full_path(path)
        url = f"{self.api_url}/{full_path}"
        params = {"ref": self.branch}
        response = requests.get(url, headers=self._get_headers(), params=params)
        if response.status_code == 200:
            return response.content # response.content devuelve el contenido binario
        elif response.status_code == 404:
            print(f"Archivo binario '{full_path}' no encontrado en rama '{self.branch}'.")
            return None
        else:
            print(f"Error al descargar archivo binario '{full_path}' en rama '{self.branch}': {response.status_code} {response.text}")
            return None


def main():
    github_api_dev = GitHubAPI() # Instancia para operar en la rama dev (por defecto)
    github_api_master = GitHubAPI() # Instancia para operar en la rama master (modificaremos branch)
    github_api_master.branch = "master" # Cambiamos la rama de la instancia para master
    github_api_dev.branch = "dev"

    # 1. Obtener el nombre del último archivo JSON desde la rama 'dev'
    try:
        latest_filename_dev_txt_content = github_api_dev.get_file_text_content("latest-json-filename.txt")
        print("Contenido de latest-json-filename.txt:", github_api_dev.get_file_text_content("latest-json-filename.txt"))

        # Obtener el contenido del archivo como string
        file_info_str = github_api_dev.get_file_text_content("latest-json-filename.txt")
        
        # Convertir el string JSON en un diccionario
        try:
            file_info = json.loads(file_info_str)  # <-- Aquí parseamos correctamente el JSON
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al decodificar JSON: {e}")
        
        # Verificar y decodificar contenido en base64
        if "content" in file_info and "encoding" in file_info and file_info["encoding"] == "base64":
            latest_filename_dev_txt_content = base64.b64decode(file_info["content"]).decode("utf-8").strip()
        else:
            raise ValueError("No se pudo obtener el contenido en base64 del archivo latest-json-filename.txt")
        
        print("Contenido decodificado:", latest_filename_dev_txt_content)
        
        print("Contenido decodificado:", latest_filename_dev_txt_content)
        if latest_filename_dev_txt_content:
            latest_json_filename_dev = latest_filename_dev_txt_content.strip() # Eliminar espacios/saltos de línea
            print(f"Nombre del último archivo JSON en dev: {latest_json_filename_dev}")
        else:
            raise Exception("No se pudo obtener el nombre del archivo JSON desde latest-json-filename.txt en dev")
    except Exception as e:
        print(f"Error al obtener nombre de archivo JSON de dev: {e}")
        return

    # 2. Descargar el archivo JSON comprimido desde la rama 'dev'
    try:
        compressed_json_content_dev = github_api_dev.download_file_binary(latest_json_filename_dev)
        if not compressed_json_content_dev:
            raise Exception(f"No se pudieron descargar contenidos del archivo JSON comprimido '{latest_json_filename_dev}' desde dev")
        print(f"Archivo JSON comprimido '{latest_json_filename_dev}' descargado desde dev.")
    except Exception as e:
        print(f"Error al descargar archivo JSON comprimido desde dev: {e}")
        return

    # 3.  Actualizar archivos en la rama 'master' usando GitHubAPI (instancia para master)
    try:
        # Eliminar archivo JSON comprimido antiguo en master
        github_api_master.delete_file_by_pattern("_json_compres.gz") # Opera en master porque usamos github_api_master

        # Crear/Actualizar nuevo archivo JSON comprimido en master
        github_api_master.create_or_update_file_binary(latest_json_filename_dev, compressed_json_content_dev, "Copiar lista de precios de dev a master") # Opera en master

        # Actualizar latest-json-filename.txt en master (con el mismo nombre de archivo de dev)
        latest_filename_content = latest_json_filename_dev + "\n"
        github_api_master.create_or_update_file_text("latest-json-filename.txt", latest_filename_content, "Copiar nombre de archivo JSON de dev a master") # Opera en master

        print(f"Script deploy_updates.py ejecutado exitosamente: Lista de precios COPIADA de dev a master en GitHub.")

    except Exception as e:
        print(f"Error en deploy_updates.py al actualizar archivos de GitHub en master: {e}")
        print(f"Detalles del error: {e}")


if __name__ == "__main__":
    main()
