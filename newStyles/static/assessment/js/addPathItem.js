function addPathItem(questionId, questionText, answerData, isFinal, assessmentPath, pathContainer, optionId) {
    const finalQuestionText = questionText || (window.assessmentApp.questionDataMap[questionId]?.text || "Unknown Question");

    assessmentPath.push({
        questionId: questionId,
        question: finalQuestionText,
        answer: answerData,
        optionId: Array.isArray(optionId) ? optionId : [optionId]
    });

    const pathItem = document.createElement('div');
    pathItem.className = 'path-item text-right';
    pathItem.dataset.questionId = questionId;

    let displayAnswerText;
    if (Array.isArray(answerData)) {
        if (answerData.length > 0) {
            displayAnswerText = '<ul class="list-disc list-inside">';
            answerData.forEach(item => {
                displayAnswerText += `<li>${item}</li>`;
            });
            displayAnswerText += '</ul>';
        } else {
            displayAnswerText = '<i>No selection made</i>';
        }
    } else {
        displayAnswerText = answerData;
    }

    const display = document.createElement('div');
    display.className = 'path-item-display';
    display.innerHTML = `<div class="question-text">${finalQuestionText}</div><div class="answer-text">${displayAnswerText}</div>`;

    pathItem.appendChild(display);
    pathContainer.appendChild(pathItem);
}
