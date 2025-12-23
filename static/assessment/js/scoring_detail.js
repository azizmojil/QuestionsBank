document.addEventListener('DOMContentLoaded', function () {
    const tableBody = document.getElementById('scoring-table-body');
    if (!tableBody) return;

    tableBody.addEventListener('click', function (e) {
        const row = e.target.closest('tr[data-target-id]');
        if (!row) return;

        const targetId = row.dataset.targetId;
        const contentRow = document.getElementById(targetId);

        if (contentRow) {
            contentRow.style.display = contentRow.style.display === 'none' ? 'table-row' : 'none';
        }
    });
});
