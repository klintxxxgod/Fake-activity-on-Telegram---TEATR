function showAddAccountModal() {
    document.getElementById('addAccountModal').style.display = 'block';
}

function showAuthForm() {
    document.getElementById('addAccountModal').style.display = 'none';
    document.getElementById('authForm').style.display = 'block';
}

// Обработка формы авторизации
document.getElementById('telegramAuthForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);

    try {
        const response = await fetch('http://localhost:8000/auth_account', {
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
                await submitCode(code, result.phoneNumber);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при авторизации');
    }
});

// Обработка загрузки файлов
document.getElementById('fileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    try {
        const response = await fetch('http://localhost:8000/upload_account_files', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Network response was not ok');
        
        const result = await response.json();
        alert(result.message);
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при загрузке файлов');
    }
});

// Закрытие модальных окон
document.querySelectorAll('.close').forEach(closeBtn => {
    closeBtn.onclick = function() {
        this.closest('.modal').style.display = 'none';
    }
}); 