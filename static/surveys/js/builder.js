(() => {
    const sectionTemplate = document.getElementById('section-template');
    const questionTemplate = document.getElementById('question-template');
    const sectionsContainer = document.getElementById('sections-container');
    const addSectionBtn = document.getElementById('add-section-btn');
    const loadSampleBtn = document.getElementById('load-sample-btn');

    if (!sectionTemplate || !questionTemplate || !sectionsContainer) {
        return;
    }

    const responseTypes = JSON.parse(document.getElementById('response-types-data').textContent);
    const sampleSections = JSON.parse(document.getElementById('sample-sections-data').textContent);

    function addOptionPill(listEl, text) {
        if (!text.trim()) return;
        const pill = document.createElement('span');
        pill.className = 'pill option-pill';
        pill.dataset.value = text.trim();
        pill.innerHTML = `${text.trim()} <button type="button" aria-label="Remove option">&times;</button>`;
        pill.querySelector('button').addEventListener('click', () => pill.remove());
        listEl.appendChild(pill);
    }

    function toggleEditors(questionEl, typeValue) {
        const optionEditor = questionEl.querySelector('.option-editor');
        const matrixEditor = questionEl.querySelector('.matrix-editor');
        const typeMeta = responseTypes.find(rt => rt.value === typeValue);
        const supportsOptions = typeMeta?.supports_options;
        const supportsMatrix = typeMeta?.supports_matrix;

        optionEditor.classList.toggle('hidden', !supportsOptions);
        matrixEditor.classList.toggle('hidden', !supportsMatrix);

        if (typeValue === 'BINARY') {
            const listEl = questionEl.querySelector('.pill-list');
            if (listEl && !listEl.children.length) {
                ['Yes', 'No'].forEach(opt => addOptionPill(listEl, opt));
            }
        }
    }

    function addQuestion(sectionEl, data = null) {
        const qEl = questionTemplate.content.firstElementChild.cloneNode(true);
        const select = qEl.querySelector('.response-type');
        const optionsList = qEl.querySelector('.pill-list');

        select.addEventListener('change', (e) => toggleEditors(qEl, e.target.value));

        qEl.querySelector('.remove-question').addEventListener('click', () => qEl.remove());
        qEl.querySelector('.add-option').addEventListener('click', () => {
            const optionInput = qEl.querySelector('.option-input');
            addOptionPill(optionsList, optionInput.value);
            optionInput.value = '';
        });

        if (data) {
            qEl.querySelector('.question-text').value = data.text || '';
            qEl.querySelector('.question-required').checked = Boolean(data.required);
            if (data.response_type) {
                select.value = data.response_type;
            }
            (data.options || []).forEach(opt => addOptionPill(optionsList, opt));
            if (data.matrix_rows) {
                qEl.querySelector('.matrix-rows').value = data.matrix_rows.join('\n');
            }
            if (data.matrix_columns) {
                qEl.querySelector('.matrix-columns').value = data.matrix_columns.join('\n');
            }
        }

        toggleEditors(qEl, select.value);
        sectionEl.querySelector('.question-list').appendChild(qEl);
    }

    function addSection(data = null) {
        const sectionEl = sectionTemplate.content.firstElementChild.cloneNode(true);
        const removeBtn = sectionEl.querySelector('.remove-section');
        removeBtn.addEventListener('click', () => sectionEl.remove());

        if (data) {
            sectionEl.querySelector('.section-name').value = data.title || '';
            sectionEl.querySelector('.section-description').value = data.description || '';
            (data.questions || []).forEach(q => addQuestion(sectionEl, q));
        }

        sectionEl.querySelector('.add-question').addEventListener('click', () => addQuestion(sectionEl));
        sectionsContainer.appendChild(sectionEl);
    }

    function collectSurvey() {
        const surveyTitle = document.getElementById('survey-title')?.value || 'Untitled survey';
        const sections = Array.from(sectionsContainer.querySelectorAll('.section-block')).map(sectionEl => {
            const questions = Array.from(sectionEl.querySelectorAll('.question-block')).map(qEl => {
                return {
                    text: qEl.querySelector('.question-text').value.trim(),
                    response_type: qEl.querySelector('.response-type').value,
                    required: qEl.querySelector('.question-required').checked,
                    options: Array.from(qEl.querySelectorAll('.option-pill')).map(p => p.dataset.value),
                    matrix_rows: qEl.querySelector('.matrix-rows')?.value.split('\n').filter(Boolean) || [],
                    matrix_columns: qEl.querySelector('.matrix-columns')?.value.split('\n').filter(Boolean) || [],
                };
            });
            return {
                title: sectionEl.querySelector('.section-name').value.trim(),
                description: sectionEl.querySelector('.section-description').value.trim(),
                questions,
            };
        });

        return { title: surveyTitle, sections };
    }

    function loadSample() {
        sectionsContainer.innerHTML = '';
        sampleSections.forEach(section => addSection(section));
    }

    addSectionBtn?.addEventListener('click', () => {
        addSection();
    });

    loadSampleBtn?.addEventListener('click', loadSample);

    // Start with the provided sample blueprint
    loadSample();
})(); 
