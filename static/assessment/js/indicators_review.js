document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-toggle-indicator]').forEach(header => {
        header.addEventListener('click', function () {
            const indicatorId = this.dataset.toggleIndicator;
            const content = document.getElementById(`indicator-${indicatorId}`);
            if (content) {
                const isVisible = content.style.display === 'block';
                content.style.display = isVisible ? 'none' : 'block';
            }
        });
    });
});
