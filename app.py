import asyncio
from pyrogram import Client
from loguru import logger
import random
import json
import os
from pathlib import Path
from pyrogram.errors import SessionPasswordNeeded

# Добавляем определение ROOT_DIR
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# API credentials
api_id = 20902632
api_hash = "9a1d8b31c0041f760ef748910c793f16"

# Списки устройств и версий систем
device_model = [
    # Apple devices
    'iPhone 14 Pro Max', 'iPhone 14 Pro', 'iPhone 14 Plus', 'iPhone 14',
    'iPhone 13 Pro Max', 'iPhone 13 Pro', 'iPhone 13', 'iPhone 13 mini',
    'iPhone 12 Pro Max', 'iPhone 12 Pro', 'iPhone 12', 'iPhone 12 mini',
    'iPhone SE (3rd generation)', 'iPhone 11 Pro Max', 'iPhone 11 Pro',
    
    # Samsung devices
    'Galaxy S23 Ultra', 'Galaxy S23+', 'Galaxy S23',
    'Galaxy Z Fold4', 'Galaxy Z Flip4',
    'Galaxy A54', 'Galaxy A53', 'Galaxy A34', 'Galaxy A33',
    'Galaxy M54', 'Galaxy M53', 'Galaxy M34', 'Galaxy M33',
    
    # Other devices...
]

system_version = [
    'Windows 11', 'Windows 10', 'Windows 8.1',
    'macOS 13 Ventura', 'macOS 12 Monterey', 'macOS 11 Big Sur',
    'Ubuntu 22.04 LTS', 'Debian 11', 'Fedora 37',
    'Android 13', 'Android 12', 'Android 11',
    'iOS 16.5', 'iOS 16.4', 'iOS 16.3', 'iOS 15.7'
]

def get_random_device_model_and_system_version():
    device = random.choice(device_model)
    
    if 'iPhone' in device or 'iPad' in device or 'Mac' in device:
        system = random.choice([s for s in system_version if 'iOS' in s or 'macOS' in s])
    elif any(brand in device for brand in ['Galaxy', 'Pixel', 'Mi', 'Redmi', 'POCO', 'Huawei']):
        system = random.choice([s for s in system_version if 'Android' in s])
    else:
        system = random.choice([s for s in system_version if 'Windows' in s])
    
    return device, system

def parse_proxy_url(proxy_url):
    """Parse proxy URL into Pyrogram proxy dict format"""
    if not proxy_url:
        return None
        
    try:
        scheme = proxy_url.split('://')[0]
        auth_host = proxy_url.split('://')[1]
        
        if '@' in auth_host:
            auth, host = auth_host.split('@')
            username, password = auth.split(':')
            hostname, port = host.split(':')
        else:
            hostname, port = auth_host.split(':')
            username = password = None
        
        proxy = {
            "scheme": scheme,
            "hostname": hostname,
            "port": int(port)
        }
        
        if username and password:
            proxy["username"] = username
            proxy["password"] = password
            
        return proxy
    except Exception as e:
        logger.error(f"Ошибка при парсинге прокси URL: {e}")
        return None

async def auth_account(data):
    """Start account authorization process"""
    try:
        phone_number = data['phoneNumber']
        session_path = os.path.join(data['save_path'], phone_number)
        
        device, system = get_random_device_model_and_system_version()
        proxy_dict = parse_proxy_url(data.get('proxyUrl', ''))
        
        client = Client(
            session_name=session_path,
            api_id=api_id,
            api_hash=api_hash,
            device_model=device,
            system_version=system,
            proxy=proxy_dict
        )

        # Connect and send code
        await client.connect()
        sent_code = await client.send_code(phone_number)
        
        # НЕ закрываем соединение здесь!
        # await client.disconnect()

        # Save config
        group_path = os.path.join(ROOT_DIR, 'accounts', data['groupName'], data.get('accountType', 'free_accs'))
        os.makedirs(group_path, exist_ok=True)
        
        config_path = os.path.join(group_path, f"{phone_number}.json")

        # Create account config
        account_config = {
            "account_name": data.get('accountName', phone_number),
            "app_id": api_id,
            "app_hash": api_hash,
            "device": device,
            "sdk": system,
            "app_version": "5.4.1 x64",
            "phone": phone_number,
            "session_file": session_path,
            "proxy": parse_proxy_url(data.get('proxyUrl')),
            "status": "new",
            "group_name": data['groupName'],
            "account_type": data.get('accountType', 'free_accs')
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(account_config, f, indent=4, ensure_ascii=False)

        return {
            'success': True,
            'needCode': True,
            'phoneHash': sent_code.phone_code_hash,
            'config': account_config,
            'client': client  # Передаем клиент для использования в complete_auth
        }

    except Exception as e:
        logger.error(f"Ошибка в auth_account: {e}")
        return {'success': False, 'error': str(e)}

async def complete_auth(data):
    """Complete account authorization with received code"""
    try:
        phone_number = data['phoneNumber']
        password = data['password']
        client = data['client']
        
        try:
            # Сначала пробуем войти с кодом
            await client.sign_in(
                phone_number=phone_number,
                phone_code_hash=data['phoneHash'],
                phone_code=data['code']
            )
        except SessionPasswordNeeded:
            # Если требуется пароль двухфакторной аутентификации
            logger.info("Требуется пароль двухфакторной аутентификации")
            await client.check_password(password)
        except Exception as e:
            logger.error(f"Ошибка при входе: {e}")
            raise
        finally:
            await client.disconnect()

        # Update config
        group_path = os.path.join(ROOT_DIR, 'accounts', data['groupName'], data.get('accountType', 'free_accs'))
        config_path = os.path.join(group_path, f"{phone_number}.json")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            account_config = json.load(f)
            
        account_config['status'] = 'active'
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(account_config, f, indent=4, ensure_ascii=False)

        return {'success': True, 'message': 'Аккаунт успешно авторизован'}

    except Exception as e:
        logger.error(f"Ошибка в complete_auth: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    logger.add("app.log", rotation="500 MB")