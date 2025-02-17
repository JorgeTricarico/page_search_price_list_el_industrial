# scripts/deploy_updates.py (MODIFICADO para COPIAR desde dev a master)
import os
import requests # Necesitamos requests para descargar desde GitHub API
from app.services.github_api import GitHubAPI  # Asegúrate de que la importación sea correcta

def main():
    github_api_dev = GitHubAPI() # Instancia para operar en la rama dev (por defecto)
    github_api_master = GitHubAPI() # Instancia para operar en la rama master (modificaremos branch)
    github_api_master.branch = "master" # Cambiamos la rama de la instancia para master

    # 1. Obtener el nombre del último archivo JSON desde la rama 'dev'
    try:
        latest_filename_dev_txt_content = github_api_dev.get_file_text_content("latest-json-filename.txt")
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

def get_file_text_content(self, path): # **NUEVA FUNCIÓN en GitHubAPI para obtener contenido de texto**
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

def download_file_binary(self, path): # **NUEVA FUNCIÓN en GitHubAPI para descargar binario**
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


if __name__ == "__main__":
    main()
