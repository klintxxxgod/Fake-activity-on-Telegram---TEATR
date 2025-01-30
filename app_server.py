from quart import Quart, request, jsonify
from quart_cors import cors
import sys
import os
from loguru import logger
from session_import import SessionImporter

# Изменяем путь для импорта app.py
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)  # Добавляем корневую директорию в путь
from app import auth_account, complete_auth

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Разрешаем запросы с любого источника

# Словарь для хранения активных клиентов
active_clients = {}

session_importer = SessionImporter()

def ensure_group_structure(group_name):
    """Создает структуру папок для группы если она не существует"""
    base_path = os.path.join(ROOT_DIR, 'accounts', group_name)
    account_types = ['free_accs', 'admin_acc', 'actors_accs', 'sleep_accs']
    
    for acc_type in account_types:
        full_path = os.path.join(base_path, acc_type)
        os.makedirs(full_path, exist_ok=True)
    
    return base_path

def get_account_path(group_name, account_type):
    """Формирует путь для сохранения файлов аккаунта"""
    type_to_folder = {
        'admin': 'admin_acc',
        'actor': 'actors_accs',
        'free': 'free_accs',
        'sleep': 'sleep_accs'
    }
    
    folder_name = type_to_folder.get(account_type, 'free_accs')
    return os.path.join(ROOT_DIR, 'accounts', group_name, folder_name)

@app.route('/auth_account', methods=['POST'])
async def start_auth():
    try:
        data = await request.get_json()
        logger.info(f"Получены данные для авторизации: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'})
            
        required_fields = ['accountName', 'phoneNumber', 'accountType', 'groupName']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            })

        # Формируем путь для сохранения
        save_path = get_account_path(data['groupName'], data['accountType'])
        os.makedirs(save_path, exist_ok=True)
        
        # Добавляем путь к данным для сохранения
        data['save_path'] = save_path
        
        # Запускаем авторизацию
        auth_result = await auth_account(data)
        
        if auth_result.get('success') and auth_result.get('client'):
            # Сохраняем клиент в словаре
            phone_number = data['phoneNumber']
            active_clients[phone_number] = auth_result.pop('client')
            
        return jsonify(auth_result)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/complete_auth', methods=['POST'])
async def finish_auth():
    try:
        data = await request.get_json()
        logger.info(f"Получены данные для завершения авторизации: {data}")
        
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'})
        
        # Получаем сохраненный клиент
        phone_number = data['phoneNumber']
        client = active_clients.get(phone_number)
        
        if not client:
            return jsonify({'success': False, 'error': 'Session expired'})
            
        # Добавляем клиент к данным
        data['client'] = client
        
        result = await complete_auth(data)
        
        # Удаляем клиент после использования
        if phone_number in active_clients:
            del active_clients[phone_number]
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка при завершении авторизации: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_groups', methods=['GET'])
async def get_groups():
    try:
        groups_path = os.path.join(ROOT_DIR, 'accounts')
        if not os.path.exists(groups_path):
            return jsonify([])
            
        groups = []
        for group_name in os.listdir(groups_path):
            group_path = os.path.join(groups_path, group_name)
            if os.path.isdir(group_path):
                groups.append({
                    'name': group_name,
                    'actors': len(os.listdir(os.path.join(group_path, 'actors_accs'))),
                    'sleep': len(os.listdir(os.path.join(group_path, 'sleep_accs'))),
                    'dead': 0,  # Можно добавить папку для мертвых аккаунтов если нужно
                    'free': len(os.listdir(os.path.join(group_path, 'free_accs')))
                })
        
        return jsonify(groups)
        
    except Exception as e:
        logger.error(f"Ошибка при получении групп: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/import_session', methods=['POST', 'OPTIONS'])
async def import_session():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        logger.info("Получен запрос на импорт session")
        files = await request.files
        form = await request.form
        
        logger.info(f"Полученные файлы: {files.keys()}")
        logger.info(f"Полученные данные формы: {form}")
        
        if 'sessionFile' not in files or 'jsonFile' not in files:
            return jsonify({'success': False, 'error': 'Не все файлы были предоставлены'})
            
        if 'accountName' not in form or 'accountType' not in form:
            return jsonify({'success': False, 'error': 'Не все поля формы были заполнены'})
        
        data = {
            'sessionFile': files['sessionFile'],
            'jsonFile': files['jsonFile'],
            'accountName': form['accountName'],
            'proxyUrl': form.get('proxyUrl'),
            'groupName': form.get('groupName'),
            'accountType': form['accountType']
        }
        
        result = await session_importer.import_session(data)
        logger.info(f"Результат импорта: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Ошибка при импорте session: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/count_accounts', methods=['GET'])
async def count_accounts():
    try:
        total_count = 0
        # Изменяем путь к папке accounts
        accounts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'accounts')
        
        if not os.path.exists(accounts_dir):
            return jsonify({
                'success': True,
                'count': 0
            })

        # Рекурсивно обходим все подпапки групп и типов аккаунтов
        for group in os.listdir(accounts_dir):
            group_path = os.path.join(accounts_dir, group)
            if os.path.isdir(group_path):
                for acc_type in os.listdir(group_path):
                    type_path = os.path.join(group_path, acc_type)
                    if os.path.isdir(type_path):
                        session_files = [f for f in os.listdir(type_path) if f.endswith('.session')]
                        total_count += len(session_files)
        
        logger.info(f"Найдено {total_count} session файлов")
        return jsonify({
            'success': True,
            'count': total_count
        })
    except Exception as e:
        logger.error(f"Ошибка при подсчете аккаунтов: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/upload-media', methods=['POST', 'OPTIONS'])
async def upload_media():
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        logger.info("Получен запрос на загрузку медиафайла")
        files = await request.files
        
        if 'media' not in files:
            return jsonify({'success': False, 'error': 'Медиафайл не найден в запросе'})
            
        media_file = files['media']
        
        # Создаем папку media в корневой директории проекта
        media_dir = os.path.join(ROOT_DIR, 'media')
        os.makedirs(media_dir, exist_ok=True)
        
        # Сохраняем файл
        filename = media_file.filename
        file_path = os.path.join(media_dir, filename)
        
        # Проверяем расширение файла
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov'}
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            return jsonify({
                'success': False, 
                'error': 'Неподдерживаемый формат файла'
            })
        
        await media_file.save(file_path)
        
        logger.info(f"Медиафайл сохранен: {file_path}")
        return jsonify({
            'success': True,
            'path': f'media/{filename}'  # Обновленный путь относительно корня проекта
        })
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке медиафайла: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    logger.add("server.log", rotation="500 MB")
    app.run(port=5000, debug=True) 