document.addEventListener('DOMContentLoaded', function () {
    const themeSwitch = document.getElementById('theme-switch');
    const body = document.body;

    // Check for saved theme in local storage
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
    }

    themeSwitch.addEventListener('click', function () {
        body.classList.toggle('dark-mode');

        // Save theme preference to local storage
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
        } else {
            localStorage.setItem('theme', 'light');
        }
    });
});
