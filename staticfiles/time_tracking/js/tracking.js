document.addEventListener('DOMContentLoaded', function(){
    // State management
    let timeEntries = [];
    let totalWorkTime = 0;
    let totalBreakTime = 0;
    let lastAction = null;
    let containerCount = 0;

    // Icon paths configuration
    const BUTTON_STATES = {
        KOMMEN: {
            active: '/static/time_tracking/icons/KommenAktivMitText.svg',
            inactive: '/static/time_tracking/icons/KommenInaktivMitText.svg',
            transparent: '/static/time_tracking/icons/KommenAktivTransparent.svg'
        },
        GEHEN: {
            active: '/static/time_tracking/icons/GehenAktivMitText.svg',
            inactive: '/static/time_tracking/icons/GehenInaktivMitText.svg',
            transparent: '/static/time_tracking/icons/GehenAktivTransparent.svg'
        },
        FEIERABEND: {
            active: '/static/time_tracking/icons/FeierabendAktivMitText.svg',
            inactive: '/static/time_tracking/icons/FeierabendInaktivMitText.svg',
            transparent: '/static/time_tracking/icons/FeierabendAktivTransparent.svg'
        }
    };

    // Button state management
    function updateButtonStates(action) {
        const kommenBtn = document.getElementById('KommenAktiv');
        const gehenBtn = document.getElementById('GehenAktiv');
        const feierabendBtn = document.getElementById('FeierabendAktiv');

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

    // Erzeugt das UI-Element für einen Zeiteintrag
    function createTimeTrackingContainer(entry) {
        const container = document.createElement('div');
        container.id = entry.containerId;
        container.className = 'time-tracking-container';
        
        // Formatierung der Zeit und des Datums (hier immer als lokaler String)
        const timeString = entry.time.toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const dateString = entry.time.toLocaleDateString('de-DE', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        
        // Icon entsprechend dem Entry-Typ auswählen
        const iconName = BUTTON_STATES[entry.type.toUpperCase()].transparent;
        
        container.innerHTML = `
            <div class="time-tracking-item">
                <img src="${iconName}" alt="Time Icon" class="time-icon">
                <div class="time-info">
                    <p class="mb-0">${timeString} ${dateString}</p>
                    ${entry.note ? `<p class="text-muted mb-0">Notiz: ${entry.note}</p>` : ''}
                </div>
            </div>
        `;

        const infoContainer = document.getElementById('info-container');
        infoContainer.parentNode.insertBefore(container, infoContainer.nextSibling);
    }

    // Aktualisiert den Info-Bereich mit Arbeits- und Pausenzeiten
    function updateInfoContainer() {
        const infoContainer = document.getElementById('info-container');
        infoContainer.style.display = 'flex';
        infoContainer.style.flexDirection = 'column';
        infoContainer.style.alignItems = 'center';
        infoContainer.innerHTML = '';

        const workHours = Math.floor(totalWorkTime / 60);
        const workMinutes = totalWorkTime % 60;
        const formattedWork = `${String(workHours).padStart(2, '0')}:${String(workMinutes).padStart(2, '0')}`;
        
        const workTimeInfo = document.createElement('p');
        workTimeInfo.textContent = `${formattedWork} h Arbeitszeit gebucht`;
        workTimeInfo.style.margin = '0.5rem 0';
        infoContainer.appendChild(workTimeInfo);

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

    // Sendet den Zeiteintrag asynchron an den Server
    async function createTimeEntry(type, note = null) {
        try {
            const csrftoken = getCookie('csrftoken');
            const response = await fetch('/api/time-entries/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    type: type,
                    note: note
                })
            });
    
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || 'Server Error');
            }
    
            if (data.status === 'success') {
                const now = new Date();
                const entry = {
                    type: type.toLowerCase(),
                    time: now,
                    containerId: `time-tracking-${++containerCount}`,
                    note: note
                };
                
                timeEntries.push(entry);
                createTimeTrackingContainer(entry);
                updateButtonStates(type.toLowerCase());
                updateTimeCalculations(entry);
                lastAction = type.toLowerCase();
    
                return data;
            } else {
                throw new Error(data.message || 'Unbekannter Fehler');
            }
        } catch (error) {
            console.error('Error:', error);
            alert(`Fehler beim Speichern des Zeiteintrags: ${error.message}`);
            throw error;
        } finally {
            // Re-enable button if needed
            const button = document.querySelector(`button[data-type="${type}"]`);
            if (button) {
                button.disabled = false;
            }
        }
    }

    // Event Listener – hier jeweils nur ein Listener pro Button
    document.getElementById('KommenAktiv').addEventListener('click', async function() {
        try {
            this.disabled = true;
            await createTimeEntry('KOMMEN');
        } catch (error) {
            this.disabled = false;
        }
    });

    document.getElementById('GehenAktiv').addEventListener('click', function(){
        this.disabled = true;
        createTimeEntry('GEHEN');
    });

    document.getElementById('FeierabendAktiv').addEventListener('click', function(){
        const note = prompt('Möchten Sie eine Notiz für den Projektleiter hinterlassen?');
        createTimeEntry('FEIERABEND', note);
    });
});
