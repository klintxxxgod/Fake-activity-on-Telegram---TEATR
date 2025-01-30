function showAddAccountModal(groupName) {
    document.getElementById('currentGroupName').textContent = groupName;
    document.getElementById('addAccountModal').style.display = 'block';
    // Сохраняем имя группы для использования в формах
    sessionStorage.setItem('currentGroup', groupName);
}

function showAuthForm() {
    document.getElementById('addAccountModal').style.display = 'none';
    document.getElementById('authForm').style.display = 'block';
}

function showFileUpload() {
    const modal = document.getElementById('fileUploadForm');
    if (modal) {
        modal.style.display = 'block';
        console.log('Modal opened');
    }
}

// Глобальная функция закрытия
window.closeFileUpload = function() {
    const modal = document.getElementById('fileUploadForm');
    if (modal) {
        modal.style.display = 'none';
        console.log('Modal closed by global function');
    }
};

// Делаем функцию showFileUpload тоже глобальной
window.showFileUpload = showFileUpload;

// Обработка формы авторизации
document.getElementById('telegramAuthForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const currentGroup = sessionStorage.getItem('currentGroup');
    
    const data = {
        accountName: formData.get('accountName'),
        phoneNumber: formData.get('phoneNumber'),
        password: formData.get('password'),
        proxyUrl: formData.get('proxyUrl'),
        accountType: formData.get('accountType'),
        groupName: currentGroup
    };

    try {
        const response = await fetch('http://localhost:5000/auth_account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Network response was not ok');
        
        const result = await response.json();
        
        if (result.needCode) {
            const code = prompt('Введите код подтверждения:');
            if (code) {
                const completeResponse = await fetch('http://localhost:5000/complete_auth', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        ...data,
                        code: code,
                        phoneHash: result.phoneHash
                    })
                });
                
                const completeResult = await completeResponse.json();
                if (completeResult.success) {
                    alert('Аккаунт успешно добавлен!');
                    document.getElementById('authForm').style.display = 'none';
                    loadGroups();
                } else {
                    throw new Error(completeResult.error);
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при авторизации: ' + error.message);
    }
});

// Обработка загрузки файлов
document.getElementById('fileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log('Form submitted'); // Отладочный вывод
    
    const formData = new FormData(e.target);
    const currentGroup = sessionStorage.getItem('currentGroup');
    
    if (!currentGroup) {
        alert('Ошибка: группа не выбрана');
        return;
    }
    
    formData.append('groupName', currentGroup);
    
    try {
        console.log('Sending request to server...'); // Отладочный вывод
        const response = await fetch('http://localhost:5000/import_session', {
            method: 'POST',
            body: formData
        });

        console.log('Response received:', response); // Отладочный вывод
        const result = await response.json();
        
        if (result.success) {
            alert('Аккаунт успешно импортирован!');
            document.getElementById('fileUploadForm').style.display = 'none';
            loadGroups();  // Перезагружаем список групп
        } else {
            throw new Error(result.error || 'Ошибка при импорте');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при импорте аккаунта: ' + error.message);
    }
});

// Закрытие модальных окон при клике вне их области
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

