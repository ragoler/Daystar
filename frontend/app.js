const STEPS = [
    'create_cluster',
    'verify_cluster',
    'create_nodepool',
    'deploy_app',
    'ping_app',
    'delete_cluster'
];

const gridContainer = document.getElementById('status-grid');
const popover = document.getElementById('popover');
const popoverTitle = document.getElementById('popover-title');
const popoverBody = document.getElementById('popover-body');
const closeBtn = document.querySelector('.close-btn');
const connectionStatus = document.getElementById('connection-status');

let currentData = [];
let scheduleData = [];

async function fetchSchedule() {
    try {
        const response = await fetch('http://localhost:8000/schedule');
        if (response.ok) {
            scheduleData = await response.json();
        }
    } catch (error) {
        console.error('Fetch schedule error:', error);
    }
}

async function fetchConfig() {
    try {
        const response = await fetch('http://localhost:8000/config');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('region-display').textContent = `Region: ${data.region}`;
        }
    } catch (error) {
        console.error('Fetch config error:', error);
    }
}

async function fetchData() {
    try {
        const response = await fetch('http://localhost:8000/status');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        currentData = data;
        connectionStatus.textContent = 'Connected';
        connectionStatus.className = 'status-indicator connected';
        renderGrid(data);
    } catch (error) {
        console.error('Fetch error:', error);
        connectionStatus.textContent = 'Disconnected';
        connectionStatus.className = 'status-indicator disconnected';
        gridContainer.innerHTML = '<div class="loading">Failed to load data. Retrying...</div>';
    }
}

function renderGrid(clusters) {
    if (!clusters || clusters.length === 0) {
        gridContainer.innerHTML = '<div class="loading">No active clusters found.</div>';
        return;
    }

    // Process data to group by time tick (minute)
    // We want to create a map: time_tick -> step_name -> status/logs
    const gridData = {};

    clusters.forEach(cluster => {
        cluster.step_logs.forEach(log => {
            const date = new Date(log.timestamp);
            const timeTick = formatTime(date); // hh:mm

            if (!gridData[timeTick]) {
                gridData[timeTick] = {};
            }

            gridData[timeTick][log.step_name] = {
                status: log.status,
                message: log.message,
                clusterName: cluster.name,
                fullTimestamp: log.timestamp
            };
        });
    });

    // Sort time ticks in reverse chronological order
    const sortedTicks = Object.keys(gridData).sort().reverse();

    // Set up dynamic grid template
    // Total columns = 1 (for time) + number of steps
    gridContainer.style.gridTemplateColumns = `100px repeat(${STEPS.length}, 1fr)`;
    gridContainer.innerHTML = '';

    // Render Headers
    const timeHeader = document.createElement('div');
    timeHeader.className = 'grid-header';
    timeHeader.textContent = 'Time';
    gridContainer.appendChild(timeHeader);

    STEPS.forEach(step => {
        const header = document.createElement('div');
        header.className = 'grid-header';
        
        const scheduleItem = scheduleData.find(item => item.step === step);
        const minuteSuffix = scheduleItem ? ` (${scheduleItem.minute})` : '';
        
        header.textContent = `${formatStepName(step)}${minuteSuffix}`;
        gridContainer.appendChild(header);
    });

    // Render Rows
    sortedTicks.forEach(tick => {
        // Time cell
        const timeCell = document.createElement('div');
        timeCell.className = 'grid-time';
        timeCell.textContent = tick;
        gridContainer.appendChild(timeCell);

        // Step cells
        STEPS.forEach(step => {
            const cell = document.createElement('div');
            cell.className = 'cell';

            const stepData = gridData[tick][step];
            if (stepData) {
                cell.innerHTML = getStatusIcon(stepData.status);
                cell.title = `${stepData.clusterName}: ${stepData.message}`;
                
                // Add click event for popover
                cell.addEventListener('click', () => {
                    showPopover(stepData.clusterName, step, stepData);
                });
            } else {
                cell.innerHTML = '<span class="status-icon status-pending">-</span>';
            }

            gridContainer.appendChild(cell);
        });
    });
}

function formatTime(date) {
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

function formatStepName(step) {
    return step.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function getStatusIcon(status) {
    if (status === 'success') {
        return '<span class="status-icon status-success">✓</span>';
    } else if (status === 'failure') {
        return '<span class="status-icon status-failure">✗</span>';
    } else {
        return '<span class="status-icon status-pending">⋮</span>';
    }
}

function showPopover(clusterName, step, data) {
    popoverTitle.textContent = `${clusterName} - ${formatStepName(step)}`;
    
    // Find API logs for this cluster and endpoint if possible
    // For now, just show the step log message
    let bodyHtml = `<p><strong>Time:</strong> ${data.fullTimestamp}</p>`;
    bodyHtml += `<p><strong>Status:</strong> ${data.status}</p>`;
    bodyHtml += `<p><strong>Message:</strong></p><pre>${data.message}</pre>`;

    // Try to find matching API logs
    const cluster = currentData.find(c => c.name === clusterName);
    if (cluster && cluster.api_logs) {
        const matchingApiLogs = cluster.api_logs.filter(apiLog => {
             // Heuristic: check if timestamp is close or if content matches
             // For now just show all API logs related to this cluster in the popover if it's the right step
             return true; // Simplify for now
        });

        if (matchingApiLogs.length > 0) {
            bodyHtml += `<h4>API Logs</h4>`;
            matchingApiLogs.forEach(apiLog => {
                bodyHtml += `<details>`;
                bodyHtml += `<summary>${apiLog.endpoint} at ${formatTime(new Date(apiLog.timestamp))}</summary>`;
                bodyHtml += `<pre>Request:\n${JSON.stringify(apiLog.request_data, null, 2)}</pre>`;
                bodyHtml += `<pre>Response:\n${JSON.stringify(apiLog.response_data, null, 2)}</pre>`;
                bodyHtml += `</details>`;
            });
        }
    }

    popoverBody.innerHTML = bodyHtml;
    popover.classList.remove('hidden');
}

closeBtn.addEventListener('click', () => {
    popover.classList.add('hidden');
});

// Close popover when clicking outside
window.addEventListener('click', (event) => {
    if (event.target === popover) {
        popover.classList.add('hidden');
    }
});

// Initial fetch
fetchSchedule().then(() => fetchData());
fetchConfig();

// Poll every 5 seconds
setInterval(fetchData, 5000);
