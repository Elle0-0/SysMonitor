document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed.");
    let cpuUsageGauge, ramUsageGauge, cpuUsageHistogram, ramUsageHistogram;
    let map;
    let markers = [];
    let weatherDataCache = {};
    const lastUpdatedTime = "{{ last_updated_time }}";
    let currentPage = 1;
    const limit = 5;

    updateLastUpdatedTime(lastUpdatedTime);

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

    function updateLastUpdatedTime(rawTimestamp) {
        if (!rawTimestamp || rawTimestamp === "N/A") {
            document.getElementById('lastUpdatedTime').innerText = "Last Updated: N/A";
            return;
        }
        // Parse the raw timestamp into a JavaScript Date object
        const dateObj = new Date(rawTimestamp);
    
        // Format the date and time into a user-friendly string
        const formattedTime = dateObj.toLocaleString('en-US', {
            weekday: 'short', // e.g., "Tue"
            year: 'numeric',  // e.g., "2025"
            month: 'short',   // e.g., "Mar"
            day: 'numeric',   // e.g., "11"
            hour: '2-digit',  // e.g., "06"
            minute: '2-digit',
            second: '2-digit',
            hour12: true      // Display time in 12-hour format with AM/PM
        });
    
        // Update the DOM with the formatted timestamp
        document.getElementById('lastUpdatedTime').innerText = `Last Updated: ${formattedTime}`;
    }

    function startDataCollection() {
        fetch('https://3916-193-1-98-140.ngrok-free.app/start_data_collection', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log(data.message);
            alert(data.message);
        })
        .catch(error => {
            console.error('Error starting data collection:', error);
            alert('Error starting data collection. Please check the console for more details.');
        });
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
        if (markers.length === 0) return; 
        console.log("Clearing markers.");
        markers.forEach(marker => marker.remove());
        markers = [];
    }

    function updateGaugesAndHistograms(metrics) {
        console.log(`Updating gauges and histograms.`);
    
        // Filter and validate data
        const cpuUsageData = metrics.filter(metric => metric.metric_name === 'CPU Usage' && metric.value !== null);
        const ramUsageData = metrics.filter(metric => metric.metric_name === 'RAM Usage' && metric.value !== null);
    
        // Safely get the latest values
        const latestCpuValue = cpuUsageData.length ? cpuUsageData[cpuUsageData.length - 1].value : 0;
        const latestRamValue = ramUsageData.length ? ramUsageData[ramUsageData.length - 1].value : 0;
    
        // Destroy previous charts if they exist
        if (cpuUsageGauge) cpuUsageGauge.destroy();
        if (ramUsageGauge) ramUsageGauge.destroy();
        if (cpuUsageHistogram) cpuUsageHistogram.destroy();
        if (ramUsageHistogram) ramUsageHistogram.destroy();
    
        // Create CPU Usage Gauge
        cpuUsageGauge = new Chart(document.getElementById('cpuUsageGauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [latestCpuValue, 100 - latestCpuValue],
                    backgroundColor: ['#4CAF50', '#ddd']
                }],
                labels: ['CPU Usage', '']
            },
            options: {
                circumference: 180,  // Use degrees instead of Math.PI
                rotation: 270,       // Start from the top instead of a slanted position
                cutout: '50%',       // Ensures the hollow effect (v3+)
                plugins: {
                    tooltip: { enabled: true },
                    datalabels: {
                        display: true,
                        formatter: (value, context) => {
                            return context.dataIndex === 0 ? `${value}%` : ''; // Display value for 'CPU Usage'
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
        
    
        // Create RAM Usage Gauge
        ramUsageGauge = new Chart(document.getElementById('ramUsageGauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [latestRamValue, 100 - latestRamValue],
                    backgroundColor: ['#4CAF50', '#ddd']
                }],
                labels: ['RAM Usage', '']
            },
            options: {
                circumference: 180,  // Use degrees instead of Math.PI
                rotation: 270,       // Start from the top instead of a slanted position
                cutout: '50%',
                plugins: {
                    tooltip: { enabled: true },
                    datalabels: {
                        display: true,
                        formatter: (value, context) => {
                            return context.dataIndex === 0 ? `${value}%` : ''; // Display value for 'RAM Usage'
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
    
        // Create CPU Usage Histogram
        cpuUsageHistogram = new Chart(document.getElementById('cpuUsageHistogram'), {
            type: 'bar',
            data: {
                labels: cpuUsageData.map(metric => {
                    const date = new Date(metric.timestamp);
                    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                }),
                datasets: [{
                    label: 'CPU Usage',
                    data: cpuUsageData.map(metric => metric.value),
                    backgroundColor: '#4CAF50'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'CPU Usage (%)'
                        }
                    }
                }
            }
        });
        
        // Create RAM Usage Histogram
        ramUsageHistogram = new Chart(document.getElementById('ramUsageHistogram'), {
            type: 'bar',
            data: {
                labels: ramUsageData.map(metric => {
                    const date = new Date(metric.timestamp);
                    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                }),
                datasets: [{
                    label: 'RAM Usage',
                    data: ramUsageData.map(metric => metric.value),
                    backgroundColor: '#4CAF50'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        type: 'category',
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'RAM Usage (%)'
                        }
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