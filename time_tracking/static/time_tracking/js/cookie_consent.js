document.addEventListener('DOMContentLoaded', function() {
    if (!localStorage.getItem('cookieConsent')) {
        const consentBanner = document.getElementById('cookieConsent');
        if (consentBanner) {
            consentBanner.style.display = 'block';
            
            document.getElementById('acceptCookies').addEventListener('click', function() {
                localStorage.setItem('cookieConsent', 'true');
                consentBanner.style.display = 'none';
            });
            
            document.getElementById('declineCookies').addEventListener('click', function() {
                localStorage.setItem('cookieConsent', 'false');
                consentBanner.style.display = 'none';
            });
        }
    }
});