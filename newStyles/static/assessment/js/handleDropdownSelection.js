async function handleDropdownSelection(event, assessmentPath, pathContainer, surveyQuestionId) {
  const selectedOptionEl = event?.params?.data?.element;
  if (!selectedOptionEl || !selectedOptionEl.value) return;

  const selectEl = event.target;

  const isMultiSelect = !!selectEl.multiple || selectEl.hasAttribute('multiple');

  if (isMultiSelect) {
    const list = selectEl.closest('.multi-select-container').querySelector('.selected-options-list');
    const selectedId = selectedOptionEl.value;

    const selectedText =
      event?.params?.data?.text?.trim() ||
      selectedOptionEl.getAttribute('data-answer-text')?.trim() ||
      selectedOptionEl.textContent?.trim() ||
      '';

    const item = document.createElement('div');
    item.className = 'selected-option-item';
    item.textContent = selectedText || 'Unidentified';
    item.dataset.optionId = selectedId;
    list.appendChild(item);

    selectedOptionEl.disabled = true;

    $(selectEl).val([]).trigger('change');
    return;
  }

  const currentQuestionDiv = selectEl.closest('.question-card');
  await handleSingleSelect(selectedOptionEl, currentQuestionDiv, assessmentPath, pathContainer, surveyQuestionId);
}

async function handleSingleSelect(selectedOptionEl, currentQuestionDiv, assessmentPath, pathContainer, surveyQuestionId) {
    const questionId = currentQuestionDiv.dataset.questionId;
    const questionText = currentQuestionDiv.querySelector('h2').textContent.trim();

    const answerText = selectedOptionEl.dataset.answerText;

    const rawConfirmation = selectedOptionEl.dataset.confirmationText;
    const confirmationText =
        (typeof rawConfirmation === 'string' && rawConfirmation.trim() === '') || rawConfirmation == null
            ? null
            : rawConfirmation;

    const selectEl = currentQuestionDiv.querySelector('.single-select-dropdown');
    const nextQuestionId = selectEl.closest('.dropdown-wrapper').dataset.nextQuestion;
    const finalLabel = selectedOptionEl.dataset.label;
    const optionId = selectedOptionEl.dataset.optionId;
    let responseValue = answerText;

    const reAnswerIndex = assessmentPath.findIndex(item => item.questionId === questionId);
    if (reAnswerIndex !== -1) {
        assessmentPath.splice(reAnswerIndex);
        const allPathItems = Array.from(pathContainer.children);
        for (let i = reAnswerIndex; i < allPathItems.length; i++) {
            allPathItems[i].remove();
        }
    }

    addPathItem(questionId, questionText, responseValue, confirmationText, !nextQuestionId, assessmentPath, pathContainer, optionId);

    if (nextQuestionId) {
        showQuestion(nextQuestionId);
    } else if (finalLabel) {
        const redirected = await saveResult(finalLabel, surveyQuestionId, assessmentPath);
        if (!redirected) {
            showQuestion(null);
            document.getElementById('final-result-card').classList.remove('hidden');
        }
    }
}
