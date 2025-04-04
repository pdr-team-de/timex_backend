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

async function createTimeEntry(type, note = null) {
    const thisButton = document.getElementById(`${type.charAt(0)}${type.slice(1).toLowerCase()}Aktiv`);
    if (!thisButton) return;
    
    try {
        thisButton.disabled = true;
        const csrftoken = getCookie('csrftoken');

        if (!csrftoken) {
            throw new Error('CSRF token not found');
        }

        const response = await fetch('/api/time-entries/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ type, note }),
            credentials: 'same-origin'
        });

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            if (response.status === 302) {
                window.location.reload();
                return;
            }
            throw new Error('Server returned non-JSON response');
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }

        if (data.status === 'success' && data.data) {
            createTimeTrackingContainer(data.data);
            updateButtonStates(type.toLowerCase());
            return data;
        } else {
            throw new Error(data.message || 'Unknown error');
        }

    } catch (error) {
        console.error('Error creating time entry:', error);
        alert(`Fehler beim Speichern des Zeiteintrags: ${error.message}`);
    } finally {
        if (thisButton) {
            thisButton.disabled = false;
        }
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