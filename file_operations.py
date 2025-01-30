import os
import shutil
from pathlib import Path

class FileOperations:
    def __init__(self):
        self.accounts_path = os.path.expanduser("~/Desktop/Коды/Teatr/accounts")
        self.default_folders = ['admin_acc', 'actors_accs', 'sleep_accs', 'dead_accs', 'free_accs']

    def create_group(self, group_name):
        """Создает новую группу аккаунтов со всеми подпапками"""
        try:
            group_path = os.path.join(self.accounts_path, group_name)
            # Создаем основную папку группы
            os.makedirs(group_path, exist_ok=True)
            
            # Создаем подпапки
            for folder in self.default_folders:
                os.makedirs(os.path.join(group_path, folder), exist_ok=True)
            
            return True
        except Exception as e:
            print(f"Ошибка при создании группы: {e}")
            return False

    def get_groups(self):
        """Возвращает список всех групп и их статистику"""
        try:
            groups = []
            if os.path.exists(self.accounts_path):
                for group in os.listdir(self.accounts_path):
                    group_path = os.path.join(self.accounts_path, group)
                    if os.path.isdir(group_path):
                        stats = self.get_group_stats(group)
                        groups.append({
                            'name': group,
                            'stats': stats
                        })
            return groups
        except Exception as e:
            print(f"Ошибка при получении списка групп: {e}")
            return []

    def get_group_stats(self, group_name):
        """Подсчитывает количество session файлов в каждой подпапке группы"""
        stats = {}
        group_path = os.path.join(self.accounts_path, group_name)
        
        for folder in self.default_folders:
            folder_path = os.path.join(group_path, folder)
            if os.path.exists(folder_path):
                session_files = len([f for f in os.listdir(folder_path) if 'session' in f])
                stats[folder.split('_')[0]] = session_files
            else:
                stats[folder.split('_')[0]] = 0
                
        return stats

    def delete_group(self, group_name):
        """Удаляет группу со всеми подпапками"""
        try:
            group_path = os.path.join(self.accounts_path, group_name)
            shutil.rmtree(group_path)
            return True
        except Exception as e:
            print(f"Ошибка при удалении группы: {e}")
            return False

    def clean_dead_accounts(self, group_name):
        """Очищает папку с мертвыми аккаунтами"""
        try:
            dead_path = os.path.join(self.accounts_path, group_name, 'dead_accs')
            for file in os.listdir(dead_path):
                os.remove(os.path.join(dead_path, file))
            return True
        except Exception as e:
            print(f"Ошибка при очистке мертвых аккаунтов: {e}")
            return False

    def wake_sleeping_accounts(self, group_name):
        """Перемещает все аккаунты из sleep_accs в actors_accs"""
        try:
            sleep_path = os.path.join(self.accounts_path, group_name, 'sleep_accs')
            actors_path = os.path.join(self.accounts_path, group_name, 'actors_accs')
            
            for file in os.listdir(sleep_path):
                shutil.move(
                    os.path.join(sleep_path, file),
                    os.path.join(actors_path, file)
                )
            return True
        except Exception as e:
            print(f"Ошибка при пробуждении аккаунтов: {e}")
            return False 