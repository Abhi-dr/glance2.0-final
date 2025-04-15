document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts only if their containers exist
    const chartContainers = {
        'line-chart': initializeLineChart,
        'area-chart': initializeAreaChart,
        'bar-chart': initializeBarChart,
        'pie-chart': initializePieChart
    };

    // Initialize each chart if its container exists
    Object.entries(chartContainers).forEach(([containerId, initFunction]) => {
        const container = document.getElementById(containerId);
        if (container) {
            try {
                initFunction(container);
            } catch (error) {
                console.error(`Error initializing ${containerId}:`, error);
            }
        }
    });
});

function initializeLineChart(container) {
    if (!container) return;

    const options = {
        series: [{
            name: "Applications",
            data: [10, 41, 35, 51, 49, 62, 69, 91, 148]
        }],
        chart: {
            height: 350,
            type: 'line',
            zoom: {
                enabled: false
            }
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'straight'
        },
        grid: {
            row: {
                colors: ['#f3f3f3', 'transparent'],
                opacity: 0.5
            },
        },
        xaxis: {
            categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'],
        }
    };

    try {
        const chart = new ApexCharts(container, options);
        chart.render();
    } catch (error) {
        console.error('Error rendering line chart:', error);
    }
}

function initializeAreaChart(container) {
    if (!container) return;

    const options = {
        series: [{
            name: 'Students',
            data: [31, 40, 28, 51, 42, 109, 100]
        }],
        chart: {
            height: 350,
            type: 'area'
        },
        dataLabels: {
            enabled: false
        },
        stroke: {
            curve: 'smooth'
        },
        xaxis: {
            type: 'datetime',
            categories: ["2018-09-19T00:00:00.000Z", "2018-09-19T01:30:00.000Z", "2018-09-19T02:30:00.000Z", "2018-09-19T03:30:00.000Z", "2018-09-19T04:30:00.000Z", "2018-09-19T05:30:00.000Z", "2018-09-19T06:30:00.000Z"]
        },
        tooltip: {
            x: {
                format: 'dd/MM/yy HH:mm'
            },
        },
    };

    try {
        const chart = new ApexCharts(container, options);
        chart.render();
    } catch (error) {
        console.error('Error rendering area chart:', error);
    }
}

function initializeBarChart(container) {
    if (!container) return;

    const options = {
        series: [{
            data: [400, 430, 448, 470, 540, 580, 690, 1100, 1200, 1380]
        }],
        chart: {
            type: 'bar',
            height: 350
        },
        plotOptions: {
            bar: {
                borderRadius: 4,
                horizontal: true,
            }
        },
        dataLabels: {
            enabled: false
        },
        xaxis: {
            categories: ['South Korea', 'Canada', 'United Kingdom', 'Netherlands', 'Italy', 'France', 'Japan',
                'United States', 'China', 'Germany'
            ],
        }
    };

    try {
        const chart = new ApexCharts(container, options);
        chart.render();
    } catch (error) {
        console.error('Error rendering bar chart:', error);
    }
}

function initializePieChart(container) {
    if (!container) return;

    const options = {
        series: [44, 55, 13, 43, 22],
        chart: {
            width: 380,
            type: 'pie',
        },
        labels: ['Team A', 'Team B', 'Team C', 'Team D', 'Team E'],
        responsive: [{
            breakpoint: 480,
            options: {
                chart: {
                    width: 200
                },
                legend: {
                    position: 'bottom'
                }
            }
        }]
    };

    
} 