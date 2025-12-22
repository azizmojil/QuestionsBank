function jumpToQuestion(e, pathContainer) {
    if (e.target.closest('.inline-editor')) {
        return;
    }

    const pathItem = e.target.closest('.path-item');
    if (!pathItem || pathItem.classList.contains('is-final')) return;

    const editorIsOpenForThisItem = pathItem.querySelector('.question-card.inline-editor');

    if (editorIsOpenForThisItem) {
        const display = pathItem.querySelector('.path-item-display');
        if (display) display.style.display = '';
        editorIsOpenForThisItem.remove();
        return;
    }

    const anyOpenEditor = pathContainer.querySelector('.question-card.inline-editor');
    if (anyOpenEditor) {
        const host = anyOpenEditor.closest('.path-item');
        if (host) {
            const disp = host.querySelector('.path-item-display');
            if (disp) disp.style.display = '';
        }
        anyOpenEditor.remove();
    }

    const questionIdToJumpTo = pathItem.dataset.questionId;
    renderInlineEditor(pathItem, questionIdToJumpTo);
}
