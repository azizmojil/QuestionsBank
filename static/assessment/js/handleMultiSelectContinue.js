function handleMultiSelectContinue(e, assessmentPath, pathContainer, surveyQuestionId) {
  const container = e.target.closest('.multi-select-container');
  if (!container) return;

  const select = container.querySelector('.multi-select-dropdown');
  const list = container.querySelector('.selected-options-list');
  const selectedItems = Array.from(list.querySelectorAll('.selected-option-item'));
  const selectedIds = selectedItems.map(el => el.dataset.optionId).filter(Boolean);

  if (!Array.isArray(selectedIds) || selectedIds.length === 0) {
    select.style.borderColor = 'red';
    select.addEventListener('change', () => { select.style.borderColor = ''; }, { once: true });
    return;
  }

  const answers = selectedIds.map(id => {
    const opt = Array.from(select.options).find(o => o.value === id);
    return (opt?.getAttribute('data-answer-text') || opt?.textContent || '').trim();
  }).filter(Boolean);

  const currentQuestionDiv = container.closest('.question-card');
  const questionId = currentQuestionDiv.dataset.questionId;
  const questionText = currentQuestionDiv.querySelector('h2').textContent.trim();

  const nextQuestionId =
    container.dataset.nextQuestionAfterMultiple ||
    container.dataset.nextQuestion ||
    null;

  const reAnswerIndex = assessmentPath.findIndex(step => String(step.questionId) === String(questionId));
  if (reAnswerIndex !== -1) {
    assessmentPath.splice(reAnswerIndex);
    const allPathItems = Array.from(pathContainer.children);
    for (let i = reAnswerIndex; i < allPathItems.length; i++) allPathItems[i].remove();
  }

  addPathItem(
    questionId,
    questionText,
    answers,
    !nextQuestionId,
    assessmentPath,
    pathContainer,
    selectedIds
  );

  $(select).val(null).trigger('change');

  if (nextQuestionId) {
    showQuestion(nextQuestionId);
  } else {
    showQuestion(null);
    document.getElementById('final-result-card').classList.remove('hidden');
  }
}
