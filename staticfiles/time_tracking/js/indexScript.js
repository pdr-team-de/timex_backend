document.addEventListener('DOMContentLoaded', function(){

    document.getElementById('header-hamburger-menu').addEventListener('click', function(){
        document.getElementById('header-overlay').style.display = 'flex';
    })

    document.getElementById('header-close-menu').addEventListener('click', function(){
        document.getElementById('header-overlay').style.display = 'none';
    })

});