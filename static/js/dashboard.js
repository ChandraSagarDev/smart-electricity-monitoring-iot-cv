// Apply collapsed state before rendering
(function() {
  var sidebar = document.getElementById('sidebar');
  if (localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
  }
})();

// Sidebar Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    
    // Desktop toggle
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
    
    // Update active nav item
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            navItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
        });
    });
});

// Initialize the limit usage chart
const limitCtx = document.getElementById('limitChart').getContext('2d');
const limitChart = new Chart(limitCtx, {
    type: 'doughnut',
    data: {
        labels: ['Used', 'Remaining'],
        datasets: [{
            data: [0, 100],
            backgroundColor: ['#4361ee', '#e9ecef'],
            borderWidth: 0
        }]
    },
    options: {
        cutout: '80%',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                enabled: true,
                callbacks: {
                    label: function(context) {
                        return `${context.label}: ${context.raw.toFixed(1)}%`;
                    }
                }
            }
        }
    }
});

// Initialize consumption trend chart
const consumptionCtx = document.getElementById('consumption-chart').getContext('2d');
const consumptionChart = new Chart(consumptionCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'kWh Consumption',
            data: [],
            borderColor: '#4361ee',
            backgroundColor: 'rgba(67, 97, 238, 0.1)',
            tension: 0.3,
            fill: true,
            borderWidth: 2
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'kWh'
                }
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    }
});

// Initialize peak hours chart
const peakHoursCtx = document.getElementById('peak-hours-chart').getContext('2d');
const peakHoursChart = new Chart(peakHoursCtx, {
    type: 'bar',
    data: {
        labels: ['12AM', '3AM', '6AM', '9AM', '12PM', '3PM', '6PM', '9PM'],
        datasets: [{
            label: 'Average Consumption (kWh)',
            data: [0, 0, 0, 0, 0, 0, 0, 0],
            backgroundColor: '#4361ee',
            borderColor: '#3f37c9',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'kWh'
                }
            }
        },
        plugins: {
            legend: {
                display: false
            }
        }
    }
});

