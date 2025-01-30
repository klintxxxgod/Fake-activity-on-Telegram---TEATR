from pyrogram import Client
import asyncio
import json
import random
from typing import Dict, List, Optional
import yaml
import logging
from datetime import datetime
import time
import os
import inquirer  # добавьте: pip install inquirer
import shutil
import colorama
from colorama import Fore, Back, Style

class TelegramSpammer:
    def __init__(self):
        """Инициализация спаммера"""
        colorama.init()
        self._setup_logging()
        self._clear_console()
        self.print_banner()
        self.logger = logging.getLogger('TelegramSpammer')
        self.accounts = {}
        self.admin_client = None
        self.scenario = None
        self.chat_id = None
        self.chat_info = None
        self.root_path = self._get_root_path()
        self.selected_folder = None
        self.settings = self._load_settings()
        self.start_time = datetime.now()
        self.role_mapping = {}  # Добавляем маппинг ролей
        self.first_cycle = True  # Добавляем флаг первого цикла
        self.old_messages = {}  # Словарь для хранения сообщений предыдущего цикла
        self.current_messages = {}  # Словарь для хранения сообщений текущего цикла

    async def setup(self):
        """Настройка спаммера"""
        self.logger.info(f"\n{Fore.CYAN}Начало настройки спаммера...{Style.RESET_ALL}")
        
        # Выбор режима работы с циклами
        cleanup_modes = {
            "1": "instant",
            "2": "none",
            "3": "gradual"
        }
        
        self.logger.info(f"\n{Fore.YELLOW}Выберите режим работы с циклами:{Style.RESET_ALL}")
        self.logger.info(f"1. Мгновенное удаление старых сообщений при начале нового цикла")
        self.logger.info(f"2. Без удаления сообщений")
        self.logger.info(f"3. Постепенное удаление (удаление старого сообщения при отправке нового)")
        
        while True:
            mode_choice = input(f"\n{Fore.YELLOW}Введите номер режима (1-3): {Style.RESET_ALL}")
            if mode_choice in cleanup_modes:
                self.settings['cleanup_mode'] = cleanup_modes[mode_choice]
                self.logger.info(f"{Fore.GREEN}✓ Выбран режим: {mode_choice}{Style.RESET_ALL}")
                break
            else:
                self.logger.error(f"{Fore.RED}Неверный выбор. Пожалуйста, выберите 1, 2 или 3{Style.RESET_ALL}")
        
        # Выбор папки с аккаунтами
        accounts_folder = self._select_account_folder()
        if not accounts_folder:
            self.logger.error(f"{Fore.RED}Не удалось выбрать папку с аккаунтами{Style.RESET_ALL}")
            return False
        self.selected_folder = accounts_folder
        
        # Загрузка админского аккаунта
        self.logger.info(f"\n{Fore.CYAN}Загрузка админского аккаунта...{Style.RESET_ALL}")
        if not await self.load_admin_account(accounts_folder):
            return False
        
        # Выбор чата и получение информации о нем
        chat_link = input(f"\n{Fore.YELLOW}Введите ссылку на чат (например, https://t.me/chat_name): {Style.RESET_ALL}")
        self.chat_id = chat_link.split('/')[-1]
        
        # Получение информации о чате через админский аккаунт
        try:
            chat = await self.admin_client.get_chat(self.chat_id)
            self.chat_info = {
                'id': chat.id,
                'title': chat.title,
                'type': chat.type,
                'identifier': self.chat_id,
                'members_count': getattr(chat, 'members_count', 0)
            }
            self.logger.info(f"{Fore.GREEN}✓ Установлен чат: {self.chat_info['title']} ({self.chat_id}){Style.RESET_ALL}")
        except Exception as e:
            self.logger.error(f"{Fore.RED}Ошибка при получении информации о чате: {str(e)}{Style.RESET_ALL}")
            return False
        
        # Загрузка аккаунтов
        self.logger.info(f"{Fore.CYAN}Загрузка аккаунтов...{Style.RESET_ALL}")
        if not await self.load_accounts(accounts_folder):
            return False
        
        # Выбор сценария
        scenario_path = self._select_scenario()
        if not scenario_path:
            self.logger.error(f"{Fore.RED}Не удалось выбрать сценарий{Style.RESET_ALL}")
            return False
        
        # Загружаем сценарий
        try:
            with open(scenario_path, 'r', encoding='utf-8') as f:
                self.scenario = json.load(f)
            if not self.scenario or 'actions' not in self.scenario:
                self.logger.error(f"{Fore.RED}Некорректный формат сценария{Style.RESET_ALL}")
                return False
        except Exception as e:
            self.logger.error(f"{Fore.RED}Ошибка при загрузке сценария: {str(e)}{Style.RESET_ALL}")
            return False
        
        self.logger.info(f"\n{Fore.GREEN}Настройка завершена:")
        self.logger.info(f"✓ Папка аккаунтов: {accounts_folder}")
        self.logger.info(f"✓ Выбран сценарий: {scenario_path}")
        self.logger.info(f"✓ Целевой чат: {self.chat_info['title']} ({self.chat_id})")
        self.logger.info(f"✓ Тип чата: {self.chat_info['type']}")
        self.logger.info(f"✓ Количество участников: {self.chat_info['members_count']}{Style.RESET_ALL}\n")
        
        return True

    def _get_root_path(self):
        """Получение корневого пути проекта"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)

    @staticmethod
    def _list_directories(path: str) -> List[str]:
        """Получение списка папок в указанном пути"""
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    
    @staticmethod
    def _list_json_files(path: str) -> List[str]:
        """Получение списка JSON файлов в указанном пути"""
        return [f for f in os.listdir(path) if f.endswith('.json')]

    def _select_account_folder(self) -> Optional[str]:
        """Выбор папки с аккаунтами через CLI"""
        accounts_path = os.path.join(self.root_path, "accounts")
        
        if not os.path.exists(accounts_path):
            self.logger.error(f"Папка accounts не найдена по пути: {accounts_path}")
            return None
            
        folders = self._list_directories(accounts_path)
        
        if not folders:
            self.logger.error("Папки с аккаунтами не найдены")
            return None
            
        questions = [
            inquirer.List('account_folder',
                         message="Выберите папку с аккаунтами",
                         choices=folders)
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return None
            
        selected_folder = answers['account_folder']
        return os.path.join(accounts_path, selected_folder)

    def _select_scenario(self) -> Optional[str]:
        """Выбор сценария через CLI"""
        root_path = self._get_root_path()
        scenarios_path = os.path.join(root_path, "scenariyes")
        
        scenarios = self._list_json_files(scenarios_path)
        
        if not scenarios:
            self.logger.error("Сценарии не найдены в scenariyes")
            return None
            
        questions = [
            inquirer.List('scenario',
                         message="Выберите сценарий",
                         choices=scenarios)
        ]
        answers = inquirer.prompt(questions)
        return os.path.join(scenarios_path, answers['scenario']) if answers else None

    def _setup_logging(self):
        """Настройка расширенного логирования"""
        # Создаем папку logs если её нет
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Имя файла лога с датой и временем
        log_filename = f"logs/spam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Форматтер для файла
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Форматтер для консоли с цветами
        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                if record.levelno >= logging.ERROR:
                    color = Fore.RED
                elif record.levelno >= logging.WARNING:
                    color = Fore.YELLOW
                elif record.levelno >= logging.INFO:
                    color = Fore.GREEN
                else:
                    color = Fore.CYAN
                
                record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
                return super().format(record)

        # Настройка логгера
        logger = logging.getLogger('TelegramSpammer')
        logger.setLevel(logging.DEBUG)
        
        # Хендлер для файла
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Хендлер для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter('%(message)s'))
        console_handler.setLevel(logging.INFO)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.logger = logger

    def print_banner(self):
        """Вывод красивого баннера"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                  Telegram Spam Script                      ║
