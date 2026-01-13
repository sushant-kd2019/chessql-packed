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

// Check if server is already running on port 9090 (synchronous check)
function isServerRunning() {
  try {
    const { execSync } = require('child_process');
    const result = execSync('lsof -ti :9090', { encoding: 'utf8', timeout: 2000 });
    const hasProcess = result.trim().length > 0;
    console.log(`Port 9090 check: ${hasProcess ? 'Server already running (PID: ' + result.trim() + ')' : 'Port is free'}`);
    return hasProcess;
  } catch (err) {
    // lsof returns exit code 1 when no process found, which throws an error
    console.log('Port 9090 check: Port is free (no process found)');
    return false;
  }
}

// Start the ChessQL server
function startChessqlServer() {
  // Check if server is already running (e.g., started by start-all.sh)
  const alreadyRunning = isServerRunning();
  if (alreadyRunning) {
    console.log('ChessQL Server already running - skipping startup');
    return;
  }

  const chessqlPath = path.join(__dirname, '..', 'backend');
  
  // Start the ChessQL server using the virtual environment
  const pythonPath = path.join(chessqlPath, '.venv', 'bin', 'python');
  const serverScript = path.join(chessqlPath, 'start_server.py');
  
  console.log(`Starting dev server: ${pythonPath} start_server.py in ${chessqlPath}`);
  
  chessqlServer = spawn(pythonPath, ['start_server.py'], {
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
