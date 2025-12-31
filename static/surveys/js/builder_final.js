(() => {
    const versionSelect = document.getElementById('survey-version-select');
    const addSectionBtn = document.getElementById('add-section-btn');
    const saveBtn = document.getElementById('save-final-btn');
    const sectionsContainer = document.getElementById('sections-container');
    const statusBox = document.getElementById('save-status');

    const localeEl = document.getElementById('builder-locale');
    const locale = localeEl ? JSON.parse(localeEl.textContent) : {};
    const configEl = document.getElementById('builder-config');
    const submitUrl = (configEl && configEl.dataset.submitUrl) || '/surveys/builder/final/submit/';

    const availableQuestionsEl = document.getElementById('available-questions-data');
    const responseTypesEl = document.getElementById('response-types-data');
    const responseGroupsEl = document.getElementById('response-groups-data');
    const matrixGroupsEl = document.getElementById('matrix-groups-data');
    const surveyStructuresEl = document.getElementById('survey-structures-data');

    const availableQuestions = availableQuestionsEl ? JSON.parse(availableQuestionsEl.textContent) : [];
    const responseTypes = responseTypesEl ? JSON.parse(responseTypesEl.textContent) : [];
    const responseGroups = responseGroupsEl ? JSON.parse(responseGroupsEl.textContent) : [];
    const matrixGroups = matrixGroupsEl ? JSON.parse(matrixGroupsEl.textContent) : [];
    const surveyStructures = surveyStructuresEl ? JSON.parse(surveyStructuresEl.textContent) : {};

    const paletteLookup = new Map();
    availableQuestions.forEach(q => paletteLookup.set(String(q.id), { ...q, id: String(q.id) }));

    const state = { sections: [] };

    function setStatus(message, tone = 'info') {
        if (!statusBox) return;
        statusBox.textContent = message || '';
        statusBox.className = 'save-status';
        if (message) {
            statusBox.classList.add('visible');
            if (tone === 'error') {
                statusBox.classList.add('is-error');
            } else if (tone === 'success') {
                statusBox.classList.add('is-success');
            }
        }
    }

    function getQuestionLabel(questionId, fallback) {
        if (!questionId) return fallback || locale.manual_placeholder || '';
        const token = paletteLookup.get(String(questionId));
        return token ? token.label : (fallback || locale.manual_placeholder || '');
    }

    function createEmptySection() {
        return {
            title: locale.untitled || 'Section',
            description: '',
            questions: [],
        };
    }

    function normalizeStructure(structure = []) {
        if (!structure.length) return [createEmptySection()];
        return structure.map((section) => ({
            id: section.id || null,
            title: section.title || locale.untitled || 'Section',
            description: section.description || '',
            questions: (section.questions || []).map((q) => ({
                id: q.question_id || q.id || null,
                label: q.label || getQuestionLabel(q.question_id || q.id),
                response_group_id: q.response_group_id || null,
                response_type_id: q.response_type_id || null,
                matrix_item_group_id: q.matrix_item_group_id || null,
                is_required: !!q.required,
                is_matrix: !!q.is_matrix,
                source: q.source || 'bank',
            })),
        }));
    }

    function buildSelect(options, value, placeholder) {
        const select = document.createElement('select');
        const empty = document.createElement('option');
        empty.value = '';
        empty.textContent = placeholder || '—';
        select.appendChild(empty);

        options.forEach((opt) => {
            const option = document.createElement('option');
            option.value = opt.value ?? opt.id;
            option.textContent = opt.label || opt.name || opt.display || option.value;
            if (String(option.value) === String(value)) {
                option.selected = true;
            }
            select.appendChild(option);
        });
        return select;
    }

    function renderQuestionRows(section, container) {
        container.innerHTML = '';
        if (!section.questions.length) {
            const empty = document.createElement('div');
            empty.className = 'muted';
            empty.textContent = locale.no_questions || '';
            container.appendChild(empty);
            return;
        }

        section.questions.forEach((question, idx) => {
            const row = document.createElement('div');
            row.className = 'question-row';

            const title = document.createElement('div');
            title.textContent = question.label || getQuestionLabel(question.id);
            row.appendChild(title);

            const meta = document.createElement('div');
            meta.className = 'question-row__meta';

            const responseTypeSelect = buildSelect(responseTypes, question.response_type_id, locale.response_type || '');
            responseTypeSelect.addEventListener('change', (e) => {
                question.response_type_id = e.target.value || null;
            });

            const responseGroupSelect = buildSelect(responseGroups, question.response_group_id, locale.response_group || '');
            responseGroupSelect.addEventListener('change', (e) => {
                question.response_group_id = e.target.value || null;
            });

            const matrixGroupSelect = buildSelect(matrixGroups, question.matrix_item_group_id, locale.matrix_label || '');
            matrixGroupSelect.addEventListener('change', (e) => {
                question.matrix_item_group_id = e.target.value || null;
            });

            const requiredWrap = document.createElement('label');
            requiredWrap.className = 'question-row__controls';
            const requiredCheckbox = document.createElement('input');
            requiredCheckbox.type = 'checkbox';
            requiredCheckbox.checked = !!question.is_required;
            requiredCheckbox.addEventListener('change', (e) => {
                question.is_required = !!e.target.checked;
            });
            requiredWrap.appendChild(requiredCheckbox);
            requiredWrap.append(locale.required_label || 'Required');

            const matrixWrap = document.createElement('label');
            matrixWrap.className = 'question-row__controls';
            const matrixCheckbox = document.createElement('input');
            matrixCheckbox.type = 'checkbox';
            matrixCheckbox.checked = !!question.is_matrix;
            matrixCheckbox.addEventListener('change', (e) => {
                question.is_matrix = !!e.target.checked;
            });
            matrixWrap.appendChild(matrixCheckbox);
            matrixWrap.append(locale.matrix_label || 'Matrix');

            meta.append(responseTypeSelect, responseGroupSelect, matrixGroupSelect, requiredWrap, matrixWrap);
            row.appendChild(meta);

            const controls = document.createElement('div');
            controls.className = 'question-row__controls';
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-secondary';
            removeBtn.textContent = locale.remove || 'Remove';
            removeBtn.addEventListener('click', () => {
                section.questions.splice(idx, 1);
                renderSections();
            });
            controls.appendChild(removeBtn);
            row.appendChild(controls);

            container.appendChild(row);
        });
    }

    function buildAddQuestionBar(section) {
        const bar = document.createElement('div');
        bar.className = 'add-question-bar';

        const questionSelect = buildSelect(availableQuestions.map((q) => ({ value: q.id, label: q.label })), '', locale.add_question);
        const manualInput = document.createElement('input');
        manualInput.type = 'text';
        manualInput.placeholder = locale.manual_placeholder || '';

        const responseTypeSelect = buildSelect(responseTypes, '', locale.response_type || '');
        const responseGroupSelect = buildSelect(responseGroups, '', locale.response_group || '');
        const matrixGroupSelect = buildSelect(matrixGroups, '', locale.matrix_label || '');

        const requiredLabel = document.createElement('label');
        const requiredCheckbox = document.createElement('input');
        requiredCheckbox.type = 'checkbox';
        requiredCheckbox.checked = false;
        requiredLabel.append(requiredCheckbox, document.createTextNode(` ${locale.required_label || ''}`));

        const matrixLabel = document.createElement('label');
        const matrixCheckbox = document.createElement('input');
        matrixCheckbox.type = 'checkbox';
        matrixCheckbox.checked = false;
        matrixLabel.append(matrixCheckbox, document.createTextNode(` ${locale.matrix_label || ''}`));

        const addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.className = 'btn btn-primary';
        addBtn.textContent = locale.add_question || 'Add';

        addBtn.addEventListener('click', () => {
            const selectedId = questionSelect.value;
            const manualText = manualInput.value.trim();
            if (!selectedId && !manualText) {
                setStatus(locale.add_question || 'Add a question first', 'error');
                return;
            }

            const question = {
                id: selectedId || null,
                label: selectedId ? getQuestionLabel(selectedId) : manualText,
                response_type_id: responseTypeSelect.value || null,
                response_group_id: responseGroupSelect.value || null,
                matrix_item_group_id: matrixGroupSelect.value || null,
                is_required: !!requiredCheckbox.checked,
                is_matrix: !!matrixCheckbox.checked,
                source: selectedId ? 'bank' : 'manual',
            };

            section.questions.push(question);
            setStatus('');
            renderSections();
        });

        bar.append(questionSelect, manualInput, responseTypeSelect, responseGroupSelect, matrixGroupSelect, requiredLabel, matrixLabel, addBtn);
        return bar;
    }

    function renderSections() {
        sectionsContainer.innerHTML = '';
        if (!state.sections.length) {
            const empty = document.createElement('div');
            empty.className = 'muted';
            empty.textContent = locale.no_sections || '';
            sectionsContainer.appendChild(empty);
            return;
        }

        state.sections.forEach((section, sectionIndex) => {
            const card = document.createElement('div');
            card.className = 'section-card';

            const header = document.createElement('div');
            header.className = 'section-card__header';

            const titleInput = document.createElement('input');
            titleInput.type = 'text';
            titleInput.value = section.title || '';
            titleInput.placeholder = locale.untitled || '';
            titleInput.addEventListener('input', (e) => {
                section.title = e.target.value;
            });

            const descInput = document.createElement('textarea');
            descInput.rows = 2;
            descInput.value = section.description || '';
            descInput.placeholder = locale.describe_section || '';
            descInput.addEventListener('input', (e) => {
                section.description = e.target.value;
            });

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-secondary';
            removeBtn.textContent = locale.remove_section || '×';
            removeBtn.addEventListener('click', () => {
                state.sections.splice(sectionIndex, 1);
                renderSections();
            });

            header.append(titleInput, descInput, removeBtn);

            const body = document.createElement('div');
            body.className = 'section-card__body';
            const questionsWrapper = document.createElement('div');
            renderQuestionRows(section, questionsWrapper);
            body.appendChild(questionsWrapper);
            body.appendChild(buildAddQuestionBar(section));

            card.append(header, body);
            sectionsContainer.appendChild(card);
        });
    }

    function loadVersion(versionId) {
        if (!versionId) {
            state.sections = [createEmptySection()];
            renderSections();
            return;
        }
        const structure = surveyStructures[versionId] || [];
        state.sections = normalizeStructure(structure);
        renderSections();
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function saveStructure() {
        const versionId = versionSelect.value;
        if (!versionId) {
            setStatus(locale.error || 'Select a survey version first.', 'error');
            return;
        }

        const payload = {
            version_id: versionId,
            sections: state.sections.map((section) => ({
                title: section.title,
                description: section.description,
                questions: section.questions.map((q) => ({
                    id: q.id,
                    label: q.label,
                    response_group_id: q.response_group_id || null,
                    response_type_id: q.response_type_id || null,
                    matrix_item_group_id: q.matrix_item_group_id || null,
                    is_required: !!q.is_required,
                    is_matrix: !!q.is_matrix,
                    source: q.source || 'bank',
                })),
            })),
        };

        fetch(submitUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(payload),
        })
            .then((res) => {
                if (!res.ok) return res.json().then((data) => Promise.reject(data));
                return res.json();
            })
            .then(() => {
                setStatus(locale.saved || 'Saved', 'success');
            })
            .catch((err) => {
                const message = err && err.message ? err.message : (locale.error || 'Error');
                setStatus(message, 'error');
            });
    }

    addSectionBtn?.addEventListener('click', () => {
        state.sections.push(createEmptySection());
        renderSections();
    });

    saveBtn?.addEventListener('click', saveStructure);
    versionSelect?.addEventListener('change', (e) => loadVersion(e.target.value));

    // Initial render
    renderSections();
})();
