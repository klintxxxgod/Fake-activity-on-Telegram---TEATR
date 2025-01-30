document.addEventListener('DOMContentLoaded', () => {
    loadScenarios();
});

function loadScenarios() {
    const scenariosContainer = document.querySelector('.scenarios-list');
    scenariosContainer.innerHTML = '<div class="loading">Загрузка сценариев...</div>';

    fetch('http://localhost:8000/get_scenarios')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(scenarios => {
            console.log('Загруженные сценарии:', scenarios);
            scenariosContainer.innerHTML = '';

            if (!scenarios || scenarios.length === 0) {
                scenariosContainer.innerHTML = '<div class="no-scenarios">Нет сохраненных сценариев</div>';
                return;
            }

            scenarios.forEach(scenario => {
                const scenarioElement = createScenarioElement(scenario);
                scenariosContainer.appendChild(scenarioElement);
            });
        })
        .catch(error => {
            console.error('Ошибка при загрузке сценариев:', error);
            scenariosContainer.innerHTML = `<div class="error">Ошибка при загрузке сценариев: ${error.message}</div>`;
        });
}

function createScenarioElement(scenario) {
    const div = document.createElement('div');
    div.className = 'scenario-block';
    
    const actionCount = scenario.actions ? scenario.actions.length : 0;
    const accountCount = scenario.actions ? new Set(scenario.actions.map(a => a.account)).size : 0;

    const actionsInfo = scenario.actions ? scenario.actions.map(action => 
        `ID: ${action.id} - ${action.type}`
    ).join('<br>') : '';

    div.innerHTML = `
        <div class="scenario-header">
            <h3>${scenario.name}</h3>
            <div class="scenario-stats">
                <span>Действий: ${actionCount}</span>
                <span>Аккаунтов: ${accountCount}</span>
            </div>
        </div>
        <div class="scenario-actions">
            <div class="action-list">
                ${actionsInfo}
            </div>
            <div class="scenario-buttons">
                <button onclick="editScenario('${scenario.name}')" class="edit-btn">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteScenario('${scenario.name}')" class="delete-btn">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;

    return div;
}

function editScenario(name) {
    console.log('Редактирование сценария:', name); // Для отладки
    
    fetch(`http://localhost:8000/scenariyes/${name}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(scenario => {
            console.log('Загруженный сценарий:', scenario); // Для отладки
            
            if (scenario.error) {
                throw new Error(scenario.error);
            }
            
            // Сохраняем сценарий в sessionStorage
            sessionStorage.setItem('editingScenario', JSON.stringify(scenario));
            
            // Перенаправляем на страницу редактирования
            window.location.href = 'scenario-builder.html';
        })
        .catch(error => {
            console.error('Ошибка при загрузке сценария:', error);
            alert(`Ошибка при загрузке сценария: ${error.message}`);
        });
}

function deleteScenario(name) {
    if (!confirm(`Удалить сценарий "${name}"?`)) {
        return;
    }

    fetch(`http://localhost:8000/scenariyes/${name}`, {
        method: 'DELETE'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                loadScenarios();
            } else {
                throw new Error(data.error || 'Ошибка при удалении');
            }
        })
        .catch(error => {
            console.error('Ошибка при удалении сценария:', error);
            alert(`Ошибка при удалении сценария: ${error.message}`);
        });
}

// Обработка отправки формы авторизации
document.getElementById('telegramAuthForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);

    try {
        const response = await fetch('http://localhost:5000/auth_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (result.success && result.needCode) {
            // Сохраняем данные для следующего шага
            sessionStorage.setItem('authData', JSON.stringify({
                phoneNumber: data.phoneNumber,
                phoneHash: result.phoneHash,
                accountType: data.accountType,
                config: result.config
            }));
            
            // Показываем окно ввода кода
            document.getElementById('codeInputModal').style.display = 'block';
        } else {
            alert(result.error || 'Произошла ошибка');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отправке запроса');
    }
});

// Обработка ввода кода подтверждения
document.getElementById('codeInputForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const code = formData.get('code');
    const authData = JSON.parse(sessionStorage.getItem('authData'));

    try {
        const response = await fetch('http://localhost:5000/complete_auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                ...authData,
                code
            })
        });

        const result = await response.json();
        if (result.success) {
            alert('Аккаунт успешно добавлен');
            location.reload();
        } else {
            alert(result.error || 'Произошла ошибка');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отправке кода');
    }
}); 