/* ============================================================
   CHARTS CONFIGURATION - Chart.js
   ============================================================ */

// Chart.js global defaults
Chart.defaults.color = 'rgba(255, 255, 255, 0.7)';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.font.family = "'Inter', sans-serif";

// Category Distribution - Doughnut Chart
const categoryCtx = document.getElementById('categoryChart');
if (categoryCtx && chartData.categories.length > 0) {
    new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
            labels: chartData.categories,
            datasets: [{
                data: chartData.category_counts,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(240, 147, 251, 0.8)',
                    'rgba(79, 172, 254, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(139, 92, 246, 0.8)',
                    'rgba(236, 72, 153, 0.8)'
                ],
                borderWidth: 2,
                borderColor: 'rgba(15, 12, 41, 0.5)',
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 15,
                        font: { size: 12, weight: '500' },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 12, 41, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(102, 126, 234, 0.5)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8
                }
            },
            cutout: '65%'
        }
    });
}

// Stock Levels - Bar Chart
const stockCtx = document.getElementById('stockChart');
if (stockCtx && chartData.product_names.length > 0) {
    const gradient = stockCtx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(102, 126, 234, 0.9)');
    gradient.addColorStop(1, 'rgba(118, 75, 162, 0.6)');
    
    new Chart(stockCtx, {
        type: 'bar',
        data: {
            labels: chartData.product_names,
            datasets: [{
                label: 'Stock Quantity',
                data: chartData.stock_levels,
                backgroundColor: gradient,
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 12, 41, 0.95)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(102, 126, 234, 0.5)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: 'rgba(255, 255, 255, 0.6)' }
                },
                x: {
                    grid: { display: false },
                    ticks: { 
                        color: 'rgba(255, 255, 255, 0.6)',
                        maxRotation: 45,
                        minRotation: 45,
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}