// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const apiStatus = document.getElementById('apiStatus');
const generateBtn = document.getElementById('generateBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingSpinner = document.getElementById('loadingSpinner');
const recommendationText = document.getElementById('recommendationText');

// KPI Elements
const avgDailyDemandEl = document.getElementById('avgDailyDemand');
const totalForecastEl = document.getElementById('totalForecast');
const safetyStockEl = document.getElementById('safetyStock');
const reorderPointEl = document.getElementById('reorderPoint');

// Chart instance
let forecastChart = null;

// Check API Health on Load
document.addEventListener('DOMContentLoaded', checkAPIHealth);

// Event Listeners
generateBtn.addEventListener('click', generateForecast);

// Check API Health
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        const data = await response.json();
        
        if (response.ok) {
            apiStatus.className = 'status connected';
            apiStatus.innerHTML = '<i class="fas fa-circle"></i><span>API Connected</span>';
            
            // Check if model is loaded
            if (!data.model_loaded) {
                showNotification('Model not loaded. Please train the model first.', 'warning');
            }
        } else {
            throw new Error('API not responding');
        }
    } catch (error) {
        apiStatus.className = 'status disconnected';
        apiStatus.innerHTML = '<i class="fas fa-circle"></i><span>API Disconnected</span>';
        showNotification('Cannot connect to backend. Make sure the API is running.', 'error');
    }
}

// Generate Forecast
async function generateForecast() {
    // Get form values
    const skuId = parseInt(document.getElementById('skuId').value);
    const locationId = parseInt(document.getElementById('locationId').value);
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const leadTime = parseInt(document.getElementById('leadTime').value);
    const serviceLevel = parseFloat(document.getElementById('serviceLevel').value);

    // Validate dates
    if (new Date(startDate) > new Date(endDate)) {
        showNotification('Start date must be before end date', 'error');
        return;
    }

    // Show loading
    loadingSpinner.style.display = 'flex';
    generateBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/forecast`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sku_id: skuId,
                location_id: locationId,
                start_date: startDate,
                end_date: endDate,
                lead_time_days: leadTime,
                service_level: serviceLevel
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Update UI with results
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Failed to generate forecast. Check console for details.', 'error');
    } finally {
        // Hide loading
        loadingSpinner.style.display = 'none';
        generateBtn.disabled = false;
    }
}

// Display Results
function displayResults(data) {
    // Update KPIs
    avgDailyDemandEl.textContent = data.average_daily_demand;
    totalForecastEl.textContent = data.total_forecast_demand;
    safetyStockEl.textContent = data.safety_stock;
    reorderPointEl.textContent = data.reorder_point;

    // Create/Update Chart
    createChart(data.forecast_dates, data.predicted_demand);
    
    // Generate Recommendation
    generateRecommendation(data);
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Create Chart
function createChart(labels, data) {
    const ctx = document.getElementById('forecastChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (forecastChart) {
        forecastChart.destroy();
    }
    
    // Create new chart
    forecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Predicted Demand',
                data: data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                pointRadius: 3,
                pointBackgroundColor: '#667eea',
                pointBorderColor: 'white',
                pointBorderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            family: 'Inter',
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `Demand: ${context.raw} units`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        font: {
                            family: 'Inter',
                            size: 10
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.05)'
                    },
                    ticks: {
                        font: {
                            family: 'Inter',
                            size: 11
                        }
                    },
                    title: {
                        display: true,
                        text: 'Demand (units)',
                        font: {
                            family: 'Inter',
                            size: 12,
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    });
}

// Generate Recommendation
function generateRecommendation(data) {
    const avgDemand = data.average_daily_demand;
    const reorderPoint = data.reorder_point;
    const safetyStock = data.safety_stock;
    
    let recommendation = '';
    
    if (avgDemand > 150) {
        recommendation = '⚠️ High demand detected. Consider increasing safety stock and reviewing supplier contracts.';
    } else if (avgDemand > 100) {
        recommendation = '📈 Moderate demand. Current inventory levels are adequate but monitor weekly.';
    } else {
        recommendation = '✅ Low demand. You can optimize by reducing safety stock to free up capital.';
    }
    
    recommendation += ` Reorder when inventory reaches ${reorderPoint} units (includes ${safetyStock} units safety stock).`;
    
    recommendationText.textContent = recommendation;
}

// Show Notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add styles for notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#f44336' : type === 'warning' ? '#ff9800' : '#2196f3'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 1001;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);