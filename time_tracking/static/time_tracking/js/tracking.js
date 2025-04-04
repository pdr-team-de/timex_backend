// State management
let timeEntries = [];
let totalWorkTime = 0;
let totalBreakTime = 0;
let lastAction = null;
let containerCount = 0;

// Helper Functions
function getCookie(name) {
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

function createTimeTrackingContainer(entry) {
    const container = document.createElement('div');
    container.className = 'time-tracking-container';
    
    const timeString = new Date(entry.timestamp).toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit'
    });
    const dateString = new Date(entry.timestamp).toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
    
    // Get the correct icon based on entry type
    const iconName = `${entry.type}AktivTransparent`;
    
    container.innerHTML = `
        <div class="time-tracking-item">
            <img src="/static/time_tracking/icons/${iconName}.svg" alt="Time Icon" class="time-icon">
            <div class="time-info">
                <p class="mb-0">${timeString} ${dateString}</p>
                ${entry.note ? `<p class="text-muted mb-0">Notiz: ${entry.note}</p>` : ''}
            </div>
        </div>
    `;

    const entriesContainer = document.getElementById('time-entries-container');
    if (entriesContainer.firstChild) {
        entriesContainer.insertBefore(container, entriesContainer.firstChild);
    } else {
        entriesContainer.appendChild(container);
    }

    const infoContainer = document.getElementById('info-container');
    if (infoContainer) {
        infoContainer.style.display = 'none';
    }

    // Update work/break time calculations
    updateTimes(entry);
}

async function createTimeEntry(type, note = null) {
    try {
        const response = await fetch('/api/time-entries/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ type, note })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Server error');
        }

        return data;
    } catch (error) {
        console.error('Error creating time entry:', error);
        throw error;
    }
}

function updateTimes(entry) {
    const now = new Date(entry.timestamp);
    
    if (entry.type === 'KOMMEN' && lastAction === 'GEHEN') {
        // Calculate break time
        const lastEntry = timeEntries[timeEntries.length - 1];
        if (lastEntry) {
            const breakTime = Math.round((now - new Date(lastEntry.timestamp)) / (1000 * 60));
            totalBreakTime += breakTime;
        }
    } else if (entry.type === 'GEHEN' || entry.type === 'FEIERABEND') {
        // Calculate work time
        const lastKommen = timeEntries.find(e => e.type === 'KOMMEN');
        if (lastKommen) {
            const workTime = Math.round((now - new Date(lastKommen.timestamp)) / (1000 * 60));
            totalWorkTime += workTime;
        }
    }

    timeEntries.push(entry);
    updateInfoContainer();
}

function updateInfoContainer() {
    const infoContainer = document.getElementById('info-container');
    if (!infoContainer) return;

    infoContainer.style.display = 'flex';
    infoContainer.style.flexDirection = 'column';
    infoContainer.style.alignItems = 'center';
    infoContainer.innerHTML = '';

    if (totalWorkTime > 0) {
        const workHours = Math.floor(totalWorkTime / 60);
        const workMinutes = totalWorkTime % 60;
        const formattedWork = `${String(workHours).padStart(2, '0')}:${String(workMinutes).padStart(2, '0')}`;
        
        const workTimeInfo = document.createElement('p');
        workTimeInfo.textContent = `${formattedWork} h Arbeitszeit gebucht`;
        workTimeInfo.style.margin = '0.5rem 0';
        infoContainer.appendChild(workTimeInfo);
    }

    if (totalBreakTime > 0) {
        const breakHours = Math.floor(totalBreakTime / 60);
        const breakMinutes = totalBreakTime % 60;
        const formattedBreak = `${String(breakHours).padStart(2, '0')}:${String(breakMinutes).padStart(2, '0')}`;
        
        const breakInfo = document.createElement('p');
        breakInfo.textContent = `${formattedBreak} h Pause gebucht`;
        breakInfo.style.margin = '0.5rem 0';
        infoContainer.appendChild(breakInfo);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize last action from server data
    lastAction = document.querySelector('[data-last-action]')?.dataset.lastAction;

    // Button event listeners
    document.getElementById('KommenAktiv')?.addEventListener('click', async () => {
        const button = document.getElementById('KommenAktiv');
        if (button.disabled) return;
        
        const entry = await createTimeEntry('KOMMEN');
        if (entry) {
            lastAction = 'KOMMEN';
            updateButtonStates('kommen');
        }
    });

    document.getElementById('GehenAktiv')?.addEventListener('click', async () => {
        const button = document.getElementById('GehenAktiv');
        if (button.disabled) return;
        
        const entry = await createTimeEntry('GEHEN');
        if (entry) {
            lastAction = 'GEHEN';
            updateButtonStates('gehen');
        }
    });

    document.getElementById('FeierabendAktiv')?.addEventListener('click', async () => {
        const note = prompt('Sie sind dabei ihren Arbeitstag zu beenden. Dieser Schritt kann nicht ruckgängig gemacht werden.\nOptional: Möchten Sie eine Notiz an den Projektleiter senden?');
        if (note !== null) {
            const entry = await createTimeEntry('FEIERABEND', note);
            if (entry) {
                lastAction = 'FEIERABEND';
                updateButtonStates('feierabend');
                alert('Ihr Arbeitstag wurde beendet. Schönen Feierabend!' + (note ? '\nNotiz wurde gespeichert.' : ''));
            }
        }
    });
});

