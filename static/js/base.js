document.addEventListener('DOMContentLoaded', function () {
    // -----------------------------------------------------------------------
    // Mode switch (☀️ / 🌙) => CHECKED = LIGHT (☀️), UNCHECKED = DARK (🌙)
    // Keeps both .dark (CSS variables) and .dark-mode (legacy styles) in sync
    // -----------------------------------------------------------------------
    const themeSwitch = document.getElementById('theme-switch');
    const body = document.body;
    const root = document.documentElement;

    if (themeSwitch) {
        const isDarkMode = () => body.classList.contains('dark-mode') || root.classList.contains('dark');

        function syncThemeState() {
            const isDark = isDarkMode();
            const labelLight = themeSwitch.dataset.labelLight || 'Switch to light mode';
            const labelDark = themeSwitch.dataset.labelDark || 'Switch to dark mode';

            // checked = light, unchecked = dark
            themeSwitch.checked = !isDark;
            themeSwitch.setAttribute('aria-checked', (!isDark).toString());
            themeSwitch.setAttribute('aria-label', isDark ? labelLight : labelDark);
        }

        function setTheme(isDark) {
            body.classList.toggle('dark-mode', isDark);
            root.classList.toggle('dark', isDark);
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            syncThemeState();
        }

        // Init from storage or system preference
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const initialDark = (savedTheme === 'dark') || (!savedTheme && prefersDark);
        setTheme(initialDark);

        // Toggle on change (checked => light)
        themeSwitch.addEventListener('change', function () {
            const wantsLight = !!themeSwitch.checked;
            setTheme(!wantsLight);
        });

        syncThemeState();
    }

    // -----------------------------------------------------------------------
    // Language switch (Ar / En) => CHECKED = AR, UNCHECKED = EN
    // Submits Django set_language form via POST
    // -----------------------------------------------------------------------
    const languageForm = document.getElementById('language-switch-form');
    const languageSwitch = document.getElementById('language-switch');
    const languageTarget = document.getElementById('language-switch-target');

    if (languageForm && languageSwitch && languageTarget) {
        function syncLanguageA11y() {
            const toArLabel = languageSwitch.dataset.labelToAr || 'Switch to Arabic';
            const toEnLabel = languageSwitch.dataset.labelToEn || 'Switch to English';

            languageSwitch.setAttribute('aria-checked', (languageSwitch.checked).toString());
            languageSwitch.setAttribute('aria-label', languageSwitch.checked ? toArLabel : toEnLabel);
        }

        syncLanguageA11y();

        languageSwitch.addEventListener('change', function () {
            languageTarget.value = languageSwitch.checked ? 'ar' : 'en';
            syncLanguageA11y();
            languageForm.submit();
        });
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
