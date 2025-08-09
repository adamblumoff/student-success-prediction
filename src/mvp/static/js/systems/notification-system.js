/**
 * Notification System
 * Handles notification panel, toasts, and persistence
 */

class NotificationSystem {
  constructor(appInstance) {
    this.app = appInstance;
    this.initialized = false;
  }

  initialize() {
    if (this.initialized) return;
    
    const notificationsToggle = document.getElementById('notifications-toggle');
    const notificationPanel = document.getElementById('notification-panel');
    const closeNotifications = document.getElementById('close-notifications');
    const markAllRead = document.getElementById('mark-all-read');
    const clearNotifications = document.getElementById('clear-notifications');
    const notificationSettings = document.getElementById('notification-settings');

    if (notificationsToggle) {
      notificationsToggle.addEventListener('click', () => this.toggleNotificationPanel());
    }

    if (closeNotifications) {
      closeNotifications.addEventListener('click', () => this.closeNotificationPanel());
    }

    if (markAllRead) {
      markAllRead.addEventListener('click', () => this.markAllNotificationsRead());
    }

    if (clearNotifications) {
      clearNotifications.addEventListener('click', () => this.clearAllNotifications());
    }

    if (notificationSettings) {
      notificationSettings.addEventListener('click', () => {
        this.closeNotificationPanel();
        this.app.openSettingsModal();
      });
    }

    // Initialize filter tabs
    const filterTabs = document.querySelectorAll('.filter-tab');
    filterTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        filterTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.filterNotifications(tab.dataset.filter);
      });
    });

    // Load existing notifications from localStorage
    this.loadNotificationsFromStorage();
    
    // Add some demo notifications if none exist
    const notifications = this.getStoredNotifications();
    if (notifications.length === 0) {
      this.addDemoNotifications();
    }

    this.initialized = true;
  }

  toggleNotificationPanel() {
    const panel = document.getElementById('notification-panel');
    if (panel) {
      const isHidden = panel.classList.contains('hidden');
      if (isHidden) {
        panel.classList.remove('hidden');
        this.updateNotificationBadge();
      } else {
        panel.classList.add('hidden');
      }
    }
  }

  closeNotificationPanel() {
    const panel = document.getElementById('notification-panel');
    if (panel) {
      panel.classList.add('hidden');
    }
  }

  addNotificationToPanel(notification) {
    // Store notification
    const notifications = this.getStoredNotifications();
    notifications.unshift(notification); // Add to beginning
    localStorage.setItem('studentSuccessNotifications', JSON.stringify(notifications.slice(0, 100))); // Keep last 100

    // Update UI
    this.renderNotifications();
    this.updateNotificationBadge();
  }

  getStoredNotifications() {
    try {
      return JSON.parse(localStorage.getItem('studentSuccessNotifications') || '[]');
    } catch {
      return [];
    }
  }

  renderNotifications() {
    const notificationList = document.getElementById('notification-list');
    const noNotifications = document.getElementById('no-notifications');
    const notifications = this.getStoredNotifications();

    if (!notificationList) return;

    if (notifications.length === 0) {
      noNotifications.style.display = 'block';
      notificationList.innerHTML = '';
      return;
    }

    noNotifications.style.display = 'none';
    
    const currentFilter = document.querySelector('.filter-tab.active')?.dataset.filter || 'all';
    const filteredNotifications = this.filterNotificationsByType(notifications, currentFilter);

    notificationList.innerHTML = filteredNotifications.map(notification => `
      <div class="notification-item ${notification.read ? 'read' : 'unread'}" data-id="${notification.id}">
        <div class="notification-icon">
          <i class="fas fa-${this.getNotificationIcon(notification.type)}"></i>
        </div>
        <div class="notification-content">
          <div class="notification-message">${notification.message}</div>
          <div class="notification-time">${this.formatNotificationTime(notification.timestamp)}</div>
        </div>
        <div class="notification-actions">
          ${!notification.read ? `<button class="btn-icon" onclick="window.modernApp.notificationSystem.markNotificationRead(${notification.id})" title="Mark as read">
            <i class="fas fa-check"></i>
          </button>` : ''}
          <button class="btn-icon" onclick="window.modernApp.notificationSystem.removeNotification(${notification.id})" title="Remove">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    `).join('');
  }

  filterNotificationsByType(notifications, filter) {
    switch (filter) {
      case 'unread':
        return notifications.filter(n => !n.read);
      case 'high-risk':
        return notifications.filter(n => n.message.toLowerCase().includes('high risk') || n.message.toLowerCase().includes('urgent'));
      case 'system':
        return notifications.filter(n => n.type === 'info' || n.message.toLowerCase().includes('system'));
      default:
        return notifications;
    }
  }

  filterNotifications(filterType) {
    this.renderNotifications();
  }

  getNotificationIcon(type) {
    switch (type) {
      case 'success': return 'check-circle';
      case 'error': return 'exclamation-triangle';
      case 'warning': return 'exclamation-circle';
      default: return 'bell';
    }
  }

  formatNotificationTime(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = now - time;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  }

  markNotificationRead(id) {
    const notifications = this.getStoredNotifications();
    const notification = notifications.find(n => n.id === id);
    if (notification) {
      notification.read = true;
      localStorage.setItem('studentSuccessNotifications', JSON.stringify(notifications));
      this.renderNotifications();
      this.updateNotificationBadge();
    }
  }

  removeNotification(id) {
    const notifications = this.getStoredNotifications().filter(n => n.id !== id);
    localStorage.setItem('studentSuccessNotifications', JSON.stringify(notifications));
    this.renderNotifications();
    this.updateNotificationBadge();
  }

  markAllNotificationsRead() {
    const notifications = this.getStoredNotifications();
    notifications.forEach(n => n.read = true);
    localStorage.setItem('studentSuccessNotifications', JSON.stringify(notifications));
    this.renderNotifications();
    this.updateNotificationBadge();
    this.showNotification('All notifications marked as read', 'success');
  }

  clearAllNotifications() {
    localStorage.removeItem('studentSuccessNotifications');
    this.renderNotifications();
    this.updateNotificationBadge();
    this.showNotification('All notifications cleared', 'success');
  }

  updateNotificationBadge() {
    const badge = document.getElementById('notification-count');
    const notifications = this.getStoredNotifications();
    const unreadCount = notifications.filter(n => !n.read).length;
    
    if (badge) {
      badge.textContent = unreadCount;
      if (unreadCount > 0) {
        badge.classList.remove('hidden');
      } else {
        badge.classList.add('hidden');
      }
    }
  }

  loadNotificationsFromStorage() {
    this.renderNotifications();
    this.updateNotificationBadge();
  }

  addDemoNotifications() {
    const demoNotifications = [
      {
        id: Date.now() - 1000,
        type: 'warning',
        message: '3 students identified as high risk - immediate attention required',
        timestamp: new Date(Date.now() - 300000), // 5 minutes ago
        read: false
      },
      {
        id: Date.now() - 2000,
        type: 'success',
        message: 'Weekly analysis completed successfully for 150 students',
        timestamp: new Date(Date.now() - 3600000), // 1 hour ago
        read: false
      },
      {
        id: Date.now() - 3000,
        type: 'info',
        message: 'New intervention recommendations available for review',
        timestamp: new Date(Date.now() - 7200000), // 2 hours ago
        read: true
      }
    ];

    demoNotifications.forEach(notification => {
      this.addNotificationToPanel(notification);
    });
  }

  showNotification(message, type = 'info') {
    // Add to notification panel
    this.addNotificationToPanel({
      id: Date.now(),
      type: type,
      message: message,
      timestamp: new Date(),
      read: false
    });

    // Create toast notification (keeping the existing behavior)
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
      </div>
      <button class="toast-close">&times;</button>
    `;

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.remove();
    }, 5000);

    // Manual close
    toast.querySelector('.toast-close').addEventListener('click', () => {
      toast.remove();
    });
  }
}

// Make NotificationSystem available globally
window.NotificationSystem = NotificationSystem;