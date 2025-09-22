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

// Notification functions
function showNotification(message, isWarning = false) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.style.backgroundColor = isWarning ? '#f72585' : '#4cc9f0';
    notification.style.display = 'block';
    setTimeout(() => {
        notification.style.display = 'none';
    }, 5000);
}

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

// Original application functions
const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
});

function formatCurrency(amount) {
    return formatter.format(amount || 0);
}

function startProcess() {
    fetch('/start_process', { method: 'POST' })
    .then(response => {
        if (response.ok) {
            showToast("Process started successfully!", "success");
            document.getElementById('camera-status').textContent = 'Live';
        } else {
            showToast("Process already running", "warning");
        }
    });
}

function stopProcess() {
    fetch('/stop_process', { method: 'POST' })
    .then(response => response.ok ? 
        (showToast("Process stopped successfully!", "success"),
        document.getElementById('camera-status').textContent = 'Offline') : 
        showToast("Error stopping process", "error"));
}

function updateReadingInfo() {
    fetch('/get_reading')
        .then(response => response.json())
        .then(data => {
            // Update reading card
            document.getElementById('reading').textContent = data.reading;
            document.getElementById('reading-time').textContent = data.timestamp || 'N/A';
            
            // Update bill card
            document.getElementById('bill-amount').textContent = formatCurrency(data.bill_amount);
            
            // Update initial reading
            if (data.initial_reading) {
                document.getElementById('initialReading').textContent = `${data.initial_reading} KWh`;
            } else {
                document.getElementById('initialReading').textContent = 'Not set';
            }
            
            // Update status
            document.getElementById('readingStatus').textContent = data.debug_info;
            document.getElementById('debug-info').textContent = data.debug_info;
        })
        .catch(error => console.error('Error:', error));
}

function updateStatus() {
    fetch('/get_status')
        .then(response => response.json())
        .then(data => {
            const nextCaptureInElement = document.getElementById('next-capture-in');
            const nextCaptureTimeElement = document.getElementById('next-capture-time');
            
            if (data.is_initial_delay) {
                nextCaptureInElement.textContent = data.next_capture_in;
                nextCaptureTimeElement.textContent = data.next_capture_time;
            } else if (data.next_capture_in !== "N/A") {
                nextCaptureInElement.textContent = data.next_capture_in;
                nextCaptureTimeElement.textContent = data.next_capture_time;
            } else {
                nextCaptureInElement.textContent = 'N/A';
                nextCaptureTimeElement.textContent = 'N/A';
            }
        })
        .catch(error => {
            console.error('Error fetching status:', error);
            document.getElementById('next-capture-in').textContent = 'N/A';
            document.getElementById('next-capture-time').textContent = 'N/A';
        });
}

function clearAllReadings() {
    if (confirm("Are you sure you want to clear all readings?")) {
        fetch('/clear_readings', { method: 'POST' })
        .then(response => {
            if (response.ok) {
                showToast("All readings cleared successfully!", "success");
                updateReadingsHistory();
            } else {
                showToast("Failed to clear readings", "error");
            }
        });
    }
}

function updateReadingsHistory() {
    fetch('/get_readings')
        .then(response => response.json())
        .then(readings => {
            const tbody = document.getElementById('readings-table');
            tbody.innerHTML = '';
            
            readings.forEach(reading => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${reading.reading}</td>
                    <td>${reading.timestamp}</td>
                    <td>${formatCurrency(reading.total_amount)}</td>
                `;
                tbody.appendChild(row);
            });
        });
}

function updatePhase() {
    const phase = document.getElementById('phase-type').value;
    fetch('/update_phase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phase })
    }).then(response => {
        response.ok ? 
            showToast("Meter phase updated successfully!", "success") : 
            showToast("Failed to update phase", "error");
    });
}

// Initialize polling
updateReadingInfo();
setInterval(updateReadingInfo, 5000);
setInterval(updateReadingsHistory, 5000);
setInterval(updateStatus, 1000);
// Shared function to update alerts badge count in navbar
function updateAlertsBadge() {
    fetch('/get_alerts')
        .then(response => response.json())
        .then(alerts => {
            const alertsCount = document.getElementById('alerts-count');
            if (alertsCount) alertsCount.textContent = alerts.length;
        })
        .catch(error => console.error('Error fetching alerts badge count:', error));
}
// Polling for alerts badge (optional for live updates only)
setInterval(updateAlertsBadge, 30000);
