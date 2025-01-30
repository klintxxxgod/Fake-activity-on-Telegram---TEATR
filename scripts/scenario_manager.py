import json
import os
from datetime import datetime
from typing import Dict, List
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Action(BaseModel):
    id: int
    type: str
    account: str
    timeDelay: int
    message: str = None
    replyId: int = None
    reactionId: int = None
    reaction: str = None
    x: int = 0
    y: int = 0

class Scenario(BaseModel):
    name: str
    actions: List[Action]

class ScenarioManager:
    def __init__(self):
        self.scenarios_dir = "scenariyes"
        self._ensure_scenarios_dir()

    def _ensure_scenarios_dir(self):
        if not os.path.exists(self.scenarios_dir):
            os.makedirs(self.scenarios_dir)

    def get_scenarios(self) -> List[Dict]:
        """Получает список всех сценариев из папки"""
        scenarios = []
        try:
            for filename in os.listdir(self.scenarios_dir):
                if filename.endswith(('.json', '.yaml')):
                    file_path = os.path.join(self.scenarios_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f) if filename.endswith('.json') else yaml.safe_load(f)
                            
                            # Подсчет уникальных аккаунтов
                            unique_accounts = set()
                            for action in data.get('actions', []):
                                if 'account' in action:
                                    unique_accounts.add(action['account'])
                            
                            scenarios.append({
                                'name': data.get('name', os.path.splitext(filename)[0]),
                                'action_count': len(data.get('actions', [])),
                                'account_count': len(unique_accounts),
                                'modified': os.path.getmtime(file_path),
                                'actions': data.get('actions', [])
                            })
                    except Exception as e:
                        print(f"Ошибка при чтении файла {file_path}: {e}")
                        continue
            return scenarios
        except Exception as e:
            print(f"Ошибка при чтении сценариев: {e}")
            return []

    def create_scenario(self, scenario_data: Dict) -> bool:
        """Создает новый сценарий"""
        try:
            name = scenario_data.get('name', '').strip()
            if not name:
                return False

            filename = f"{name}.json"
            file_path = os.path.join(self.scenarios_dir, filename)

            # Сохраняем сценарий
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(scenario_data, f, ensure_ascii=False, indent=1)

            return True
        except Exception as e:
            print(f"Ошибка при создании сценария: {e}")
            return False

    def get_scenario(self, name: str) -> Dict:
        """Получает конкретный сценарий по имени"""
        try:
            file_path = os.path.join(self.scenarios_dir, f"{name}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Ошибка при чтении сценария {name}: {e}")
            return None

    def delete_scenario(self, name: str) -> bool:
        """Удаляет сценарий"""
        try:
            file_path = os.path.join(self.scenarios_dir, f"{name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Ошибка при удалении сценария {name}: {e}")
            return False

# API endpoints
scenario_manager = ScenarioManager()

@app.post("/api/scenarios")
async def create_scenario(scenario: Scenario):
    success = scenario_manager.create_scenario(scenario)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create scenario")
    return {"status": "success"}

@app.get("/api/scenarios")
async def get_scenarios():
    return scenario_manager.get_scenarios() 