║                    Version: 1.0.0                         ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)

    def _clear_console(self):
        """Очистка консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _load_config(self, path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _load_scenario(self, path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    async def random_delay(self, min_seconds=1, max_seconds=5):
        """Случайная задержка между действиями"""
        delay = random.uniform(min_seconds, max_seconds)
        self.logger.debug(f"Ожидание {delay:.2f} секунд")
        await asyncio.sleep(delay)

    def _select_chat_type(self) -> dict:
        """Выбор типа чата и получение идентификатора"""
        questions = [
            inquirer.List('chat_type',
                         message="Выберите тип чата",
                         choices=[
                             ('Публичный чат (username)', 'username'),
                             ('Приватный чат (invite link)', 'invite_link')
                         ])
        ]
        
        chat_type = inquirer.prompt(questions)['chat_type']
        
        chat_id_question = [
            inquirer.Text('identifier',
                         message="Введите username чата или invite link")
        ]
        
        identifier = inquirer.prompt(chat_id_question)['identifier']
        
        return {
            'type': chat_type,
            'identifier': identifier
        }

    async def join_chat(self, force_join=False) -> int:
        """Присоединение к чату"""
        if not self.chat_info:
            self.logger.error(f"{Fore.RED}Информация о чате не найдена{Style.RESET_ALL}")
            return None
        
        # Присоединяемся только если это первый цикл или force_join=True
        if not self.first_cycle and not force_join:
            return self.chat_info['id']
        
        self.logger.info(f"Начало процесса присоединения к чату: {self.chat_info['title']}")
        
        try:
            # Присоединяем админский аккаунт
            chat = await self.admin_client.join_chat(self.chat_id)
            self.logger.info(f"{Fore.GREEN}✓ Админский аккаунт успешно присоединился к чату{Style.RESET_ALL}")
            
            # Присоединяем аккаунты актеров
            for account_name, mapping_data in self.role_mapping.items():
                phone = mapping_data['phone']
                if phone in self.accounts:
                    try:
                        client = self.accounts[phone]['client']
                        await client.join_chat(self.chat_id)
                        self.logger.info(f"{Fore.GREEN}✓ Аккаунт {account_name} ({phone}) присоединился к чату{Style.RESET_ALL}")
                        await asyncio.sleep(2)
                    except Exception as e:
                        self.logger.error(f"{Fore.RED}Ошибка при присоединении аккаунта {account_name} ({phone}): {str(e)}{Style.RESET_ALL}")
            
            return chat.id
            
        except Exception as e:
            self.logger.error(f"{Fore.RED}Ошибка при присоединении к чату: {str(e)}{Style.RESET_ALL}")
            return None

    async def _generate_and_set_username(self, client) -> str:
        """Генерация и установка username для аккаунта"""
        try:
            # Генерируем случайный username
            while True:
                username = f"user_{random.randint(100000, 999999)}"
                try:
                    # Проверяем доступность username
                    available = await client.check_username(username)
                    if available:
                        # Устанавливаем username
                        await client.update_username(username)
                        self.logger.info(f"Установлен новый username: {username}")
                        return username
                except Exception:
                    continue
                
        except Exception as e:
            self.logger.error(f"Ошибка при генерации username: {str(e)}")
            raise

    async def start_scenario(self):
        """Запуск сценария с полной инициализацией"""
        try:
            # 1. Выбор чата
            self.chat_info = self._select_chat_type()
            
            # 2. Инициализация аккаунтов
            await self.init_accounts()
            
            # 3. Загрузка админского аккаунта
            await self.load_admin_account()
            
            # 4. Присоединение к чату
            self.chat_id = await self.join_chat()
            if not self.chat_id:
                raise Exception("Не удалось присоединиться к чату")
            
            # 5. Запуск цикла сценария
            await self.execute_scenario_loop()
            
        except Exception as e:
            self.logger.error(f"Ошибка при запуске сценария: {str(e)}", exc_info=True)
            raise

    def _generate_random_device(self) -> dict:
        devices = [
            {"model": "Samsung Galaxy S21", "system": "Android 12"},
            {"model": "iPhone 13", "system": "iOS 15.4"},
            # Добавьте больше устройств
        ]
        device = random.choice(devices)
        device['app_version'] = f"9.{random.randint(0,9)}.{random.randint(0,9)}"
        return device

    async def execute_scenario(self):
        self.logger.info("Начало выполнения сценария")
        
        chat_id = await self.join_chat()
        if not chat_id:
            self.logger.error("Не удалось получить доступ к чату")
            return

        message_history = {}
        
        sorted_messages = sorted(self.scenario['actions'], key=lambda x: x['id'])
        
        for message in sorted_messages:
            try:
                msg_id = message['id']
                context = message['type']
                account_name = message['account']
                delay = message['timeDelay']
                
                # Проверяем наличие аккаунта в маппинге
                if account_name not in self.role_mapping:
                    self.logger.error(f"{Fore.RED}Аккаунт {account_name} не найден в маппинге{Style.RESET_ALL}")
                    continue
                
                phone = self.role_mapping[account_name]['phone']
                if phone not in self.accounts:
                    self.logger.error(f"{Fore.RED}Аккаунт {account_name} (телефон {phone}) не найден{Style.RESET_ALL}")
                    continue
                
                self.logger.info(f"Обработка сообщения ID:{msg_id}, тип:{context}, аккаунт:{account_name} ({phone})")
                
                # Задержка перед действием
                self.logger.info(f"Ожидание {delay} секунд перед следующим действием")
                await asyncio.sleep(delay)
                
                # Обработка разных типов сообщений
                result = None
                if context == 'message':
                    result = await self._send_message(chat_id, message)
                    self.logger.info(f"Сообщение ID:{msg_id} успешно отправлено")
                    
                elif context == 'reply':
                    if message['replyId'] not in message_history:
                        self.logger.error(f"Не найдено сообщение {message['replyId']} для ответа")
                        continue
                    result = await self._send_reply(chat_id, message, message_history)
                    self.logger.info(f"Ответ на сообщение ID:{message['replyId']} успешно отправлен")
                    
                elif context == 'reaction':
                    if message['reactionId'] not in message_history:
                        self.logger.error(f"Не найдено сообщение {message['reactionId']} для реакции")
                        continue
                    result = await self._add_reaction(chat_id, message, message_history)
                    self.logger.info(f"Реакция на сообщение ID:{message['reactionId']} успешно добавлена")
                
                elif context == 'media':
                    result = await self._send_media(chat_id, message)
                
                elif context == 'media_message':
                    result = await self._send_media_with_message(chat_id, message)
                
                # Сохраняем результат в историю
                if result:
                    message_history[msg_id] = result
                
            except Exception as e:
                self.logger.error(f"Ошибка при обработке сообщения ID:{message['id']}: {str(e)}", exc_info=True)
                continue

    async def _send_message(self, chat_id: int, message_data: dict):
        """Отправка сообщения"""
        account_name = message_data['account']
        phone = self.role_mapping[account_name]['phone']
        client = self.accounts[phone]['client']
        
        self.logger.debug(f"Отправка сообщения от {account_name} ({phone})")
        
        try:
            msg = await client.send_message(
                chat_id=chat_id,
                text=message_data['message']
            )
            return msg
        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения: {str(e)}", exc_info=True)
            raise

    async def _send_reply(self, chat_id: int, message_data: dict, history: dict):
        """Отправка ответа на сообщение"""
        account_name = message_data['account']
        phone = self.role_mapping[account_name]['phone']
        client = self.accounts[phone]['client']
        reply_to = history[message_data['replyId']]
        
        msg = await client.send_message(
            chat_id=chat_id,
            text=message_data['message'],
            reply_to_message_id=reply_to.id
        )
        return msg

    async def _add_reaction(self, chat_id: int, message_data: dict, history: dict):
        """Добавление реакции на сообщение"""
        account_name = message_data['account']
        phone = self.role_mapping[account_name]['phone']
        client = self.accounts[phone]['client']
        target_msg = history[message_data['reactionId']]
        
        try:
            # Используем новый метод для реакций в Pyrogram
            await client.send_reaction(
                chat_id=chat_id,
                message_id=target_msg.id,
                emoji=message_data['reaction']  # Должно быть в формате "👍" или другой эмодзи
            )
            self.logger.info(f"Реакция {message_data['reaction']} успешно добавлена к сообщению {target_msg.id}")
            return target_msg
        except Exception as e:
            self.logger.error(f"Ошибка при добавлении реакции: {str(e)}")
            raise

    def _get_account_files(self, directory: str) -> List[dict]:
        """Получение всех конфигов аккаунтов из директории"""
        account_files = []
        try:
            for file in os.listdir(directory):
                if file.endswith('.json'):
                    file_path = os.path.join(directory, file)
                    self.logger.info(f"{Fore.CYAN}Чтение конфига: {file}{Style.RESET_ALL}")
                    
                    # Получаем номер телефона из имени файла
                    phone = file.replace('.json', '')
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        # Проверяем и устанавливаем номер телефона
                        if not config.get('phone'):
                            config['phone'] = phone
                        # Устанавливаем имя сессии
                        config['session_file'] = f"{phone}.session"
                        config['config_path'] = file_path
                        account_files.append(config)
                            
        except Exception as e:
            self.logger.error(f"{Fore.RED}Ошибка при чтении файлов аккаунтов: {str(e)}{Style.RESET_ALL}")
        return account_files

    async def load_admin_account(self, accounts_folder: str) -> bool:
        """Загрузка админского аккаунта"""
        try:
            admin_acc_dir = os.path.join(accounts_folder, "admin_acc")
            if not os.path.exists(admin_acc_dir):
                self.logger.error(f"{Fore.RED}Папка admin_acc не найдена: {admin_acc_dir}{Style.RESET_ALL}")
                return False

            admin_configs = self._get_account_files(admin_acc_dir)
            if not admin_configs:
                self.logger.error(f"{Fore.RED}Не найдены конфиги админских аккаунтов{Style.RESET_ALL}")
                return False

            admin_data = admin_configs[0]
            phone = str(admin_data['phone'])
            
            self.logger.info(f"{Fore.CYAN}Инициализация админского аккаунта {phone}...{Style.RESET_ALL}")
            
            # Создаем клиента с настройками из конфига
            self.admin_client = await self._init_client(admin_data)
            
            try:
                # Запускаем клиента и проверяем подключение
                await self.admin_client.start()
                me = await self.admin_client.get_me()
                self.logger.info(f"{Fore.GREEN}✓ Подключение успешно{Style.RESET_ALL}")
                return True
                
            except Exception as e:
                self.logger.error(f"{Fore.RED}Ошибка при подключении: {str(e)}{Style.RESET_ALL}")
                return False
                
        except Exception as e:
            self.logger.error(f"{Fore.RED}Ошибка при инициализации админского аккаунта: {str(e)}{Style.RESET_ALL}")
            return False

    async def load_accounts(self, accounts_folder: str) -> bool:
        """Загрузка аккаунтов актеров"""
        actors_dir = os.path.join(accounts_folder, "actors_accs")
        if not os.path.exists(actors_dir):
            self.logger.error(f"{Fore.RED}Папка actors_accs не найдена: {actors_dir}{Style.RESET_ALL}")
            return False

        actor_configs = self._get_account_files(actors_dir)
        if not actor_configs:
            self.logger.error(f"{Fore.RED}Не найдены конфиги аккаунтов актеров{Style.RESET_ALL}")
            return False

        self.logger.info(f"{Fore.CYAN}Найдено аккаунтов: {len(actor_configs)}{Style.RESET_ALL}")
        
        # Сначала создаем маппинг ролей по account_name
        for account_data in actor_configs:
            account_name = account_data.get('account_name')
            if not account_name:
                self.logger.warning(f"{Fore.YELLOW}У аккаунта {account_data.get('phone')} не указан account_name{Style.RESET_ALL}")
                continue
            
            phone = str(account_data['phone'])
            self.role_mapping[account_name] = {
                'phone': phone,
                'status': 'active'
            }
        
        self.logger.info(f"\n{Fore.CYAN}Маппинг ролей:")
        for role, data in self.role_mapping.items():
            self.logger.info(f"Роль {role} -> Телефон {data['phone']} (Статус: {data['status']}){Style.RESET_ALL}")
        
        # Далее загружаем аккаунты как обычно
        for account_data in actor_configs:
            phone = str(account_data['phone'])
            
            # Проверяем, не используется ли уже этот аккаунт
            if phone in self.accounts and self.accounts[phone].get('client'):
                self.logger.warning(f"{Fore.YELLOW}Аккаунт {phone} уже загружен, пропускаем{Style.RESET_ALL}")
                continue
            
            try:
                client = await self._init_client(account_data)
                await client.start()  # Запускаем клиент сразу
                
                me = await client.get_me()
                self.accounts[phone] = {
                    'client': client,
                    'config': account_data,
                    'username': me.username,
                    'user_id': me.id,
                    'active': True
                }
                
                self.logger.info(f"{Fore.GREEN}✓ Аккаунт успешно загружен:")
                self.logger.info(f"  • Телефон: +{phone}")
                self.logger.info(f"  • Username: @{me.username}")
                self.logger.info(f"  • User ID: {me.id}")
                self.logger.info(f"  • Имя: {me.first_name}{Style.RESET_ALL}")
                
            except Exception as e:
                self.logger.error(f"{Fore.RED}Ошибка при загрузке аккаунта {phone}: {str(e)}{Style.RESET_ALL}")
                if phone in self.accounts:
                    del self.accounts[phone]
                continue

        return len(self.accounts) > 0

    async def _init_client(self, account_data: dict) -> Client:
        """Инициализация клиента Telegram"""
        phone = str(account_data['phone'])
        account_dir = os.path.dirname(account_data['config_path'])
        
        # Настройка прокси
        proxy = None
        if account_data.get('proxy'):
            proxy = {
                'scheme': account_data['proxy']['scheme'],
                'hostname': account_data['proxy']['hostname'],
                'port': account_data['proxy']['port'],
                'username': account_data['proxy'].get('username'),
                'password': account_data['proxy'].get('password')
            }

        # Создаем клиента
        client = Client(
            name=phone,
            api_id=account_data['api_id'],
            api_hash=account_data['api_hash'],
            workdir=account_dir,
            proxy=proxy,
            no_updates=True
        )
        
        return client

    async def handle_account_issue(self, account_name: str, issue_type: str):
        """Обработка проблем с аккаунтом"""
        root_path = self._get_root_path()
        account_config = self.accounts[account_name]
        
        if issue_type == "spam_block":
            # Перемещаем в sleep_accs
            target_dir = os.path.join(root_path, "sleep_accs")
            await self._move_account(account_name, target_dir)
            
            # Заменяем из free_accs
            replacement = await self._get_replacement_account()
            if replacement:
                await self._setup_replacement(replacement, account_config)
                
        elif issue_type == "dead":
            # Перемещаем в dead_accs
            target_dir = os.path.join(root_path, "dead_accs")
            await self._move_account(account_name, target_dir)
            
            # Заменяем из free_accs
            replacement = await self._get_replacement_account()
            if replacement:
                await self._setup_replacement(replacement, account_config)

    async def _move_account(self, account_name: str, target_dir: str):
        """Перемещение аккаунта и его конфига в другую папку"""
        # Реализация перемещения файлов
        pass

    async def _get_replacement_account(self) -> Optional[dict]:
        """Получение замещающего аккаунта из free_accs"""
        free_accs_path = os.path.join(self._get_root_path(), "free_accs")
        # Реализация выбора свободного аккаунта
        pass

    async def _setup_replacement(self, replacement_config: dict, old_account_data: dict):
        """Настройка замещающего аккаунта"""
        try:
            old_phone = old_account_data['config']['phone']
            new_phone = replacement_config['phone']
            account_name = old_account_data['config'].get('account_name')
            
            # Обновляем маппинг ролей
            if account_name and account_name in self.role_mapping:
                self.role_mapping[account_name] = {
                    'phone': new_phone,
                    'status': 'active'
                }
                self.logger.info(f"{Fore.GREEN}✓ Обновлен маппинг роли {account_name} на новый телефон {new_phone}{Style.RESET_ALL}")
            
            # Инициализируем новый аккаунт
            client = await self._init_client(replacement_config)
            await client.start()
            me = await client.get_me()
            
            # Обновляем данные аккаунта
            self.accounts[new_phone] = {
                'client': client,
                'config': replacement_config,
                'username': me.username,
                'user_id': me.id,
                'active': True
            }
            
            # Присоединяем новый аккаунт к чату
            try:
                await client.join_chat(self.chat_id)
                self.logger.info(f"{Fore.GREEN}✓ Новый аккаунт {account_name} ({new_phone}) присоединился к чату{Style.RESET_ALL}")
            except Exception as e:
                self.logger.error(f"{Fore.RED}Ошибка при присоединении нового аккаунта к чату: {str(e)}{Style.RESET_ALL}")
            
            # Удаляем старый аккаунт
            if old_phone in self.accounts:
                del self.accounts[old_phone]
            
            self.logger.info(f"{Fore.GREEN}✓ Аккаунт {old_phone} успешно заменен на {new_phone}{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            self.logger.error(f"{Fore.RED}Ошибка при замене аккаунта: {str(e)}{Style.RESET_ALL}")
            return False

    async def execute_scenario_loop(self):
        """Выполнение сценария в цикле"""
        cycle_count = 0
        self._clear_console()
        self.print_status_header()
        
        while True:
            try:
                cycle_count += 1
                self.logger.info(f"\n{Fore.CYAN}╔════ Цикл #{cycle_count} ════╗{Style.RESET_ALL}")
                
                # Выполнение сценария
                await self.execute_scenario()
                
                # Очистка сообщений
                self.logger.info(f"{Fore.YELLOW}Очистка сообщений...{Style.RESET_ALL}")
                await self._cleanup_messages()
                
                self.logger.info(f"{Fore.GREEN}Цикл #{cycle_count} завершен успешно{Style.RESET_ALL}")
                self.print_cycle_stats(cycle_count)
                
                self.first_cycle = False  # Отмечаем, что первый цикл завершен
                
                await asyncio.sleep(self.settings["delay_between_actions"])
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле #{cycle_count}: {str(e)}")
                raise

    def print_status_header(self):
        """Вывод шапки статуса"""
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                     Статус выполнения                      ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """)

    def print_cycle_stats(self, cycle_count):
        """Вывод статистики цикла"""
        print(f"""
{Fore.CYAN}╔══════════════════ Статистика ══════════════════╗
║ Выполнено циклов: {cycle_count:<32} ║
║ Активных аккаунтов: {len(self.accounts):<28} ║
║ Время работы: {self.get_uptime():<34} ║
╚═══════════════════════════════════════════════╝{Style.RESET_ALL}
        """)

    def get_uptime(self):
        """Получение времени работы скрипта"""
        if hasattr(self, 'start_time'):
            uptime = datetime.now() - self.start_time
            return str(uptime).split('.')[0]
        return "00:00:00"

    async def _cleanup_messages(self):
        """Очистка сообщений в зависимости от выбранного режима"""
        cleanup_mode = self.settings.get("cleanup_mode", "instant")
        
        if cleanup_mode == "none":
            self.logger.info(f"{Fore.YELLOW}Очистка сообщений отключена{Style.RESET_ALL}")
            return
            
        deleted_count = 0
        self.logger.info(f"{Fore.YELLOW}Начало очистки сообщений...{Style.RESET_ALL}")
        
        try:
            # Создаем список ID наших аккаунтов
            our_user_ids = set()
            our_usernames = set()
            
            for account_data in self.accounts.values():
                if account_data.get('user_id'):
                    our_user_ids.add(account_data['user_id'])
                if account_data.get('username'):
                    our_usernames.add(account_data['username'])
            
            if cleanup_mode == "instant":
                # Удаляем все сообщения сразу
                async for message in self.admin_client.get_chat_history(self.chat_id):
                    if message.from_user and (
                        message.from_user.id in our_user_ids or 
                        (message.from_user.username and message.from_user.username in our_usernames)
                    ):
                        try:
                            await message.delete()
                            deleted_count += 1
                            if deleted_count % 10 == 0:
                                self.logger.info(f"{Fore.YELLOW}Удалено сообщений: {deleted_count}{Style.RESET_ALL}")
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            self.logger.warning(f"Не удалось удалить сообщение: {str(e)}")
                            
            elif cleanup_mode == "gradual":
                # Сохраняем текущие сообщения для следующего цикла
                self.old_messages = self.current_messages.copy()
                self.current_messages = {}
                
        except Exception as e:
            self.logger.error(f"Ошибка при очистке сообщений: {str(e)}")

    def _load_settings(self) -> dict:
        """Загрузка общих настроек"""
        try:
            # Получаем путь к settings.json в той же папке, где находится скрипт
            settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке настроек: {str(e)}")
            return {
                "delay_between_actions": 2,
                "max_retries": 3,
                "flood_wait_multiplier": 1.5,
                "auto_replace_accounts": True,
                "check_sleeping_accounts_interval": 3600,
                "max_spam_block_duration": 3600,
                "chat_join_delay": 30,
                "cleanup_mode": "instant"
            }

    async def _send_media(self, chat_id: int, message_data: dict, reply_to_message_id=None):
        """Отправка медиафайла"""
        account_name = message_data['account']
        phone = self.role_mapping[account_name]['phone']
        client = self.accounts[phone]['client']
        
        # Получаем полный путь к файлу относительно корня проекта
        media_path = os.path.join(self.root_path, message_data['mediaPath'])
        
        if not os.path.exists(media_path):
            self.logger.error(f"Файл не найден: {media_path}")
            raise FileNotFoundError(f"Медиафайл не найден: {media_path}")
        
        try:
            if media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                msg = await client.send_photo(
                    chat_id=chat_id,
                    photo=media_path,
                    reply_to_message_id=reply_to_message_id
                )
            elif media_path.lower().endswith(('.mp4', '.avi', '.mov')):
                msg = await client.send_video(
                    chat_id=chat_id,
                    video=media_path,
                    reply_to_message_id=reply_to_message_id
                )
            return msg
        except Exception as e:
            self.logger.error(f"Ошибка при отправке медиа: {str(e)}")
            raise

    async def _send_media_with_message(self, chat_id: int, message_data: dict, reply_to_message_id=None):
        """Отправка медиафайла с сообщением"""
        account_name = message_data['account']
        phone = self.role_mapping[account_name]['phone']
        client = self.accounts[phone]['client']
        
        # Получаем полный путь к файлу относительно корня проекта
        media_path = os.path.join(self.root_path, message_data['mediaPath'])
        
        if not os.path.exists(media_path):
            self.logger.error(f"Файл не найден: {media_path}")
            raise FileNotFoundError(f"Медиафайл не найден: {media_path}")
        
        try:
            if media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                msg = await client.send_photo(
                    chat_id=chat_id,
                    photo=media_path,
                    caption=message_data.get('message', ''),
                    reply_to_message_id=reply_to_message_id
                )
            elif media_path.lower().endswith(('.mp4', '.avi', '.mov')):
                msg = await client.send_video(
                    chat_id=chat_id,
                    video=media_path,
                    caption=message_data.get('message', ''),
                    reply_to_message_id=reply_to_message_id
                )
            return msg
        except Exception as e:
            self.logger.error(f"Ошибка при отправке медиа с сообщением: {str(e)}")
            raise

    async def execute_action(self, chat_id: int, message_data: dict, history: dict):
        """Выполнение действия с учетом возможного reply"""
        account_name = message_data['account']
        phone = self.role_mapping[account_name]['phone']
        client = self.accounts[phone]['client']
        
        # Получаем ID сообщения для ответа, если есть
        reply_to_message_id = None
        if message_data.get('replyId'):
            reply_msg = history.get(message_data['replyId'])
            if reply_msg:
                reply_to_message_id = reply_msg.id
                self.logger.info(f"{Fore.CYAN}Ответ на сообщение #{message_data['replyId']}{Style.RESET_ALL}")
        
        try:
            msg = None
            cleanup_mode = self.settings.get("cleanup_mode", "instant")
            
            # Если включено постепенное удаление, удаляем старое сообщение
            if cleanup_mode == "gradual" and message_data['id'] in self.old_messages:
                try:
                    old_msg = self.old_messages[message_data['id']]
                    if message_data['type'] != 'reaction':
                        await old_msg.delete()
                        self.logger.info(f"Удалено старое сообщение #{message_data['id']}")
                except Exception as e:
                    self.logger.warning(f"Не удалось удалить старое сообщение: {str(e)}")

            # Обработка разных типов действий
            if message_data['type'] == 'message':
                msg = await client.send_message(
                    chat_id=chat_id,
                    text=message_data['message'],
                    reply_to_message_id=reply_to_message_id
                )
                
            elif message_data['type'] == 'media':
                msg = await self._send_media(
                    chat_id=chat_id,
                    message_data=message_data,
                    reply_to_message_id=reply_to_message_id
                )
                
            elif message_data['type'] == 'media_message':
                msg = await self._send_media_with_message(
                    chat_id=chat_id,
                    message_data=message_data,
                    reply_to_message_id=reply_to_message_id
                )
                
            elif message_data['type'] == 'reaction':
                msg = await self._add_reaction(
                    chat_id=chat_id,
                    message_data=message_data,
                    history=history
                )

            # Сохраняем сообщение в текущий цикл
            if msg and cleanup_mode == "gradual":
                self.current_messages[message_data['id']] = msg
                
            return msg
            
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении действия: {str(e)}")
            raise

