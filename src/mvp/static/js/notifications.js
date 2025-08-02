/**
 * Real-time Notification System JavaScript
 * Handles WebSocket connections, alert display, and notification management
 */

class NotificationSystem {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.alerts = [];
        this.settings = {
            enableSound: true,
            enableDesktop: true,
            enableNotifications: true,  // New setting to completely disable notifications
            riskThreshold: 0.7
        };
        this.reconnectInterval = null;
        this.maxReconnectAttempts = 5;
        this.reconnectAttempts = 0;
        
        this.init();
    }

    init() {
        this.loadSettings();
        this.bindEvents();
        this.requestNotificationPermission();
        this.connectWebSocket();
        this.showNotificationsPanel();
    }

    bindEvents() {
        // Settings modal
        document.getElementById('toggle-notifications')?.addEventListener('click', () => this.showSettings());
        document.getElementById('close-notification-settings')?.addEventListener('click', () => this.hideSettings());
        
        // Clear all alerts
        document.getElementById('clear-alerts')?.addEventListener('click', () => this.clearAllAlerts());
        
        // Settings changes
        document.getElementById('enable-sound')?.addEventListener('change', (e) => {
            this.settings.enableSound = e.target.checked;
            this.saveSettings();
        });
        
        document.getElementById('enable-desktop')?.addEventListener('change', (e) => {
            this.settings.enableDesktop = e.target.checked;
            this.saveSettings();
        });
        
        document.getElementById('enable-notifications')?.addEventListener('change', (e) => {
            this.settings.enableNotifications = e.target.checked;
            this.saveSettings();
            this.toggleNotificationsPanel();
        });
        
        document.getElementById('risk-threshold')?.addEventListener('change', (e) => {
            this.settings.riskThreshold = parseFloat(e.target.value);
            this.saveSettings();
        });
    }

    loadSettings() {
        const saved = localStorage.getItem('notification-settings');
        if (saved) {
            this.settings = { ...this.settings, ...JSON.parse(saved) };
            this.applySettings();
        }
    }

    saveSettings() {
        localStorage.setItem('notification-settings', JSON.stringify(this.settings));
    }

    applySettings() {
        document.getElementById('enable-sound').checked = this.settings.enableSound;
        document.getElementById('enable-desktop').checked = this.settings.enableDesktop;
        document.getElementById('enable-notifications').checked = this.settings.enableNotifications;
        document.getElementById('risk-threshold').value = this.settings.riskThreshold;
    }

    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            await Notification.requestPermission();
        }
    }

    connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/notifications/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('🔔 Connected to notification system');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected', '🟢 Connected');
                
                if (this.reconnectInterval) {
                    clearInterval(this.reconnectInterval);
                    this.reconnectInterval = null;
                }
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('🔔 Disconnected from notification system');
                this.isConnected = false;
                this.updateConnectionStatus('disconnected', '🔴 Disconnected');
                this.scheduleReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error', '⚠️ Connection Error');
            };
            
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.updateConnectionStatus('error', '❌ Connection Failed');
            this.scheduleReconnect();
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts && !this.reconnectInterval) {
            this.reconnectInterval = setInterval(() => {
                this.reconnectAttempts++;
                console.log(`🔄 Reconnecting attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                this.updateConnectionStatus('reconnecting', `🔄 Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connectWebSocket();
            }, 5000);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'connection_established':
                console.log('🔔 Notification connection established');
                this.updateAlertCount(data.active_alerts || 0);
                break;
                
            case 'student_alert':
                this.handleStudentAlert(data.alert);
                break;
                
            case 'alert_update':
                this.handleAlertUpdate(data);
                break;
                
            case 'pong':
                // Handle ping/pong for connection keepalive
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleStudentAlert(alert) {
        console.log('🚨 New student alert received:', alert);
        
        // If notifications are disabled, don't show any alerts
        if (!this.settings.enableNotifications) {
            console.log('🔕 Notifications disabled, alert suppressed');
            return;
        }
        
        // Add to alerts list
        this.alerts.unshift(alert);
        this.displayAlert(alert);
        this.updateAlertCount(this.alerts.length);
        
        // Play sound if enabled
        if (this.settings.enableSound) {
            this.playAlertSound(alert.alert_level);
        }
        
        // Show desktop notification if enabled
        if (this.settings.enableDesktop && alert.risk_score >= this.settings.riskThreshold) {
            this.showDesktopNotification(alert);
        }
        
        // Animate notification panel if hidden
        this.animateNewAlert();
    }

    handleAlertUpdate(data) {
        const alert = this.alerts.find(a => a.alert_id === data.alert_id);
        if (alert) {
            if (data.update_type === 'acknowledged') {
                alert.acknowledged = true;
            } else if (data.update_type === 'resolved') {
                alert.resolved = true;
                // Remove from active alerts
                this.alerts = this.alerts.filter(a => a.alert_id !== data.alert_id);
                this.updateAlertCount(this.alerts.length);
            }
            this.refreshAlertsDisplay();
        }
    }

    displayAlert(alert) {
        const alertsContainer = document.getElementById('alerts-list');
        const noAlertsDiv = document.getElementById('no-alerts');
        
        // Hide "no alerts" message
        if (noAlertsDiv) {
            noAlertsDiv.style.display = 'none';
        }
        
        // Create alert element
        const alertElement = document.createElement('div');
        alertElement.className = `alert-item alert-${alert.alert_level}`;
        alertElement.dataset.alertId = alert.alert_id;
        
        const timeAgo = this.formatTimeAgo(new Date(alert.timestamp));
        const riskPercentage = (alert.risk_score * 100).toFixed(1);
        
        alertElement.innerHTML = `
            <div class="alert-header">
                <div class="alert-student">
                    <span class="student-name">${alert.student_name}</span>
                    <span class="alert-level-badge ${alert.alert_level}">${alert.alert_level.toUpperCase()}</span>
                </div>
                <div class="alert-time">${timeAgo}</div>
            </div>
            
            <div class="alert-content">
                <div class="alert-message">${alert.message}</div>
                <div class="alert-details">
                    <span class="risk-score">Risk: ${riskPercentage}%</span>
                    ${alert.previous_risk_score ? `<span class="risk-change">+${((alert.risk_score - alert.previous_risk_score) * 100).toFixed(1)}%</span>` : ''}
                </div>
            </div>
            
            <div class="alert-actions">
                <button class="btn btn-small btn-primary acknowledge-btn" onclick="notificationSystem.acknowledgeAlert('${alert.alert_id}')">
                    ✓ Acknowledge
                </button>
                <button class="btn btn-small btn-secondary resolve-btn" onclick="notificationSystem.resolveAlert('${alert.alert_id}')">
                    ✓ Resolve
                </button>
                ${alert.intervention_recommended ? '<span class="intervention-flag">🎯 Intervention Recommended</span>' : ''}
            </div>
        `;
        
        // Add to alerts container
        alertsContainer.insertBefore(alertElement, alertsContainer.firstChild);
        
        // Animate in
        setTimeout(() => {
            alertElement.classList.add('alert-show');
        }, 100);
    }

    async acknowledgeAlert(alertId) {
        try {
            const response = await fetch(`/api/notifications/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getApiKey()}`
                },
                body: JSON.stringify({
                    alert_id: alertId,
                    user_id: 'mvp_user'
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log('✓ Alert acknowledged:', alertId);
                // Update UI
                const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
                if (alertElement) {
                    alertElement.classList.add('acknowledged');
                    const acknowledgeBtn = alertElement.querySelector('.acknowledge-btn');
                    if (acknowledgeBtn) {
                        acknowledgeBtn.textContent = '✓ Acknowledged';
                        acknowledgeBtn.disabled = true;
                    }
                }
            } else {
                throw new Error(result.detail || 'Failed to acknowledge alert');
            }
        } catch (error) {
            console.error('Error acknowledging alert:', error);
            this.showToast('Failed to acknowledge alert', 'error');
        }
    }

    async resolveAlert(alertId) {
        try {
            const response = await fetch(`/api/notifications/alerts/${alertId}/resolve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.getApiKey()}`
                },
                body: JSON.stringify({
                    alert_id: alertId,
                    user_id: 'mvp_user',
                    resolution_notes: 'Resolved via web interface'
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log('✓ Alert resolved:', alertId);
                // Remove from UI
                const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
                if (alertElement) {
                    alertElement.classList.add('resolving');
                    setTimeout(() => {
                        alertElement.remove();
                        this.alerts = this.alerts.filter(a => a.alert_id !== alertId);
                        this.updateAlertCount(this.alerts.length);
                        this.checkNoAlerts();
                    }, 500);
                }
            } else {
                throw new Error(result.detail || 'Failed to resolve alert');
            }
        } catch (error) {
            console.error('Error resolving alert:', error);
            this.showToast('Failed to resolve alert', 'error');
        }
    }

    clearAllAlerts() {
        if (this.alerts.length === 0) return;
        
        if (confirm('Clear all alerts? This action cannot be undone.')) {
            this.alerts = [];
            this.updateAlertCount(0);
            this.refreshAlertsDisplay();
            this.showToast('All alerts cleared', 'success');
        }
    }

    refreshAlertsDisplay() {
        const alertsContainer = document.getElementById('alerts-list');
        const alertElements = alertsContainer.querySelectorAll('.alert-item');
        alertElements.forEach(el => el.remove());
        
        this.alerts.forEach(alert => this.displayAlert(alert));
        this.checkNoAlerts();
    }

    checkNoAlerts() {
        const noAlertsDiv = document.getElementById('no-alerts');
        if (noAlertsDiv) {
            noAlertsDiv.style.display = this.alerts.length === 0 ? 'block' : 'none';
        }
    }

    playAlertSound(alertLevel) {
        try {
            // Create audio context for web audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Generate different tones based on alert level
            const frequencies = {
                'low': [440, 660],       // A4, E5
                'medium': [660, 880],    // E5, A5
                'high': [880, 1320],     // A5, E6
                'critical': [1320, 1760] // E6, A6
            };
            
            const freqs = frequencies[alertLevel] || frequencies['medium'];
            
            // Play two-tone alert
            freqs.forEach((freq, index) => {
                setTimeout(() => {
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.value = freq;
                    oscillator.type = 'sine';
                    
                    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                    
                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.3);
                }, index * 150);
            });
        } catch (error) {
            console.warn('Could not play alert sound:', error);
        }
    }

    showDesktopNotification(alert) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const riskPercentage = (alert.risk_score * 100).toFixed(1);
            
            const notification = new Notification(`Student Alert: ${alert.student_name}`, {
                body: `${alert.message}\nRisk Score: ${riskPercentage}%`,
                icon: '/static/images/notification-icon.png',
                tag: alert.alert_id,
                requireInteraction: alert.alert_level === 'critical'
            });
            
            notification.onclick = () => {
                window.focus();
                this.showNotificationsPanel();
                notification.close();
            };
            
            // Auto-close after 10 seconds unless critical
            if (alert.alert_level !== 'critical') {
                setTimeout(() => notification.close(), 10000);
            }
        }
    }

    animateNewAlert() {
        const panel = document.getElementById('notifications-panel');
        if (panel) {
            panel.classList.add('new-alert-pulse');
            setTimeout(() => {
                panel.classList.remove('new-alert-pulse');
            }, 1000);
        }
    }

    updateConnectionStatus(status, text) {
        const indicator = document.getElementById('ws-status-indicator');
        const statusText = document.getElementById('ws-status-text');
        
        if (indicator && statusText) {
            indicator.className = `status-indicator ${status}`;
            statusText.textContent = text;
        }
    }

    updateAlertCount(count) {
        const countElement = document.getElementById('alert-count');
        if (countElement) {
            countElement.textContent = count;
            countElement.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    showNotificationsPanel() {
        const panel = document.getElementById('notifications-panel');
        if (panel && this.settings.enableNotifications) {
            panel.style.display = 'block';
        }
    }

    toggleNotificationsPanel() {
        const panel = document.getElementById('notifications-panel');
        if (panel) {
            if (this.settings.enableNotifications) {
                panel.style.display = 'block';
            } else {
                panel.style.display = 'none';
            }
        }
    }

    showSettings() {
        const modal = document.getElementById('notification-settings-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    hideSettings() {
        const modal = document.getElementById('notification-settings-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        
        if (diffSecs < 60) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return date.toLocaleDateString();
    }

    getApiKey() {
        return localStorage.getItem('api-key') || 'dev-key-change-me';
    }

    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // Test method to simulate alerts for demonstration
    simulateAlert(studentName = 'Test Student', riskScore = 0.85) {
        const testAlert = {
            alert_id: `test_${Date.now()}`,
            student_id: 'test_001',
            student_name: studentName,
            alert_type: 'risk_threshold',
            alert_level: riskScore >= 0.85 ? 'critical' : riskScore >= 0.7 ? 'high' : 'medium',
            risk_score: riskScore,
            previous_risk_score: riskScore - 0.15,
            message: `🚨 ${studentName} has crossed the high risk threshold`,
            timestamp: new Date().toISOString(),
            acknowledged: false,
            resolved: false,
            intervention_recommended: riskScore >= 0.7
        };
        
        this.handleStudentAlert(testAlert);
    }
}

// Initialize notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.notificationSystem = new NotificationSystem();
    
    // Add test button for development (remove in production)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('🧪 Development mode: Use notificationSystem.simulateAlert() to test notifications');
    }
});