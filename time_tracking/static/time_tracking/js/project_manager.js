// Status indicators
const STATUS_INDICATORS = {
    OFFLINE: '⚪',
    ONLINE: '🟢',
    WORKING: '🔵',
    BREAK: '🟡'
}

// Action icons
const ACTION_ICONS = {
    KOMMEN: '→',
    GEHEN: '←',
    FEIERABEND: '⭕'
}

class WorkerActivityMonitor {
    constructor() {
        this.workers = new Map();
        this.checkInterval = 30000; // 30 seconds
        this.isMonitoring = false;
        this.monitoringInterval = null;
        this.init();
    }
    init() {
        // Initialize tooltips
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));

        // Set up worker status monitoring
        document.querySelectorAll('.worker-row').forEach(row => {
            const workerId = row.dataset.workerId;
            this.workers.set(workerId, {
                element: row,
                lastSeen: null,
                currentStatus: 'OFFLINE',
                lastAction: null,
                retryCount: 0
            });
        });

        this.startMonitoring();
        this.setupEventListeners();
    }

    async updateWorkerStatus(workerId) {
        const worker = this.workers.get(workerId);
        if (!worker || worker.retryCount > 3) return;

        try {
            const response = await fetch(`/api/worker/${workerId}/status/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log(`Worker ${workerId} status:`, data); // Debug log
            
            const statusIndicator = document.getElementById(`status-${workerId}`);
            const actionSpan = document.getElementById(`action-${workerId}`);
            const timeSpan = document.getElementById(`time-${workerId}`);

            if (!statusIndicator) return;

            let statusIcon = STATUS_INDICATORS.OFFLINE;
            let statusTitle = 'Offline';

            if (data.is_online) {
                if (data.last_action?.is_recent) {
                    statusIcon = STATUS_INDICATORS.WORKING;
                    statusTitle = `Arbeitet - ${data.last_action.type}`;
                } else {
                    statusIcon = STATUS_INDICATORS.ONLINE;
                    statusTitle = 'Online';
                }

                // Update last action if available
                if (data.last_action) {
                    if (actionSpan) {
                        actionSpan.textContent = ACTION_ICONS[data.last_action.type] || '-';
                        actionSpan.title = data.last_action.type;
                    }
                    if (timeSpan) {
                        const timestamp = new Date(data.last_action.timestamp);
                        timeSpan.textContent = timestamp.toLocaleTimeString('de-DE', {
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    }
                }
            }

            // Update status indicator
            statusIndicator.textContent = statusIcon;
            statusIndicator.title = statusTitle;
            
            // Update tooltip if using Bootstrap tooltips
            const tooltip = bootstrap.Tooltip.getInstance(statusIndicator);
            if (tooltip) {
                tooltip.dispose();
                new bootstrap.Tooltip(statusIndicator);
            }

            // Update worker state
            worker.currentStatus = data.is_online ? 'ONLINE' : 'OFFLINE';
            worker.lastSeen = data.last_seen;
            worker.lastAction = data.last_action;
            worker.retryCount = 0;

        } catch (error) {
            console.error(`Error updating worker ${workerId} status:`, error);
            worker.retryCount++;
            
            if (worker.retryCount > 3) {
                const statusIndicator = document.getElementById(`status-${workerId}`);
                if (statusIndicator) {
                    statusIndicator.textContent = STATUS_INDICATORS.OFFLINE;
                    statusIndicator.title = 'Verbindungsfehler';
                }
            }
        }
    }

    startMonitoring() {
         if (this.isMonitoring) return;

        this.isMonitoring = true;
        this.updateAllWorkers(); // Initial update

        this.monitoringInterval = setInterval(() => {
            this.updateAllWorkers();
        }, this.checkInterval);
    }

    stopMonitoring() {
        this.isMonitoring = false;
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
    }

    updateAllWorkers() {
        this.workers.forEach((worker, id) => {
            if (worker.retryCount <= 3) {
                this.updateWorkerStatus(id);
            }
        });
    }

    setupEventListeners() {
        // View activity log
        document.querySelectorAll('.view-log').forEach(button => {
            button.addEventListener('click', async (e) => {
                const workerId = e.currentTarget.dataset.workerId;
                await this.showActivityLog(workerId);
            });
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopMonitoring();
            } else {
                this.startMonitoring();
            }
        });
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }


    async showActivityLog(workerId) {
        try {
            const response = await fetch(`/api/worker/${workerId}/activity-log/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            const logContainer = document.getElementById('activityLog');
            if (!logContainer) return;

            logContainer.innerHTML = data.activities.length ? '' : '<p class="text-muted">Keine Aktivitäten heute</p>';

            data.activities.forEach(activity => {
                const activityElement = this.createActivityElement(activity);
                logContainer.appendChild(activityElement);
            });

        } catch (error) {
            console.error('Error loading activity log:', error);
            alert('Fehler beim Laden des Aktivitätsprotokolls');
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const monitor = new WorkerActivityMonitor();
});