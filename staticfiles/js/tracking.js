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
            active: '../icons/KommenAktivMitText.svg',
            inactive: '../icons/KommenInaktivMitText.svg',
            transparent: '../icons/KommenAktivTransparent.svg'
        },
        GEHEN: {
            active: '../icons/GehenAktivMitText.svg',
            inactive: '../icons/GehenInaktivMitText.svg',
            transparent: '../icons/GehenAktivTransparent.svg'
        },
        FEIERABEND: {
            active: '../icons/FeierabendAktivMitText.svg',
            inactive: '../icons/FeierabendInaktivMitText.svg',
            transparent: '../icons/FeierabendAktivTransparent.svg'
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

    // Event Listeners
    document.getElementById('KommenAktiv').addEventListener('click', function(){
        const now = new Date();
        const entry = {
            type: 'kommen',
            time: now,
            containerId: `time-tracking-${++containerCount}`
        };
        timeEntries.push(entry);

        if (!lastAction) {
            document.getElementById('info-container').style.display = 'none';
        } else if (lastAction === 'gehen') {
            const lastGehen = timeEntries.find(e => e.type === 'gehen');
            if (lastGehen) {
                const breakTime = Math.round((now - lastGehen.time) / (1000 * 60));
                totalBreakTime += breakTime;
                updateInfoContainer();
            }
        }
        
        createTimeTrackingContainer(entry);
        lastAction = 'kommen';
        updateButtonStates('kommen');
    });

    document.getElementById('GehenAktiv').addEventListener('click', function(){
        const now = new Date();
        const entry = {
            type: 'gehen',
            time: now,
            containerId: `time-tracking-${++containerCount}`
        };
        timeEntries.push(entry);

        const lastKommen = timeEntries.filter(e => e.type === 'kommen').pop();
        if (lastKommen) {
            const workTime = Math.round((now - lastKommen.time) / (1000 * 60));
            totalWorkTime += workTime;
            updateInfoContainer();
        }

        createTimeTrackingContainer(entry);
        lastAction = 'gehen';
        updateButtonStates('gehen');
    });

    document.getElementById('FeierabendAktiv').addEventListener('click', function(){
        const note = prompt('Sie sind dabei ihren Arbeitstag zu beenden. Dieser Schritt kann nicht rückgängig gemacht werden. \nOptional: Möchten Sie eine Notiz an den Projektleiter senden?');
        if (note !== null) {
            const now = new Date();
            const entry = {
                type: 'feierabend',
                time: now,
                containerId: `time-tracking-${++containerCount}`,
                note: note
            };
            timeEntries.push(entry);

            if (lastAction === 'kommen') {
                const lastKommen = timeEntries.filter(e => e.type === 'kommen').pop();
                if (lastKommen) {
                    const workTime = Math.round((now - lastKommen.time) / (1000 * 60));
                    totalWorkTime += workTime;
                    updateInfoContainer();
                }
            }

            createTimeTrackingContainer(entry);
            lastAction = 'feierabend';
            updateButtonStates('feierabend');
            
            // Send data to server
            sendTimeEntries(timeEntries, note);
        }
    });

    function createTimeTrackingContainer(entry) {
        const container = document.createElement('div');
        container.id = entry.containerId;
        container.className = 'time-tracking-container';
        
        const timeString = entry.time.toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const dateString = entry.time.toLocaleDateString('de-DE', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        
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

    function updateInfoContainer() {
        const infoContainer = document.getElementById('info-container');
        infoContainer.style.display = 'flex';
        infoContainer.style.flexDirection = 'column'; // Add this line
        infoContainer.style.alignItems = 'center'; // Add this line
        infoContainer.innerHTML = '';

        const workHours = Math.floor(totalWorkTime / 60);
        const workMinutes = totalWorkTime % 60;
        const formattedWork = `${String(workHours).padStart(2, '0')}:${String(workMinutes).padStart(2, '0')}`;
        
        const workTimeInfo = document.createElement('p');
        workTimeInfo.textContent = `${formattedWork} h Arbeitszeit gebucht`;
        workTimeInfo.style.margin = '0.5rem 0'; // Add spacing
        infoContainer.appendChild(workTimeInfo);

        if (totalBreakTime > 0) {
            const breakHours = Math.floor(totalBreakTime / 60);
            const breakMinutes = totalBreakTime % 60;
            const formattedBreak = `${String(breakHours).padStart(2, '0')}:${String(breakMinutes).padStart(2, '0')}`;
            
            const breakInfo = document.createElement('p');
            breakInfo.textContent = `${formattedBreak} h Pause gebucht`;
            breakInfo.style.margin = '0.5rem 0'; // Add spacing
            infoContainer.appendChild(breakInfo);
        }
    }

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
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    entry_type: type,
                    note: note
                })
            });

            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            
            // Update UI with new entry
            createTimeTrackingContainer(data);
            updateButtonStates(type);
            updateInfoContainer();

        } catch (error) {
            console.error('Error:', error);
            alert('Fehler beim Speichern des Zeiteintrags');
        }
    }

    document.getElementById('KommenAktiv').addEventListener('click', function(){
        this.disabled = true;
        createTimeEntry('KOMMEN');
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