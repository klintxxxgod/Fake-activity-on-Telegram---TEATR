const { contextBridge, ipcRenderer } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

// Экспортируем необходимые API в окно браузера
contextBridge.exposeInMainWorld('api', {
    executeCommand: async (command) => {
        return new Promise((resolve, reject) => {
            try {
                const powershell = spawn('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', command], {
                    windowsHide: false,
                    detached: true,
                    stdio: 'inherit'
                });

                powershell.on('error', (error) => {
                    reject(error);
                });

                powershell.unref();
                resolve(true);

            } catch (error) {
                reject(error);
            }
        });
    },
    path: path,
    __dirname: __dirname
}); 