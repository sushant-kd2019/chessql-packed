const { ipcRenderer, shell } = require('electron');
const { Chess, Chess960 } = require('chess.js');

class ChessQLApp {
    constructor() {
        this.currentGames = [];
        this.currentGame = null;
        this.currentMoveIndex = 0;
        this.chess = new Chess();
        this.gameMoves = []; // Store the moves separately
        this.startingFen = null; // Starting FEN for Chess960 games
        this.isChess960 = false; // Flag for Chess960 games
        
        // Pagination
        this.currentPage = 1;
        this.gamesPerPage = 20; // Frontend page size
        this.backendPageSize = 500; // Backend page size
        this.hasMoreGames = false;
        this.isLoadingMore = false;
        this.currentQuery = '';
        this.currentSearchType = 'natural';
        this.totalCount = 0;
        this.totalPages = 0;
        this.allGames = []; // Store all loaded games
        this.currentBackendPage = 1; // Track which backend page we're on
        
        // Accounts
        this.accounts = [];
        this.syncIntervals = {}; // Store sync status polling intervals
        this.pendingOAuth = null; // Store pending OAuth data
        
        // OpenAI key state
        this.openaiKeyConfigured = false;
        
        this.initializeElements();
        this.bindEvents();
        this.loadAccounts(); // Load accounts on startup
        this.checkOpenAIKeyStatus(); // Check OpenAI key on startup
    }

