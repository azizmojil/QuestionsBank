async function handleSelection(event, assessmentPath, pathContainer, surveyQuestionId) {
  event.preventDefault();
  const target = event.target;

  const optionWrapper = target.closest('.option-wrapper');
  if (!optionWrapper) return;

  const currentQuestionDiv = optionWrapper.closest('.question-card');
  const questionId = currentQuestionDiv.dataset.questionId;
  const questionText = currentQuestionDiv.querySelector('h2').textContent.trim();

  const optionId = optionWrapper.dataset.optionId;
  const nextQuestionId = optionWrapper.dataset.nextQuestion;
  const finalLabel = optionWrapper.dataset.label;
  const answerText = optionWrapper.dataset.answerText;

  let responseValue = answerText;

  const form = target.closest('form');
  if (form) {
    const input = form.querySelector('input[name="response"]');

    if (!input || !input.value.trim()) {
      if (input) input.focus();
      return;
    }

    if (input.type === 'url') {
      if (typeof input.checkValidity === 'function' && !input.checkValidity()) {
        try { input.reportValidity?.(); } catch (_) {}
        input.focus();
        return;
      }
      try {
        new URL(input.value.trim());
      } catch {
        try { input.reportValidity?.(); } catch (_) {}
        input.focus();
        return;
      }
    }

    responseValue = input.value.trim();
  }

  const reAnswerIndex = assessmentPath.findIndex(item => item.questionId === questionId);
  if (reAnswerIndex !== -1) {
    assessmentPath.splice(reAnswerIndex);
    const allPathItems = Array.from(pathContainer.children);
    for (let i = reAnswerIndex; i < allPathItems.length; i++) {
      allPathItems[i].remove();
    }
  }

  if (nextQuestionId) {
    addPathItem(
      questionId,
      questionText,
      responseValue,
      false,
      assessmentPath,
      pathContainer,
      optionId
    );
    showQuestion(nextQuestionId);
    return;
  }

  if (!nextQuestionId && !finalLabel) {
    console.error(`Path configuration error: Option ID ${optionId} on Question ID ${questionId} has no next question and no final label.`);
    return;
  }

  addPathItem(
    questionId,
    questionText,
    responseValue,
    true,
    assessmentPath,
    pathContainer,
    optionId
  );

  const success = await saveResult(finalLabel, surveyQuestionId, assessmentPath);

  if (!success) {
    assessmentPath.pop();
    const pathItemToRemove = pathContainer.querySelector(`.path-item[data-question-id="${questionId}"]`);
    if (pathItemToRemove) {
      pathItemToRemove.remove();
    }
    showQuestion(questionId);
    const input = currentQuestionDiv.querySelector('input[name="response"]');
    if (input) { try { input.focus(); } catch (_) {} }
    return;
  }
}
