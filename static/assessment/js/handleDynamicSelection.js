function handleDynamicSelection(e, assessmentPath, pathContainer) {
  const wrapper = e.target.closest('.dynamic-survey-question-wrapper');
  if (!wrapper) return;

  const selectElement = wrapper.querySelector('.dynamic-survey-question-dropdown');
  const selectedValue = $(selectElement).val();

  if (!selectedValue || (Array.isArray(selectedValue) && selectedValue.length === 0)) {
    selectElement.style.borderColor = 'red';
    selectElement.addEventListener('change', () => { selectElement.style.borderColor = ''; }, { once: true });
    return;
  }

  const currentQuestionDiv = wrapper.closest('.question-card');
  const questionId = currentQuestionDiv.dataset.questionId;
  const questionText = currentQuestionDiv.querySelector('h2').textContent.trim();

  const nextQuestionId = Array.isArray(selectedValue)
    ? wrapper.dataset.nextQuestionAfterMultiple
    : wrapper.dataset.nextQuestion;

  let responseValue;
  let optionIds;

  if (Array.isArray(selectedValue)) {
    const selectedOptions = Array.from(selectElement.options).filter(opt => selectedValue.includes(opt.value));
    const responseTexts = selectedOptions.map(opt => opt.textContent.trim());

    responseValue = responseTexts;
    optionIds = selectedValue;

  } else {
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    if (!selectedOption || !selectedOption.value) {
        return;
    }
    responseValue = `"${selectedOption.textContent.trim()}"`;
    optionIds = selectedValue;
  }

  const reAnswerIndex = assessmentPath.findIndex(item => item.questionId === questionId);
  if (reAnswerIndex !== -1) {
    assessmentPath.splice(reAnswerIndex);
    const allPathItems = Array.from(pathContainer.children);
    for (let i = reAnswerIndex; i < allPathItems.length; i++) allPathItems[i].remove();
  }

  addPathItem(questionId, questionText, responseValue, null, !nextQuestionId, assessmentPath, pathContainer, optionIds);

  $(selectElement).val(null).trigger('change');

  if (nextQuestionId) {
    showQuestion(nextQuestionId);
  } else {
    showQuestion(null);
    document.getElementById('final-result-card').classList.remove('hidden');
  }
}
