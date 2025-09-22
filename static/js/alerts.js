// Sidebar Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    // Desktop toggle
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
    
    // Load saved state
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
    }
    
    // Update active nav item
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            navItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function updateAlerts() {
    fetch('/get_alerts')
        .then(response => response.json())
        .then(alerts => {
            const alertsList = document.getElementById('alerts-list');
            const alertsCount = document.getElementById('alerts-count');
            
            // Update alerts count in sidebar
            alertsCount.textContent = alerts.length;
            
            if (alerts.length === 0) {
                alertsList.innerHTML = `
                    <div class="no-alerts">
                        <i class="fas fa-check-circle"></i>
                        <p>No alerts to display</p>
                    </div>
                `;
                return;
            }

            alertsList.innerHTML = alerts.map(alert => `
                <div class="alert-card ${alert.type}" data-id="${alert.id}">
                    <div class="alert-header">
                        <span class="alert-type ${alert.type}">${alert.type}</span>
                        <span class="alert-timestamp">${formatTimestamp(alert.timestamp)}</span>
                    </div>
                    <div class="alert-message">${alert.message}</div>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error fetching alerts:', error));
}

function clearAllAlerts() {
    if (confirm('Are you sure you want to clear all alerts?')) {
        fetch('/clear_alerts', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('All alerts cleared successfully', 'success');
                updateAlerts();
            } else {
                showToast('Failed to clear alerts', 'error');
            }
        })
        .catch(error => {
            console.error('Error clearing alerts:', error);
            showToast('Error clearing alerts', 'error');
        });
    }
}

// Enhanced toast notification
function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-message">${message}</div>
        <button class="toast-close">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
    
    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    });
}

// Update alerts every 30 seconds
updateAlerts();
setInterval(updateAlerts, 30000);

// Logout button handler
document.querySelector('.logout-btn').addEventListener('click', function() {
    if (confirm('Are you sure you want to logout?')) {
        // In a real app, you would call your Flask logout endpoint
        // fetch('/api/logout', { method: 'POST' })
        //     .then(() => window.location.href = '/login');
        
        // For demo purposes:
        window.location.href = '/logout';
    }
});
