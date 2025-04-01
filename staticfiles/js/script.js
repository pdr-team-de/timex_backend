document.addEventListener('DOMContentLoaded', function(){
    let timeEntries = []; // Array to store time entries
    let totalWorkTime = 0; // Total work time 
    let totalBreakTime = 0; // Total break time
    let lastAction = null;
    let containerCount = 0;

    document.getElementById('hamburger-menu').addEventListener('click', function(){
        document.getElementById('menu-overlay').style.display = 'flex';
    });

    document.getElementById('close-menu').addEventListener('click', function(){
        document.getElementById('menu-overlay').style.display = 'none';
    });

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
            // Calculate and add break time
            const lastGehen = timeEntries.find(e => e.type === 'gehen');
            if (lastGehen) {
                const breakTime = Math.round((now - lastGehen.time) / (1000 * 60));
                totalBreakTime += breakTime;
                updateInfoContainer();
            }
        }
        
        // Create new tracking container
        createTimeTrackingContainer(entry);
        lastAction = 'kommen';
        
        // Button states
        this.disabled = true;
        this.querySelector('img').src = 'assets/icons/KommenInaktivMitText.svg';
        document.getElementById('GehenAktiv').disabled = false;
        document.getElementById('GehenAktiv').querySelector('img').src = 'assets/icons/GehenAktivMitText.svg';
    });

    document.getElementById('GehenAktiv').addEventListener('click', function(){
        const now = new Date();
        const entry = {
            type: 'gehen',
            time: now,
            containerId: `time-tracking-${++containerCount}`
        };
        timeEntries.push(entry);

        // Calculate work time since last 'kommen'
        const lastKommen = timeEntries.filter(e => e.type === 'kommen').pop();
        if (lastKommen) {
            const workTime = Math.round((now - lastKommen.time) / (1000 * 60));
            totalWorkTime += workTime;
            updateInfoContainer();
        }

        // Create new tracking container
        createTimeTrackingContainer(entry);
        
        lastAction = 'gehen';
        document.getElementById('FeierabendAktiv').style.display = 'flex';

        // Button states
        this.disabled = true;
        this.querySelector('img').src = 'assets/icons/GehenInaktivMitText.svg';
        document.getElementById('KommenAktiv').disabled = false;
        document.getElementById('KommenAktiv').querySelector('img').src = 'assets/icons/KommenAktivMitText.svg';
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
        
        let iconName;
        switch(entry.type) {
            case 'kommen':
                iconName = 'KommenAktivTransparent';
                break;
            case 'gehen':
                iconName = 'GehenAktivTransparent';
                break;
            case 'feierabend':
                iconName = 'FeierabendAktivTransparent';
                break;
        }
        
        container.innerHTML = `
            <div class="time-tracking-item">
                <img src="assets/icons/${iconName}.svg" alt="Time Icon" class="time-icon">
                <div class="time-info">
                    <p class="mb-0">${timeString} ${dateString}</p>
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

    document.getElementById('FeierabendAktiv').addEventListener('click', function(){
        const note = prompt('Sie sind dabei ihren Arbeitstag zu beenden. Dieser Schritt kann nicht ruckgängig gemacht werden. \nOptional: Möchten Sie eine Notiz an den Projektleiter senden?');
        if (note !== null){
            const now = new Date();
            // Create final time tracking entry for Feierabend
            const entry = {
                type: 'feierabend',
                time: now,
                containerId: `time-tracking-${++containerCount}`
            };
            createTimeTrackingContainer(entry);

            // Calculate final work time if last action was 'kommen'
            if (lastAction === 'kommen') {
                const lastKommen = timeEntries.filter(e => e.type === 'kommen').pop();
                if (lastKommen) {
                    const workTime = Math.round((now - lastKommen.time) / (1000 * 60));
                    totalWorkTime += workTime;
                    updateInfoContainer();
                }
            }

            alert('Ihr Arbeitstag wurde beendet. Schönen Feierabend! \n' + (note || ' Keine Notiz'));
            
            // Reset buttons
            document.getElementById('KommenAktiv').disabled = true;
            document.getElementById('GehenAktiv').disabled = true;
            this.disabled = true;
            
            // Update button images
            document.getElementById('KommenAktiv').querySelector('img').src = 'assets/icons/KommenInaktivMitText.svg';
            document.getElementById('GehenAktiv').querySelector('img').src = 'assets/icons/GehenInaktivMitText.svg';
            this.querySelector('img').src = 'assets/icons/FeierabendInaktivMitText.svg';
        }
       
    });

});