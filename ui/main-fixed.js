const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let authWindow;
let chessqlServer;
let pendingOAuthData = null;

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
  let serverPath, serverArgs, serverCwd;
  
  if (app.isPackaged) {
    // Production: Use bundled PyInstaller executable
    const resourcesPath = process.resourcesPath;
    serverPath = path.join(resourcesPath, 'chessql-server');
    
    // On Windows, add .exe extension
    if (process.platform === 'win32') {
      serverPath += '.exe';
    }
    
    serverArgs = [];
    serverCwd = undefined;
    
    console.log(`Starting bundled server: ${serverPath}`);
  } else {
    // Development: Use venv Python
    const chessqlPath = path.join(__dirname, '..', 'backend');
    const venvPython = process.platform === 'win32'
      ? path.join(chessqlPath, '.venv', 'Scripts', 'python.exe')
      : path.join(chessqlPath, '.venv', 'bin', 'python');
    
    serverPath = venvPython;
    serverArgs = ['start_server.py'];
    serverCwd = chessqlPath;
    
    console.log(`Starting dev server: ${serverPath} ${serverArgs.join(' ')} in ${serverCwd}`);
  }
  
  // Start the ChessQL server
  chessqlServer = spawn(serverPath, serverArgs, {
    cwd: serverCwd,
    stdio: 'pipe',
    env: { ...process.env }
  });

  chessqlServer.stdout.on('data', (data) => {
    console.log(`ChessQL Server: ${data}`);
  });

  chessqlServer.stderr.on('data', (data) => {
    console.error(`ChessQL Server Error: ${data}`);
  });

  chessqlServer.on('error', (err) => {
    console.error(`Failed to start ChessQL Server: ${err.message}`);
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

// Handle OAuth flow - open auth window
ipcMain.handle('start-oauth', async (event, { authUrl, codeVerifier, state }) => {
  return new Promise((resolve, reject) => {
    // Store OAuth data for callback
    pendingOAuthData = { codeVerifier, state };
    
    // Create OAuth window
    authWindow = new BrowserWindow({
      width: 600,
      height: 700,
      parent: mainWindow,
      modal: true,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true
      },
      title: 'Login with Lichess'
    });

    // Load the auth URL
    authWindow.loadURL(authUrl);

    // Listen for navigation to callback URL
    authWindow.webContents.on('will-redirect', (event, url) => {
      handleOAuthCallback(url, resolve, reject);
    });

    authWindow.webContents.on('will-navigate', (event, url) => {
      handleOAuthCallback(url, resolve, reject);
    });

    // Handle window close
    authWindow.on('closed', () => {
      authWindow = null;
      if (pendingOAuthData) {
        reject(new Error('OAuth window closed'));
        pendingOAuthData = null;
      }
    });
  });
});

async function handleOAuthCallback(url, resolve, reject) {
  const callbackUrl = 'http://localhost:9090/auth/lichess/callback';
  
  if (url.startsWith(callbackUrl)) {
    try {
      const urlObj = new URL(url);
      const code = urlObj.searchParams.get('code');
      const state = urlObj.searchParams.get('state');
      const error = urlObj.searchParams.get('error');

      if (error) {
        reject(new Error(error));
        if (authWindow) {
          authWindow.close();
        }
        return;
      }

      if (code && state && pendingOAuthData) {
        // Exchange code for token using our backend
        const fetch = require('node-fetch');
        const response = await fetch(`http://localhost:9090/auth/lichess/callback`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code: code,
            state: state,
            code_verifier: pendingOAuthData.codeVerifier
          })
        });

        const result = await response.json();
        
        if (response.ok) {
          resolve({ success: true, data: result });
          
          // Send success to renderer
          if (mainWindow) {
            mainWindow.webContents.send('oauth-success', result);
          }
        } else {
          reject(new Error(result.detail || 'OAuth failed'));
        }
      }

      pendingOAuthData = null;
      if (authWindow) {
        authWindow.close();
      }
    } catch (err) {
      reject(err);
      if (authWindow) {
        authWindow.close();
      }
    }
  }
}
