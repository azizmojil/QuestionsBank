document.addEventListener('DOMContentLoaded', function () {
    const themeSwitch = document.getElementById('theme-switch');
    const body = document.body;

    // Check for saved theme in local storage
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
    }

    // Add keyboard accessibility to theme switch
    themeSwitch.setAttribute('role', 'button');
    themeSwitch.setAttribute('aria-label', 'Toggle dark mode');
    themeSwitch.setAttribute('tabindex', '0');

    function toggleTheme() {
        body.classList.toggle('dark-mode');

        // Save theme preference to local storage
        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            themeSwitch.setAttribute('aria-label', 'Toggle light mode');
        } else {
            localStorage.setItem('theme', 'light');
            themeSwitch.setAttribute('aria-label', 'Toggle dark mode');
        }
    }

    themeSwitch.addEventListener('click', toggleTheme);
    
    // Add keyboard support for theme switch
    themeSwitch.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleTheme();
        }
    });

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