// Function to update dashboard data
function updateDashboard() {
    fetch('/get_dashboard_data')
        .then(response => response.json())
        .then(data => {
            console.log('Dashboard data:', data); // Debug log
            
            // Update stats based on reading history
            if (data.has_readings) {
                document.getElementById('currentReading').textContent = data.current_reading;
                document.getElementById('avgDailyUsage').textContent = data.average_daily + ' KWh';
                document.getElementById('currentBill').textContent = '₹' + data.current_bill.toFixed(2);

                if (data.consumption_data.length > 0) {
                    consumptionChart.data.labels = data.consumption_labels;
                    consumptionChart.data.datasets[0].data = data.consumption_data;
                    consumptionChart.update();
                }

                // Update peak hours chart with real data
                peakHoursChart.data.datasets[0].data = data.peak_hours_data;
                peakHoursChart.update();
            } else {
                document.getElementById('currentReading').textContent = '0 KWh';
                document.getElementById('avgDailyUsage').textContent = '0 KWh';
                document.getElementById('currentBill').textContent = '₹0.00';
                
                // Clear charts when no readings
                consumptionChart.data.labels = [];
                consumptionChart.data.datasets[0].data = [];
                consumptionChart.update();
                
                peakHoursChart.data.datasets[0].data = [0, 0, 0, 0, 0, 0, 0, 0];
                peakHoursChart.update();
            }

            // Update limit chart and form
            if (data.cost_limit && data.cost_limit > 0) {
                // Show current limit in the input field
                document.getElementById('costLimit').value = data.cost_limit;
                
                // Calculate remaining amount
                const remainingAmount = data.cost_limit - data.current_bill;
                
                // If remaining is less than 0, show 100% filled
                const usedPercent = remainingAmount < 0 ? 100 : Math.min(data.limit_used_percent, 100);
                const remainingPercent = remainingAmount < 0 ? 0 : Math.max(0, 100 - usedPercent);
                
                // Set color to red if usage exceeds or equals 100%, otherwise blue
                let usedColor;
                if (data.limit_used_percent >= 100) {
                    usedColor = '#f72585'; // Red
                } else if (data.limit_used_percent >= 90) {
                    usedColor = '#ff9e00'; // Orange
                } else {
                    usedColor = '#43aa8b'; // Green
                }
                limitChart.data.datasets[0].data = [usedPercent, remainingPercent];
                limitChart.data.datasets[0].backgroundColor = [usedColor, '#e9ecef'];
                limitChart.update();
                
                const limitInfo = document.querySelector('.limit-info');
                limitInfo.innerHTML = `
                    <div class="limit-value" id="limitUsedPercent">${usedPercent.toFixed(1)}%</div>
                    <div class="limit-current">Daily Limit: ₹${data.cost_limit}</div>
                    <div class="limit-label">Current Usage: ₹${data.current_bill.toFixed(2)}</div>
                    <div class="limit-remaining" style="color: ${remainingAmount < 0 ? '#f72585' : '#4361ee'}">
                        ${remainingAmount < 0 ? 
                            `₹${Math.abs(remainingAmount).toFixed(2)} over limit` : 
                            `₹${remainingAmount.toFixed(2)} remaining`}
                    </div>
                `;
            } else {
                document.getElementById('costLimit').value = '';
                
                limitChart.data.datasets[0].data = [0, 100];
                limitChart.data.datasets[0].backgroundColor = ['#4361ee', '#e9ecef'];
                limitChart.update();
                
                const limitInfo = document.querySelector('.limit-info');
                limitInfo.innerHTML = `
                    <div class="limit-value" id="limitUsedPercent">0.0%</div>
                    <div class="limit-label">Please set a daily limit</div>
                    <div class="limit-remaining" style="color: var(--warning);">No limit set</div>
                `;
            }

            // Show notifications only if limit is set and there are readings
            if (data.cost_limit > 0 && data.has_readings) {
                if (data.limit_used_percent >= 100) {
                    // showNotification removed`Alert: Daily cost limit exceeded! Current bill: ₹${data.current_bill.toFixed(2)}, Limit: ₹${data.cost_limit}`, true);
                } else if (data.limit_used_percent >= 90) {
                    const remainingAmount = data.cost_limit - data.current_bill;
                    // showNotification removed`Warning: Approaching daily limit! Used: ${data.limit_used_percent.toFixed(1)}%, Remaining: ₹${remainingAmount.toFixed(2)}`);
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

// Function to load cost limit from database
function loadCostLimit() {
    fetch('/get_dashboard_data')
        .then(response => response.json())
        .then(data => {
            if (data.cost_limit && data.cost_limit > 0) {
                // Update the input field with the limit from database
                document.getElementById('costLimit').value = data.cost_limit;
                
                // Calculate remaining amount
                const remainingAmount = data.cost_limit - data.current_bill;
                const usedPercent = remainingAmount < 0 ? 100 : Math.min(data.limit_used_percent, 100);
                
                // Set color to red if usage exceeds or equals 100%, otherwise blue
                let usedColor;
                if (data.limit_used_percent >= 100) {
                    usedColor = '#f72585'; // Red
                } else if (data.limit_used_percent >= 90) {
                    usedColor = '#ff9e00'; // Orange
                } else {
                    usedColor = '#43aa8b'; // Green
                }
                // Update the chart
                limitChart.data.datasets[0].data = [usedPercent, remainingAmount < 0 ? 0 : 100 - usedPercent];
                limitChart.data.datasets[0].backgroundColor = [usedColor, '#e9ecef'];
                limitChart.update();
                
                // Update the display text
                const limitInfo = document.querySelector('.limit-info');
                limitInfo.innerHTML = `
                    <div class="limit-value" id="limitUsedPercent">${usedPercent.toFixed(1)}%</div>
                    <div class="limit-current">Daily Limit: ₹${data.cost_limit}</div>
                    <div class="limit-label">Current Usage: ₹${data.current_bill.toFixed(2)}</div>
                    <div class="limit-remaining" id="limitRemaining" style="color: ${remainingAmount < 0 ? '#f72585' : '#4361ee'}">
                        ${remainingAmount < 0 ? 
                            `₹${Math.abs(remainingAmount).toFixed(2)} over limit` : 
                            `₹${remainingAmount.toFixed(2)} remaining`}
                    </div>
                `;
            }
        })
        .catch(error => console.error('Error loading cost limit:', error));
}

// Call loadCostLimit when the page loads
document.addEventListener('DOMContentLoaded', loadCostLimit);

// Function to set cost limit
function setCostLimit() {
    const limit = document.getElementById('costLimit').value;
    if (!limit || limit <= 0) {
        alert('Please enter a valid cost limit greater than 0');
        return;
    }

    fetch('/set_cost_limit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `cost_limit=${encodeURIComponent(limit)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Optionally show a success toast or reload
            window.location.reload();
        } else {
            alert(data.message || 'Error setting cost limit');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error setting cost limit');
    });
}

// Function to clear cost limit
function clearCostLimit() {
    if (confirm('Are you sure you want to clear the cost limit?')) {
        fetch('/clear_cost_limit', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Cost limit cleared successfully');
                // Force an immediate dashboard update
                updateDashboard();
            } else {
                alert(data.message || 'Error clearing cost limit');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error clearing cost limit');
        });
    }
}

// Function to clear all readings
function clearAllReadings() {
    if (confirm('Are you sure you want to clear all readings? This will not affect your cost limit.')) {
        fetch('/clear_readings', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('All readings cleared successfully');
                // Force an immediate dashboard update
                updateDashboard();
            } else {
                alert(data.message || 'Error clearing readings');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error clearing readings');
        });
    }
}

// Update dashboard every 30 seconds
updateDashboard();
setInterval(updateDashboard, 30000);

// Apply time range filter
document.getElementById('applyRange').addEventListener('click', function() {
    const timeRange = document.getElementById('timeRange').value;
    // Optionally show a toast or alert for time range update
    // alert(`Time range updated to ${document.getElementById('timeRange').options[document.getElementById('timeRange').selectedIndex].text}`);
    // Here you would typically send this to your backend to filter data
    // For now, we'll just update the dashboard
    updateDashboard();
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

// Logout button functionality
document.addEventListener('DOMContentLoaded', function() {
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to logout?')) {
                window.location.href = '/logout';
            }
        });
    }
});
