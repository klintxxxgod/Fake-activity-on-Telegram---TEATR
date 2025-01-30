class ActionSettingsModal {
    constructor(scenarioBuilder) {
        this.scenarioBuilder = scenarioBuilder;
        this.modal = document.getElementById('actionSettingsModal');
        this.dynamicFields = document.getElementById('dynamicFields');
        this.initEventListeners();
    }

    initEventListeners() {
        document.getElementById('actionType').addEventListener('change', (e) => {
            this.updateFields(e.target.value);
        });

        document.querySelector('.close').addEventListener('click', () => {
            this.hide();
        });

        document.getElementById('saveActionBtn').addEventListener('click', () => {
            this.saveAction();
        });

        // Инициализируем поля для начального типа действия
        this.updateFields(document.getElementById('actionType').value);
    }

    updateFields(actionType) {
        this.dynamicFields.innerHTML = '';

        // Добавляем поле ответа для всех типов кроме reaction
        if (actionType !== 'reaction') {
            this.addReplyField();
        }

        switch (actionType) {
            case 'message':
                this.addMessageField();
                break;
            case 'media':
                this.addMediaField();
                break;
            case 'media_message':
                this.addMediaField();
                this.addMessageField();
                break;
            case 'reaction':
                this.addReactionField();
                break;
        }
    }

    addReplyField() {
        const div = document.createElement('div');
        div.className = 'form-group';
        div.innerHTML = `
            <label>Ответить на сообщение</label>
            <select id="replySelect">
                <option value="">Без ответа</option>
                ${this.getExistingMessagesOptions()}
            </select>
        `;
        this.dynamicFields.appendChild(div);
    }

    addMessageField() {
        const div = document.createElement('div');
        div.className = 'form-group';
        div.innerHTML = `
            <label>Текст сообщения</label>
            <textarea id="messageText" rows="4"></textarea>
        `;
        this.dynamicFields.appendChild(div);
    }

    addMediaField() {
        const div = document.createElement('div');
        div.className = 'form-group';
        div.innerHTML = `
            <label>Медиафайл</label>
            <input type="file" id="mediaFile" accept="image/*,video/*">
            <div class="media-preview"></div>
        `;
        this.dynamicFields.appendChild(div);

        // Добавляем обработчик загрузки файла
        div.querySelector('#mediaFile').addEventListener('change', (e) => {
            this.handleMediaUpload(e);
        });
    }

    addReactionField() {
        const div = document.createElement('div');
        div.className = 'form-group';
        div.innerHTML = `
            <label>Реакция на сообщение</label>
            <select id="reactionMessageSelect" required>
                <option value="">Выберите сообщение</option>
                ${this.getExistingMessagesOptions()}
            </select>
            <label>Эмодзи</label>
            <select id="reactionEmoji">
                <option value="👍">👍 Палец вверх</option>
                <option value="❤️">❤️ Сердце</option>
                <option value="🔥">🔥 Огонь</option>
                <option value="👏">👏 Аплодисменты</option>
                <option value="😊">😊 Улыбка</option>
                <option value="🎉">🎉 Праздник</option>
                <option value="👌">👌 Окей</option>
            </select>
        `;
        this.dynamicFields.appendChild(div);
    }

    getExistingMessagesOptions() {
        return this.scenarioBuilder.actions
            .filter(a => ['message', 'media', 'media_message'].includes(a.type))
            .map(a => {
                let label = `Действие #${a.id} (${a.type})`;
                if (a.message) {
                    label += `: ${a.message.substring(0, 30)}${a.message.length > 30 ? '...' : ''}`;
                }
                if (a.mediaPath) {
                    label += ' [медиа]';
                }
                return `<option value="${a.id}">${label}</option>`;
            })
            .join('');
    }

    show() {
        this.modal.style.display = 'block';
        this.updateFields(document.getElementById('actionType').value);
    }

    hide() {
        this.modal.style.display = 'none';
    }

    async handleMediaUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const formData = new FormData();
            formData.append('media', file);

            const response = await fetch('http://localhost:5000/upload-media', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error);
            }

            // Обновляем информацию о медиафайле
            const mediaPreview = document.querySelector('.media-preview');
            mediaPreview.innerHTML = `Загружен файл: ${data.path}`;
            mediaPreview.dataset.path = data.path;

        } catch (error) {
            console.error('Error uploading media:', error);
            alert('Ошибка при загрузке медиафайла: ' + error.message);
        }
    }

    async saveAction() {
        try {
            const actionType = document.getElementById('actionType').value;
            const account = document.getElementById('accountName').value;
            const timeDelay = parseInt(document.getElementById('timeDelay').value) || 0;
            
            // Базовый объект действия
            const action = {
                id: this.modal.querySelector('#saveActionBtn').dataset.editId || this.scenarioBuilder.nextId++,
                type: actionType,
                account: account,
                timeDelay: timeDelay,
                x: 50, // Начальная позиция на холсте
                y: 50
            };

            // Добавляем поле reply для всех типов кроме reaction
            if (actionType !== 'reaction') {
                const replySelect = document.getElementById('replySelect');
                if (replySelect && replySelect.value) {
                    action.replyId = parseInt(replySelect.value);
                }
            }

            // Добавляем специфичные поля в зависимости от типа
            switch (actionType) {
                case 'message':
                    action.message = document.getElementById('messageText').value;
                    break;

                case 'media':
                    const mediaFile = document.getElementById('mediaFile');
                    const mediaPreview = document.querySelector('.media-preview');
                    if (mediaPreview && mediaPreview.dataset.path) {
                        action.mediaPath = mediaPreview.dataset.path;
                    } else if (mediaFile.files.length > 0) {
                        const formData = new FormData();
                        formData.append('media', mediaFile.files[0]);
                        
                        const response = await fetch('http://localhost:5000/upload-media', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            action.mediaPath = result.path;
                        } else {
                            throw new Error(result.error || 'Ошибка при загрузке медиа');
                        }
                    }
                    break;

                case 'media_message':
                    action.message = document.getElementById('messageText').value;
                    const mediaFileMsg = document.getElementById('mediaFile');
                    const mediaPreviewMsg = document.querySelector('.media-preview');
                    if (mediaPreviewMsg && mediaPreviewMsg.dataset.path) {
                        action.mediaPath = mediaPreviewMsg.dataset.path;
                    } else if (mediaFileMsg.files.length > 0) {
                        const formData = new FormData();
                        formData.append('media', mediaFileMsg.files[0]);
                        
                        const response = await fetch('http://localhost:5000/upload-media', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        if (result.success) {
                            action.mediaPath = result.path;
                        } else {
                            throw new Error(result.error || 'Ошибка при загрузке медиа');
                        }
                    }
                    break;

                case 'reaction':
                    action.reaction = document.getElementById('reactionEmoji').value;
                    action.reactionId = parseInt(document.getElementById('reactionMessageSelect').value);
                    break;
            }

            // Добавляем действие в сценарий
            this.scenarioBuilder.addActionToCanvas(action);
            this.hide();
            return true;

        } catch (error) {
            console.error('Error saving action:', error);
            alert('Ошибка при сохранении действия: ' + error.message);
            return false;
        }
    }

    // Продолжение в следующем сообщении...
} 