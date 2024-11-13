import requests
import os
import re
import schedule
import time
from datetime import datetime
import json
from typing import Dict, Union, List, Any

class Config:
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> dict:
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Le fichier de configuration {self.config_file} n'existe pas")

    @property
    def github_token(self) -> str:
        return self.config.get('github_token')

    @property
    def repo_owner(self) -> str:
        return self.config.get('repo_owner')

    @property
    def repo_name(self) -> str:
        return self.config.get('repo_name')

class N8nNodeScanner:
    N8N_REPO_OWNER = "n8n-io"
    N8N_REPO_NAME = "n8n"

    def __init__(self, github_token: str):
        """
        Initialise le scanner de nodes pour le dépôt officiel n8n

        Args:
            github_token (str): Token d'authentification GitHub
        """
        self.github_token = github_token
        self.headers = {'Authorization': f'token {github_token}'}
        self.repo_owner = self.N8N_REPO_OWNER
        self.repo_name = self.N8N_REPO_NAME
        self.base_url = f'https://api.github.com/repos/{self.repo_owner}/{self.repo_name}'
        self.results_file = 'node_versions.json'
        self.scan_paths = [
            'packages/nodes-base/nodes',
            'packages/@n8n/nodes-langchain/nodes'
        ]

    def get_node_files(self, branch: str = 'master') -> List[dict]:
        """Récupère tous les fichiers .node.ts du dépôt"""
        files = []

        for scan_path in self.scan_paths:
            url = f'{self.base_url}/git/trees/{branch}?recursive=1'
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                tree = response.json().get('tree', [])
                matching_files = [
                    item for item in tree
                    if item['path'].endswith('.node.ts')
                    and scan_path in item['path']
                ]
                files.extend(matching_files)

        return files

    def extract_version(self, content: str) -> Union[float, List[float], None]:
        """
        Extrait la version ou defaultVersion du fichier
        Gère à la fois les versions uniques et les tableaux de versions
        """
        # Recherche de defaultVersion
        default_version_match = re.search(r'defaultVersion:\s*([\d.]+)', content)
        if default_version_match:
            return float(default_version_match.group(1))

        # Recherche de version au format tableau
        version_array_match = re.search(r'version:\s*\[([\d.,\s]+)\]', content)
        if version_array_match:
            versions_str = version_array_match.group(1)
            try:
                versions = [float(v.strip()) for v in versions_str.split(',')]
                return versions
            except ValueError:
                pass

        # Recherche de version simple
        version_match = re.search(r'version:\s*([\d.]+)', content)
        if version_match:
            return float(version_match.group(1))

        return None

    def get_file_content(self, file_path: str, branch: str = 'master') -> str:
        """Récupère le contenu d'un fichier"""
        url = f'{self.base_url}/contents/{file_path}?ref={branch}'
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            content = response.json().get('content', '')
            if content:
                import base64
                return base64.b64decode(content).decode('utf-8')
        return ''

    def format_version_info(self, version: Union[float, List[float]]) -> Dict[str, Any]:
        """Formate les informations de version pour la sauvegarde"""
        if isinstance(version, list):
            return {
                'latest_version': max(version),
                'all_versions': version,
                'is_multi_version': True,
                'last_updated': datetime.now().isoformat()
            }
        else:
            return {
                'version': version,
                'is_multi_version': False,
                'last_updated': datetime.now().isoformat()
            }

    def scan_nodes(self, branch: str = 'master') -> Dict:
        """Scanne tous les fichiers nodes et extrait leurs versions"""
        print(f"Démarrage du scan à {datetime.now()} sur la branche {branch}")
        results = {}
        files = self.get_node_files(branch)

        for file in files:
            file_path = file['path']
            content = self.get_file_content(file_path, branch)
            version = self.extract_version(content)

            if version is not None:
                # Extraire le nom du node du chemin
                node_name = os.path.basename(file_path).replace('.node.ts', '')

                results[node_name] = {
                    'path': file_path,
                    'version_info': self.format_version_info(version)
                }

                print(f"Node traité: {node_name}")
                print(f"  Chemin: {file_path}")
                print(f"  Version: {version}")
                print("---")

        # Sauvegarde des résultats
        self.save_results(results)
        return results

    def save_results(self, results: Dict):
        """Sauvegarde les résultats dans un fichier JSON"""
        # Charger les résultats existants s'ils existent
        existing_results = {}
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                existing_results = json.load(f)

        # Comparer et noter les changements
        changes = []
        for node_name, new_info in results.items():
            if node_name in existing_results:
                old_version = existing_results[node_name]['version_info']
                new_version = new_info['version_info']
                if old_version != new_version:
                    changes.append({
                        'node': node_name,
                        'old_version': old_version,
                        'new_version': new_version,
                        'timestamp': datetime.now().isoformat()
                    })

        # Sauvegarder les nouveaux résultats
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Sauvegarder l'historique des changements
        if changes:
            with open('version_changes.json', 'a') as f:
                for change in changes:
                    f.write(json.dumps(change) + '\n')
                    print(f"Changement détecté pour {change['node']}")

        print(f"Résultats sauvegardés dans {self.results_file}")

    def schedule_weekly_scan(self):
        """Programme un scan hebdomadaire"""
        schedule.every().monday.at("00:00").do(self.scan_nodes)

        while True:
            schedule.run_pending()
            time.sleep(3600)  # Vérifie toutes les heures

def main():
    # Configuration
    config = Config()
    GITHUB_TOKEN = config.github_token
    REPO_OWNER = config.repo_owner
    REPO_NAME = config.repo_name

    # Initialisation et exécution
    scanner = N8nNodeScanner(
        github_token=GITHUB_TOKEN,
        repo_owner=REPO_OWNER,
        repo_name=REPO_NAME
    )

    # Premier scan
    scanner.scan_nodes()

    # Démarrage du planning hebdomadaire
    scanner.schedule_weekly_scan()

# Exemple d'utilisation
if __name__ == "__main__":
    config = Config()
    scanner = N8nNodeScanner(config)