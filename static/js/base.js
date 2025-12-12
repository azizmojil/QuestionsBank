document.addEventListener('DOMContentLoaded', function () {
    const themeSwitch = document.getElementById('theme-switch');
    const body = document.body;
    const themeIcon = themeSwitch.querySelector('.theme-icon');

    // Check for saved theme in local storage
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
    }

    // Add keyboard accessibility to theme switch
    themeSwitch.setAttribute('tabindex', '0');

    function syncThemeState() {
        const isDark = body.classList.contains('dark-mode');
        themeSwitch.setAttribute('aria-pressed', isDark.toString());
        themeSwitch.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
        if (themeIcon) {
            themeIcon.textContent = isDark ? '🌙' : '☀️';
        }
    }

    function toggleTheme() {
        body.classList.toggle('dark-mode');
        localStorage.setItem('theme', body.classList.contains('dark-mode') ? 'dark' : 'light');
        syncThemeState();
    }

    themeSwitch.addEventListener('click', toggleTheme);
    
    // Add keyboard support for theme switch
    themeSwitch.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleTheme();
        }
    });

    syncThemeState();

    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add loading state helper function
    window.showLoading = function(element) {
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
        }
    };

    window.hideLoading = function(element) {
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
        }
    };

    // Enhance table interactivity
    const tables = document.querySelectorAll('.data-table');
    tables.forEach(table => {
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.setAttribute('tabindex', '0');
            row.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    const link = row.querySelector('a');
                    if (link) {
                        link.click();
                    }
                }
            });
        });
    });
});
