document.addEventListener('DOMContentLoaded', function () {
    const tableBody = document.querySelector('.table-body');
    if (!tableBody) return;

    tableBody.addEventListener('click', function (e) {
        if (e.target.tagName.toLowerCase() === 'select') {
            e.stopPropagation();
            return;
        }

        const row = e.target.closest('tr[data-target-id]');
        if (!row) return;

        const targetId = row.dataset.targetId;
        const contentRow = document.getElementById(targetId);

        if (contentRow) {
            const isVisible = contentRow.style.display === 'table-row';
            contentRow.style.display = isVisible ? 'none' : 'table-row';
        }
    });
});
