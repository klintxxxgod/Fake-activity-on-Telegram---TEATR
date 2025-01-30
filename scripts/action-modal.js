class ActionModal {
    constructor(scenarioBuilder) {
        this.scenarioBuilder = scenarioBuilder;
        this.modal = this.createModal();
        document.body.appendChild(this.modal);
    }

    createModal() {
        const modal = document.createElement('div');
        modal.className = 'action-modal';
        modal.innerHTML = `
            <div class="action-modal-content">
                <div class="modal-header">
                    <h3>Добавление действия</h3>
                    <button class="close-btn" id="closeActionModal">×</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Тип действия</label>
                        <select id="actionType">
                            <option value="message">Сообщение</option>
                            <option value="reply">Ответ</option>
                            <option value="reaction">Реакция</option>
                            <option value="media">Медиа</option>
                            <option value="media_message">Медиа + Сообщение</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Аккаунт</label>
                        <input type="text" id="accountName" required>
                    </div>

                    <div class="form-group">
                        <label>Задержка (сек)</label>
                        <input type="number" id="timeDelay" min="0" value="0">
                    </div>

                    <div class="form-group message-fields">
                        <label>Сообщение</label>
                        <textarea id="messageText" rows="4"></textarea>
                    </div>

                    <div class="form-group reply-fields" style="display: none;">
                        <label>ID сообщения для ответа</label>
                        <select id="replyId"></select>
                    </div>

                    <div class="form-group reaction-fields" style="display: none;">
                        <label>ID сообщения для реакции</label>
                        <select id="reactionId"></select>
                        <label>Реакция</label>
                        <select id="reactionEmoji">
                            <option value="👍">👍 Палец вверх</option>
                            <option value="❤️">❤️ Сердце</option>
                            <option value="🔥">🔥 Огонь</option>
                            <option value="👏">👏 Аплодисменты</option>
                            <option value="😊">😊 Улыбка</option>
                            <option value="🎉">🎉 Праздник</option>
                            <option value="👌">👌 Окей</option>
                        </select>
                    </div>

                    <div class="form-group media-fields" style="display: none;">
                        <label>Медиафайл</label>
                        <input type="file" id="mediaFile" accept="image/*,video/*">
                    </div>

                    <button class="save-action-btn" id="saveActionBtn">Сохранить действие</button>
                </div>
            </div>
        `;

        this.initEventListeners(modal);
        return modal;
    }

    initEventListeners(modal) {
        modal.querySelector('#closeActionModal').addEventListener('click', () => {
            this.hide();
        });

        modal.querySelector('#actionType').addEventListener('change', (e) => {
            this.toggleActionFields(e.target.value);
        });

        modal.querySelector('#saveActionBtn').addEventListener('click', async () => {
            const action = await this.createActionFromForm();
            if (action) {
                const editId = modal.querySelector('#saveActionBtn').dataset.editId;
                if (editId) {
                    // Режим редактирования
                    const index = this.scenarioBuilder.actions.findIndex(a => a.id === parseInt(editId));
                    if (index !== -1) {
                        action.id = parseInt(editId); // Сохраняем исходный ID
                        action.x = this.scenarioBuilder.actions[index].x; // Сохраняем позицию
                        action.y = this.scenarioBuilder.actions[index].y;
                        this.scenarioBuilder.actions[index] = action;
                        
                        // Обновляем отображение
                        const node = document.querySelector(`.action-node[data-id="${editId}"]`);
                        if (node) node.remove();
                        this.scenarioBuilder.addActionToCanvas(action);
                    }
                    // Сбрасываем режим редактирования
                    modal.querySelector('#saveActionBtn').dataset.editId = '';
                    modal.querySelector('#saveActionBtn').textContent = 'Добавить';
                } else {
                    // Режим добавления нового действия
                    this.scenarioBuilder.addActionToCanvas(action);
                }
                this.hide();
                this.clearForm();
            }
        });
    }

    show() {
        this.modal.style.display = 'block';
        this.updateActionSelects();
    }

    hide() {
        this.modal.style.display = 'none';
    }

    toggleActionFields(actionType) {
        const messageFields = this.modal.querySelector('.message-fields');
        const replyFields = this.modal.querySelector('.reply-fields');
        const reactionFields = this.modal.querySelector('.reaction-fields');
        const mediaFields = this.modal.querySelector('.media-fields');
        
        // Скрываем все поля
        [messageFields, replyFields, reactionFields, mediaFields].forEach(
            field => field.style.display = 'none'
        );
        
        // Показываем нужные поля
        switch(actionType) {
            case 'media':
                mediaFields.style.display = 'block';
                break;
            case 'media_message':
                mediaFields.style.display = 'block';
                messageFields.style.display = 'block';
                break;
            case 'message':
                messageFields.style.display = 'block';
                break;
            case 'reply':
                messageFields.style.display = 'block';
                replyFields.style.display = 'block';
                break;
            case 'reaction':
                reactionFields.style.display = 'block';
                break;
        }
    }

    updateActionSelects() {
        const replySelect = this.modal.querySelector('#replyId');
        const reactionSelect = this.modal.querySelector('#reactionId');
        
        // Очищаем существующие опции
        replySelect.innerHTML = '';
        reactionSelect.innerHTML = '';
        
        // Добавляем пустую опцию
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Выберите сообщение';
        replySelect.appendChild(defaultOption.cloneNode(true));
        reactionSelect.appendChild(defaultOption.cloneNode(true));
        
        // Добавляем все сообщения и ответы как возможные цели
        this.scenarioBuilder.actions.forEach(action => {
            if (action.type === 'message' || action.type === 'reply') {
                const option = document.createElement('option');
                option.value = action.id;
                
                let prefix = action.type === 'reply' ? '[Ответ] ' : '[Сообщение] ';
                let targetInfo = action.type === 'reply' ? `(на ${action.replyId}) ` : '';
                let preview = action.message.substring(0, 30) + (action.message.length > 30 ? '...' : '');
                
                option.textContent = `${prefix}ID: ${action.id} ${targetInfo}${preview}`;
                
                replySelect.appendChild(option.cloneNode(true));
                reactionSelect.appendChild(option.cloneNode(true));
            }
        });
    }

    async createActionFromForm() {
        try {
            const type = this.modal.querySelector('#actionType').value;
            const account = this.modal.querySelector('#accountName').value;
            const timeDelay = parseInt(this.modal.querySelector('#timeDelay').value) || 0;
            const replyId = this.modal.querySelector('#replySelect').value || null;
            
            // Базовый объект действия
            const action = {
                id: this.modal.querySelector('#saveActionBtn').dataset.editId || this.scenarioBuilder.nextId++,
                type,
                account,
                timeDelay,
                replyId: replyId ? parseInt(replyId) : null
            };

            // Добавляем сообщение для типов, которые его поддерживают
            if (['message', 'media_message'].includes(type)) {
                const message = this.modal.querySelector('#messageText').value.trim();
                if (!message) {
                    alert('Введите текст сообщения');
                    return null;
                }
                action.message = message;
            }

            // Для медиа действий
            if (type === 'media' || type === 'media_message') {
                const mediaFile = this.modal.querySelector('#mediaFile').files[0];
                if (!mediaFile && !this.modal.querySelector('.current-media')) {
                    alert('Выберите медиафайл');
                    return null;
                }

                if (mediaFile) {
                    const formData = new FormData();
                    formData.append('media', mediaFile);
                    
                    try {
                        const response = await fetch('http://localhost:5000/upload-media', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        if (!data.success) {
                            throw new Error(data.error || 'Ошибка загрузки файла');
                        }
                        
                        action.mediaPath = data.path;
                        
                        // Обновляем отображение текущего медиафайла
                        const mediaInfo = document.createElement('div');
                        mediaInfo.className = 'current-media';
                        mediaInfo.textContent = `Текущий файл: ${data.path}`;
                        
                        const mediaFields = this.modal.querySelector('.media-fields');
                        const existingInfo = mediaFields.querySelector('.current-media');
                        if (existingInfo) {
                            existingInfo.remove();
                        }
                        mediaFields.prepend(mediaInfo);
                        
                    } catch (error) {
                        console.error('Error uploading media:', error);
                        alert(error.message || 'Ошибка при загрузке файла');
                        return null;
                    }
                } else {
                    action.mediaPath = this.modal.querySelector('.current-media').textContent.split(': ')[1];
                }
            }

            return action;
        } catch (error) {
            console.error('Error creating action:', error);
            return null;
        }
    }

    async saveMediaFile(file) {
        const formData = new FormData();
        formData.append('media', file);
        
        try {
            const response = await fetch('/api/upload-media', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error('Ошибка загрузки файла');
            
            const data = await response.json();
            return data.path; // Путь к сохраненному файлу
        } catch (error) {
            console.error('Error uploading media:', error);
            throw error;
        }
    }

    clearForm() {
        // Очищаем все поля формы
        this.modal.querySelector('#actionType').value = 'message';
        this.modal.querySelector('#accountName').value = '';
        this.modal.querySelector('#timeDelay').value = '0';
        this.modal.querySelector('#messageText').value = '';
        this.modal.querySelector('#replyId').value = '';
        this.modal.querySelector('#reactionId').value = '';
        this.modal.querySelector('#reactionEmoji').value = '👍';
        
        // Очищаем информацию о медиа
        const mediaFields = this.modal.querySelector('.media-fields');
        const existingMediaInfo = mediaFields.querySelector('.current-media');
        if (existingMediaInfo) {
            existingMediaInfo.remove();
        }
        
        // Очищаем input файла
        const mediaFileInput = this.modal.querySelector('#mediaFile');
        if (mediaFileInput) {
            mediaFileInput.value = '';
        }
        
        // Сбрасываем отображение полей
        this.toggleActionFields('message');
    }

    editAction(action) {
        // Очищаем предыдущую информацию о медиа
        const mediaFields = this.modal.querySelector('.media-fields');
        const existingMediaInfo = mediaFields.querySelector('.current-media');
        if (existingMediaInfo) {
            existingMediaInfo.remove();
        }

        // Очищаем input файла
        const mediaFileInput = this.modal.querySelector('#mediaFile');
        if (mediaFileInput) {
            mediaFileInput.value = '';
        }

        // Заполняем форму данными действия
        this.modal.querySelector('#actionType').value = action.type;
        this.modal.querySelector('#accountName').value = action.account;
        this.modal.querySelector('#timeDelay').value = action.timeDelay;
        
        // Показываем нужные поля
        this.toggleActionFields(action.type);
        
        // Заполняем специфичные поля в зависимости от типа
        switch(action.type) {
            case 'message':
                this.modal.querySelector('#messageText').value = action.message;
                break;
            case 'reply':
                this.modal.querySelector('#messageText').value = action.message;
                this.modal.querySelector('#replyId').value = action.replyId;
                break;
            case 'reaction':
                this.modal.querySelector('#reactionId').value = action.reactionId;
                this.modal.querySelector('#reactionEmoji').value = action.reaction;
                break;
            case 'media':
            case 'media_message':
                if (action.mediaPath) {
                    const mediaInfo = document.createElement('div');
                    mediaInfo.className = 'current-media';
                    mediaInfo.textContent = `Текущий файл: ${action.mediaPath}`;
                    mediaFields.prepend(mediaInfo);
                }
                if (action.type === 'media_message') {
                    this.modal.querySelector('#messageText').value = action.message || '';
                }
                break;
        }
        
        // Сохраняем ID редактируемого действия
        this.modal.querySelector('#saveActionBtn').dataset.editId = action.id;
        
        // Меняем текст кнопки
        this.modal.querySelector('#saveActionBtn').textContent = 'Сохранить изменения';
        
        // Показываем модальное окно
        this.show();
    }
} 