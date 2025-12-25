document.addEventListener('DOMContentLoaded', function () {
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
        const percentage = progressFill.dataset.percentage;
        if (percentage) {
            // Small delay to allow transition to work
            setTimeout(() => {
                progressFill.style.width = percentage + '%';
            }, 100);
        }
    }
});