class AccountManager:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.logger = logging.getLogger('AccountManager')

    async def load_account_config(self, config_path: str) -> dict:
        """Загрузка конфига аккаунта"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def save_account_config(self, config: dict, path: str):
        """Сохранение конфига аккаунта"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    async def move_account(self, account_name: str, from_dir: str, to_dir: str):
        """Перемещение аккаунта между папками"""
        try:
            # Перемещаем файлы сессии
            session_files = [
                f for f in os.listdir(from_dir) 
                if f.startswith(account_name) and (f.endswith('.session') or f.endswith('.json'))
            ]
            
            for file in session_files:
                src = os.path.join(from_dir, file)
                dst = os.path.join(to_dir, file)
                shutil.move(src, dst)
                self.logger.info(f"Перемещен файл {file} из {from_dir} в {to_dir}")
                
        except Exception as e:
            self.logger.error(f"Ошибка при перемещении аккаунта {account_name}: {str(e)}")
            raise

    async def copy_account_profile(self, source_account: dict, target_account: dict):
        """Копирование профиля одного аккаунта в другой"""
        profile_fields = ['first_name', 'last_name', 'bio', 'username']
        for field in profile_fields:
            if field in source_account:
                target_account[field] = source_account[field]
        return target_account

class AccountStateHandler:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.account_manager = AccountManager(root_path)
        self.logger = logging.getLogger('AccountStateHandler')

    async def handle_spam_block(self, account_name: str, block_duration: int = None):
        """Обработка спам блока"""
        try:
            if block_duration and block_duration < 3600:  # если блок меньше часа
                self.logger.info(f"Короткий спам блок на аккаунте {account_name}, ожидаем...")
                await asyncio.sleep(block_duration)
                return True
            
            # Перемещаем аккаунт в sleep_accs
            await self.account_manager.move_account(
                account_name,
                os.path.join(self.root_path, "actors_accs"),
                os.path.join(self.root_path, "sleep_accs")
            )
            
            # Получаем замену из free_accs
            replacement = await self.get_replacement_account()
            if replacement:
                return replacement
                
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке спам блока: {str(e)}")
            raise

    async def handle_dead_session(self, account_name: str):
        """Обработка мертвой сессии"""
        try:
            # Перемещаем аккаунт в dead_accs
            await self.account_manager.move_account(
                account_name,
                os.path.join(self.root_path, "actors_accs"),
                os.path.join(self.root_path, "dead_accs")
            )
            
            # Получаем замену из free_accs
            replacement = await self.get_replacement_account()
            if replacement:
                return replacement
                
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке мертвой сессии: {str(e)}")
            raise

    async def get_replacement_account(self) -> Optional[dict]:
        """Получение замещающего аккаунта из free_accs"""
        free_accs_path = os.path.join(self.root_path, "free_accs")
        try:
            # Получаем список доступных аккаунтов
            available_accounts = [
                f for f in os.listdir(free_accs_path) 
                if f.endswith('.json')
            ]
            
            if not available_accounts:
                self.logger.error("Нет доступных аккаунтов для замены")
                return None
                
            # Берем первый доступный аккаунт
            account_config = await self.account_manager.load_account_config(
                os.path.join(free_accs_path, available_accounts[0])
            )
            
            # Перемещаем его в actors_accs
            await self.account_manager.move_account(
                account_config['account_name'],
                free_accs_path,
                os.path.join(self.root_path, "actors_accs")
            )
            
            return account_config
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении замещающего аккаунта: {str(e)}")
            return None

