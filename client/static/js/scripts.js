document.addEventListener('DOMContentLoaded', function() {
    let cpuUsageGauge, ramUsageGauge, cpuUsageHistogram, ramUsageHistogram;
    let weatherDataCache = {};

    window.openTab = function(evt, tabName) {
        var i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }
        tablinks = document.getElementsByClassName("tablink");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.className += " active";

        // Update map with the selected weather data
        window.updateMap(tabName);
    }

    window.updateMap = function(metricType) {
        const map = new maplibregl.Map({
            container: 'map',
            style: 'https://demotiles.maplibre.org/style.json',
            center: [-8.24389, 53.41291], // Center on Ireland
            zoom: 6
        });

        const metrics = weatherDataCache[metricType] || [];

        metrics.forEach(metric => {
            new maplibregl.Marker()
                .setLngLat([metric.longitude, metric.latitude])
                .setPopup(new maplibregl.Popup().setHTML(`<h3>${metric.name}</h3><p>${metric.value}</p>`))
                .addTo(map);
        });
    }

    function fetchMetrics() {
        fetch('/api/metrics')
            .then(response => response.json())
            .then(data => {
                const deviceMetricsTable = document.getElementById("deviceMetricsTable").getElementsByTagName('tbody')[0];
                deviceMetricsTable.innerHTML = '';
                if (data.device_metrics) {
                    data.device_metrics.forEach(metric => {
                        const row = deviceMetricsTable.insertRow();
                        row.insertCell(0).innerText = metric.device_id;
                        row.insertCell(1).innerText = metric.metric_id;
                        row.insertCell(2).innerText = metric.value;
                        row.insertCell(3).innerText = metric.timestamp;
                    });
                } else {
                    console.error('No device metrics found in the response.');
                }

                updateGauges(data.device_metrics);
                updateHistograms(data.device_metrics);
                cacheWeatherData(data.third_party_metrics);
                window.updateMap('AirQuality');
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    function updateGauges(deviceMetrics) {
        const cpuUsageData = deviceMetrics.filter(metric => metric.metric_id === 'cpu_usage');
        const ramUsageData = deviceMetrics.filter(metric => metric.metric_id === 'ram_usage');

        if (cpuUsageGauge) cpuUsageGauge.destroy();
        if (ramUsageGauge) ramUsageGauge.destroy();

        cpuUsageGauge = new Chart(document.getElementById('cpuUsageGauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [cpuUsageData.length ? cpuUsageData[cpuUsageData.length - 1].value : 0, 100 - (cpuUsageData.length ? cpuUsageData[cpuUsageData.length - 1].value : 0)],
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
                    hover: { mode: null }
                }
            }
        });

        ramUsageGauge = new Chart(document.getElementById('ramUsageGauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [ramUsageData.length ? ramUsageData[ramUsageData.length - 1].value : 0, 100 - (ramUsageData.length ? ramUsageData[ramUsageData.length - 1].value : 0)],
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
                    hover: { mode: null }
                }
            }
        });
    }

    function updateHistograms(deviceMetrics) {
        const cpuUsageData = deviceMetrics.filter(metric => metric.metric_id === 'cpu_usage').map(metric => metric.value);
        const ramUsageData = deviceMetrics.filter(metric => metric.metric_id === 'ram_usage').map(metric => metric.value);

        if (cpuUsageHistogram) cpuUsageHistogram.destroy();
        if (ramUsageHistogram) ramUsageHistogram.destroy();

        cpuUsageHistogram = new Chart(document.getElementById('cpuUsageHistogram'), {
            type: 'bar',
            data: {
                labels: cpuUsageData,
                datasets: [{
                    label: 'CPU Usage',
                    data: cpuUsageData,
                    backgroundColor: '#4CAF50'
                }]
            },
            options: {
                scales: {
                    x: { display: false },
                    y: { beginAtZero: true, max: 100 }
                }
            }
        });

        ramUsageHistogram = new Chart(document.getElementById('ramUsageHistogram'), {
            type: 'bar',
            data: {
                labels: ramUsageData,
                datasets: [{
                    label: 'RAM Usage',
                    data: ramUsageData,
                    backgroundColor: '#4CAF50'
                }]
            },
            options: {
                scales: {
                    x: { display: false },
                    y: { beginAtZero: true, max: 100 }
                }
            }
        });
    }

    function cacheWeatherData(thirdPartyMetrics) {
        weatherDataCache = {
            AirQuality: thirdPartyMetrics.filter(metric => metric.name.includes('Air Quality Index')),
            Humidity: thirdPartyMetrics.filter(metric => metric.name.includes('Humidity')),
            Precipitation: thirdPartyMetrics.filter(metric => metric.name.includes('Precipitation')),
            Pressure: thirdPartyMetrics.filter(metric => metric.name.includes('Pressure')),
            Temperature: thirdPartyMetrics.filter(metric => metric.name.includes('Temperature')),
            UVIndex: thirdPartyMetrics.filter(metric => metric.name.includes('UV Index')),
            WindSpeed: thirdPartyMetrics.filter(metric => metric.name.includes('Wind Speed'))
        };
    }

    setInterval(fetchMetrics, 60000);  // Update interval to 60000 milliseconds (60 seconds)
    fetchMetrics();

    // Set default tab
    document.getElementsByClassName("tablink")[0].click();
});