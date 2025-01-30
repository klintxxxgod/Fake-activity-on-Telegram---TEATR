let runningScenarios = 0;

// Функция подсчета аккаунтов
async function countAccounts() {
    try {
        console.log('Запрос количества аккаунтов...'); // Отладочный вывод
        const response = await fetch('http://localhost:5000/count_accounts');
        const data = await response.json();
        console.log('Получены данные:', data); // Отладочный вывод
        
        if (data.success) {
            const accountsElement = document.querySelector('.stat-card:nth-child(1) h3');
            accountsElement.textContent = data.count;
            console.log('Обновлено количество аккаунтов:', data.count); // Отладочный вывод
        } else {
            console.error('Ошибка при получении количества аккаунтов:', data.error);
        }
    } catch (error) {
        console.error('Ошибка при подсчете аккаунтов:', error);
    }
}

// Обновляем статистику каждые 30 секунд
setInterval(countAccounts, 30000);

// Функция обновления количества запущенных сценариев
function updateRunningScenarios() {
    document.querySelector('.stat-card:nth-child(2) h3').textContent = runningScenarios;
}

// Функция обновления времени
function updateClock() {
    const clockElement = document.getElementById('clock');
    setInterval(() => {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        clockElement.textContent = `${hours}:${minutes}:${seconds}`;
    }, 1000);
}

// Инициализация статистики
document.addEventListener('DOMContentLoaded', () => {
    countAccounts();
    updateRunningScenarios();
    updateClock();

    // Обработчик кнопки "Начать работу"
    const startButton = document.getElementById('startButton');
    if (startButton) {
        startButton.addEventListener('click', () => {
            runningScenarios++;
            updateRunningScenarios();
        });
    }
}); 