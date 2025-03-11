document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed.");
    let cpuUsageGauge, ramUsageGauge, cpuUsageHistogram, ramUsageHistogram;
    let map;
    let markers = [];
    let weatherDataCache = {};
    const lastUpdatedTime = "{{ last_updated_time }}";
    let currentPage = 1;
    const limit = 5;

    document.getElementById('lastUpdatedTime').innerText = lastUpdatedTime;

    window.openTab = function(evt, tabName) {
        console.log(`Opening tab: ${tabName}`);
        var i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }
        tablinks = document.getElementsByClassName("tablink");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        var tab = document.getElementById(tabName);
        if (tab) {
            tab.style.display = "block";
            evt.currentTarget.className += " active";
        }

        if (tabName in weatherDataCache) {
            updateMap(tabName);
        } else if (tabName === 'CPUUsage' || tabName === 'RAMUsage') {
            updateGaugesAndHistograms();
        }
    }

    function updateMap(metricType) {
        console.log(`Updating map for metric type: ${metricType}`);
        if (!map) {
            map = new maplibregl.Map({
                container: 'map',
                style: 'https://demotiles.maplibre.org/style.json',
                center: [-8.24389, 53.41291],
                zoom: 6
            });
        }

        const metrics = weatherDataCache[metricType] || [];

        clearMarkers();

        metrics.forEach(metric => {
            const marker = new maplibregl.Marker()
                .setLngLat([metric.longitude, metric.latitude])
                .setPopup(new maplibregl.Popup().setHTML(`<h3>${metric.name}</h3><p>${metric.value}</p>`))
                .addTo(map);
            markers.push(marker);
        });
    }

    function clearMarkers() {
        console.log("Clearing markers.");
        markers.forEach(marker => marker.remove());
        markers = [];
    }

    function updateGaugesAndHistograms(metrics) {
        console.log(`Updating gauges and histograms.`);
        const cpuUsageData = metrics.filter(metric => metric.metric_name === 'CPU Usage');
        const ramUsageData = metrics.filter(metric => metric.metric_name === 'RAM Usage');

        if (cpuUsageGauge) cpuUsageGauge.destroy();
        if (ramUsageGauge) ramUsageGauge.destroy();
        if (cpuUsageHistogram) cpuUsageHistogram.destroy();
        if (ramUsageHistogram) ramUsageHistogram.destroy();

        const gaugeData = cpuUsageData.length ? cpuUsageData[cpuUsageData.length - 1].value : 0;
        const ramData = ramUsageData.length ? ramUsageData[ramUsageData.length - 1].value : 0;

        cpuUsageGauge = new Chart(document.getElementById('cpuUsageGauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [gaugeData, 100 - gaugeData],
                    backgroundColor: ['#4CAF50', '#ddd']
                }],
                labels: ['CPU Usage', '']
            },
            options: {
                circumference: Math.PI,
                rotation: Math.PI,
                cutout: '50%',
                plugins: {
                    tooltip: { enabled: false },
                    hover: { mode: null },
                    datalabels: {
                        display: true,
                        formatter: (value, context) => {
                            return context.chart.data.labels[context.dataIndex] + ': ' + value + '%';
                        },
                        color: '#000',
                        font: {
                            weight: 'bold',
                            size: 16
                        }
                    }
                }
            }
        });

        ramUsageGauge = new Chart(document.getElementById('ramUsageGauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [ramData, 100 - ramData],
                    backgroundColor: ['#4CAF50', '#ddd']
                }],
                labels: ['RAM Usage', '']
            },
            options: {
                circumference: Math.PI,
                rotation: Math.PI,
                cutout: '50%',
                plugins: {
                    tooltip: { enabled: false },
                    hover: { mode: null },
                    datalabels: {
                        display: true,
                        formatter: (value, context) => {
                            return context.chart.data.labels[context.dataIndex] + ': ' + value + '%';
                        },
                        color: '#000',
                        font: {
                            weight: 'bold',
                            size: 16
                        }
                    }
                }
            }
        });

        cpuUsageHistogram = new Chart(document.getElementById('cpuUsageHistogram'), {
            type: 'bar',
            data: {
                labels: cpuUsageData.map(metric => metric.timestamp),
                datasets: [{
                    label: 'CPU Usage',
                    data: cpuUsageData.map(metric => metric.value),
                    backgroundColor: '#4CAF50'
                }]
            },
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });

        ramUsageHistogram = new Chart(document.getElementById('ramUsageHistogram'), {
            type: 'bar',
            data: {
                labels: ramUsageData.map(metric => metric.timestamp),
                datasets: [{
                    label: 'RAM Usage',
                    data: ramUsageData.map(metric => metric.value),
                    backgroundColor: '#4CAF50'
                }]
            },
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    function fetchMetrics(page, limit) {
        fetch(`/api/device_metrics?page=${page}&limit=${limit}`)
            .then(response => response.json())
            .then(data => {
                updateDeviceMetricsTable(data.device_metrics);
                updateGaugesAndHistograms(data.device_metrics);
                document.getElementById('currentPage').innerText = page;
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    function updateDeviceMetricsTable(metrics) {
        const deviceMetricsTable = document.getElementById("deviceMetricsTable").getElementsByTagName('tbody')[0];
        deviceMetricsTable.innerHTML = '';
        metrics.forEach(metric => {
            const row = deviceMetricsTable.insertRow();
            row.insertCell(0).innerText = metric.device_name;
            row.insertCell(1).innerText = metric.metric_name;
            row.insertCell(2).innerText = metric.value;
            row.insertCell(3).innerText = metric.timestamp;
        });
    }

    window.changePage = function(direction) {
        currentPage += direction;
        if (currentPage < 1) currentPage = 1;
        fetchMetrics(currentPage, limit);
    };

    document.getElementById('weatherTypeDropdown').addEventListener('change', async function (event) {
        const weatherType = event.target.value;
        const response = await fetch(`/api/weather_data?type=${weatherType}`);
        const data = await response.json();

        weatherDataCache[weatherType] = data.weather_data;
        updateMap(weatherType);
    });

    fetchMetrics(currentPage, limit);

    console.log("Hiding loading screen and showing content.");
    document.getElementById('loading-screen').style.display = 'none';
    document.querySelector('.container').style.display = 'block';

    document.getElementsByClassName("tablink")[0].click();
});