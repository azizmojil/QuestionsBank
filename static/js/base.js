document.addEventListener('DOMContentLoaded', function () {
    const themeSwitch = document.getElementById('theme-switch');
    const languageSwitch = document.getElementById('language-switch');
    const languageForm = document.getElementById('language-switch-form');
    const languageInput = languageForm ? languageForm.querySelector('input[name="language"]') : null;
    const body = document.body;
    const root = document.documentElement;
    const themeIcon = themeSwitch ? themeSwitch.querySelector('.theme-icon') : null;

    if (themeSwitch) {
        // Add keyboard accessibility to theme switch
        themeSwitch.setAttribute('tabindex', '0');

        // Keep both .dark (CSS variables) and .dark-mode (legacy styles) in sync
        const isDarkMode = () => body.classList.contains('dark-mode') || root.classList.contains('dark');

        function setTheme(isDark) {
            body.classList.toggle('dark-mode', isDark);
            root.classList.toggle('dark', isDark);
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            syncThemeState();
        }

        // Check for saved theme in local storage or system preference
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            setTheme(true);
        }

        function syncThemeState() {
            const isDark = isDarkMode();
            const labelLight = themeSwitch.dataset.labelLight || 'Switch to light mode';
            const labelDark = themeSwitch.dataset.labelDark || 'Switch to dark mode';
            themeSwitch.setAttribute('aria-pressed', isDark.toString());
            themeSwitch.setAttribute('aria-label', isDark ? labelLight : labelDark);
            if (themeIcon) {
                const moonIcon = themeSwitch.dataset.iconMoon || '🌙';
                const sunIcon = themeSwitch.dataset.iconSun || '☀️';
                themeIcon.textContent = isDark ? moonIcon : sunIcon;
            }
        }

        function toggleTheme() {
            setTheme(!isDarkMode());
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
    }

    if (languageSwitch && languageForm && languageInput) {
        const syncLanguageState = () => {
            const currentLang = languageSwitch.dataset.currentLanguage || 'ar';
            const nextLang = currentLang === 'ar' ? 'en' : 'ar';
            languageInput.value = nextLang;
            const label = currentLang === 'ar' ? languageSwitch.dataset.labelAr : languageSwitch.dataset.labelEn;
            const ariaLabel = currentLang === 'ar' ? languageSwitch.dataset.switchToEn : languageSwitch.dataset.switchToAr;
            languageSwitch.setAttribute('aria-label', ariaLabel || '');
            languageSwitch.setAttribute('aria-pressed', currentLang === 'en');
            const labelSpan = languageSwitch.querySelector('.language-label');
            if (labelSpan && label) {
                labelSpan.textContent = label;
            }
        };

        languageSwitch.addEventListener('click', (e) => {
            e.preventDefault();
            const currentLang = languageSwitch.dataset.currentLanguage || 'ar';
            const nextLang = currentLang === 'ar' ? 'en' : 'ar';
            languageInput.value = nextLang;
            languageForm.submit();
        });

        languageSwitch.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                languageSwitch.click();
            }
        });

        syncLanguageState();
    }

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