function loadGroups() {
    fetch('http://localhost:8000/get_groups')
        .then(response => response.json())
        .then(groups => {
            const container = document.querySelector('.container') || document.body;
            container.innerHTML = `
                <button class="back-btn" onclick="window.location.href='/'">
                    <i class="fas fa-arrow-left"></i> Вернуться в главное меню
                </button>
                <button class="create-group-btn" onclick="showCreateGroupModal()">
                    <i class="fas fa-plus"></i> Создать группу аккаунтов
                </button>
            `;

            groups.forEach(group => {
                const groupBlock = document.createElement('div');
                groupBlock.className = 'group-block';
                
                groupBlock.innerHTML = `
                    <h3>${group.name}</h3>
                    <div class="accounts-stats">
                        <div class="stat-block">
                            <span class="stat-value">${group.workingAccounts || 0}</span>
                            <span class="stat-label">Рабочие аккаунты</span>
                        </div>
                        <div class="stat-block">
                            <span class="stat-value">${group.sleepingAccounts || 0}</span>
                            <span class="stat-label">Спящие аккаунты</span>
                        </div>
                        <div class="stat-block">
                            <span class="stat-value">${group.deadAccounts || 0}</span>
                            <span class="stat-label">Мертвые аккаунты</span>
                        </div>
                        <div class="stat-block">
                            <span class="stat-value">${group.freeAccounts || 0}</span>
                            <span class="stat-label">Свободные аккаунты</span>
                        </div>
                    </div>
                    <div class="group-actions">
                        <button class="add-account-btn" onclick="showAddAccountModal('${group.name}')">
                            <i class="fas fa-user-plus"></i> Добавить аккаунт
                        </button>
                        <button class="clean-btn" onclick="cleanDeadAccounts('${group.name}')">
                            <i class="fas fa-broom"></i> Очистить мертвые
                        </button>
                        <button class="wake-btn" onclick="wakeSleepingAccounts('${group.name}')">
                            <i class="fas fa-bell"></i> Пробудить спящие
                        </button>
                        <button class="delete-btn" onclick="deleteGroup('${group.name}')">
                            <i class="fas fa-trash"></i> Удалить группу
                        </button>
                    </div>
                `;
                
                container.appendChild(groupBlock);
            });
        })
        .catch(error => {
            console.error('Error loading groups:', error);
            document.body.innerHTML = '<div class="error">Ошибка при загрузке групп</div>';
        });
}

// Добавляем стили для новых кнопок
const style = document.createElement('style');
style.textContent = `
    .group-actions {
        display: flex;
        gap: 10px;
        margin-top: 15px;
    }

    .add-account-btn {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 8px 15px;
        border-radius: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .add-account-btn:hover {
        background-color: #45a049;
    }
`;
document.head.appendChild(style);

// Загружаем группы при загрузке страницы
document.addEventListener('DOMContentLoaded', loadGroups);

// Добавляем обработчик после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    // Находим кнопку закрытия
    const closeButtons = document.querySelectorAll('.transparent-close');
    console.log('Found close buttons:', closeButtons.length); // Проверяем, найдены ли кнопки
    
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            console.log('Close button clicked'); // Проверяем, срабатывает ли клик
            const modal = document.getElementById('fileUploadForm');
            console.log('Modal found:', modal); // Проверяем, найдено ли модальное окно
            if (modal) {
                console.log('Current display state:', modal.style.display);
                modal.style.display = 'none';
                console.log('New display state:', modal.style.display);
            }
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
    // Прямое добавление обработчика на кнопку закрытия
    const closeButton = document.querySelector('#fileUploadForm .transparent-close');
    if (closeButton) {
        closeButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const modal = document.getElementById('fileUploadForm');
            if (modal) {
                modal.style.display = 'none';
            }
        }, true); // Используем capturing phase
    }
});

// Проверяем, как окно создается и закрывается
document.addEventListener('DOMContentLoaded', () => {
    // Находим форму загрузки файлов
    const fileForm = document.getElementById('fileForm');
    const fileUploadModal = document.getElementById('fileUploadForm');
    
    if (fileForm && fileUploadModal) {
        // Добавляем обработчик отправки формы
        fileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            // ... обработка отправки формы ...
        });
        
        // Добавляем обработчик закрытия
        const closeBtn = fileUploadModal.querySelector('.transparent-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                fileUploadModal.style.display = 'none';
                console.log('Modal closed by button');
            });
        }
        
        // Добавляем обработчик закрытия по клику на фон
        fileUploadModal.addEventListener('click', function(e) {
            if (e.target === fileUploadModal) {
                fileUploadModal.style.display = 'none';
                console.log('Modal closed by background click');
            }
        });
    }
}); 