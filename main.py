import requests
import os
import re
# import schedule
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
            raise FileNotFoundError(f"Файл конфигурации {self.config_file} не существует")

    @property
    def github_token(self) -> str:
        return self.config.get('github_token')

class N8nNodeScanner:
    N8N_REPO_OWNER = "n8n-io"
    N8N_REPO_NAME = "n8n"

    def __init__(self, github_token: str):
        """
        Инициализирует сканер узлов для официального репозитория n8n

        Args:
            github_token (str): Токен аутентификации GitHub
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
        """Получает все файлы .node.ts из репозитория"""
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
        Извлекает version или defaultVersion из файла
        Обрабатывает как уникальные версии, так и массивы версий
        """
        # Поиск defaultVersion
        default_version_match = re.search(r'defaultVersion:\s*([\d.]+)', content)
        if default_version_match:
            return float(default_version_match.group(1))

        # Поиск version в формате массива
        version_array_match = re.search(r'version:\s*\[([\d.,\s]+)\]', content)
        if version_array_match:
            versions_str = version_array_match.group(1)
            try:
                versions = [float(v.strip()) for v in versions_str.split(',')]
                return versions
            except ValueError:
                pass

        # Поиск простой version
        version_match = re.search(r'version:\s*([\d.]+)', content)
        if version_match:
            return float(version_match.group(1))

        return None

    def extract_name(self, content: str) -> str:
        """Извлекает имя узла из содержимого"""
        name_match = re.search(r'name:\s*[\'"](.+)[\'"]', content)
        if name_match:
            return name_match.group(1)
        return ''

    def get_file_content(self, file_path: str, branch: str = 'master') -> str:
        """Получает содержимое файла"""
        url = f'{self.base_url}/contents/{file_path}?ref={branch}'
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            content = response.json().get('content', '')
            if content:
                import base64
                return base64.b64decode(content).decode('utf-8')
        return ''

    def format_version_info(self, version: Union[float, List[float]]) -> Dict[str, Any]:
        """Форматирует информацию о версии для сохранения"""
        if isinstance(version, list):
            return {
                'latest_version': max(version),
                'all_versions': version,
                'is_multi_version': True,
                'last_updated': datetime.now().isoformat()
            }
        else:
            return {
                'latest_version': version,
                'all_versions': [version],
                'is_multi_version': False,
                'last_updated': datetime.now().isoformat()
            }

    def scan_nodes(self, branch: str = 'master') -> Dict:
        """Сканирует все файлы узлов и извлекает их версии"""
        print(f"Начало сканирования в {datetime.now()} на ветке {branch}")
        results = {}
        files = self.get_node_files(branch)

        for file in files:
            file_path = file['path']
            content = self.get_file_content(file_path, branch)
            version = self.extract_version(content)
            name = self.extract_name(content)

            if name and version is not None:
                # Извлечение имени узла из пути
                node_name = os.path.basename(file_path).replace('.node.ts', '')

                results[name] = {
                    'path': file_path,
                    'name': node_name,
                    'version_info': self.format_version_info(version)
                }

                print(f"Обработанный узел: {name}")
                print(f"  Путь: {file_path}")
                print(f"  Имя: {node_name}")
                print(f"  Версия: {version}")
                print("---")

        # Сохранение результатов
        self.save_results(results)
        return results

    def save_results(self, results: Dict):
        """Сохраняет результаты в файл JSON"""
        # Загружает существующие результаты, если они есть
        existing_results = {}
        if os.path.exists(self.results_file):
            with open(self.results_file, 'r') as f:
                existing_results = json.load(f)

        # Сравнивает и фиксирует изменения
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

        # Сохраняет новые результаты
        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Сохраняет историю изменений
        if changes:
            with open('version_changes.json', 'a') as f:
                for change in changes:
                    f.write(json.dumps(change) + '\n')
                    print(f"Обнаружено изменение для {change['node']}")

        print(f"Результаты сохранены в {self.results_file}")

    def schedule_weekly_scan(self):
        """Запланировать еженедельное сканирование"""
        schedule.every().monday.at("00:00").do(self.scan_nodes)

        while True:
            schedule.run_pending()
            time.sleep(3600)  # Проверяет каждый час

def main():
    # Конфигурация
    config = Config()
    GITHUB_TOKEN = config.github_token

    # Инициализация и выполнение
    scanner = N8nNodeScanner(
        github_token=GITHUB_TOKEN
    )

    # Первое сканирование
    scanner.scan_nodes()

    # Запуск еженедельного планирования
    # scanner.schedule_weekly_scan()

# Пример использования
if __name__ == "__main__":
    main()