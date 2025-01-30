class ScenarioBuilder {
    constructor() {
        this.actions = [];
        this.nextId = 1;
        this.canvas = document.getElementById('scenarioCanvas');
        this.connections = [];
        this.draggedNode = null;
        this.selectedNode = null;
        this.dragOffset = { x: 0, y: 0 };
        
        this.actionSettingsModal = new ActionSettingsModal(this);
        this.initEventListeners();
        this.initCanvas();
        this.loadScenarioFromStorage();
    }

    loadScenarioFromStorage() {
        const savedScenario = sessionStorage.getItem('editingScenario');
        if (savedScenario) {
            try {
                const scenarioData = JSON.parse(savedScenario);
                document.querySelector('.scenario-name-input').value = scenarioData.name;

                if (scenarioData.actions && scenarioData.actions.length > 0) {
                    this.nextId = Math.max(...scenarioData.actions.map(a => a.id)) + 1;
                    scenarioData.actions.forEach(action => {
                        this.addActionToCanvas(action);
                    });
                }
            } catch (error) {
                console.error('Ошибка при загрузке сценария:', error);
            }
        }
    }

    initCanvas() {
        this.canvas.style.position = 'relative';
        this.canvas.style.minHeight = '400px';
    }

    initEventListeners() {
        document.getElementById('addActionBtn').addEventListener('click', () => {
            this.actionSettingsModal.show();
        });

        document.getElementById('saveScenario').addEventListener('click', () => {
            this.saveScenario();
        });

        this.canvas.addEventListener('mousemove', (e) => this.handleDrag(e));
        this.canvas.addEventListener('mouseup', () => this.stopDragging());
        this.canvas.addEventListener('mouseleave', () => this.stopDragging());

        document.querySelector('.close').addEventListener('click', () => {
            const modal = document.getElementById('actionSettingsModal');
            modal.style.display = 'none';
        });

        window.addEventListener('click', (e) => {
            const modal = document.getElementById('actionSettingsModal');
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    addActionToCanvas(action) {
        const node = document.createElement('div');
        node.className = 'action-node';
        node.dataset.id = action.id;
        
        let content = `
            <div class="action-header">
                <span class="action-type">${action.type}</span>
                <span class="action-account">${action.account}</span>
                <div class="action-controls">
                    <button class="edit-btn" onclick="window.scenarioBuilder.editAction(${action.id})">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                    <button class="delete-action-btn" onclick="window.scenarioBuilder.deleteAction(${action.id})">×</button>
                </div>
            </div>
            <div class="action-content">
                <div>Задержка: ${action.timeDelay}с</div>
        `;

        switch (action.type) {
            case 'message':
                content += `<div>Сообщение: ${action.message}</div>`;
                break;
            case 'reply':
                content += `
                    <div>Ответ на: #${action.replyId}</div>
                    <div>Сообщение: ${action.message}</div>
                `;
                break;
            case 'reaction':
                content += `
                    <div>Реакция на: #${action.reactionId}</div>
                    <div>Эмодзи: ${action.reaction}</div>
                `;
                break;
        }

        content += '</div>';
        node.innerHTML = content;

        // Добавляем точки соединения
        const inputPoint = document.createElement('div');
        inputPoint.className = 'connection-point input';
        node.appendChild(inputPoint);

        const outputPoint = document.createElement('div');
        outputPoint.className = 'connection-point output';
        node.appendChild(outputPoint);

        // Позиционируем узел
        node.style.left = `${action.x}px`;
        node.style.top = `${action.y}px`;

        // Добавляем обработчики для drag&drop
        node.addEventListener('mousedown', (e) => this.startDragging(e, node));

        this.canvas.appendChild(node);
        this.actions.push(action);

        // Создаем соединения
        if (action.type === 'reply' && action.replyId) {
            this.createConnection(
                document.querySelector(`.action-node[data-id="${action.replyId}"]`),
                node,
                'reply'
            );
        } else if (action.type === 'reaction' && action.reactionId) {
            this.createConnection(
                document.querySelector(`.action-node[data-id="${action.reactionId}"]`),
                node,
                'reaction'
            );
        }
    }

    startDragging(e, node) {
        this.draggedNode = node;
        const rect = node.getBoundingClientRect();
        this.dragOffset = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    }

    handleDrag(e) {
        if (!this.draggedNode) return;

        const canvasRect = this.canvas.getBoundingClientRect();
        let x = e.clientX - canvasRect.left - this.dragOffset.x;
        let y = e.clientY - canvasRect.top - this.dragOffset.y;

        // Ограничиваем движение пределами canvas
        x = Math.max(0, Math.min(x, canvasRect.width - this.draggedNode.offsetWidth));
        y = Math.max(0, Math.min(y, canvasRect.height - this.draggedNode.offsetHeight));

        this.draggedNode.style.left = `${x}px`;
        this.draggedNode.style.top = `${y}px`;

        // Обновляем позицию в данных действия
        const actionId = parseInt(this.draggedNode.dataset.id);
        const action = this.actions.find(a => a.id === actionId);
        if (action) {
            action.x = x;
            action.y = y;
        }

        // Обновляем соединения
        this.updateConnections();
    }

    stopDragging() {
        this.draggedNode = null;
    }

    deleteAction(id) {
        const index = this.actions.findIndex(a => a.id === id);
        if (index !== -1) {
            this.actions.splice(index, 1);
            const node = document.querySelector(`.action-node[data-id="${id}"]`);
            if (node) node.remove();
            this.updateConnections();
        }
    }

    updateConnections() {
        // Удаляем все существующие соединения
        this.canvas.querySelectorAll('.connection-line').forEach(line => line.remove());

        // Пересоздаем соединения
        this.actions.forEach(action => {
            if (action.type === 'reply' && action.replyId) {
                const fromNode = document.querySelector(`.action-node[data-id="${action.replyId}"]`);
                const toNode = document.querySelector(`.action-node[data-id="${action.id}"]`);
                if (fromNode && toNode) {
                    this.createConnection(fromNode, toNode, 'reply');
                }
            } else if (action.type === 'reaction' && action.reactionId) {
                const fromNode = document.querySelector(`.action-node[data-id="${action.reactionId}"]`);
                const toNode = document.querySelector(`.action-node[data-id="${action.id}"]`);
                if (fromNode && toNode) {
                    this.createConnection(fromNode, toNode, 'reaction');
                }
            }
        });
    }

    createConnection(fromNode, toNode, type) {
        if (!fromNode || !toNode) return;

        const line = document.createElement('div');
        line.className = `connection-line connection-${type}`;
        
        const fromRect = fromNode.getBoundingClientRect();
        const toRect = toNode.getBoundingClientRect();
        const canvasRect = this.canvas.getBoundingClientRect();
        
        const from = {
            x: fromRect.right - canvasRect.left,
            y: fromRect.top + (fromRect.height / 2) - canvasRect.top
        };
        
        const to = {
            x: toRect.left - canvasRect.left,
            y: toRect.top + (toRect.height / 2) - canvasRect.top
        };
        
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const length = Math.sqrt(dx * dx + dy * dy);
        const angle = Math.atan2(dy, dx);
        
        Object.assign(line.style, {
            width: `${length}px`,
            left: `${from.x}px`,
            top: `${from.y}px`,
            transform: `rotate(${angle}rad)`,
            position: 'absolute',
            height: '0',
            borderTopStyle: 'dashed',
            borderTopWidth: '2px',
            borderTopColor: type === 'reply' ? '#4d9fff' : '#ff4d00',
            background: 'none',
            pointerEvents: 'none',
            zIndex: '1',
            transformOrigin: 'left center'
        });
        
        this.canvas.appendChild(line);
    }

    saveScenario() {
        const name = document.querySelector('.scenario-name-input').value;
        if (!name) {
            alert('Укажите название сценария');
            return;
        }

        const scenario = {
            name: name,
            actions: this.actions.map(action => ({
                ...action,
                x: parseInt(action.x),
                y: parseInt(action.y)
            }))
        };

        // Создаем Blob с данными сценария
        const blob = new Blob([JSON.stringify(scenario, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        
        // Создаем ссылку для скачивания
        const a = document.createElement('a');
        a.href = url;
        a.download = `${name}.json`;
        
        // Добавляем ссылку в DOM и эмулируем клик
        document.body.appendChild(a);
        a.click();
        
        // Очищаем
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        // Перенаправляем на страницу со списком сценариев
        window.location.href = 'scripts.html';
    }

    editAction(id) {
        const action = this.actions.find(a => a.id === id);
        if (action) {
            this.actionSettingsModal.editAction(action);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.scenarioBuilder = new ScenarioBuilder();
}); 