function createTimeTrackingContainer(entry) {
    const container = document.createElement('div');
    container.className = 'time-tracking-container';
    
    const timeString = new Date(entry.timestamp).toLocaleTimeString('de-DE', {
        hour: '2-digit',
        minute: '2-digit'
    });
    const dateString = new Date(entry.timestamp).toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
    
    const iconName = BUTTON_STATES[entry.type].transparent;
    
    container.innerHTML = `
        <div class="time-tracking-item">
            <img src="${iconName}" alt="Time Icon" class="time-icon">
            <div class="time-info">
                <p class="mb-0">${timeString} ${dateString}</p>
                ${entry.note ? `<p class="text-muted mb-0">Notiz: ${entry.note}</p>` : ''}
            </div>
        </div>
    `;

    const entriesContainer = document.getElementById('time-entries-container');
    entriesContainer.insertBefore(container, entriesContainer.firstChild);

    const infoContainer = document.getElementById('info-container');
    if (infoContainer) {
        infoContainer.style.display = 'none';
    }
}

function updateButtonStates(action) {
    const kommenBtn = document.getElementById('KommenAktiv');
    const gehenBtn = document.getElementById('GehenAktiv');
    const feierabendBtn = document.getElementById('FeierabendAktiv');

    if (!kommenBtn || !gehenBtn || !feierabendBtn) return;

    switch(action) {
        case 'kommen':
            kommenBtn.disabled = true;
            kommenBtn.querySelector('img').src = BUTTON_STATES.KOMMEN.inactive;
            gehenBtn.disabled = false;
            gehenBtn.querySelector('img').src = BUTTON_STATES.GEHEN.active;
            feierabendBtn.style.display = 'none';
            break;

        case 'gehen':
            gehenBtn.disabled = true;
            gehenBtn.querySelector('img').src = BUTTON_STATES.GEHEN.inactive;
            kommenBtn.disabled = false;
            kommenBtn.querySelector('img').src = BUTTON_STATES.KOMMEN.active;
            feierabendBtn.style.display = 'flex';
            feierabendBtn.querySelector('img').src = BUTTON_STATES.FEIERABEND.active;
            break;

        case 'feierabend':
            kommenBtn.disabled = true;
            gehenBtn.disabled = true;
            feierabendBtn.disabled = true;
            kommenBtn.querySelector('img').src = BUTTON_STATES.KOMMEN.inactive;
            gehenBtn.querySelector('img').src = BUTTON_STATES.GEHEN.inactive;
            feierabendBtn.querySelector('img').src = BUTTON_STATES.FEIERABEND.inactive;
            break;
    }
}

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('KommenAktiv')?.addEventListener('click', async () => {
        await createTimeEntry('KOMMEN');
    });

    document.getElementById('GehenAktiv')?.addEventListener('click', async () => {
        await createTimeEntry('GEHEN');
    });

    document.getElementById('FeierabendAktiv')?.addEventListener('click', async () => {
        const note = prompt('Möchten Sie eine Notiz für den Projektleiter hinterlassen?');
        if (note !== null) {
            await createTimeEntry('FEIERABEND', note);
        }
    });
});