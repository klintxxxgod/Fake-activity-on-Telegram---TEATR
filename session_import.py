import os
import shutil
import json
from loguru import logger
import random
from pathlib import Path

class SessionImporter:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
    async def import_session(self, data):
        """
        Импортирует session файл и обновляет JSON конфиг
        """
        try:
            session_file = data['sessionFile']
            json_file = data['jsonFile']
            
            # Читаем JSON конфиг
            json_data = json.loads(json_file.read().decode('utf-8'))
            
            # Добавляем пользовательские данные в конфиг
            json_data.update({
                "account_name": data['accountName'],
                "proxy": data.get('proxyUrl') or json_data.get('proxy'),
                "group_name": data['groupName'],
                "account_type": data['accountType'],
                "status": "active"
            })
            
            # Создаем путь для сохранения
            group_path = os.path.join(self.root_dir, 'accounts', data['groupName'], data['accountType'])
            os.makedirs(group_path, exist_ok=True)
            
            # Сохраняем session файл
            session_path = os.path.join(group_path, session_file.filename)
            with open(session_path, 'wb') as f:
                f.write(session_file.read())
            
            # Сохраняем обновленный JSON
            json_path = os.path.join(group_path, os.path.splitext(session_file.filename)[0] + '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            
            return {
                'success': True,
                'message': f'Аккаунт успешно импортирован в группу {data["groupName"]}'
            }
            
        except Exception as e:
            logger.error(f"Ошибка при импорте session: {e}")
            return {'success': False, 'error': str(e)} 