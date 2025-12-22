function showQuestion(questionId) {
  document.querySelectorAll('.question-card').forEach(q => q.classList.add('hidden'));
  const finalCard = document.getElementById('final-result-card');
  if (finalCard) finalCard.classList.add('hidden');

  if (!questionId) {
    document.querySelectorAll('.section-title-box-instance').forEach(el => el.remove());
    return;
  }

  const questionToShow = document.getElementById(`question-${questionId}`);
  if (!questionToShow) return;

  const isStarter   = questionToShow.dataset.isSectionStarter === 'true';
  const sectionName = (questionToShow.dataset.sectionName || '').trim();

  let scrollTarget = questionToShow;

  const optionType = questionToShow.dataset.optionType;
  if (optionType === 'DYNAMIC_FROM_PREVIOUS_MULTI_SELECT') {
    const sourceQuestionId = questionToShow.dataset.dynamicSourceId;
    const dynamicWrapper = questionToShow.querySelector('.dynamic-from-previous-wrapper');

    if (sourceQuestionId && dynamicWrapper) {
      dynamicWrapper.innerHTML = '';

      const sourceStep = window.assessmentApp.assessmentPath.find(
        step => String(step.questionId) === String(sourceQuestionId)
      );

      const sourceAnswers = sourceStep ? (Array.isArray(sourceStep.answer) ? sourceStep.answer : []) : [];

      if (sourceAnswers.length > 0) {
        sourceAnswers.forEach(answerText => {
          if (!answerText) return;

          const newOption = document.createElement('div');
          newOption.className = 'option-wrapper';
          newOption.dataset.nextQuestion = dynamicWrapper.dataset.nextQuestion || '';
          newOption.dataset.answerText = answerText;

          const link = document.createElement('a');
          link.href = '#';
          link.className = 'option-action option-link text-right';
          link.textContent = answerText;

          newOption.appendChild(link);
          dynamicWrapper.appendChild(newOption);
        });
      }
    }
  }

  if (isStarter && sectionName) {
    document.querySelectorAll('.section-title-box-instance').forEach(el => el.remove());

    const template = document.getElementById('section-title-template');
    if (template && template.firstElementChild) {
      const newTitleBox = template.firstElementChild.cloneNode(true);
      newTitleBox.classList.add('section-title-box-instance');
      newTitleBox.dataset.sectionName = sectionName;

      const h3 = newTitleBox.querySelector('h3');
      if (h3) h3.textContent = sectionName;

      questionToShow.parentNode.insertBefore(newTitleBox, questionToShow);

      scrollTarget = newTitleBox;
    }
  }

  questionToShow.classList.remove('hidden');

  requestAnimationFrame(() => {
    const headerOffset = 96;
    const rect = scrollTarget.getBoundingClientRect();
    const y = rect.top + window.scrollY - headerOffset;
    window.scrollTo({ top: y, behavior: 'smooth' });
  });
}
