document.addEventListener('DOMContentLoaded', function() {
    const safeJsonParse = (jsonString, fallback = {}) => {
        try {
            let data = JSON.parse(jsonString || JSON.stringify(fallback));
            if (typeof data === 'string') {
                data = JSON.parse(data);
            }
            return data;
        } catch (e) {
            console.error('Failed to parse JSON data:', e);
            return fallback;
        }
    };

    window.assessmentApp = {
        assessmentContainer: document.getElementById('assessment-container'),
        pathContainer: document.getElementById('assessment-path'),
        surveyQuestionId: safeJsonParse(document.getElementById('survey_question_id').textContent, null),
        assessmentPath: [],
        questionDataMap: safeJsonParse(document.getElementById('question_data_map').textContent, {})
    };

    const { assessmentContainer, pathContainer, surveyQuestionId, assessmentPath, questionDataMap } = window.assessmentApp;

    assessmentContainer.addEventListener('click', (e) => {
        if (e.target.closest('.multi-select-continue-btn')) {
            handleMultiSelectContinue(e, assessmentPath, pathContainer, surveyQuestionId);
        } else if (e.target.closest('.dynamic-option-action')) {
            handleDynamicSelection(e, assessmentPath, pathContainer);
        } else if (e.target.closest('.option-action')) {
            handleSelection(e, assessmentPath, pathContainer, surveyQuestionId);
        }
    });

    pathContainer.addEventListener('click', function(e) {
        if (e.target.closest('.option-action')) {
            handleSelection(e, assessmentPath, pathContainer, surveyQuestionId);
        } else {
            jumpToQuestion(e, pathContainer);
        }
    });

    let hydrated = false;
    try {
        const savedNode = document.getElementById('saved_path_data');
        const savedPathData = safeJsonParse(savedNode ? savedNode.textContent : '[]', []);

        if (Array.isArray(savedPathData) && savedPathData.length > 0) {
            hydrated = !!hydrateFromSavedResponses(
                savedPathData,
                questionDataMap,
                assessmentPath,
                pathContainer
            );
        }
    } catch (err) {
        console.error('Error during assessment hydration:', err);
    }

    if (!hydrated) {
        startAssessment(pathContainer, assessmentPath);
    }
});
