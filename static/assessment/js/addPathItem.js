function addPathItem(questionId, questionText, answerData, isFinal, assessmentPath, pathContainer, optionId) {
    const finalQuestionText = questionText || (window.assessmentApp.questionDataMap[questionId]?.text || "Unknown Question");

    const normalizedOptionIds = optionId === undefined || optionId === null
        ? []
        : Array.isArray(optionId) ? optionId : [optionId];

    assessmentPath.push({
        questionId: questionId,
        question: finalQuestionText,
        answer: answerData,
        optionId: normalizedOptionIds
    });

    const pathItem = document.createElement('div');
    pathItem.className = 'path-item text-right';
    pathItem.dataset.questionId = questionId;

    const display = document.createElement('div');
    display.className = 'path-item-display';

    const questionEl = document.createElement('div');
    questionEl.className = 'question-text';
    questionEl.textContent = finalQuestionText;

    const answerEl = document.createElement('div');
    answerEl.className = 'answer-text';
    if (Array.isArray(answerData)) {
        const list = document.createElement('ul');
        list.className = 'list-disc list-inside';
        answerData.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            list.appendChild(li);
        });
        if (answerData.length === 0) {
            const empty = document.createElement('i');
            const fallbackEmpty = (window.assessmentApp && window.assessmentApp.messages && window.assessmentApp.messages.noSelection) || 'لم يتم اختيار أي إجابة';
            empty.textContent = fallbackEmpty;
            answerEl.appendChild(empty);
        } else {
            answerEl.appendChild(list);
        }
    } else if (answerData != null) {
        answerEl.textContent = answerData;
    }

    display.appendChild(questionEl);
    display.appendChild(answerEl);

    pathItem.appendChild(display);
    pathContainer.appendChild(pathItem);
}
