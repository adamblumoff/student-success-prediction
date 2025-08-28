/**
 * Simple Login Component
 * Basic username/password authentication
 */

class LoginComponent extends Component {
    constructor(selector, appState) {
        super(selector, appState);
        this.isLoggingIn = false;
        this.checkAuthStatus();
    }

    init() {
        this.render();
        this.setupEventListeners();
    }

    render() {
        const html = `
            <div class="login-form">
                <h2>🎓 Student Success Platform</h2>
                <form id="login-form">
                    <div class="form-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" name="username" required autocomplete="username">
                    </div>
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" name="password" required autocomplete="current-password">
                    </div>
                    <button type="submit" class="login-button" id="login-btn">
                        Sign In
                    </button>
                    <div id="error-message" class="error-message" style="display: none;"></div>
                </form>
                
                <div class="demo-credentials">
                    <h4>Demo Credentials</h4>
                    <p><strong>Username:</strong> teacher</p>
                    <p><strong>Password:</strong> demo123</p>
                    <p><em>Or use: admin / admin123</em></p>
                </div>
            </div>
        `;
        
        this.element.innerHTML = html;
    }

    setupEventListeners() {
        const form = document.getElementById('login-form');
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');

        this.bindEvent(form, 'submit', (e) => this.handleLogin(e));
        
        // Clear errors on input
        this.bindEvent(usernameInput, 'input', () => this.clearError());
        this.bindEvent(passwordInput, 'input', () => this.clearError());
    }

    async handleLogin(event) {
        event.preventDefault();
        
        if (this.isLoggingIn) return;
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        
        if (!username || !password) {
            this.showError('Please enter both username and password');
            return;
        }

        this.setLoading(true);
        
        try {
            const response = await fetch('/api/mvp/auth/web-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();

            if (response.ok && result.success) {
                this.onLoginSuccess(result);
            } else {
                this.showError(result.message || 'Login failed. Please check your credentials.');
            }
        } catch (error) {
            this.showError('Connection error. Please try again.');
            console.error('Login error:', error);
        } finally {
            this.setLoading(false);
        }
    }

    onLoginSuccess(result) {
        // Store auth info
        sessionStorage.setItem('auth_token', result.token);
        sessionStorage.setItem('user_info', JSON.stringify(result.user));
        
        // Update app state
        this.appState.setState({
            user: result.user,
            isAuthenticated: true
        });
        
        // Show main app
        document.body.classList.remove('login-active');
        document.body.classList.add('logged-in');
        
        // Update header UI
        this.updateHeaderUI(result.user);
        
        // Show success message briefly
        this.showSuccess('Welcome back!');
    }

    checkAuthStatus() {
        const token = sessionStorage.getItem('auth_token');
        const userInfo = sessionStorage.getItem('user_info');
        
        if (token && userInfo) {
            try {
                const user = JSON.parse(userInfo);
                this.appState.setState({
                    user,
                    isAuthenticated: true
                });
                document.body.classList.add('logged-in');
                this.updateHeaderUI(user);
            } catch (error) {
                this.logout();
            }
        } else {
            document.body.classList.add('login-active');
        }
    }

    logout() {
        sessionStorage.removeItem('auth_token');
        sessionStorage.removeItem('user_info');
        
        this.appState.setState({
            user: null,
            isAuthenticated: false
        });
        
        document.body.classList.remove('logged-in');
        document.body.classList.add('login-active');
        
        // Clear form
        document.getElementById('login-form')?.reset();
        this.clearError();
    }

    setLoading(loading) {
        this.isLoggingIn = loading;
        const button = document.getElementById('login-btn');
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        
        if (button) {
            button.disabled = loading;
            button.textContent = loading ? 'Signing In...' : 'Sign In';
        }
        
        if (usernameInput) usernameInput.disabled = loading;
        if (passwordInput) passwordInput.disabled = loading;
    }

    showError(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    showSuccess(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.color = '#27ae60';
            errorElement.style.display = 'block';
            
            setTimeout(() => {
                errorElement.style.display = 'none';
                errorElement.style.color = '#e74c3c';
            }, 2000);
        }
    }

    clearError() {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    updateHeaderUI(user) {
        // Show user info and logout button
        const userInfo = document.getElementById('user-info');
        const userName = document.getElementById('user-name');
        const logoutBtn = document.getElementById('logout-btn');
        const bulkModeToggle = document.getElementById('bulk-mode-toggle');

        if (userInfo && userName) {
            userName.textContent = user.name || user.username;
            userInfo.style.display = 'inline-block';
        }

        if (logoutBtn) {
            logoutBtn.style.display = 'inline-block';
            // Add logout event listener
            logoutBtn.onclick = () => this.handleLogout();
        }

        // Bulk mode toggle is now embedded in the analyze tab content

        if (bulkModeToggle) {
            // Add bulk mode toggle event listener
            bulkModeToggle.onclick = () => {
                if (window.selectionManager) {
                    window.selectionManager.toggleSelectionMode();
                    bulkModeToggle.classList.toggle('active');
                    
                    // Update button text and icon based on new state
                    const icon = bulkModeToggle.querySelector('i');
                    const span = bulkModeToggle.querySelector('span');
                    
                    if (window.selectionManager.selectionMode) {
                        // Bulk mode is now ON
                        icon.className = 'fas fa-times-square';
                        span.textContent = 'Turn Off Bulk Actions';
                        bulkModeToggle.title = 'Disable bulk selection mode';
                    } else {
                        // Bulk mode is now OFF
                        icon.className = 'fas fa-check-square';
                        span.textContent = 'Turn On Bulk Actions';
                        bulkModeToggle.title = 'Enable bulk selection to create interventions for multiple students';
                    }
                }
            };
        }
    }

    async handleLogout() {
        try {
            const token = sessionStorage.getItem('auth_token');
            if (token) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.logout();
        }
    }
}

// Make available globally
window.LoginComponent = LoginComponent;