    initializeElements() {
        this.queryInput = document.getElementById('queryInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        this.errorMessage = document.getElementById('errorMessage');
        this.resultsContainer = document.getElementById('resultsContainer');
        this.gameModal = document.getElementById('gameModal');
        this.closeModal = document.getElementById('closeModal');
        this.chessBoard = document.getElementById('chessBoard');
        this.movesList = document.getElementById('movesList');
        
        // Game info elements
        this.gameTitle = document.getElementById('gameTitle');
        this.whitePlayerName = document.getElementById('whitePlayerName');
        this.blackPlayerName = document.getElementById('blackPlayerName');
        this.whitePlayerElo = document.getElementById('whitePlayerElo');
        this.blackPlayerElo = document.getElementById('blackPlayerElo');
        this.gameResult = document.getElementById('gameResult');
        this.gameDate = document.getElementById('gameDate');
        this.gameTimeControl = document.getElementById('gameTimeControl');
        this.gameSpeed = document.getElementById('gameSpeed');
        this.gameVariant = document.getElementById('gameVariant');
        this.gameSite = document.getElementById('gameSite');
        this.copySiteBtn = document.getElementById('copySiteBtn');
        this.gameOpening = document.getElementById('gameOpening');
        this.gameTermination = document.getElementById('gameTermination');
        
        // Move controls
        this.prevMoveBtn = document.getElementById('prevMove');
        this.nextMoveBtn = document.getElementById('nextMove');
        this.firstMoveBtn = document.getElementById('firstMove');
        this.lastMoveBtn = document.getElementById('lastMove');
        this.flipBoardBtn = document.getElementById('flipBoardBtn');
        
        // Board state
        this.isBoardFlipped = false;
        
        // Account elements
        this.accountsBtn = document.getElementById('accountsBtn');
        this.accountsBadge = document.getElementById('accountsBadge');
        this.accountsPanel = document.getElementById('accountsPanel');
        this.closeAccountsPanel = document.getElementById('closeAccountsPanel');
        this.addLichessAccountBtn = document.getElementById('addLichessAccountBtn');
        this.addChesscomAccountBtn = document.getElementById('addChesscomAccountBtn');
        
        // Debug: Check if buttons exist
        if (!this.addChesscomAccountBtn) {
            console.error('Chess.com account button not found!');
        }
        this.accountsList = document.getElementById('accountsList');
        this.accountModal = document.getElementById('accountModal');
        this.closeAccountModal = document.getElementById('closeAccountModal');
        this.startOAuthBtn = document.getElementById('startOAuthBtn');
        this.oauthStatus = document.getElementById('oauthStatus');
        
        // Account selector in search
        this.accountSelect = document.getElementById('accountSelect');
        
        // Sync toast elements
        this.syncToast = document.getElementById('syncToast');
        this.syncUsername = document.getElementById('syncUsername');
        this.syncStatusText = document.getElementById('syncStatusText');
        this.syncProgressFill = document.getElementById('syncProgressFill');
        this.syncGamesCount = document.getElementById('syncGamesCount');
        this.syncNewGames = document.getElementById('syncNewGames');
        this.closeSyncToast = document.getElementById('closeSyncToast');
        
        // OpenAI key modal elements
        this.openaiKeyModal = document.getElementById('openaiKeyModal');
        this.openaiKeyInput = document.getElementById('openaiKeyInput');
        this.toggleKeyVisibilityBtn = document.getElementById('toggleKeyVisibility');
        this.openaiKeyError = document.getElementById('openaiKeyError');
        this.openaiHelpLink = document.getElementById('openaiHelpLink');
        this.saveOpenaiKeyBtn = document.getElementById('saveOpenaiKeyBtn');
        this.skipOpenaiKeyBtn = document.getElementById('skipOpenaiKeyBtn');
    }

    bindEvents() {
        this.searchBtn.addEventListener('click', () => this.performSearch());
        this.clearBtn.addEventListener('click', () => this.clearSearch());
        this.queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Example query clicks
        document.querySelectorAll('.example-query').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.queryInput.value = e.target.dataset.query;
                this.performSearch();
            });
        });
        
        // Modal events
        this.closeModal.addEventListener('click', () => this.closeGameModal());
        this.gameModal.addEventListener('click', (e) => {
            if (e.target === this.gameModal) {
                this.closeGameModal();
            }
        });
        
        // Move controls
        this.prevMoveBtn.addEventListener('click', () => this.previousMove());
        this.nextMoveBtn.addEventListener('click', () => this.nextMove());
        this.firstMoveBtn.addEventListener('click', () => this.goToFirstMove());
        this.lastMoveBtn.addEventListener('click', () => this.goToLastMove());
        
        // Flip board button
        this.flipBoardBtn.addEventListener('click', () => this.flipBoard());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        
        // Copy site URL button
        this.copySiteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.copySiteUrl();
        });
        
        // Event delegation for pagination buttons
        document.addEventListener('click', (e) => {
            if (e.target && e.target.dataset.action === 'go-to-page') {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                this.goToPage(page);
            }
        });
        
        // Account panel events
        this.accountsBtn.addEventListener('click', () => this.toggleAccountsPanel());
        this.closeAccountsPanel.addEventListener('click', () => this.hideAccountsPanel());
        if (this.addLichessAccountBtn) {
            this.addLichessAccountBtn.addEventListener('click', () => this.showAccountModal('lichess'));
        }
        if (this.addChesscomAccountBtn) {
            this.addChesscomAccountBtn.addEventListener('click', () => {
                console.log('Chess.com button clicked');
                this.showChesscomAccountModal();
            });
        } else {
            console.error('Cannot attach event listener: Chess.com account button not found');
        }
        this.closeAccountModal.addEventListener('click', () => this.hideAccountModal());
        this.startOAuthBtn.addEventListener('click', () => this.startOAuthFlow());
        this.closeSyncToast.addEventListener('click', () => this.hideSyncToast());
        
        // OpenAI key modal events
        this.saveOpenaiKeyBtn.addEventListener('click', () => this.saveOpenAIKey());
        this.skipOpenaiKeyBtn.addEventListener('click', () => this.hideOpenAIKeyModal());
        this.toggleKeyVisibilityBtn.addEventListener('click', () => this.toggleKeyVisibility());
        this.openaiHelpLink.addEventListener('click', (e) => {
            e.preventDefault();
            shell.openExternal('https://platform.openai.com/api-keys');
        });
        this.openaiKeyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.saveOpenAIKey();
            }
        });
        
        // Close account modal on background click
        this.accountModal.addEventListener('click', (e) => {
            if (e.target === this.accountModal) {
                this.hideAccountModal();
            }
        });
        
        // Listen for OAuth success from main process
        ipcRenderer.on('oauth-success', (event, data) => {
            console.log('OAuth success:', data);
            this.loadAccounts();
            this.hideAccountModal();
            this.oauthStatus.classList.add('hidden');
            this.startOAuthBtn.disabled = false;
        });
    }

    // ==================== Account Management ====================

    async loadAccounts() {
        try {
            const response = await ipcRenderer.invoke('api-request', {
                endpoint: '/auth/accounts',
                method: 'GET'
            });

            if (response.success) {
                this.accounts = response.data || [];
                this.updateAccountsBadge();
                this.renderAccountsList();
                this.updateAccountSelector();
            }
        } catch (error) {
            console.error('Failed to load accounts:', error);
        }
    }

    updateAccountSelector() {
        // Preserve current selection
        const currentValue = this.accountSelect.value;
        
        // Clear existing options except "All accounts"
        this.accountSelect.innerHTML = '<option value="">All accounts</option>';
        
        // Add account options with platform indicator
        this.accounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account.username;
            const platform = account.platform || 'lichess';
            const platformInfo = this.getPlatformInfo(platform);
            option.textContent = `${account.username} ${platformInfo.icon}`;
            option.dataset.platform = platform;
            this.accountSelect.appendChild(option);
        });
        
        // Restore selection if still valid
        if (currentValue && this.accounts.some(a => a.username === currentValue)) {
            this.accountSelect.value = currentValue;
        } else if (this.accounts.length === 1) {
            // Auto-select if only one account
            this.accountSelect.value = this.accounts[0].username;
        }
    }

    getSelectedAccount() {
        return this.accountSelect.value || null;
    }


    updateAccountsBadge() {
        if (this.accounts.length > 0) {
            this.accountsBadge.textContent = this.accounts.length;
            this.accountsBadge.classList.remove('hidden');
        } else {
            this.accountsBadge.classList.add('hidden');
        }
    }

    toggleAccountsPanel() {
        if (this.accountsPanel.classList.contains('hidden')) {
            this.showAccountsPanel();
        } else {
            this.hideAccountsPanel();
        }
    }

    showAccountsPanel() {
        this.accountsPanel.classList.remove('hidden');
        this.loadAccounts(); // Refresh accounts list
    }

    hideAccountsPanel() {
        this.accountsPanel.classList.add('hidden');
    }

    showAccountModal(platform = 'lichess') {
        this.accountModal.classList.remove('hidden');
        this.oauthStatus.classList.add('hidden');
        // Update modal title based on platform
        const titleEl = document.getElementById('accountModalTitle');
        if (titleEl) {
            titleEl.textContent = platform === 'lichess' ? 'Link Lichess Account' : 'Add Chess.com Account';
        }
    }

    async showChesscomAccountModal() {
        console.log('showChesscomAccountModal called');
        try {
            const username = prompt('Enter your Chess.com username:');
            if (!username) {
                console.log('User cancelled username input');
                return;
            }

            // Trim whitespace
            const trimmedUsername = username.trim();
            if (!trimmedUsername) {
                alert('Username cannot be empty.');
                return;
            }

            // Validate username
            if (trimmedUsername.length < 3 || trimmedUsername.length > 25) {
                alert('Invalid Chess.com username. Username must be 3-25 characters.');
                return;
            }
            
            if (!/^[a-zA-Z0-9_-]+$/.test(trimmedUsername)) {
                alert('Invalid Chess.com username. Username can only contain letters, numbers, hyphens, and underscores.');
                return;
            }

            console.log('Adding Chess.com account:', trimmedUsername);
            
            const response = await ipcRenderer.invoke('api-request', {
                endpoint: '/auth/chesscom/add',
                method: 'POST',
                data: { username: trimmedUsername }
            });

            console.log('API response:', response);

            if (response.success) {
                await this.loadAccounts();
                alert(`Successfully added Chess.com account: ${trimmedUsername}`);
            } else {
                const errorMsg = response.error || response.data?.error || 'Failed to add account';
                throw new Error(errorMsg);
            }
        } catch (error) {
            console.error('Add Chess.com account error:', error);
            alert('Failed to add Chess.com account: ' + error.message);
        }
    }

    hideAccountModal() {
        this.accountModal.classList.add('hidden');
        this.pendingOAuth = null;
    }

    async startOAuthFlow() {
        try {
            this.oauthStatus.classList.remove('hidden');
            this.startOAuthBtn.disabled = true;

            // Start OAuth flow - get auth URL from backend
            const response = await ipcRenderer.invoke('api-request', {
                endpoint: '/auth/lichess/start',
                method: 'POST'
            });

            if (response.success && response.data.auth_url) {
                // Open OAuth window in Electron
                const oauthResult = await ipcRenderer.invoke('start-oauth', {
                    authUrl: response.data.auth_url,
                    codeVerifier: response.data.code_verifier,
                    state: response.data.state
                });

                if (oauthResult.success) {
                    // Refresh accounts list
                    await this.loadAccounts();
                    this.hideAccountModal();
                    
                    // Show success message
                    const username = oauthResult.data.username || 'Unknown';
                    alert(`Successfully linked account: ${username}`);
                }
            } else {
                throw new Error(response.error || 'Failed to start OAuth flow');
            }
        } catch (error) {
            console.error('OAuth flow error:', error);
            if (error.message !== 'OAuth window closed') {
                this.showError('Failed to link account: ' + error.message);
            }
        } finally {
            this.oauthStatus.classList.add('hidden');
            this.startOAuthBtn.disabled = false;
        }
    }

    // Listen for OAuth success from main process
    setupOAuthListener() {
        ipcRenderer.on('oauth-success', (event, data) => {
            console.log('OAuth success:', data);
            this.loadAccounts();
            this.hideAccountModal();
        });
    }

    renderAccountsList() {
        if (this.accounts.length === 0) {
            this.accountsList.innerHTML = `
                <div class="no-accounts">
                    <p>No accounts linked yet.</p>
                    <p class="hint">Click "Link Lichess Account" to get started.</p>
                </div>
            `;
            return;
        }

        this.accountsList.innerHTML = this.accounts.map(account => this.createAccountCard(account)).join('');

        // Bind events for account cards
        this.accountsList.querySelectorAll('.sync-btn.primary').forEach(btn => {
            btn.addEventListener('click', () => {
                const username = btn.dataset.username;
                const platform = btn.dataset.platform || 'lichess';
                const endpoint = btn.dataset.endpoint || '/sync/start';
                this.startSync(username, false, platform, endpoint);
            });
        });

        this.accountsList.querySelectorAll('.sync-btn.secondary').forEach(btn => {
            btn.addEventListener('click', () => {
                const username = btn.dataset.username;
                const platform = btn.dataset.platform || 'lichess';
                const endpoint = btn.dataset.endpoint || '/sync/start';
                this.startFullSync(username, platform, endpoint);
            });
        });

        this.accountsList.querySelectorAll('.account-action-btn.delete').forEach(btn => {
            btn.addEventListener('click', () => {
                const username = btn.dataset.username;
                const platform = btn.dataset.platform || 'lichess';
                this.deleteAccount(username, platform);
            });
        });

        this.accountsList.querySelectorAll('.account-action-btn.refresh').forEach(btn => {
            btn.addEventListener('click', () => {
                const username = btn.dataset.username;
                const platform = btn.dataset.platform || 'lichess';
                this.refreshAccountStatus(username, platform);
            });
        });
    }

    getPlatformInfo(platform) {
        const platforms = {
            'lichess': { name: 'Lichess', icon: '♞', color: '#4CAF50', class: 'lichess' },
            'chesscom': { name: 'Chess.com', icon: '♟', color: '#7FA650', class: 'chesscom' }
        };
        return platforms[platform] || { name: platform || 'Unknown', icon: '?', color: '#999', class: 'unknown' };
    }

    createAccountCard(account) {
        const lastSync = account.last_sync_at 
            ? new Date(account.last_sync_at).toLocaleDateString() 
            : 'Never';
        const gamesCount = account.games_count || 0;
        const initial = (account.username || 'U')[0].toUpperCase();
        const platform = account.platform || 'lichess'; // Default to lichess for backward compatibility
        const platformInfo = this.getPlatformInfo(platform);
        const syncEndpoint = platform === 'chesscom' ? '/sync/chesscom/start' : '/sync/start';
        
        return `
            <div class="account-card" data-username="${account.username}" data-platform="${platform}">
                <div class="account-card-header">
                    <div class="account-info">
                        <div class="account-avatar">${initial}</div>
                        <div class="account-details">
                            <div class="account-username-row">
                                <span class="account-username">${account.username}</span>
                                <span class="platform-badge platform-${platformInfo.class}" title="${platformInfo.name}">
                                    ${platformInfo.icon}
                                </span>
                            </div>
                            <span class="account-status">
                                <span class="status-dot"></span>
                                Connected
                            </span>
                        </div>
                    </div>
                    <div class="account-actions">
                        <button class="account-action-btn refresh" data-username="${account.username}" data-platform="${platform}" title="Refresh status">
                            🔄
                        </button>
                        <button class="account-action-btn delete" data-username="${account.username}" data-platform="${platform}" title="Remove account">
                            🗑️
                        </button>
                    </div>
                </div>
                <div class="account-stats">
                    <div class="stat-item">
                        <div class="stat-value">${gamesCount.toLocaleString()}</div>
                        <div class="stat-label">Games</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${lastSync}</div>
                        <div class="stat-label">Last Sync</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${platformInfo.icon}</div>
                        <div class="stat-label">${platformInfo.name}</div>
                    </div>
                </div>
                <div class="account-sync-section">
                    <button class="sync-btn primary" data-username="${account.username}" data-platform="${platform}" data-endpoint="${syncEndpoint}">
                        🔄 Sync New Games
                    </button>
                    <button class="sync-btn secondary" data-username="${account.username}" data-platform="${platform}" data-endpoint="${syncEndpoint}">
                        Full Sync
                    </button>
                </div>
            </div>
        `;
    }

    async startSync(username, fullSync = false, platform = 'lichess', endpoint = '/sync/start') {
        try {
            const syncEndpoint = endpoint || (platform === 'chesscom' ? '/sync/chesscom/start' : '/sync/start');
            const response = await ipcRenderer.invoke('api-request', {
                endpoint: `${syncEndpoint}/${username}`,
                method: 'POST',
                data: { full_sync: fullSync }
            });

            if (response.success) {
                this.showSyncToast(username);
                this.startSyncPolling(username, platform);
            } else {
                throw new Error(response.error || 'Failed to start sync');
            }
        } catch (error) {
            console.error('Sync error:', error);
            this.showError('Failed to start sync: ' + error.message);
        }
    }

    startFullSync(username, platform = 'lichess', endpoint = '/sync/start') {
        if (confirm(`This will re-sync all games for ${username}. This may take a while. Continue?`)) {
            this.startSync(username, true, platform, endpoint);
        }
    }

    showSyncToast(username) {
        this.syncUsername.textContent = username;
        this.syncStatusText.textContent = 'Starting...';
        this.syncProgressFill.style.width = '0%';
        this.syncGamesCount.textContent = '0 games';
        this.syncNewGames.textContent = '0 new';
        this.syncToast.classList.remove('hidden');
    }

    hideSyncToast() {
        this.syncToast.classList.add('hidden');
    }

    startSyncPolling(username, platform = 'lichess') {
        // Clear any existing interval
        if (this.syncIntervals[username]) {
            clearInterval(this.syncIntervals[username]);
        }

        // Determine status endpoint based on platform
        const statusEndpoint = platform === 'chesscom' ? `/sync/chesscom/status/${username}` : `/sync/status/${username}`;

        // Poll every 1 second
        this.syncIntervals[username] = setInterval(async () => {
            try {
                const response = await ipcRenderer.invoke('api-request', {
                    endpoint: statusEndpoint,
                    method: 'GET'
                });

                if (response.success) {
                    this.updateSyncProgress(username, response.data);
                }
            } catch (error) {
                console.error('Sync polling error:', error);
            }
        }, 1000);
    }

    updateSyncProgress(username, progress) {
        this.syncUsername.textContent = username;
        this.syncStatusText.textContent = progress.status || 'Syncing...';
        
        const syncedGames = progress.synced_games || 0;
        const newGames = progress.new_games || 0;
        const totalGames = progress.total_games || 0;
        
        // Calculate progress percentage
        let percentage = 0;
        if (totalGames > 0) {
            percentage = Math.round((syncedGames / totalGames) * 100);
        } else if (syncedGames > 0) {
            // If we don't know total, just show activity
            percentage = Math.min(90, syncedGames);
        }
        
        this.syncProgressFill.style.width = `${percentage}%`;
        this.syncGamesCount.textContent = `${syncedGames.toLocaleString()} games`;
        this.syncNewGames.textContent = `${newGames.toLocaleString()} new`;

        // Check if sync is complete
        if (progress.status === 'completed' || progress.status === 'cancelled' || progress.status === 'error') {
            clearInterval(this.syncIntervals[username]);
            delete this.syncIntervals[username];
            
            // Update the accounts list
            this.loadAccounts();
            
            // Show completion message
            if (progress.status === 'completed') {
                this.syncStatusText.textContent = 'Complete!';
                this.syncProgressFill.style.width = '100%';
                
                // Auto-hide toast after 3 seconds
                setTimeout(() => this.hideSyncToast(), 3000);
            } else if (progress.status === 'error') {
                this.syncStatusText.textContent = 'Error: ' + (progress.error_message || 'Unknown error');
            }
        }
    }

    async deleteAccount(username) {
        if (!confirm(`Are you sure you want to remove the account "${username}"? This will not delete your synced games.`)) {
            return;
        }

        try {
            const response = await ipcRenderer.invoke('api-request', {
                endpoint: `/auth/accounts/${username}`,
                method: 'DELETE'
            });

            if (response.success) {
                await this.loadAccounts();
            } else {
                throw new Error(response.error || 'Failed to delete account');
            }
        } catch (error) {
            console.error('Delete account error:', error);
            this.showError('Failed to remove account: ' + error.message);
        }
    }

    async refreshAccountStatus(username) {
        try {
            const response = await ipcRenderer.invoke('api-request', {
                endpoint: `/auth/accounts/${username}/verify`,
                method: 'GET'
            });

            if (response.success) {
                if (response.data.valid) {
                    alert(`Account "${username}" is valid and connected.`);
                } else {
                    alert(`Account "${username}" token is invalid or expired. Please re-link the account.`);
                }
            }
        } catch (error) {
            console.error('Verify account error:', error);
        }
    }

    async performSearch() {
        const query = this.queryInput.value.trim();
        if (!query) return;

        const searchType = document.querySelector('input[name="searchType"]:checked').value;
        
        this.showLoading(true);
        this.hideError();

        try {
            // Reset pagination for new search
            this.currentPage = 1;
            this.currentBackendPage = 1;
            this.currentQuery = query;
            this.currentSearchType = searchType;
            this.allGames = [];
            this.currentGames = [];
            this.hasMoreGames = false;

            // Load first backend page (500 games)
            const games = await this.searchGames(query, searchType, this.currentBackendPage);
            this.allGames = games; // Store all loaded games
            this.currentGames = this.getCurrentPageGames(); // Get first 20 games
            this.totalPages = Math.ceil(this.totalCount / this.gamesPerPage);
            this.displayGames();
        } catch (error) {
            this.showError('Search failed: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    getCurrentPageGames() {
        const startIndex = (this.currentPage - 1) * this.gamesPerPage;
        const endIndex = startIndex + this.gamesPerPage;
        return this.allGames.slice(startIndex, endIndex);
    }

    async searchGames(query, searchType, page = 1) {
        const endpoint = searchType === 'natural' ? '/ask' : '/cql';
        const offset = (page - 1) * this.backendPageSize;
        const selectedAccount = this.getSelectedAccount();
        
        const data = searchType === 'natural' 
            ? { 
                question: query, 
                limit: this.backendPageSize, 
                page_no: page, 
                offset: offset,
                reference_player: selectedAccount  // Pass selected account for context
            }
            : { 
                query: query, 
                limit: this.backendPageSize, 
                page_no: page, 
                offset: offset,
                reference_player: selectedAccount  // Pass selected account for filtering
            };

        const response = await ipcRenderer.invoke('api-request', {
            endpoint: endpoint,
            method: 'POST',
            data: data
        });

        if (response.success) {
            console.log('API Response:', response.data);
            console.log('Results count:', response.data.results?.length);
            console.log('Total count:', response.data.total_count);
            console.log('Has next:', response.data.has_next);
            
            // Store pagination info for this search
            this.hasMoreGames = response.data.has_next || false;
            this.totalCount = response.data.total_count || 0;
            this.totalPages = Math.ceil(this.totalCount / this.gamesPerPage);
            console.log('Set hasMoreGames to:', this.hasMoreGames);
            console.log('Set totalCount to:', this.totalCount);
            console.log('Set totalPages to:', this.totalPages);
            
            return response.data.results || [];
        } else {
            throw new Error(response.error || 'Search failed');
        }
    }

    async goToPage(page) {
        console.log('goToPage called - page:', page, 'currentPage:', this.currentPage);
        
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            console.log('Invalid page or same page - ignoring');
            return;
        }

        this.currentPage = page;
        
        // Check if we need to load more backend data
        const requiredBackendPage = Math.ceil((page * this.gamesPerPage) / this.backendPageSize);
        
        if (requiredBackendPage > this.currentBackendPage) {
            console.log('Need to load backend pages from', this.currentBackendPage + 1, 'to', requiredBackendPage);
            this.showLoading(true);
            
            try {
                // Load ALL intermediate backend pages, not just the target one
                for (let backendPage = this.currentBackendPage + 1; backendPage <= requiredBackendPage; backendPage++) {
                    console.log('Loading backend page:', backendPage);
                    const newGames = await this.searchGames(this.currentQuery, this.currentSearchType, backendPage);
                    this.allGames = [...this.allGames, ...newGames]; // Append new games
                    this.currentBackendPage = backendPage;
                }
            } catch (error) {
                console.error('Failed to load backend page:', error);
                this.showError('Failed to load more games: ' + error.message);
                return;
            } finally {
                this.showLoading(false);
            }
        }
        
        // Get current page games from loaded data
        this.currentGames = this.getCurrentPageGames();
        this.displayGames();
    }



    clearSearch() {
        this.queryInput.value = '';
        this.currentGames = [];
        this.resultsContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to ChessQL Desktop</h2>
                <p>Search for chess games using natural language or ChessQL queries.</p>
                <div class="example-queries">
                    <h3>Try these examples:</h3>
                    <div class="example-query" data-query="lecorvus won">lecorvus won</div>
                    <div class="example-query" data-query="queen sacrificed">queen sacrificed</div>
                    <div class="example-query" data-query="pawn promoted to queen">pawn promoted to queen</div>
                    <div class="example-query" data-query="SELECT * FROM games WHERE white_player = 'lecorvus'">SQL: lecorvus as white</div>
                </div>
            </div>
        `;
        
        // Re-bind example query events
        document.querySelectorAll('.example-query').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.queryInput.value = e.target.dataset.query;
                this.performSearch();
            });
        });
    }

    displayGames() {
        if (this.currentGames.length === 0) {
            this.resultsContainer.innerHTML = '<div class="welcome-message"><h2>No games found</h2><p>Try a different search query.</p></div>';
            return;
        }

        const gamesGrid = document.createElement('div');
        gamesGrid.className = 'games-grid';

        this.currentGames.forEach((game, index) => {
            const gameCard = this.createGameCard(game, index);
            gamesGrid.appendChild(gameCard);
        });

        // No loading indicator needed here - main loading indicator handles it

        this.resultsContainer.innerHTML = '';
        this.resultsContainer.appendChild(gamesGrid);
        
        // Add pagination controls
        if (this.totalPages > 1) {
            this.addPaginationControls();
        }
    }

    addPaginationControls() {
        const paginationDiv = document.createElement('div');
        paginationDiv.className = 'pagination-container';
        
        // Show fewer page numbers for better mobile experience
        const maxVisiblePages = window.innerWidth < 768 ? 3 : 5;
        const halfVisible = Math.floor(maxVisiblePages / 2);
        
        let startPage = Math.max(1, this.currentPage - halfVisible);
        let endPage = Math.min(this.totalPages, this.currentPage + halfVisible);
        
        // Adjust if we're near the beginning or end
        if (endPage - startPage + 1 < maxVisiblePages) {
            if (startPage === 1) {
                endPage = Math.min(this.totalPages, startPage + maxVisiblePages - 1);
            } else {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }
        }
        
        let paginationHTML = '<div class="pagination">';
        
        // Previous button (fixed left position)
        if (this.currentPage > 1) {
            paginationHTML += `<button class="pagination-btn prev-btn" data-action="go-to-page" data-page="${this.currentPage - 1}">←</button>`;
        }
        
        // Center section with page numbers
        paginationHTML += '<div class="pagination-center">';
        
        // First page (only if not in visible range)
        if (startPage > 1) {
            paginationHTML += `<button class="pagination-btn" data-action="go-to-page" data-page="1">1</button>`;
            if (startPage > 2) {
                paginationHTML += '<span class="pagination-ellipsis">...</span>';
            }
        }
        
        // Page numbers
        for (let i = startPage; i <= endPage; i++) {
            const isActive = i === this.currentPage ? 'active' : '';
            paginationHTML += `<button class="pagination-btn ${isActive}" data-action="go-to-page" data-page="${i}">${i}</button>`;
        }
        
        // Last page (only if not in visible range)
        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                paginationHTML += '<span class="pagination-ellipsis">...</span>';
            }
            paginationHTML += `<button class="pagination-btn" data-action="go-to-page" data-page="${this.totalPages}">${this.totalPages}</button>`;
        }
        
        paginationHTML += '</div>'; // Close center section
        
        // Next button (fixed right position)
        if (this.currentPage < this.totalPages) {
            paginationHTML += `<button class="pagination-btn next-btn" data-action="go-to-page" data-page="${this.currentPage + 1}">→</button>`;
        }
        
        paginationHTML += '</div>';
        
        // Page info (more compact)
        const startItem = (this.currentPage - 1) * this.gamesPerPage + 1;
        const endItem = Math.min(this.currentPage * this.gamesPerPage, this.totalCount);
        const loadedGames = this.allGames.length;
        paginationHTML += `<div class="pagination-info">${startItem}-${endItem} of ${this.totalCount} (${loadedGames} loaded)</div>`;
        
        paginationDiv.innerHTML = paginationHTML;
        this.resultsContainer.appendChild(paginationDiv);
    }

    detectGamePlatform(game) {
        // Detect platform from site URL or game ID fields
        if (game.site) {
            if (game.site.includes('lichess.org')) {
                return 'lichess';
            } else if (game.site.includes('chess.com')) {
                return 'chesscom';
            }
        }
        // Check for ID fields
        if (game.lichess_id) {
            return 'lichess';
        }
        if (game.chesscom_id) {
            return 'chesscom';
        }
        return null;
    }

    createGameCard(game, index) {
        const card = document.createElement('div');
        card.className = 'game-card';
        card.addEventListener('click', () => this.openGameModal(game));

        const thumbnail = document.createElement('div');
        thumbnail.className = 'game-thumbnail';
        
        // Detect and add platform badge
        const platform = this.detectGamePlatform(game);
        if (platform) {
            const platformInfo = this.getPlatformInfo(platform);
            const platformBadge = document.createElement('div');
            platformBadge.className = `platform-badge-overlay platform-${platformInfo.class}`;
            platformBadge.innerHTML = `<span class="platform-icon">${platformInfo.icon}</span><span class="platform-text">${platformInfo.name}</span>`;
            platformBadge.title = platformInfo.name;
            thumbnail.appendChild(platformBadge);
        }
        
        // Add speed badge overlay if speed is available (collapsible)
        if (game.speed) {
            const speedBadge = document.createElement('div');
            speedBadge.className = `speed-badge-overlay speed-${game.speed.toLowerCase()}`;
            speedBadge.innerHTML = `<span class="speed-icon">${this.getSpeedIcon(game.speed)}</span><span class="speed-text">${this.getSpeedName(game.speed)}</span>`;
            thumbnail.appendChild(speedBadge);
        }
        
        // Add variant badge overlay for non-standard variants
        if (game.variant && game.variant !== 'standard') {
            const variantBadge = document.createElement('div');
            variantBadge.className = `variant-badge-overlay variant-${game.variant.toLowerCase()}`;
            variantBadge.innerHTML = `<span class="variant-icon">${this.formatVariant(game.variant)}</span><span class="variant-text">${this.getVariantFullName(game.variant)}</span>`;
            thumbnail.appendChild(variantBadge);
        }
        
        // Create mini chess board
        const miniBoard = this.createMiniChessBoard(game);
        thumbnail.appendChild(miniBoard);

        const info = document.createElement('div');
        info.className = 'game-info';
        
        const players = document.createElement('div');
        players.className = 'game-players';
        players.textContent = `${game.white_player || 'White'} vs ${game.black_player || 'Black'}`;
        
        const result = document.createElement('div');
        result.className = 'game-result';
        result.textContent = `Result: ${game.result || 'Unknown'}`;
        
        // Add time control and date row
        const metaRow = document.createElement('div');
        metaRow.className = 'game-meta-row';
        
        const date = document.createElement('span');
        date.className = 'game-date';
        date.textContent = game.date_played || 'Unknown date';
        metaRow.appendChild(date);
        
        if (game.time_control) {
            const timeControl = document.createElement('span');
            timeControl.className = 'game-time-control';
            timeControl.textContent = this.formatTimeControl(game.time_control);
            metaRow.appendChild(timeControl);
        }

        info.appendChild(players);
        info.appendChild(result);
        info.appendChild(metaRow);

        card.appendChild(thumbnail);
        card.appendChild(info);

        return card;
    }

    formatSpeed(speed) {
        // Format speed for display (icon + name)
        const speedLabels = {
            'ultraBullet': '⚡ UltraBullet',
            'bullet': '🔫 Bullet',
            'blitz': '⚡ Blitz',
            'rapid': '🕐 Rapid',
            'classical': '♟️ Classical',
            'correspondence': '📬 Correspondence'
        };
        return speedLabels[speed] || speed;
    }

    getSpeedIcon(speed) {
        // Get just the icon for speed
        const speedIcons = {
            'ultraBullet': '⚡',
            'bullet': '🔫',
            'blitz': '⚡',
            'rapid': '🕐',
            'classical': '♟️',
            'correspondence': '📬'
        };
        return speedIcons[speed] || '⏱️';
    }

    getSpeedName(speed) {
        // Get just the name for speed
        const speedNames = {
            'ultraBullet': 'UltraBullet',
            'bullet': 'Bullet',
            'blitz': 'Blitz',
            'rapid': 'Rapid',
            'classical': 'Classical',
            'correspondence': 'Correspondence'
        };
        return speedNames[speed] || speed;
    }

    formatVariant(variant) {
        // Format variant icon for display
        const variantIcons = {
            'standard': '♟️',
            'chess960': '🎲'
        };
        return variantIcons[variant] || variant;
    }

    getVariantFullName(variant) {
        // Get full variant name for tooltips/hover
        const variantNames = {
            'standard': 'Standard',
            'chess960': 'Chess960'
        };
        return variantNames[variant] || variant;
    }

    formatTimeControl(timeControl) {
        // Format time control for display (e.g., "300+0" -> "5+0")
        if (!timeControl) return '';
        
        const match = timeControl.match(/^(\d+)\+(\d+)$/);
        if (match) {
            const minutes = Math.floor(parseInt(match[1]) / 60);
            const increment = match[2];
            return `${minutes}+${increment}`;
        }
        return timeControl;
    }

    formatTermination(termination) {
        // Format termination reason for better readability
        if (!termination) return '';
        
        const terminationLabels = {
            'mate': 'Checkmate',
            'resign': 'Resignation',
            'outoftime': 'Timeout',
            'timeout': 'Timeout',
            'draw': 'Draw',
            'stalemate': 'Stalemate',
            'normal': 'Normal',
            'abandoned': 'Abandoned',
            'cheat': 'Terminated'
        };
        
        return terminationLabels[termination.toLowerCase()] || termination;
    }

    copySiteUrl() {
        const site = this.currentGame?.site;
        if (!site || site === 'Unknown') {
            return;
        }
        
        navigator.clipboard.writeText(site).then(() => {
            // Visual feedback
            this.copySiteBtn.textContent = '✓';
            this.copySiteBtn.classList.add('copied');
            
            // Reset after 2 seconds
            setTimeout(() => {
                this.copySiteBtn.textContent = '📋';
                this.copySiteBtn.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy URL:', err);
        });
    }

    flipBoard() {
        this.isBoardFlipped = !this.isBoardFlipped;
        
        if (this.isBoardFlipped) {
            this.chessBoard.classList.add('flipped');
        } else {
            this.chessBoard.classList.remove('flipped');
        }
    }

    createMiniChessBoard(game) {
        const board = document.createElement('div');
        board.className = 'chess-board-mini';
        
        // Parse the final position from moves (pass PGN for Chess960 FEN)
        const finalPosition = this.getFinalPosition(game.moves, game.pgn_text);
        
        // Create 8x8 grid
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const square = document.createElement('div');
                square.className = `square ${(row + col) % 2 === 0 ? 'light' : 'dark'}`;
                
                const piece = finalPosition[row][col];
                if (piece) {
                    const pieceElement = document.createElement('span');
                    pieceElement.textContent = this.getPieceSymbol(piece);
                    pieceElement.className = piece === piece.toUpperCase() ? 'white-piece' : 'black-piece';
                    square.appendChild(pieceElement);
                }
                
                board.appendChild(square);
            }
        }
        
        return board;
    }

    getFinalPosition(moves, pgnText = null) {
        try {
            let tempChess = new Chess();
            
            // Check if this is a Chess960 game and get FEN from PGN
            const isChess960Game = pgnText && pgnText.includes('[Variant "Chess960"]');
            
            if (pgnText) {
                const fenMatch = pgnText.match(/\[FEN\s+"([^"]+)"\]/);
                if (fenMatch) {
                    try {
                        // Use Chess960 class for Chess960 games
                        if (isChess960Game) {
                            tempChess = new Chess960(fenMatch[1]);
                        } else {
                            tempChess = new Chess(fenMatch[1]);
                        }
                    } catch (e) {
                        console.log('Failed to load FEN for thumbnail:', e);
                        tempChess = new Chess();
                    }
                }
            }
            
            // Parse moves and apply them
            if (moves && moves.trim()) {
                const moveList = moves.split(' ').filter(move => 
                    move && 
                    !move.match(/^\d+\./) && 
                    !move.match(/^[0-9-]+$/) &&
                    move !== '*'
                );
                
                for (const move of moveList) {
                    try {
                        tempChess.move(move, { sloppy: true });
                    } catch (e) {
                        // Skip invalid moves (e.g., Chess960 castling)
                    }
                }
            }
            
            // Get the final position
            const board = Array(8).fill(null).map(() => Array(8).fill(null));
            
            for (let row = 0; row < 8; row++) {
                for (let col = 0; col < 8; col++) {
                    const square = String.fromCharCode(97 + col) + (8 - row);
                    const piece = tempChess.get(square);
                    if (piece) {
                        const pieceSymbol = piece.color === 'w' ? piece.type.toUpperCase() : piece.type.toLowerCase();
                        board[row][col] = pieceSymbol;
                    }
                }
            }
            
            return board;
        } catch (error) {
            console.error('Error getting final position:', error);
            // Return initial position as fallback
            return [
                ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
                ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
                [null, null, null, null, null, null, null, null],
                [null, null, null, null, null, null, null, null],
                [null, null, null, null, null, null, null, null],
                [null, null, null, null, null, null, null, null],
                ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
                ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
            ];
        }
    }

    getPieceSymbol(piece) {
        // Use more distinctive piece symbols
        const symbols = {
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
            'KK': '♔', 'QQ': '♕', 'RR': '♖', 'BB': '♗', 'NN': '♘', 'PP': '♙',
            'kk': '♚', 'qq': '♛', 'rr': '♜', 'bb': '♝', 'nn': '♞', 'pp': '♟'
        };
        return symbols[piece] || '';
    }

    openGameModal(game) {
        this.currentGame = game;
        this.currentMoveIndex = 0;
        
        // Reset board orientation
        this.isBoardFlipped = false;
        this.chessBoard.classList.remove('flipped');
        
        // Update modal content
        this.gameTitle.textContent = `${game.white_player || 'White'} vs ${game.black_player || 'Black'}`;
        this.whitePlayerName.textContent = game.white_player || 'Unknown';
        this.blackPlayerName.textContent = game.black_player || 'Unknown';
        this.whitePlayerElo.textContent = game.white_elo ? `(${game.white_elo})` : '';
        this.blackPlayerElo.textContent = game.black_elo ? `(${game.black_elo})` : '';
        this.gameResult.textContent = game.result || 'Unknown';
        this.gameDate.textContent = game.date_played || 'Unknown';
        
        // Time control and speed
        this.gameTimeControl.textContent = game.time_control ? this.formatTimeControl(game.time_control) : 'Unknown';
        
        // Update speed badge with appropriate styling
        if (game.speed) {
            this.gameSpeed.textContent = this.formatSpeed(game.speed);
            this.gameSpeed.className = `speed-badge speed-${game.speed.toLowerCase()}`;
        } else {
            this.gameSpeed.textContent = 'Unknown';
            this.gameSpeed.className = 'speed-badge';
        }
        
        // Update variant badge (always show full text in modal)
        if (game.variant && game.variant !== 'standard') {
            this.gameVariant.innerHTML = `<span class="variant-icon">${this.formatVariant(game.variant)}</span><span class="variant-text-modal">${this.getVariantFullName(game.variant)}</span>`;
            this.gameVariant.className = `variant-badge variant-badge-modal variant-${game.variant.toLowerCase()}`;
            this.gameVariant.parentElement.classList.remove('hidden');
        } else {
            // Hide variant pill for standard games
            this.gameVariant.parentElement.classList.add('hidden');
        }
        
        // Handle site field - make it clickable if it's a URL
        const site = game.site || 'Unknown';
        if (site !== 'Unknown' && (site.startsWith('http://') || site.startsWith('https://'))) {
            this.gameSite.innerHTML = `<a href="${site}" target="_blank" rel="noopener noreferrer">${site}</a>`;
        } else {
            this.gameSite.textContent = site;
        }
        
        // Opening with tooltip for full name on hover
        const openingName = game.opening || 'Unknown';
        this.gameOpening.textContent = openingName;
        this.gameOpening.title = openingName; // Tooltip shows full name on hover
        
        // Termination with formatted text
        this.gameTermination.textContent = this.formatTermination(game.termination) || 'Unknown';
        
        // Load the game
        this.loadGame(game);
        
        // Show modal
        this.gameModal.classList.remove('hidden');
    }

    loadGame(game) {
        try {
            console.log('Loading game PGN:', game.pgn_text);
            
            // Check if this is a Chess960 game
            this.isChess960 = game.variant === 'chess960' || 
                (game.pgn_text && game.pgn_text.includes('[Variant "Chess960"]'));
            
            // Extract starting FEN from PGN if present (for Chess960)
            this.startingFen = null;
            if (this.isChess960 && game.pgn_text) {
                const fenMatch = game.pgn_text.match(/\[FEN\s+"([^"]+)"\]/);
                if (fenMatch) {
                    this.startingFen = fenMatch[1];
                }
            }
            console.log('Is Chess960:', this.isChess960, 'Starting FEN:', this.startingFen);
            
            // Try to load via PGN first (works for standard games)
            this.chess = new Chess();
            let pgnLoaded = false;
            
            if (game.pgn_text && !this.isChess960) {
                try {
                    this.chess.loadPgn(game.pgn_text);
                    this.gameMoves = [...this.chess.history()];
                    pgnLoaded = true;
                    console.log('Loaded via PGN, moves:', this.gameMoves.length);
                } catch (e) {
                    console.log('PGN load failed:', e.message);
                }
            }
            
            // For Chess960 or failed PGN load, use moves string
            if (!pgnLoaded) {
                this.loadGameFromMoves(game.moves);
                return;
            }
            
            this.currentMoveIndex = this.gameMoves.length;
            this.updateBoard();
            this.updateMovesList();
            this.updateMoveControls();
        } catch (error) {
            console.error('Error loading game:', error);
            this.isChess960 = false;
            this.startingFen = null;
            this.chess = new Chess();
            this.loadGameFromMoves(game.moves);
        }
    }

    extractFenFromPgn(pgn) {
        // Extract FEN from PGN headers (for Chess960 games)
        if (!pgn) return null;
        const fenMatch = pgn.match(/\[FEN\s+"([^"]+)"\]/);
        return fenMatch ? fenMatch[1] : null;
    }

    convertToChess960Fen(fen) {
        // Convert standard castling notation (KQkq) to Chess960 file-based notation
        // Chess960 uses the file letters where the rooks are located
        const parts = fen.split(' ');
        if (parts.length < 3) return fen;
        
        const position = parts[0];
        const castling = parts[2];
        
        if (castling === '-' || !castling.match(/[KQkq]/)) {
            return fen; // No castling or already in file-based notation
        }
        
        // Parse the position to find rook locations
        const ranks = position.split('/');
        const whiteRank = ranks[7]; // Rank 1 (white's back rank)
        const blackRank = ranks[0]; // Rank 8 (black's back rank)
        
        // Expand ranks to 8 characters
        const expandRank = (rank) => {
            let expanded = '';
            for (const char of rank) {
                if (char >= '1' && char <= '8') {
                    expanded += '.'.repeat(parseInt(char));
                } else {
                    expanded += char;
                }
            }
            return expanded;
        };
        
        const whiteExpanded = expandRank(whiteRank);
        const blackExpanded = expandRank(blackRank);
        
        // Find king and rook positions
        const whiteKingFile = whiteExpanded.indexOf('K');
        const blackKingFile = blackExpanded.indexOf('k');
        
        // Find rook files
        const findRooks = (rank, rookChar) => {
            const rooks = [];
            for (let i = 0; i < rank.length; i++) {
                if (rank[i] === rookChar) rooks.push(i);
            }
            return rooks;
        };
        
        const whiteRooks = findRooks(whiteExpanded, 'R');
        const blackRooks = findRooks(blackExpanded, 'r');
        
        // Build new castling string using file letters
        let newCastling = '';
        const fileLetters = 'ABCDEFGH';
        
        // White kingside (rook to the right of king)
        if (castling.includes('K') && whiteRooks.some(r => r > whiteKingFile)) {
            const kingsideRook = whiteRooks.find(r => r > whiteKingFile);
            newCastling += fileLetters[kingsideRook];
        }
        // White queenside (rook to the left of king)
        if (castling.includes('Q') && whiteRooks.some(r => r < whiteKingFile)) {
            const queensideRook = whiteRooks.filter(r => r < whiteKingFile).pop();
            newCastling += fileLetters[queensideRook];
        }
        // Black kingside (rook to the right of king)
        if (castling.includes('k') && blackRooks.some(r => r > blackKingFile)) {
            const kingsideRook = blackRooks.find(r => r > blackKingFile);
            newCastling += fileLetters[kingsideRook].toLowerCase();
        }
        // Black queenside (rook to the left of king)
        if (castling.includes('q') && blackRooks.some(r => r < blackKingFile)) {
            const queensideRook = blackRooks.filter(r => r < blackKingFile).pop();
            newCastling += fileLetters[queensideRook].toLowerCase();
        }
        
        if (!newCastling) newCastling = '-';
        
        parts[2] = newCastling;
        console.log('Converted Chess960 FEN castling from', castling, 'to', newCastling);
        return parts.join(' ');
    }

    resetToStartingPosition() {
        // Reset to starting position (uses Chess960 class for Chess960 games)
        if (this.isChess960 && this.startingFen) {
            try {
                this.chess = new Chess960(this.startingFen);
            } catch (e) {
                console.error('Failed to reset to starting position:', e);
                this.chess = new Chess();
            }
        } else if (this.startingFen) {
            try {
                this.chess = new Chess(this.startingFen);
            } catch (e) {
                console.error('Failed to reset to starting position:', e);
                this.chess = new Chess();
            }
        } else {
            this.chess = new Chess();
        }
    }

    loadGameFromMoves(moves) {
        try {
            console.log('Loading game from moves:', moves);
            
            // Reset chess instance - use Chess960 class for Chess960 games
            if (this.isChess960 && this.startingFen) {
                try {
                    this.chess = new Chess960(this.startingFen);
                    console.log('Chess960 starting FEN (using Chess960 class):', this.startingFen);
                } catch (e) {
                    console.error('Failed to load Chess960 FEN:', e);
                    this.chess = new Chess();
                    this.startingFen = null;
                }
            } else {
                this.chess = new Chess();
            }
            
            if (!moves) {
                this.gameMoves = [];
                this.currentMoveIndex = 0;
                this.updateBoard();
                this.updateMovesList();
                this.updateMoveControls();
                return;
            }
            
            const moveList = moves.split(' ').filter(move => 
                move && 
                !move.match(/^\d+\./) && 
                !move.match(/^[0-9-]+$/) && 
                move !== '*'
            );
            
            console.log('Parsed move list:', moveList);
            
            for (const move of moveList) {
                try {
                    const result = this.chess.move(move, { sloppy: true });
                    if (!result) {
                        console.log('Move returned null:', move);
                    }
                } catch (e) {
                    console.log('Invalid move:', move, e.message);
                }
            }
            
            this.gameMoves = [...this.chess.history()];
            console.log('Final chess history:', this.gameMoves.length, 'moves');
            this.currentMoveIndex = this.gameMoves.length;
            this.updateBoard();
            this.updateMovesList();
            this.updateMoveControls();
        } catch (error) {
            console.error('Error loading game from moves:', error);
            this.gameMoves = [];
            this.currentMoveIndex = 0;
            this.updateBoard();
            this.updateMovesList();
            this.updateMoveControls();
        }
    }

    updateBoard() {
        this.chessBoard.innerHTML = '';
        
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const square = document.createElement('div');
                square.className = `square ${(row + col) % 2 === 0 ? 'light' : 'dark'}`;
                square.dataset.square = `${String.fromCharCode(97 + col)}${8 - row}`;
                
                const piece = this.chess.get(`${String.fromCharCode(97 + col)}${8 - row}`);
                if (piece) {
                    const pieceSymbol = piece.color === 'w' ? piece.type.toUpperCase() : piece.type.toLowerCase();
                    const pieceElement = document.createElement('span');
                    pieceElement.textContent = this.getPieceSymbol(pieceSymbol);
                    pieceElement.className = `piece ${piece.color === 'w' ? 'white-piece' : 'black-piece'}`;
                    square.appendChild(pieceElement);
                }
                
                this.chessBoard.appendChild(square);
            }
        }
    }


    updateMovesList() {
        this.movesList.innerHTML = '';
        
        for (let i = 0; i < this.gameMoves.length; i += 2) {
            const moveDiv = document.createElement('div');
            moveDiv.className = 'move';
            
            const moveNumber = Math.floor(i / 2) + 1;
            const whiteMove = this.gameMoves[i];
            const blackMove = this.gameMoves[i + 1];
            
            moveDiv.innerHTML = `
                <span class="move-number">${moveNumber}.</span>
                <span class="white-move">${whiteMove}</span>
                ${blackMove ? `<span class="black-move">${blackMove}</span>` : ''}
            `;
            
            moveDiv.addEventListener('click', () => this.goToMoveDirect(i + 1));
            this.movesList.appendChild(moveDiv);
        }
    }

    updateMoveControls() {
        this.currentMoveIndex = Math.min(this.currentMoveIndex, this.gameMoves.length);
        
        this.prevMoveBtn.disabled = this.currentMoveIndex <= 0;
        this.nextMoveBtn.disabled = this.currentMoveIndex >= this.gameMoves.length;
        this.firstMoveBtn.disabled = this.currentMoveIndex <= 0;
        this.lastMoveBtn.disabled = this.currentMoveIndex >= this.gameMoves.length;
    }

    goToMove(moveIndex) {
        console.log('Going to move index:', moveIndex, 'from current:', this.currentMoveIndex);
        
        // If going to start, reset and show starting position
        if (moveIndex === 0) {
            this.resetToStartingPosition();
            this.updateBoard();
            this.currentMoveIndex = moveIndex;
            this.updateMoveControls();
            this.highlightCurrentMove();
            return;
        }
        
        // If moving forward from current position, animate only the next move
        if (moveIndex > this.currentMoveIndex) {
            console.log('Moving forward - using animateNextMove');
            this.animateNextMove(moveIndex);
        } else {
            // If going backward, animate only the previous move
            console.log('Moving backward - using animatePreviousMove');
            this.animatePreviousMove(moveIndex);
        }
    }

    goToMoveDirect(moveIndex) {
        console.log('Going directly to move index:', moveIndex);
        
        // Reset chess to starting position
        this.resetToStartingPosition();
        
        // Apply all moves up to the target index
        for (let i = 0; i < moveIndex && i < this.gameMoves.length; i++) {
            try {
                this.chess.move(this.gameMoves[i]);
            } catch (e) {
                console.log('Error applying move:', this.gameMoves[i], e.message);
            }
        }
        
        // Update the board and controls
        this.currentMoveIndex = moveIndex;
        this.updateBoard();
        this.updateMoveControls();
        this.highlightCurrentMove();
    }

    async animateNextMove(targetMoveIndex) {
        console.log('Animating next move from', this.currentMoveIndex, 'to', targetMoveIndex);
        
        // Reset chess to current position and replay moves to ensure consistency
        this.resetToStartingPosition();
        for (let i = 0; i < this.currentMoveIndex; i++) {
            this.chess.move(this.gameMoves[i]);
        }
        
        // Animate only the moves from current position to target
        for (let i = this.currentMoveIndex; i < targetMoveIndex && i < this.gameMoves.length; i++) {
            try {
                const move = this.gameMoves[i];
                console.log('Processing move', i, ':', move);
                
                // Get the move object before applying it (use Chess960 for Chess960 games)
                const tempChess = this.isChess960 ? new Chess960(this.chess.fen()) : new Chess(this.chess.fen());
                const moveObj = tempChess.move(move, { sloppy: true });
                
                if (moveObj) {
                    console.log('Move object:', moveObj);
                    
                    // Animate the move
                    await this.animateMove(moveObj);
                    
                    // Apply the move to the actual chess instance
                    this.chess.move(move);
                    console.log('Applied move to chess instance');
                    
                    // Update the entire board to ensure consistency
                    this.updateBoard();
                    console.log('Updated board after move');
                } else {
                    console.log('Invalid move object, skipping animation');
                    // Still try to apply the move
                    this.chess.move(move);
                    this.updateBoard();
                }
                
                console.log('Completed move in navigation:', move);
            } catch (e) {
                console.log('Error applying move in navigation:', this.gameMoves[i], e.message);
                // If there's an error, try to continue with the next move
                try {
                    this.chess.move(this.gameMoves[i]);
                    this.updateBoard();
                } catch (e2) {
                    console.log('Failed to apply move even without animation:', e2.message);
                }
            }
        }
        
        this.currentMoveIndex = targetMoveIndex;
        this.updateMoveControls();
        this.highlightCurrentMove();
    }

    async animatePreviousMove(targetMoveIndex) {
        console.log('Animating previous move from', this.currentMoveIndex, 'to', targetMoveIndex);
        
        // For going backward, we'll just undo moves without complex animation
        // This is simpler and more reliable
        for (let i = this.currentMoveIndex - 1; i >= targetMoveIndex; i--) {
            try {
                const move = this.gameMoves[i];
                console.log('Undoing move', i, ':', move);
                
                // Undo the move in the actual chess instance
                this.chess.undo();
                console.log('Undid move in chess instance');
                
                // Update the board to reflect the undone position
                this.updateBoard();
                console.log('Updated board after undo');
                
                // Small delay to make the undo visible
                await new Promise(resolve => setTimeout(resolve, 50));
                
                console.log('Completed undo in navigation:', move);
            } catch (e) {
                console.log('Error undoing move in navigation:', this.gameMoves[i], e.message);
                // If there's an error, just undo without animation
                this.chess.undo();
                this.updateBoard();
            }
        }
        
        this.currentMoveIndex = targetMoveIndex;
        this.updateMoveControls();
        this.highlightCurrentMove();
    }

    async animateMovesToPosition(targetMoveIndex) {
        console.log('Animating moves from 0 to', targetMoveIndex);
        
        // Start from the beginning and animate to target
        for (let i = 0; i < targetMoveIndex && i < this.gameMoves.length; i++) {
            try {
                const move = this.gameMoves[i];
                console.log('Processing move', i, ':', move);
                
                // Get the move object before applying it (use Chess960 for Chess960 games)
                const tempChess = this.isChess960 ? new Chess960(this.chess.fen()) : new Chess(this.chess.fen());
                const moveObj = tempChess.move(move, { sloppy: true });
                
                if (moveObj) {
                    console.log('Move object:', moveObj);
                    
                    // Animate the move
                    await this.animateMove(moveObj);
                    
                    // Apply the move to the actual chess instance
                    this.chess.move(move);
                    console.log('Applied move to chess instance');
                    
                    // Update only the affected squares instead of recreating the board
                    this.updateBoardAfterMove(moveObj);
                    console.log('Updated board after move');
                }
                
                console.log('Completed move in navigation:', move);
            } catch (e) {
                console.log('Error applying move in navigation:', this.gameMoves[i], e.message);
            }
        }
        
        this.currentMoveIndex = targetMoveIndex;
        this.updateMoveControls();
        this.highlightCurrentMove();
    }

    async animateMove(moveObj) {
        return new Promise((resolve) => {
            const fromSquare = document.querySelector(`[data-square="${moveObj.from}"]`);
            const toSquare = document.querySelector(`[data-square="${moveObj.to}"]`);
            
            if (!fromSquare || !toSquare) {
                resolve();
                return;
            }
            
            // Get the piece element from the source square
            const pieceElement = fromSquare.querySelector('.piece');
            if (!pieceElement) {
                resolve();
                return;
            }
            
            // Clone the piece for animation
            const animatedPiece = pieceElement.cloneNode(true);
            animatedPiece.classList.add('moving');
            
            // Get bounding rects (these are in screen coordinates)
            const fromRect = fromSquare.getBoundingClientRect();
            const toRect = toSquare.getBoundingClientRect();
            const boardRect = this.chessBoard.getBoundingClientRect();
            
            // Use the destination square size for consistent appearance
            const squareSize = Math.min(toRect.width, toRect.height);
            
            // Calculate positions relative to board's screen position
            // When the board is flipped (rotated 180deg), we need to convert screen coords
            // to the rotated coordinate system
            let fromX, fromY, toX, toY;
            
            if (this.isBoardFlipped) {
                // When board is rotated 180deg, the coordinate system is inverted
                // We need to map screen coords to the rotated local coords
                fromX = boardRect.right - fromRect.right;
                fromY = boardRect.bottom - fromRect.bottom;
                toX = boardRect.right - toRect.right;
                toY = boardRect.bottom - toRect.bottom;
                
                // Rotate the piece to appear right-side up
                animatedPiece.style.transform = 'rotate(180deg)';
            } else {
                fromX = fromRect.left - boardRect.left;
                fromY = fromRect.top - boardRect.top;
                toX = toRect.left - boardRect.left;
                toY = toRect.top - boardRect.top;
            }
            
            animatedPiece.style.position = 'absolute';
            animatedPiece.style.left = fromX + 'px';
            animatedPiece.style.top = fromY + 'px';
            animatedPiece.style.pointerEvents = 'none';
            animatedPiece.style.zIndex = '1000';
            animatedPiece.style.width = squareSize + 'px';
            animatedPiece.style.height = squareSize + 'px';
            animatedPiece.style.margin = '0';
            animatedPiece.style.padding = '0';
            animatedPiece.style.fontSize = (squareSize * 0.8) + 'px';
            animatedPiece.style.display = 'flex';
            animatedPiece.style.alignItems = 'center';
            animatedPiece.style.justifyContent = 'center';
            
            // Make sure the board has relative positioning for absolute children
            if (getComputedStyle(this.chessBoard).position === 'static') {
                this.chessBoard.style.position = 'relative';
            }
            
            this.chessBoard.appendChild(animatedPiece);
            
            // Remove the source piece immediately when animation starts
            pieceElement.remove();
            
            // If there's a capture, hide the captured piece
            const capturedPiece = toSquare.querySelector('.piece');
            if (capturedPiece) {
                capturedPiece.style.opacity = '0';
            }
            
            // Small delay to ensure the piece is rendered before animation
            requestAnimationFrame(() => {
                animatedPiece.style.transition = 'left 0.1s ease-in-out, top 0.1s ease-in-out';
                animatedPiece.style.left = toX + 'px';
                animatedPiece.style.top = toY + 'px';
            });
            
            // After animation completes
            setTimeout(() => {
                animatedPiece.remove();
                resolve();
            }, 100);
        });
    }

    async animateReverseMove(moveObj) {
        return new Promise((resolve) => {
            const fromSquare = document.querySelector(`[data-square="${moveObj.from}"]`);
            const toSquare = document.querySelector(`[data-square="${moveObj.to}"]`);
            
            if (!fromSquare || !toSquare) {
                resolve();
                return;
            }
            
            // Get the piece element from the destination square (where it currently is)
            const pieceElement = toSquare.querySelector('.piece');
            if (!pieceElement) {
                resolve();
                return;
            }
            
            // Clone the piece for animation
            const animatedPiece = pieceElement.cloneNode(true);
            animatedPiece.classList.add('moving');
            
            // Get bounding rects
            const fromRect = fromSquare.getBoundingClientRect();
            const toRect = toSquare.getBoundingClientRect();
            const boardRect = this.chessBoard.getBoundingClientRect();
            
            // Use the source square size for consistent appearance
            const squareSize = Math.min(fromRect.width, fromRect.height);
            
            // Calculate positions based on board orientation
            let fromX, fromY, toX, toY;
            
            if (this.isBoardFlipped) {
                fromX = boardRect.right - fromRect.right;
                fromY = boardRect.bottom - fromRect.bottom;
                toX = boardRect.right - toRect.right;
                toY = boardRect.bottom - toRect.bottom;
                animatedPiece.style.transform = 'rotate(180deg)';
            } else {
                fromX = fromRect.left - boardRect.left;
                fromY = fromRect.top - boardRect.top;
                toX = toRect.left - boardRect.left;
                toY = toRect.top - boardRect.top;
            }
            
            animatedPiece.style.position = 'absolute';
            animatedPiece.style.left = toX + 'px'; // Start at current position
            animatedPiece.style.top = toY + 'px';
            animatedPiece.style.pointerEvents = 'none';
            animatedPiece.style.zIndex = '1000';
            animatedPiece.style.width = squareSize + 'px';
            animatedPiece.style.height = squareSize + 'px';
            animatedPiece.style.margin = '0';
            animatedPiece.style.padding = '0';
            animatedPiece.style.fontSize = (squareSize * 0.8) + 'px';
            animatedPiece.style.display = 'flex';
            animatedPiece.style.alignItems = 'center';
            animatedPiece.style.justifyContent = 'center';
            
            // Make sure the board has relative positioning for absolute children
            if (getComputedStyle(this.chessBoard).position === 'static') {
                this.chessBoard.style.position = 'relative';
            }
            
            this.chessBoard.appendChild(animatedPiece);
            
            // Remove the current piece immediately when animation starts
            pieceElement.remove();
            
            // Small delay to ensure the piece is rendered before animation
            requestAnimationFrame(() => {
                animatedPiece.style.transition = 'left 0.1s ease-in-out, top 0.1s ease-in-out';
                animatedPiece.style.left = fromX + 'px'; // Move back to source
                animatedPiece.style.top = fromY + 'px';
            });
            
            // After animation completes
            setTimeout(() => {
                animatedPiece.remove();
                resolve();
            }, 100);
        });
    }

    previousMove() {
        if (this.currentMoveIndex > 0) {
            this.goToMove(this.currentMoveIndex - 1);
        }
    }

    nextMove() {
        if (this.currentMoveIndex < this.gameMoves.length) {
            this.goToMove(this.currentMoveIndex + 1);
        }
    }

    goToFirstMove() {
        this.currentMoveIndex = 0;
        this.resetToStartingPosition();
        this.updateBoard();
        this.updateMoveControls();
        this.highlightCurrentMove();
    }

    goToLastMove() {
        this.goToMoveDirect(this.gameMoves.length);
    }

    handleKeyPress(e) {
        const isModalOpen = !this.gameModal.classList.contains('hidden');
        console.log('Key pressed:', e.key, 'Modal open:', isModalOpen);
        
        // Only handle keyboard navigation when game modal is open
        if (!isModalOpen) {
            console.log('Modal not open, ignoring key press');
            return;
        }
        
        // Prevent default behavior for arrow keys
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' || e.key === 'ArrowUp' || e.key === 'ArrowDown') {
            e.preventDefault();
        }
        
        switch (e.key) {
            case 'ArrowLeft':
                console.log('Left arrow - going to previous move');
                this.previousMove();
                break;
            case 'ArrowRight':
                console.log('Right arrow - going to next move');
                this.nextMove();
                break;
            case 'ArrowUp':
                console.log('Up arrow - going to first move');
                this.goToFirstMove();
                break;
            case 'ArrowDown':
                console.log('Down arrow - going to last move');
                this.goToLastMove();
                break;
            case 'f':
            case 'F':
                console.log('F key - flipping board');
                this.flipBoard();
                break;
        }
    }

    highlightCurrentMove() {
        // Remove previous highlights
        document.querySelectorAll('.move.current').forEach(move => {
            move.classList.remove('current');
        });
        
        // Highlight current move
        const moves = this.movesList.querySelectorAll('.move');
        const moveIndex = Math.floor((this.currentMoveIndex - 1) / 2);
        if (moves[moveIndex]) {
            moves[moveIndex].classList.add('current');
        }
    }

    closeGameModal() {
        this.gameModal.classList.add('hidden');
        this.currentGame = null;
    }

    showLoading(show) {
        if (show) {
            this.loadingIndicator.classList.remove('hidden');
        } else {
            this.loadingIndicator.classList.add('hidden');
        }
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.classList.remove('hidden');
    }

    hideError() {
        this.errorMessage.classList.add('hidden');
    }

    // ============================================================================
    // OpenAI API Key Management
    // ============================================================================

    async checkOpenAIKeyStatus() {
        try {
            const response = await fetch('http://localhost:9090/settings/openai-key/status');
            if (!response.ok) {
                console.log('Could not check OpenAI key status - server may not be ready');
                // Retry after a delay if server isn't ready
                setTimeout(() => this.checkOpenAIKeyStatus(), 2000);
                return;
            }
            
            const status = await response.json();
            this.openaiKeyConfigured = status.configured && status.valid;
            
            if (!this.openaiKeyConfigured) {
                // Show the modal after a short delay to let the app load
                setTimeout(() => this.showOpenAIKeyModal(), 500);
            }
        } catch (error) {
            console.log('Error checking OpenAI key status:', error.message);
            // Retry after a delay if server isn't ready
            setTimeout(() => this.checkOpenAIKeyStatus(), 2000);
        }
    }

    showOpenAIKeyModal() {
        this.openaiKeyModal.classList.remove('hidden');
        this.openaiKeyInput.value = '';
        this.openaiKeyError.classList.add('hidden');
        this.openaiKeyInput.classList.remove('valid', 'invalid');
        this.openaiKeyInput.focus();
    }

    hideOpenAIKeyModal() {
        this.openaiKeyModal.classList.add('hidden');
        this.openaiKeyInput.value = '';
        this.openaiKeyError.classList.add('hidden');
    }

    toggleKeyVisibility() {
        const isPassword = this.openaiKeyInput.type === 'password';
        this.openaiKeyInput.type = isPassword ? 'text' : 'password';
        this.toggleKeyVisibilityBtn.textContent = isPassword ? '🙈' : '👁';
    }

    async saveOpenAIKey() {
        const apiKey = this.openaiKeyInput.value.trim();
        
        if (!apiKey) {
            this.showOpenAIKeyError('Please enter an API key');
            return;
        }
        
        if (!apiKey.startsWith('sk-')) {
            this.showOpenAIKeyError('Invalid API key format. Keys should start with "sk-"');
            return;
        }
        
        // Show loading state
        this.saveOpenaiKeyBtn.disabled = true;
        const btnText = this.saveOpenaiKeyBtn.querySelector('.btn-text');
        const btnSpinner = this.saveOpenaiKeyBtn.querySelector('.btn-spinner');
        btnText.textContent = 'Validating...';
        btnSpinner.classList.remove('hidden');
        this.openaiKeyError.classList.add('hidden');
        
        try {
            const response = await fetch('http://localhost:9090/settings/openai-key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ api_key: apiKey })
            });
            
            const result = await response.json();
            
            if (result.success && result.valid) {
                // Success!
                this.openaiKeyInput.classList.remove('invalid');
                this.openaiKeyInput.classList.add('valid');
                this.openaiKeyConfigured = true;
                
                // Show success briefly then close
                btnText.textContent = '✓ Saved!';
                btnSpinner.classList.add('hidden');
                
                setTimeout(() => {
                    this.hideOpenAIKeyModal();
                    // Reset button state
                    btnText.textContent = 'Validate & Save';
                    this.saveOpenaiKeyBtn.disabled = false;
                }, 1000);
            } else {
                // Validation failed
                this.openaiKeyInput.classList.remove('valid');
                this.openaiKeyInput.classList.add('invalid');
                this.showOpenAIKeyError(result.message || 'Invalid API key');
                
                // Reset button
                btnText.textContent = 'Validate & Save';
                btnSpinner.classList.add('hidden');
                this.saveOpenaiKeyBtn.disabled = false;
            }
        } catch (error) {
            this.showOpenAIKeyError('Failed to connect to server. Please try again.');
            
            // Reset button
            btnText.textContent = 'Validate & Save';
            btnSpinner.classList.add('hidden');
            this.saveOpenaiKeyBtn.disabled = false;
        }
    }

    showOpenAIKeyError(message) {
        this.openaiKeyError.textContent = message;
        this.openaiKeyError.classList.remove('hidden');
        this.openaiKeyInput.classList.add('invalid');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChessQLApp();
});
