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

let isSubmitting = false;

async function createTimeEntry(type, note = null) {
    if (isSubmitting) return;
    
    const thisButton = document.getElementById(`${type.charAt(0)}${type.slice(1).toLowerCase()}Aktiv`);
    if (!thisButton) return;
    
    try {
        isSubmitting = true;
        thisButton.disabled = true;
        const csrftoken = getCookie('csrftoken');

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

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response');
        }

        const data = await response.json();
        console.log('Server response:', data);

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
        isSubmitting = false;
        if (thisButton) {
            thisButton.disabled = false;
        }
    }
}

// Only initialize the event listeners once
document.addEventListener('DOMContentLoaded', function() {
    const buttons = {
        'KommenAktiv': 'KOMMEN',
        'GehenAktiv': 'GEHEN',
        'FeierabendAktiv': 'FEIERABEND'
    };

    Object.entries(buttons).forEach(([id, type]) => {
        const button = document.getElementById(id);
        if (button) {
            // Remove existing listeners
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add new listener
            newButton.addEventListener('click', async () => {
                if (type === 'FEIERABEND') {
                    const note = prompt('Möchten Sie eine Notiz für den Projektleiter hinterlassen?');
                    if (note !== null) {
                        await createTimeEntry(type, note);
                    }
                } else {
                    await createTimeEntry(type);
                }
            });
        }
    });
});