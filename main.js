const { app, BrowserWindow } = require('electron');
const path = require('path');

// Добавляем обработку путей для Python скрипта
app.on('ready', () => {
    // Добавляем путь к Python в PATH
    const pythonPath = 'C:\\Python39;C:\\Python39\\Scripts';
    process.env.PATH = `${process.env.PATH};${pythonPath};${path.join(__dirname, 'scripts')}`;
    
    // Устанавливаем рабочую директорию
    process.chdir(__dirname);
});

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: true,
            enableRemoteModule: true,
            preload: path.join(__dirname, 'preload.js')
        }
    });

    win.loadFile('index.html');
    
    // Автоматически открываем DevTools
    // win.webContents.openDevTools();
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
