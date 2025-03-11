document.addEventListener('DOMContentLoaded', function() {
    let cpuUsageGauge, ramUsageGauge, cpuUsageHistogram, ramUsageHistogram;
    let weatherDataCache = {};
    let map;

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
        if (tabName in weatherDataCache) {
            window.updateMap(tabName);
        } else if (tabName === 'CPUUsage' || tabName === 'RAMUsage') {
            updateGauges(tabName);
        }
    }

    window.updateMap = function(metricType) {
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
        map.eachLayer(function(layer) {
            if (layer.type === 'symbol') {
                map.removeLayer(layer.id);
                map.removeSource(layer.id);
            }
        });

        metrics.forEach(metric => {
            new maplibregl.Marker()
                .setLngLat([metric.longitude, metric.latitude])
                .setPopup(new maplibregl.Popup().setHTML(`<h3>${metric.name}</h3><p>${metric.value}</p>`))
                .addTo(map);
        });
    }

    function fetchMetrics() {
        fetch('https://michellevaz.pythonanywhere.com/api/metrics')
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

                updateHistograms(data.device_metrics);
                cacheWeatherData(data.third_party_metrics);
                window.updateMap('AirQuality');
            })
            .catch(error => console.error('Error fetching data:', error));
    }

    function updateGauges(metricType) {
        const cpuUsageData = deviceMetrics.filter(metric => metric.metric_id === 'a96727f1-e90a-4965-831b-af1fd162cfca');
        const ramUsageData = deviceMetrics.filter(metric => metric.metric_id === '2c368bee-acbc-45b3-91f8-02fa27b22434');

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

    function updateHistograms(deviceMetrics) {
        const cpuUsageData = deviceMetrics.filter(metric => metric.metric_id === 'a96727f1-e90a-4965-831b-af1fd162cfca').map(metric => metric.value);
        const ramUsageData = deviceMetrics.filter(metric => metric.metric_id === '2c368bee-acbc-45b3-91f8-02fa27b22434').map(metric => metric.value);

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