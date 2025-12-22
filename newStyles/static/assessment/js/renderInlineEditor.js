function renderInlineEditor(pathItem, questionId) {
    const sourceCard = document.getElementById(`question-${questionId}`);
    if (!sourceCard) return;

    const editor = sourceCard.cloneNode(true);
    editor.classList.remove('hidden');
    editor.classList.add('inline-editor');
    editor.removeAttribute('id');

    const display = pathItem.querySelector('.path-item-display');
    if (display) display.style.display = 'none';

    pathItem.appendChild(editor);
    pathItem.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
