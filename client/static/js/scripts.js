document.addEventListener('DOMContentLoaded', function() {
    let cpuUsageGauge, ramUsageGauge, cpuUsageHistogram, ramUsageHistogram;
    let weatherDataCache = JSON.parse(document.getElementById('weatherData').textContent);
    let deviceMetricsCache = JSON.parse(document.getElementById('deviceMetrics').textContent);
    let map;
    let markers = [];
    const lastUpdatedTime = "{{ last_updated_time }}";

    document.getElementById('lastUpdatedTime').innerText = lastUpdatedTime;

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
        markers.forEach(marker => marker.remove());
        markers = [];
    }

    function updateGauges(metricType) {
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

    // Hide loading screen and show content
    document.getElementById('loading-screen').style.display = 'none';
    document.querySelector('.container').style.display = 'block';

    // Set default tab
    document.getElementsByClassName("tablink")[0].click();
});