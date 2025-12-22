function hydrateFromSavedResponses(savedPathData, questionDataMap, assessmentPath, pathContainer) {
    if (!Array.isArray(savedPathData) || savedPathData.length === 0) {
        return false;
    }

    pathContainer.innerHTML = '';
    assessmentPath.length = 0;

    for (const step of savedPathData) {
        const questionId = step.questionId;
        const optionId = step.optionId;
        const savedAnswer = step.answer;

        if (!questionId || typeof optionId === 'undefined') {
            console.warn('Skipping invalid step in saved path:', step);
            continue;
        }

        const currentQuestionText = questionDataMap[questionId]?.text || 'Unknown Question';
        let answerForPath;

        if (Array.isArray(optionId)) {
            const savedTexts = Array.isArray(savedAnswer) ? savedAnswer : [savedAnswer].filter(Boolean);
            answerForPath = optionId.map((id, index) =>
                (questionDataMap[questionId]?.options?.[id]) || savedTexts[index] || ''
            );
        } else {
            answerForPath = (questionDataMap[questionId]?.options?.[optionId]) || savedAnswer;
        }

        addPathItem(questionId, currentQuestionText, answerForPath, false, assessmentPath, pathContainer, optionId);

        const questionCard = document.getElementById(`question-${questionId}`);
        if (questionCard) {
            const multiSelect = questionCard.querySelector('.multi-select-dropdown');
            const singleSelect = questionCard.querySelector('.single-select-dropdown');
            const input = questionCard.querySelector('.form-input');

            if (multiSelect) {
                const valueToSet = Array.isArray(optionId) ? optionId : [optionId];
                $(multiSelect).val(valueToSet).trigger('change');
            } else if (singleSelect) {
                const valueToSet = Array.isArray(optionId) ? optionId[0] : optionId;
                $(singleSelect).val(valueToSet).trigger('change');
            } else if (input && savedAnswer) {
                input.value = savedAnswer;
            }
        }
    }

    showQuestion(null);

    return true;
}
