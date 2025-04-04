async function createTimeEntry(type, note = null) {
    try {
        const csrftoken = getCookie('csrftoken');
        console.log('Creating time entry:', { type, note, csrftoken: !!csrftoken });

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

        console.log('Response status:', response.status);

        if (response.redirected) {
            window.location.href = response.url;
            return;
        }

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response');
        }

        const data = await response.json();
        console.log('Response data:', data);

        if (!response.ok) {
            throw new Error(data.message || `HTTP error! status: ${response.status}`);
        }

        if (data.status === 'success') {
            updateTimeEntryDisplay(data.data);
            updateButtonStates(type.toLowerCase());
            return data;
        } else {
            throw new Error(data.message || 'Unknown error');
        }

    } catch (error) {
        console.error('Error details:', error);
        
        if (error.message.includes('non-JSON response')) {
            // Refresh the page if session expired
            window.location.reload();
            return;
        }
        
        alert(`Fehler beim Speichern des Zeiteintrags: ${error.message}`);
        throw error;
    } finally {
        // Re-enable buttons if needed
        const buttons = ['KommenAktiv', 'GehenAktiv', 'FeierabendAktiv'];
        buttons.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.disabled = false;
        });
    }
}
document.addEventListener('DOMContentLoaded', function() {
    const kommenBtn = document.getElementById('KommenAktiv');
    const gehenBtn = document.getElementById('GehenAktiv');
    const feierabendBtn = document.getElementById('FeierabendAktiv');

    if (kommenBtn) {
        kommenBtn.addEventListener('click', async function() {
            if (this.disabled) return;
            try {
                this.disabled = true;
                await createTimeEntry('KOMMEN');
            } catch (error) {
                console.error('Kommen error:', error);
                this.disabled = false;
            }
        });
    }

    if (gehenBtn) {
        gehenBtn.addEventListener('click', async function() {
            if (this.disabled) return;
            try {
                this.disabled = true;
                await createTimeEntry('GEHEN');
            } catch (error) {
                console.error('Gehen error:', error);
                this.disabled = false;
            }
        });
    }

    if (feierabendBtn) {
        feierabendBtn.addEventListener('click', async function() {
            if (this.disabled) return;
            try {
                this.disabled = true;
                const note = prompt('Möchten Sie eine Notiz für den Projektleiter hinterlassen?');
                await createTimeEntry('FEIERABEND', note);
            } catch (error) {
                console.error('Feierabend error:', error);
                this.disabled = false;
            }
        });
    }
});