async def main():
    spammer = None
    try:
        spammer = TelegramSpammer()
        if not await spammer.setup():
            return
        await spammer.execute_scenario_loop()
        
    except Exception as e:
        if spammer and spammer.logger:
            spammer.logger.error(f"{Fore.RED}Критическая ошибка: {str(e)}{Style.RESET_ALL}", exc_info=True)
        else:
            print(f"Критическая ошибка: {str(e)}")
    finally:
        if spammer:
            spammer.logger.info(f"\n{Fore.YELLOW}Завершение работы...{Style.RESET_ALL}")
            
            # Останавливаем админский клиент
            if hasattr(spammer, 'admin_client') and spammer.admin_client:
                try:
                    if spammer.admin_client.is_connected:
                        await spammer.admin_client.stop()
                        spammer.logger.info(f"{Fore.GREEN}✓ Админский клиент остановлен{Style.RESET_ALL}")
                except Exception as e:
                    spammer.logger.error(f"{Fore.RED}Ошибка при остановке админского клиента: {str(e)}{Style.RESET_ALL}")
            
            # Останавливаем клиенты аккаунтов
            if hasattr(spammer, 'accounts'):
                for phone, account_data in spammer.accounts.items():
                    try:
                        client = account_data.get('client')
                        if client and client.is_connected:
                            await client.stop()
                            spammer.logger.info(f"{Fore.GREEN}✓ Клиент {phone} остановлен{Style.RESET_ALL}")
                    except Exception as e:
                        spammer.logger.error(f"{Fore.RED}Ошибка при остановке клиента {phone}: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(main())
