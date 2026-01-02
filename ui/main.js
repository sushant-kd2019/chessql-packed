const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let chessqlServer;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, 'assets/icon.png'), // Optional icon
    title: 'ChessQL Desktop'
  });

  // Load the index.html file
  mainWindow.loadFile('index.html');

  // Open DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// This method will be called when Electron has finished initialization
app.whenReady().then(() => {
  createWindow();
  startChessqlServer();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Start the ChessQL server
function startChessqlServer() {
  const chessqlPath = path.join(__dirname, '..', 'chessql');
  
  // Start the ChessQL server
  chessqlServer = spawn('python3', ['server.py'], {
    cwd: chessqlPath,
    stdio: 'pipe'
  });

  chessqlServer.stdout.on('data', (data) => {
    console.log(`ChessQL Server: ${data}`);
  });

  chessqlServer.stderr.on('data', (data) => {
    console.error(`ChessQL Server Error: ${data}`);
  });

  chessqlServer.on('close', (code) => {
    console.log(`ChessQL Server exited with code ${code}`);
  });

  // Give the server a moment to start
  setTimeout(() => {
    console.log('ChessQL Server should be running on http://localhost:9090');
  }, 2000);
}

// Clean up server when app quits
app.on('before-quit', () => {
  if (chessqlServer) {
    chessqlServer.kill();
  }
});

// Handle API requests from renderer
ipcMain.handle('api-request', async (event, { endpoint, method, data }) => {
  try {
    const fetch = require('node-fetch');
    const response = await fetch(`http://localhost:9090${endpoint}`, {
      method: method || 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined
    });
    
    const result = await response.json();
    return { success: true, data: result };
  } catch (error) {
    console.error('API Request Error:', error);
    return { success: false, error: error.message };
  }
});
