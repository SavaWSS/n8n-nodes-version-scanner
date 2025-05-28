# version_comparator.py

Скрипт для анализа версий нод в n8n воркфлоу.

## Описание

Скрипт анализирует версии нод в n8n воркфлоу, сравнивая их с последними доступными версиями. Результаты анализа сохраняются в JSON-файл и выводятся на экран.

## Функциональность

- Загрузка и анализ JSON-файлов с данными о нодах и их версиях.
- Сравнение текущих версий нод с последними доступными версиями.
- Группировка результатов по имени воркфлоу.
- Вывод результатов на экран и сохранение в JSON-файл.

## Использование

1. Убедитесь, что у вас есть файлы `nodes-in-use.json` и `node_versions.json`.
2. Запустите скрипт с помощью команды:
   ```bash
   python3 version_comparator.py
   ```
3. Результаты анализа будут выведены на экран и сохранены в файл `results.json`.

## Получение данных для nodes-in-use.json

Данные для файла `nodes-in-use.json` можно получить с помощью ноды n8n node version 1 (Latest). Пример конфигурации ноды:

```json
{
  "nodes": [
    {
      "parameters": {
        "returnAll": false,
        "limit": 10,
        "filters": {},
        "requestOptions": {}
      },
      "type": "n8n-nodes-base.n8n",
      "typeVersion": 1,
      "position": [
        220,
        0
      ],
      "id": "27315590-60a8-4ec9-ba54-a6a88e92d37a",
      "name": "n8n",
      "credentials": {
        "n8nApi": {
          "id": "a15hxev5jQWgcOgl",
          "name": "n8n account"
        }
      }
    }
  ],
  "connections": {
    "n8n": {
      "main": [
        []
      ]
    }
  },
  "pinData": {},
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "9230f0b0e9c27677fa7e8fd7f833e5122f81810548e220706ae06f9cbbf9d39a"
  }
}
```

## Формат вывода

Результаты анализа выводятся в следующем формате:

```
Результаты анализа по воркфлоу:
====================================================================================================

Воркфлоу: Имя_воркфлоу
----------------------------------------------------------------------------------------------------
Нода                            Текущая версия  Последняя версия Имя ноды                        Match     
----------------------------------------------------------------------------------------------------
node_type                       1.0            2.0             Node Name                        True      
node_type_full                  0.0            0.0             Node Name                        False     
```

## JSON-формат

Результаты сохраняются в файл `results.json` в следующем формате:

```json
{
    "workflow": {
        "workflow_name": [
            {
                "node_type": "node_type",
                "current_version": 1.0,
                "latest_version": 2.0,
                "node_name": "Node Name",
                "match": true
            },
            {
                "node_type": "node_type_full",
                "current_version": 0.0,
                "latest_version": 0.0,
                "node_name": "Node Name",
                "match": false
            }
        ]
    }
}
```

## Требования

- Python 3.6 или выше
- Файлы `nodes-in-use.json` и `node_versions.json`

## Лицензия

MIT 