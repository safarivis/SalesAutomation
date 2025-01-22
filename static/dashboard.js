// Dashboard JavaScript

// API Token - In production, this should be handled more securely
const API_TOKEN = localStorage.getItem('api_token') || 'your-token-here';

// Chart instances
let stageChart;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    refreshData();
    // Refresh every 30 seconds
    setInterval(refreshData, 30000);
});

// Refresh all dashboard data
async function refreshData() {
    try {
        await Promise.all([
            updateMetrics(),
            updateProspects(),
            updateStageChart(),
            updateRecentActivity()
        ]);
        updateLastUpdated();
    } catch (error) {
        console.error('Error refreshing data:', error);
        showError('Failed to refresh dashboard data');
    }
}

// Update metrics
async function updateMetrics() {
    try {
        const response = await fetch('/api/metrics', {
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });
        const metrics = await response.json();
        console.log('Metrics:', metrics);  // Debug log
        
        document.getElementById('totalProspects').textContent = metrics.total_prospects;
        document.getElementById('responseRate').textContent = `${metrics.response_rate}%`;
        document.getElementById('responseRateBar').style.width = `${metrics.response_rate}%`;
        document.getElementById('demoScheduled').textContent = metrics.demo_scheduled;
        document.getElementById('conversionRate').textContent = `${metrics.conversion_rate}%`;
        document.getElementById('conversionRateBar').style.width = `${metrics.conversion_rate}%`;
    } catch (error) {
        console.error('Error updating metrics:', error);
    }
}

// Update prospects table
async function updateProspects() {
    try {
        const response = await fetch('/api/prospects', {
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });
        const prospects = await response.json();
        console.log('Prospects:', prospects);  // Debug log
        
        const tbody = document.getElementById('prospectsTable');
        tbody.innerHTML = '';
        
        prospects.forEach(prospect => {
            const tr = document.createElement('tr');
            tr.className = 'prospect-row';
            tr.innerHTML = `
                <td>${prospect.email}</td>
                <td><span class="badge bg-primary">${prospect.current_stage}</span></td>
                <td>${new Date(prospect.updated_at).toLocaleString()}</td>
                <td>
                    <span class="status-indicator status-${prospect.current_stage}"></span>
                    ${prospect.current_stage}
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary" onclick="viewProspect('${prospect.email}')">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="updateStage('${prospect.email}')">
                            <i class="bi bi-arrow-right"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Error updating prospects:', error);
    }
}

// Update stage distribution chart
async function updateStageChart() {
    try {
        const response = await fetch('/api/metrics', {
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });
        const metrics = await response.json();
        console.log('Stage Distribution:', metrics.stage_distribution);  // Debug log
        
        const stages = metrics.stage_distribution;
        const labels = stages.map(s => s.current_stage);
        const data = stages.map(s => s.count);
        
        const ctx = document.getElementById('stageChart');
        if (!ctx) {
            console.error('Stage chart canvas not found');
            return;
        }

        if (!window.stageChart) {
            window.stageChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#0d6efd',
                            '#198754',
                            '#ffc107',
                            '#dc3545'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        } else {
            window.stageChart.data.labels = labels;
            window.stageChart.data.datasets[0].data = data;
            window.stageChart.update();
        }
    } catch (error) {
        console.error('Error updating stage chart:', error);
    }
}

// Update recent activity
async function updateRecentActivity() {
    try {
        const response = await fetch('/api/metrics', {
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });
        const metrics = await response.json();
        console.log('Recent Activity:', metrics.recent_activity);  // Debug log
        
        const activityDiv = document.getElementById('recentActivity');
        activityDiv.innerHTML = '';
        
        metrics.recent_activity.forEach(activity => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            
            if (activity.type === 'email') {
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="bi bi-envelope me-2"></i>
                            <strong>${activity.from_email}</strong> ${activity.action} to <strong>${activity.to_email}</strong>
                            <br>
                            <small class="text-muted">${activity.subject}</small>
                        </div>
                        <small>${new Date(activity.timestamp).toLocaleString()}</small>
                    </div>
                `;
            } else {
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="bi bi-arrow-right-circle me-2"></i>
                            <strong>${activity.email}</strong> ${activity.action}
                        </div>
                        <small>${new Date(activity.timestamp).toLocaleString()}</small>
                    </div>
                `;
            }
            
            activityDiv.appendChild(item);
        });
    } catch (error) {
        console.error('Error updating recent activity:', error);
    }
}

// View prospect details
async function viewProspect(email) {
    try {
        const response = await fetch(`/api/prospects?q=${email}`, {
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });
        const prospects = await response.json();
        const prospect = prospects[0];
        
        if (prospect) {
            const modal = new bootstrap.Modal(document.getElementById('prospectModal'));
            document.getElementById('prospectDetails').innerHTML = `
                <dl class="row">
                    <dt class="col-sm-3">Email</dt>
                    <dd class="col-sm-9">${prospect.email}</dd>
                    
                    <dt class="col-sm-3">Current Stage</dt>
                    <dd class="col-sm-9"><span class="badge bg-primary">${prospect.current_stage}</span></dd>
                    
                    <dt class="col-sm-3">Response Rate</dt>
                    <dd class="col-sm-9">${prospect.response_rate}%</dd>
                    
                    <dt class="col-sm-3">Last Updated</dt>
                    <dd class="col-sm-9">${new Date(prospect.updated_at).toLocaleString()}</dd>
                    
                    <dt class="col-sm-3">Created At</dt>
                    <dd class="col-sm-9">${new Date(prospect.created_at).toLocaleString()}</dd>
                </dl>
            `;
            modal.show();
        }
    } catch (error) {
        console.error('Error viewing prospect:', error);
    }
}

// Update prospect stage
async function updateStage(email) {
    const stages = ['initial_contact', 'interested', 'demo_scheduled', 'proposal_sent', 'converted'];
    const currentStage = document.querySelector(`tr[data-email="${email}"] .stage-badge`).textContent;
    const currentIndex = stages.indexOf(currentStage);
    const nextStage = stages[(currentIndex + 1) % stages.length];
    
    try {
        const response = await fetch(`/api/stage/${email}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ stage: nextStage })
        });
        
        if (response.ok) {
            refreshData();
        }
    } catch (error) {
        console.error('Error updating stage:', error);
    }
}

// Search prospects
function searchProspects() {
    const query = document.getElementById('searchInput').value;
    window.location.href = `/search?q=${encodeURIComponent(query)}`;
}

// Update last updated time
function updateLastUpdated() {
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleString();
}

// Show error message
function showError(message) {
    console.error(message);
    alert(message);  // Simple error display
}
