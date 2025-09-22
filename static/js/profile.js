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

// Profile picture upload
document.getElementById('profile-upload').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            document.querySelector('.profile-picture').src = event.target.result;
            document.querySelector('.user-avatar').src = event.target.result;
            showToast('Profile picture updated successfully', 'success');
            
            // In a real app, you would upload to your Flask backend
            // const formData = new FormData();
            // formData.append('profile_picture', file);
            // fetch('/api/upload-profile-picture', {
            //     method: 'POST',
            //     body: formData
            // });
        };
        reader.readAsDataURL(file);
    }
});

// Edit profile button
document.getElementById('editProfileBtn').addEventListener('click', function() {
    // In a real app, this would open an edit form
    showToast('Edit profile functionality would open a form here', 'warning');
});

// Change password button
document.getElementById('changePasswordBtn').addEventListener('click', function() {
    // In a real app, this would open a password change form
    showToast('Change password functionality would open a form here', 'warning');
});

// Logout button
document.getElementById('logoutBtn').addEventListener('click', function() {
    if (confirm('Are you sure you want to logout?')) {
        // In a real app, you would call your Flask logout endpoint
        // fetch('/api/logout', { method: 'POST' })
        //     .then(() => window.location.href = '/login');
        
        // For demo purposes:
        window.location.href = '/logout';
    }
});

// Sidebar logout button
document.querySelector('.logout-btn').addEventListener('click', function() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
});
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
