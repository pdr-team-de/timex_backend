// State management
let timeEntries = [];
let totalWorkTime = 0;
let totalBreakTime = 0;
let lastAction = null;

// Button icon states
const BUTTON_STATES = {
    KOMMEN: {
        active: '/static/time_tracking/icons/KommenAktiv.svg',
        inactive: '/static/time_tracking/icons/KommenInaktiv.svg',
        transparent: '/static/time_tracking/icons/KommenAktivTransparent.svg',
    },
    GEHEN: {
        active: '/static/time_tracking/icons/GehenAktiv.svg',
        inactive: '/static/time_tracking/icons/GehenInaktiv.svg',
        transparent: '/static/time_tracking/icons/GehenAktivTransparent.svg',
    },
    FEIERABEND: {
        active: '/static/time_tracking/icons/FeierabendAktiv.svg',
        inactive: '/static/time_tracking/icons/FeierabendInaktiv.svg',
        transparent: '/static/time_tracking/icons/FeierabendAktivTransparent.svg',
    }
};

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

async function createTimeEntry(type, note = null) {
    try {
        const response = await fetch('/api/time-entries/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ type, note })
        });

        console.log('Response:', response);

        const contentType = response.headers.get('Content-Type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server response is not JSON');
        }

        const data = await response.json();
        if (!response.ok) throw new Error(data.message || 'Server error');

        timeEntries.push(data);
        updateTimes(data);
        createTimeTrackingContainer(data);
        return data;
    } catch (error) {
        console.error('Error creating time entry:', error);
        alert('Fehler beim Erstellen des Eintrags.');
    }
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

    const iconName = BUTTON_STATES[entry.type]?.transparent || '';

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
    if (entriesContainer) {
        entriesContainer.insertBefore(container, entriesContainer.firstChild);
    }

    const infoContainer = document.getElementById('info-container');
    if (infoContainer) {
        infoContainer.style.display = 'none';
    }
}

function updateTimes(entry) {
    const now = new Date(entry.timestamp);

    if (entry.type === 'KOMMEN' && lastAction === 'GEHEN') {
        const lastEntry = timeEntries.find(e => e.type === 'GEHEN');
        if (lastEntry) {
            const breakTime = Math.round((now - new Date(lastEntry.timestamp)) / (1000 * 60));
            totalBreakTime += breakTime;
        }
    } else if (entry.type === 'GEHEN' || entry.type === 'FEIERABEND') {
        const lastKommen = [...timeEntries].reverse().find(e => e.type === 'KOMMEN');
        if (lastKommen) {
            const workTime = Math.round((now - new Date(lastKommen.timestamp)) / (1000 * 60));
            totalWorkTime += workTime;
        }
    }

    updateInfoContainer();
    lastAction = entry.type;
    updateButtonStates(entry.type.toLowerCase());
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
        infoContainer.appendChild(workTimeInfo);
    }

    if (totalBreakTime > 0) {
        const breakHours = Math.floor(totalBreakTime / 60);
        const breakMinutes = totalBreakTime % 60;
        const formattedBreak = `${String(breakHours).padStart(2, '0')}:${String(breakMinutes).padStart(2, '0')}`;
        const breakInfo = document.createElement('p');
        breakInfo.textContent = `${formattedBreak} h Pause gebucht`;
        infoContainer.appendChild(breakInfo);
    }
}

function updateButtonStates(action) {
    const kommenBtn = document.getElementById('KommenAktiv');
    const gehenBtn = document.getElementById('GehenAktiv');
    const feierabendBtn = document.getElementById('FeierabendAktiv');

    if (!kommenBtn || !gehenBtn || !feierabendBtn) return;

    switch (action) {
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

// Initial event bindings
document.addEventListener('DOMContentLoaded', () => {
    lastAction = document.querySelector('[data-last-action]')?.dataset.lastAction;

    const kommenBtn = document.getElementById('KommenAktiv');
    const gehenBtn = document.getElementById('GehenAktiv');
    const feierabendBtn = document.getElementById('FeierabendAktiv');

    if (!lastAction) {
        // Keine vorherige Aktion, die Buttons richtig setzen:
        kommenBtn?.removeAttribute('disabled');
        kommenBtn?.querySelector('img').setAttribute('src', BUTTON_STATES.KOMMEN.active);

        gehenBtn?.setAttribute('disabled', true);
        gehenBtn?.querySelector('img').setAttribute('src', BUTTON_STATES.GEHEN.inactive);

        const feierabendBtn = document.getElementById('FeierabendAktiv');
        if (feierabendBtn) feierabendBtn.style.display = 'none';
    } else if (lastAction === 'FEIERABEND') {
        updateButtonStates('feierabend');
    } else if (lastAction === 'GEHEN') {
        updateButtonStates('gehen');
    } else {
        updateButtonStates('kommen');
    }

    if (kommenBtn) {
        kommenBtn.addEventListener('click', async () => {
            const entry = await createTimeEntry('KOMMEN');
            if (entry) updateButtonStates('kommen');
        });
    }

    if (gehenBtn) {
        gehenBtn.addEventListener('click', async () => {
            const entry = await createTimeEntry('GEHEN');
            if (entry) updateButtonStates('gehen');
        });
    }

    if (feierabendBtn) {
        feierabendBtn.addEventListener('click', async () => {
            const note = prompt('Sie sind dabei Ihren Arbeitstag zu beenden. Dieser Schritt kann nicht rückgängig gemacht werden.\nOptional: Möchten Sie eine Notiz an den Projektleiter senden?');
            if (note !== null) {
                const entry = await createTimeEntry('FEIERABEND', note);
                if (entry) {
                    updateButtonStates('feierabend');
                    alert('Ihr Arbeitstag wurde beendet. Schönen Feierabend!' + (note ? '\nNotiz wurde gespeichert.' : ''));
                }
            }
        });
    }
});
