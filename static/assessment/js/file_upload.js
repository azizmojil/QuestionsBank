document.addEventListener('DOMContentLoaded', function () {
    function toggleInputs(optId, selectedValue) {
        const fileWrapper = document.querySelector(`[data-upload-wrapper-for="${optId}"]`);
        const linkWrapper = document.querySelector(`[data-link-wrapper-for="${optId}"]`);

        if (!fileWrapper || !linkWrapper) return;

        const fileInput = fileWrapper.querySelector('input[type="file"]');
        const linkInput = linkWrapper.querySelector('input[type="url"]');

        fileWrapper.classList.add('hidden');
        linkWrapper.classList.add('hidden');

        if (fileInput) fileInput.removeAttribute('required');
        if (linkInput) linkInput.removeAttribute('required');

        if (selectedValue === 'new') {
            fileWrapper.classList.remove('hidden');
            if (fileInput) fileInput.setAttribute('required', 'required');
        } else if (selectedValue === 'link') {
            linkWrapper.classList.remove('hidden');
            if (linkInput) linkInput.setAttribute('required', 'required');
        }
    }

    document.body.addEventListener('change', function (e) {
        const radio = e.target.closest('input[type="radio"][name^="action_"]');
        if (!radio) return;

        const optId = radio.name.split('_').pop();
        toggleInputs(optId, radio.value);
    });

    document.querySelectorAll('input[type="radio"][name^="action_"]:checked').forEach(function (rb) {
        const optId = rb.name.split('_').pop();
        toggleInputs(optId, rb.value);
    });
});
