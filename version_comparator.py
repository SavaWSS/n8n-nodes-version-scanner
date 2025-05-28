import json
from datetime import datetime
from typing import Dict, List, Tuple

DEBUG = False  # Включить/выключить отладочный вывод

def load_json_file(file_path: str) -> dict:
    """Загрузка JSON файла"""
    try:
        if DEBUG:
            print(f"Попытка загрузить файл: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if DEBUG:
                print(f"Файл {file_path} успешно загружен")
            return data
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден")
        return {}
    except json.JSONDecodeError as e:
        print(f"Ошибка: Файл {file_path} содержит некорректный JSON: {str(e)}")
        return {}
    except Exception as e:
        print(f"Неожиданная ошибка при загрузке файла {file_path}: {str(e)}")
        return {}

def extract_node_name(type_field: str) -> str:
    """Извлекает имя ноды после 'n8n-nodes-base.'"""
    if type_field and 'n8n-nodes-base.' in type_field:
        return type_field.split('n8n-nodes-base.')[-1]
    return type_field

def compare_versions(current_version: float, latest_version: float) -> bool:
    """Сравнение версий"""
    return current_version < latest_version

def get_version_info(node_data: dict) -> float:
    """Получение последней версии из данных ноды"""
    try:
        version_info = node_data.get('version_info', {})
        latest_version = version_info.get('latest_version', 0.0)
        if DEBUG:
            print(f"    Извлечена последняя версия: {latest_version}")
        return latest_version
    except Exception as e:
        print(f"    Ошибка при извлечении версии: {str(e)}")
        return 0.0

def analyze_workflows(nodes_in_use: list, node_versions: dict):
    """Анализ воркфловов и поиск устаревших нод и нод без соответствия"""
    outdated_nodes = []
    unmatched_nodes = []  # Для хранения нод без соответствия
    if DEBUG:
        print(f"Всего воркфлоу: {len(nodes_in_use)}")
        print(f"Всего нод в node_versions: {len(node_versions)}")
    
    for workflow in nodes_in_use:
        workflow_name = workflow.get('name', 'Unknown Workflow')
        nodes = workflow.get('nodes', [])
        if DEBUG:
            print(f"\nВоркфлоу: {workflow_name}, количество нод: {len(nodes)}")
        
        for node in nodes:
            try:
                node_type_full = node.get('type', '')
                node_type = extract_node_name(node_type_full)
                current_version = float(node.get('typeVersion', 0.0))
                node_name = node.get('name', 'Unknown Node')  # Получаем имя ноды из поля 'name'
                
                if DEBUG:
                    print(f"  Обрабатывается нода: type='{node_type_full}', извлечённое имя='{node_type}', текущая версия={current_version}, имя='{node_name}'")
                
                if node_type in node_versions:
                    latest_version = get_version_info(node_versions[node_type])
                    if DEBUG:
                        print(f"    Найдена в node_versions.json: последняя версия={latest_version}")
                    
                    if compare_versions(current_version, latest_version):
                        if DEBUG:
                            print(f"    >>> Устаревшая нода!")
                        outdated_nodes.append((
                            workflow_name,
                            node_type,
                            current_version,
                            latest_version,
                            node_name  # Добавляем имя ноды в результат
                        ))
                    else:
                        if DEBUG:
                            print(f"    Версия актуальна.")
                else:
                    if DEBUG:
                        print(f"    Не найдена в node_versions.json!")
                    unmatched_nodes.append((workflow_name, node_type_full, current_version, node_name))  # Добавляем имя ноды в unmatched_nodes
            except Exception as e:
                print(f"    Ошибка при обработке ноды: {str(e)}")
                continue
    
    return outdated_nodes, unmatched_nodes

def save_results_to_json(outdated_nodes, unmatched_nodes, output_file='results.json'):
    """Сохранение результатов в JSON-файл с группировкой по имени воркфлоу"""
    # Группировка outdated_nodes по имени воркфлоу
    outdated_by_workflow = {}
    for workflow_name, node_type, current_version, latest_version, node_name in outdated_nodes:
        if workflow_name not in outdated_by_workflow:
            outdated_by_workflow[workflow_name] = []
        outdated_by_workflow[workflow_name].append({
            'node_type': node_type,
            'current_version': current_version,
            'latest_version': latest_version,
            'node_name': node_name,
            'match': True  # Добавляем поле match для определённых нод
        })
    
    # Группировка unmatched_nodes по имени воркфлоу
    unmatched_by_workflow = {}
    for workflow_name, node_type_full, current_version, node_name in unmatched_nodes:
        if workflow_name not in unmatched_by_workflow:
            unmatched_by_workflow[workflow_name] = []
        unmatched_by_workflow[workflow_name].append({
            'node_type': node_type_full,  # Используем node_type_full как node_type
            'current_version': 0.0,  # Устанавливаем значение 0.0 для unmatched_nodes
            'latest_version': 0.0,  # Устанавливаем значение 0.0 для latest_version
            'node_name': node_name,
            'match': False  # Добавляем поле match для неопределённых нод
        })
    
    # Объединение результатов
    results = {
        'workflow': {
            workflow_name: outdated_by_workflow.get(workflow_name, []) + unmatched_by_workflow.get(workflow_name, [])
            for workflow_name in set(outdated_by_workflow.keys()) | set(unmatched_by_workflow.keys())
        }
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"Результаты сохранены в {output_file}")

def main():
    try:
        # Загрузка файлов
        if DEBUG:
            print("Начало работы скрипта")
        nodes_in_use = load_json_file('nodes-in-use.json')
        node_versions = load_json_file('node_versions.json')
        
        if not nodes_in_use:
            print("Ошибка: файл nodes-in-use.json пуст или не загружен")
            return
        if not node_versions:
            print("Ошибка: файл node_versions.json пуст или не загружен")
            return
        
        # Анализ воркфловов
        outdated_nodes, unmatched_nodes = analyze_workflows(nodes_in_use, node_versions)
        
        # Группировка результатов по имени воркфлоу
        workflow_results = {}
        for workflow_name, node_type, current_version, latest_version, node_name in outdated_nodes:
            if workflow_name not in workflow_results:
                workflow_results[workflow_name] = []
            workflow_results[workflow_name].append({
                'node_type': node_type,
                'current_version': current_version,
                'latest_version': latest_version,
                'node_name': node_name,
                'match': True
            })
        
        for workflow_name, node_type_full, current_version, node_name in unmatched_nodes:
            if workflow_name not in workflow_results:
                workflow_results[workflow_name] = []
            workflow_results[workflow_name].append({
                'node_type': node_type_full,
                'current_version': 0.0,
                'latest_version': 0.0,
                'node_name': node_name,
                'match': False
            })
        
        # Вывод результатов по воркфлоу
        print("\nРезультаты анализа по воркфлоу:")
        print("=" * 100)
        for workflow_name, nodes in workflow_results.items():
            print(f"\nВоркфлоу: {workflow_name}")
            print("-" * 100)
            print(f"{'Нода':<30} {'Текущая версия':<15} {'Последняя версия':<15} {'Имя ноды':<30} {'Match':<10}")
            print("-" * 100)
            for node in nodes:
                print(f"{node['node_type']:<30} {node['current_version']:<15} {node['latest_version']:<15} {node['node_name']:<30} {node['match']:<10}")
        
        # Сохранение результатов в JSON
        save_results_to_json(outdated_nodes, unmatched_nodes)
    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")

if __name__ == "__main__":
    main() 