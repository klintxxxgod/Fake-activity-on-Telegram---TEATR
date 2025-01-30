from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from file_operations import FileOperations
import os
import json
from account_manager import AccountManager
import subprocess
import sys
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
file_ops = FileOperations()
account_manager = AccountManager()

# Путь к папке со сценариями
SCENARIOS_DIR = 'scenariyes'

# Маршруты для статических файлов
@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Маршруты для групп
@app.route('/create_group', methods=['POST'])
def create_group():
    data = request.json
    success = file_ops.create_group(data['name'])
    return jsonify({'success': success})

@app.route('/get_groups', methods=['GET'])
def get_groups():
    groups = file_ops.get_groups()
    return jsonify(groups)

@app.route('/delete_group', methods=['POST'])
def delete_group():
    data = request.json
    success = file_ops.delete_group(data['name'])
    return jsonify({'success': success})

@app.route('/clean_dead_accounts', methods=['POST'])
def clean_dead_accounts():
    data = request.json
    success = file_ops.clean_dead_accounts(data['name'])
    return jsonify({'success': success})

@app.route('/wake_sleeping_accounts', methods=['POST'])
def wake_sleeping_accounts():
    data = request.json
    success = file_ops.wake_sleeping_accounts(data['name'])
    return jsonify({'success': success})

# Маршруты для сценариев
@app.route('/get_scenarios', methods=['GET'])
def get_scenarios_list():
    try:
        if not os.path.exists(SCENARIOS_DIR):
            os.makedirs(SCENARIOS_DIR)
            
        scenarios = []
        for filename in os.listdir(SCENARIOS_DIR):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(SCENARIOS_DIR, filename), 'r', encoding='utf-8') as f:
                        scenario_data = json.load(f)
                        scenarios.append({
                            'name': scenario_data.get('name', filename[:-5]),
                            'actions': scenario_data.get('actions', [])
                        })
                except Exception as e:
                    print(f"Ошибка при чтении файла {filename}: {e}")
                    continue
        
        return jsonify(scenarios)
    except Exception as e:
        print(f"Ошибка при получении списка сценариев: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/scenariyes/<name>', methods=['GET'])
def get_scenario(name):
    try:
        file_path = os.path.join(SCENARIOS_DIR, f"{name}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({'error': 'Сценарий не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scenariyes/<name>', methods=['DELETE'])
def delete_scenario(name):
    try:
        file_path = os.path.join(SCENARIOS_DIR, f"{name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True})
        return jsonify({'error': 'Сценарий не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload_account_files', methods=['POST'])
def upload_account_files():
    try:
        session_file = request.files['sessionFile']
        json_file = request.files['jsonFile']
        account_name = request.form['accountName']
        proxy_url = request.form['proxyUrl']
        account_type = request.form['accountType']
        group_name = request.form['groupName']

        # Создаем директории если их нет
        account_dir = os.path.join('accounts', account_type)
        os.makedirs(account_dir, exist_ok=True)

        # Сохраняем session файл
        session_path = os.path.join(account_dir, f"{account_name}.session")
        session_file.save(session_path)

        # Читаем и обновляем JSON конфиг
        json_config = json.loads(json_file.read().decode('utf-8'))
        json_config['name'] = account_name
        json_config['proxy'] = parse_proxy_url(proxy_url)

        # Сохраняем обновленный JSON
        config_path = os.path.join(account_dir, f"{account_name}.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(json_config, f, indent=4, ensure_ascii=False)

        # Добавляем аккаунт в группу
        add_account_to_group(group_name, account_name)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/start_script', methods=['POST'])
def start_script():
    logger.info('Получен запрос на запуск скрипта')
    try:
        # Получаем путь к скрипту
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'spam_po_scenariyu.py')
        logger.debug(f'Путь к скрипту: {script_path}')
        
        # Формируем команду для PowerShell
        powershell_command = f'''
        Start-Process powershell -ArgumentList "-NoExit","-Command",
        "cd '{os.path.dirname(script_path)}'; python spam_po_scenariyu.py"
        '''
        logger.debug(f'Команда PowerShell: {powershell_command}')
        
        # Запускаем PowerShell с нашим скриптом
        process = subprocess.Popen(
            ['powershell', '-Command', powershell_command], 
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        logger.info(f'Скрипт запущен, PID: {process.pid}')
        
        response = {
            'success': True,
            'message': 'Скрипт успешно запущен',
            'timestamp': datetime.now().isoformat(),
            'pid': process.pid
        }
        logger.info('Отправка успешного ответа')
        return jsonify(response)
        
    except Exception as e:
        error_msg = f"Ошибка при запуске скрипта: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())
    logger.debug('URL: %s', request.url)
    logger.debug('Method: %s', request.method)

@app.after_request
def log_response_info(response):
    logger.debug('Response Status: %s', response.status)
    logger.debug('Response Headers: %s', response.headers)
    return response

if __name__ == '__main__':
    logger.info('Запуск сервера Flask')
    if not os.path.exists(SCENARIOS_DIR):
        os.makedirs(SCENARIOS_DIR)
    app.run(port=8000, debug=True) 