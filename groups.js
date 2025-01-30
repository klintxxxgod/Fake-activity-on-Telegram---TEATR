document.getElementById('fileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const currentGroup = sessionStorage.getItem('currentGroup');
    
    try {
        const response = await fetch('http://localhost:5000/import_session', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            document.getElementById('fileUploadForm').style.display = 'none';
            loadGroups();  // Перезагружаем список групп
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Ошибка при импорте аккаунта: ' + error.message);
    }
}); 

document.addEventListener('DOMContentLoaded', () => {
    // Обработчик для всех кнопок закрытия
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.onclick = function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        }
    });

    // Закрытие модальных окон при клике вне их области
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    }
}); 