document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed.");
    let cpuUsageGauge, ramUsageGauge, cpuUsageHistogram, ramUsageHistogram;
    let map;
    let markers = [];
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

        // Update map with the selected weather data
        if (tabName in weatherDataCache) {
            updateMap(tabName);
        } else if (tabName === 'CPUUsage' || tabName === 'RAMUsage') {
            updateGauges(tabName);
        }
    }

    function updateMap(metricType) {
        console.log(`Updating map for metric type: ${metricType}`);
        if (!map) {
            map = new maplibregl.Map({
                container: 'map',
                style: 'https://demotiles.maplibre.org/style.json',
                center: [-8.24389, 53.41291], // Center on Ireland
                zoom: 6
            });
        }

        const metrics = weatherDataCache[metricType] || [];

        // Clear existing markers
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

    function updateGauges(metricType) {
        console.log(`Updating gauges for metric type: ${metricType}`);
        const cpuUsageData = deviceMetricsCache.filter(metric => metric.metric_id === 'a96727f1-e90a-4965-831b-af1fd162cfca');
        const ramUsageData = deviceMetricsCache.filter(metric => metric.metric_id === '2c368bee-acbc-45b3-91f8-02fa27b22434');

        if (cpuUsageGauge) cpuUsageGauge.destroy();
        if (ramUsageGauge) ramUsageGauge.destroy();

        const gaugeData = metricType === 'CPUUsage' ? cpuUsageData : ramUsageData;
        const gaugeLabel = metricType === 'CPUUsage' ? 'CPU Usage' : 'RAM Usage';

        const gauge = new Chart(document.getElementById('usageGauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [gaugeData.length ? gaugeData[gaugeData.length - 1].value : 0, 100 - (gaugeData.length ? gaugeData[gaugeData.length - 1].value : 0)],
                    backgroundColor: ['#4CAF50', '#ddd']
                }],
                labels: [gaugeLabel, '']
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

        if (metricType === 'CPUUsage') {
            cpuUsageGauge = gauge;
        } else {
            ramUsageGauge = gauge;
        }
    }

    function fetchMetrics(page, limit) {
        fetch(`/api/device_metrics?page=${page}&limit=${limit}`)
            .then(response => response.json())
            .then(data => {
                updateDeviceMetricsTable(data.device_metrics);
                document.getElementById('currentPage').innerText = page;
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    function updateDeviceMetricsTable(metrics) {
        const deviceMetricsTable = document.getElementById("deviceMetricsTable").getElementsByTagName('tbody')[0];
        deviceMetricsTable.innerHTML = ''; // Clear existing rows
        metrics.forEach(metric => {
            const row = deviceMetricsTable.insertRow();
            row.insertCell(0).innerText = metric.device_id;
            row.insertCell(1).innerText = metric.metric_id;
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

        updateMap(data.weather_data);  // Function to update your map with new data
    });

    // Initial fetch
    fetchMetrics(currentPage, limit);

    // Hide loading screen and show content
    console.log("Hiding loading screen and showing content.");
    document.getElementById('loading-screen').style.display = 'none';
    document.querySelector('.container').style.display = 'block';

    // Set default tab
    document.getElementsByClassName("tablink")[0].click();
});