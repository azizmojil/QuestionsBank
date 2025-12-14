(() => {
    console.log('Builder script initialized');
    const sectionTemplate = document.getElementById('section-template');
    const questionTemplate = document.getElementById('question-template');
    const matrixQuestionTemplate = document.getElementById('matrix-question-template');
    const sectionsContainer = document.getElementById('sections-container');
    const addSectionBtn = document.getElementById('add-section-btn');
    const surveyVersionSelect = document.getElementById('survey-version-select');
    const builderLocaleEl = document.getElementById('builder-locale');
    const builderLocale = builderLocaleEl ? JSON.parse(builderLocaleEl.textContent) : {};
    const untitledLabel = builderLocale.untitled || 'Untitled survey';

    if (!sectionTemplate || !questionTemplate || !matrixQuestionTemplate || !sectionsContainer) {
        console.error('Missing required templates or container');
        return;
    }

    const responseTypesEl = document.getElementById('response-types-data');
    const responseTypes = responseTypesEl ? JSON.parse(responseTypesEl.textContent) : [];
    
    const availableQuestionsDataEl = document.getElementById('available-questions-data');
    const availableQuestions = availableQuestionsDataEl ? JSON.parse(availableQuestionsDataEl.textContent) : [];

    const surveyStructuresEl = document.getElementById('survey-structures-data');
    const surveyStructures = surveyStructuresEl ? JSON.parse(surveyStructuresEl.textContent) : {};
    
    const legacyQuestionLookup = new Map();
    const codedQuestionLookup = new Map();
    availableQuestions.forEach((q) => {
        const key = `${(q.label || '').trim()}|${q.response_type || ''}`;
        const bucket = legacyQuestionLookup.get(key) || [];
        bucket.push({
            id: String(q.id),
            code: q.code || '',
            created_at: q.created_at || '',
        });
        legacyQuestionLookup.set(key, bucket);
        if (q.code) {
            codedQuestionLookup.set(q.code, {
                id: String(q.id),
                created_at: q.created_at || '',
            });
        }
    });

    function initializeTomSelect(el) {
        if (el && !el.tomselect) {
            new TomSelect(el, {
                create: false,
                sortField: {
                    field: "text",
                    direction: "asc"
                }
            });
        }
    }

    function addQuestion(sectionEl, data = null, isMatrix = false) {
        console.log('addQuestion called for section', sectionEl);
        const template = isMatrix ? matrixQuestionTemplate : questionTemplate;
        const qEl = template.content.firstElementChild.cloneNode(true);
        
        qEl.querySelectorAll('select').forEach(initializeTomSelect);

        if (isMatrix) {
            const matrixQuestionSelect = qEl.querySelector('.matrix-question-select');
            const selectedContainer = qEl.querySelector('.selected-matrix-questions');
            
            matrixQuestionSelect.addEventListener('change', (e) => {
                const selectedOption = e.target.options[e.target.selectedIndex];
                if (!selectedOption.value) return;

                const pill = document.createElement('span');
                pill.className = 'pill';
                pill.textContent = selectedOption.text;
                pill.dataset.questionId = selectedOption.value;
                
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.innerHTML = '&times;';
                removeBtn.addEventListener('click', () => pill.remove());
                pill.appendChild(removeBtn);

                selectedContainer.appendChild(pill);
                e.target.tomselect.setValue(''); // Reset dropdown
            });
        }

        qEl.querySelector('.remove-question').addEventListener('click', () => qEl.remove());

        sectionEl.querySelector('.question-list').appendChild(qEl);
    }

    function addSection(data = null) {
        console.log('addSection called');
        const sectionEl = sectionTemplate.content.firstElementChild.cloneNode(true);
        sectionEl.querySelector('.remove-section').addEventListener('click', () => sectionEl.remove());
        
        const addQuestionBtn = sectionEl.querySelector('.add-question');
        if (addQuestionBtn) {
            addQuestionBtn.addEventListener('click', (e) => {
                e.preventDefault();
                addQuestion(sectionEl);
            });
        }

        const addMatrixQuestionBtn = sectionEl.querySelector('.add-matrix-question');
        if (addMatrixQuestionBtn) {
            addMatrixQuestionBtn.addEventListener('click', (e) => {
                e.preventDefault();
                addQuestion(sectionEl, null, true);
            });
        }

        if (data) {
            sectionEl.querySelector('.section-name').value = data.title || '';
            sectionEl.querySelector('.section-description').value = data.description || '';
            (data.questions || []).forEach(q => addQuestion(sectionEl, q));
        }

        sectionsContainer.appendChild(sectionEl);
    }

    function loadSurveyVersion(versionId) {
        sectionsContainer.innerHTML = '';
        const structure = surveyStructures[versionId];
        if (structure) {
            structure.forEach(sectionData => addSection(sectionData));
        }
    }

    function collectSurvey() {
        const surveyTitle = document.getElementById('survey-title')?.value || untitledLabel;
        const sections = Array.from(sectionsContainer.querySelectorAll('.section-block')).map(sectionEl => {
            const questions = Array.from(sectionEl.querySelectorAll('.question-block')).map(qEl => {
                const isMatrix = qEl.classList.contains('matrix-question-block');
                const questionData = {
                    question_ids: Array.from(qEl.querySelectorAll('.question-select option:checked')).map(opt => opt.value),
                    response_type: qEl.querySelector('.response-type').value,
                    required: qEl.querySelector('.question-required').checked,
                };

                if (isMatrix) {
                    questionData.matrix_group_id = qEl.querySelector('.matrix-group').value;
                } else {
                    questionData.response_group_id = qEl.querySelector('.response-group').value;
                }

                return questionData;
            });
            return {
                title: sectionEl.querySelector('.section-name').value.trim(),
                description: sectionEl.querySelector('.section-description').value.trim(),
                questions,
            };
        });

        return { title: surveyTitle, sections };
    }

    addSectionBtn?.addEventListener('click', () => {
        addSection();
    });

    initializeTomSelect(surveyVersionSelect);
})();
