document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('theme-toggle');
    if (!toggleButton) return;

    const root = document.documentElement;
    const body = document.body;

    const isDark = () => root.classList.contains('dark') || body.classList.contains('dark-mode');

    const applyTheme = (dark) => {
        root.classList.toggle('dark', dark);
        body.classList.toggle('dark-mode', dark);
        toggleButton.setAttribute('aria-pressed', String(dark));
    };

    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const startDark = savedTheme ? savedTheme === 'dark' : prefersDark;
    applyTheme(startDark);

    toggleButton.addEventListener('click', () => {
        const next = !isDark();
        applyTheme(next);
        localStorage.setItem('theme', next ? 'dark' : 'light');
    });
});
