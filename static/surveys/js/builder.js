(() => {
    console.log('Builder script initialized');
    const sectionTemplate = document.getElementById('section-template');
    const questionTemplate = document.getElementById('question-template');
    const matrixQuestionTemplate = document.getElementById('matrix-question-template');
    const sectionsContainer = document.getElementById('sections-container');
    const addSectionBtn = document.getElementById('add-section-btn');
    const surveyVersionSelect = document.getElementById('survey-version-select');
    const bankQuestionSelect = document.getElementById('bank-question-select');
    const addBankQuestionBtn = document.getElementById('add-bank-question');
    const manualQuestionInput = document.getElementById('manual-question-text');
    const addManualQuestionBtn = document.getElementById('add-manual-question');
    const initialQuestionsEl = document.getElementById('initial-questions');
    const sendToAssessmentBtn = document.getElementById('send-to-assessment-btn');
    const assessmentLists = document.querySelectorAll('[data-kanban-list]');
    const sendToScoringBtn = document.getElementById('send-to-scoring-btn');
    const scoringListEl = document.getElementById('scoring-list');
    const markReviewCompleteBtn = document.getElementById('mark-review-complete');
    const paletteEl = document.getElementById('question-palette');
    const routingConditionsEl = document.getElementById('routing-conditions');
    const routingTargetsEl = document.getElementById('routing-targets');
    const businessConditionsEl = document.getElementById('business-conditions');
    const businessActionsEl = document.getElementById('business-actions');
    const workflowDots = {
        draft: document.getElementById('draft-count'),
        assessment: document.getElementById('assessment-count'),
        scoring: document.getElementById('scoring-count'),
        final: document.getElementById('final-count'),
    };
    const builderLocaleEl = document.getElementById('builder-locale');
    const builderLocale = builderLocaleEl ? JSON.parse(builderLocaleEl.textContent) : {};
    const untitledLabel = builderLocale.untitled || 'Untitled survey';

    if (!sectionTemplate || !questionTemplate || !matrixQuestionTemplate || !sectionsContainer) {
        console.error('Missing required templates or container');
        return;
    }

    const availableQuestionsDataEl = document.getElementById('available-questions-data');
    const availableQuestions = availableQuestionsDataEl ? JSON.parse(availableQuestionsDataEl.textContent) : [];

    const surveyStructuresEl = document.getElementById('survey-structures-data');
    const surveyStructures = surveyStructuresEl ? JSON.parse(surveyStructuresEl.textContent) : {};

    const paletteLookup = new Map();
    availableQuestions.forEach((q) => {
        paletteLookup.set(String(q.id), {
            id: String(q.id),
            label: q.label || q.code || untitledLabel,
            source: 'bank',
        });
    });

    const state = {
        initialQueue: [],
        assessment: {
            backlog: [],
            active: [],
            done: [],
        },
        scoring: [],
        routing: {
            conditions: [],
            targets: [],
        },
        business: {
            conditions: [],
            actions: [],
        },
    };

    let manualCounter = 0;
    let draggedAssessment = null;
    let draggedRuleToken = null;
    let draggedSection = null;
    let draggedQuestion = null;

    function initializeTomSelect(el) {
        if (typeof TomSelect === 'undefined') {
            if (el) {
                el.dataset.tomselectFallback = 'true';
            }
            return;
        }
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

    function findQuestionLabel(questionId) {
        const token = paletteLookup.get(String(questionId));
        return token ? token.label : untitledLabel;
    }

    function ensureToken(token) {
        if (!paletteLookup.has(token.id)) {
            paletteLookup.set(token.id, token);
        }
        renderPalette();
        syncQuestionSelectOptions(token);
    }

    function createManualId() {
        let candidate;
        do {
            manualCounter += 1;
            candidate = `manual-${Date.now()}-${manualCounter}-${Math.random().toString(16).slice(2)}`;
        } while (paletteLookup.has(candidate));
        return candidate;
    }

    function renderPalette() {
        if (!paletteEl) return;
        paletteEl.innerHTML = '';
        Array.from(paletteLookup.values()).forEach((token) => {
            const chip = document.createElement('div');
            chip.className = 'draggable-chip';
            chip.draggable = true;
            chip.dataset.tokenId = token.id;
            const labelSpan = document.createElement('span');
            labelSpan.className = 'chip-label';
            labelSpan.textContent = token.label;
            const sourceSpan = document.createElement('span');
            sourceSpan.className = 'chip-source';
            sourceSpan.textContent = token.source === 'manual' ? (builderLocale.manual || 'يدوي') : (builderLocale.bank || 'بنك');
            chip.append(labelSpan, sourceSpan);
            chip.addEventListener('dragstart', () => {
                draggedRuleToken = token;
            });
            chip.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    addRuleToken(routingConditionsEl, state.routing.conditions, token);
                }
            });
            paletteEl.appendChild(chip);
        });
    }

    function renderInitialList() {
        if (!initialQuestionsEl) return;
        initialQuestionsEl.innerHTML = '';
        state.initialQueue.forEach((item) => {
            const pill = document.createElement('span');
            pill.className = 'pill';
            pill.textContent = item.label;
            pill.draggable = true;
            pill.dataset.tokenId = item.id;
            pill.addEventListener('dragstart', () => {
                draggedRuleToken = item;
            });
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', () => {
                state.initialQueue = state.initialQueue.filter((q) => q.id !== item.id);
                renderInitialList();
                updateWorkflowCounts();
            });
            pill.appendChild(removeBtn);
            initialQuestionsEl.appendChild(pill);
        });

        if (!state.initialQueue.length) {
            const empty = document.createElement('p');
            empty.className = 'muted';
            empty.textContent = builderLocale.emptyInitial || 'لا توجد أسئلة مبدئية بعد';
            initialQuestionsEl.appendChild(empty);
        }
    }

    function updateWorkflowCounts() {
        if (workflowDots.draft) workflowDots.draft.textContent = state.initialQueue.length;
        const assessmentCount = state.assessment.backlog.length + state.assessment.active.length + state.assessment.done.length;
        if (workflowDots.assessment) workflowDots.assessment.textContent = assessmentCount;
        if (workflowDots.scoring) workflowDots.scoring.textContent = state.scoring.length;
        if (workflowDots.final) {
            const rulesCount = state.routing.conditions.length + state.routing.targets.length + state.business.conditions.length + state.business.actions.length;
            workflowDots.final.textContent = rulesCount;
        }
    }

    function createKanbanCard(item) {
        const card = document.createElement('div');
        card.className = 'kanban-card';
        card.draggable = true;
        card.dataset.tokenId = item.id;
        const strong = document.createElement('strong');
        strong.textContent = item.label;
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.textContent = item.source === 'manual' ? (builderLocale.manual || 'يدوي') : (builderLocale.bank || 'بنك');
        card.append(strong, chip);
        card.addEventListener('dragstart', (e) => {
            draggedAssessment = {
                id: item.id,
                from: e.target.closest('[data-kanban-list]')?.dataset.kanbanList,
            };
            draggedRuleToken = item;
            card.classList.add('dragging');
        });
        card.addEventListener('dragend', () => card.classList.remove('dragging'));
        return card;
    }

    function renderAssessmentBoard() {
        assessmentLists.forEach((listEl) => {
            const bucketName = listEl.dataset.kanbanList;
            const bucket = state.assessment[bucketName] || [];
            listEl.innerHTML = '';
            if (!bucket.length) {
                const empty = document.createElement('p');
                empty.className = 'muted';
                empty.textContent = builderLocale.emptyColumn || 'لا توجد عناصر في هذا العمود بعد';
                listEl.appendChild(empty);
            } else {
                bucket.forEach((item) => listEl.appendChild(createKanbanCard(item)));
            }
            const countBadge = document.querySelector(`[data-count-for="${bucketName}"]`);
            if (countBadge) {
                countBadge.textContent = bucket.length;
            }
        });
    }

    function moveAssessmentItem(id, from, to) {
        if (!state.assessment[from] || !state.assessment[to]) return;
        const idx = state.assessment[from].findIndex((item) => item.id === id);
        if (idx === -1) return;
        const [item] = state.assessment[from].splice(idx, 1);
        state.assessment[to].push(item);
        renderAssessmentBoard();
        updateWorkflowCounts();
    }

    function renderScoringList() {
        if (!scoringListEl) return;
        scoringListEl.innerHTML = '';
        if (!state.scoring.length) {
            const empty = document.createElement('p');
            empty.className = 'muted';
            empty.textContent = builderLocale.emptyScoring || 'لا توجد عناصر بانتظار التسجيل.';
            scoringListEl.appendChild(empty);
            return;
        }

        state.scoring.forEach((item) => {
            const row = document.createElement('div');
            row.className = 'scoring-item';
            const label = document.createElement('span');
            label.textContent = item.label;
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-secondary';
            button.textContent = item.reviewed ? (builderLocale.reviewed || 'مُراجع') : (builderLocale.markReviewed || 'تمت المراجعة');
            button.addEventListener('click', () => {
                item.reviewed = !item.reviewed;
                renderScoringList();
                updateWorkflowCounts();
            });
            row.append(label, button);
            scoringListEl.appendChild(row);
        });
    }

    function syncQuestionSelectOptions(token) {
        document.querySelectorAll('.question-select, .matrix-question-select').forEach((select) => {
            if (select.tomselect) {
                select.tomselect.addOption({ value: token.id, text: token.label });
            } else {
                const exists = Array.from(select.options).some((opt) => opt.value === token.id);
                if (!exists) {
                    const opt = document.createElement('option');
                    opt.value = token.id;
                    opt.textContent = token.label;
                    select.appendChild(opt);
                }
            }
        });
    }

    function addQuestion(sectionEl, data = null, isMatrix = false) {
        const template = isMatrix ? matrixQuestionTemplate : questionTemplate;
        const qEl = template.content.firstElementChild.cloneNode(true);
        qEl.draggable = true;

        qEl.querySelectorAll('select').forEach(initializeTomSelect);

        qEl.querySelectorAll('.question-select, .matrix-question-select').forEach((select) => {
            paletteLookup.forEach((token) => {
                if (select.tomselect) {
                    select.tomselect.addOption({ value: token.id, text: token.label });
                } else {
                    const exists = Array.from(select.options).some((opt) => opt.value === token.id);
                    if (!exists) {
                        const opt = document.createElement('option');
                        opt.value = token.id;
                        opt.textContent = token.label;
                        select.appendChild(opt);
                    }
                }
            });
        });

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

        if (data) {
            const questionSelect = qEl.querySelector(isMatrix ? '.matrix-question-select' : '.question-select');
            if (questionSelect && data.question_id) {
                const value = String(data.question_id);
                ensureToken({ id: value, label: findQuestionLabel(value), source: 'bank' });
                if (questionSelect.tomselect) {
                    questionSelect.tomselect.addOption({ value, text: findQuestionLabel(value) });
                    questionSelect.tomselect.setValue(value, true);
                } else {
                    questionSelect.value = value;
                }
            }

            const requiredInput = qEl.querySelector('.question-required');
            if (requiredInput) {
                requiredInput.checked = !!data.required;
            }
        }

        sectionEl.querySelector('.question-list').appendChild(qEl);
    }

    function addSection(data = null) {
        const sectionEl = sectionTemplate.content.firstElementChild.cloneNode(true);
        sectionEl.draggable = true;
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
            (data.questions || []).forEach((q) => addQuestion(sectionEl, q));
        }

        sectionsContainer.appendChild(sectionEl);
    }

    function seedInitialFromStructure(structure) {
        const seen = new Set();
        state.initialQueue = [];
        structure.forEach((sectionData) => {
            (sectionData.questions || []).forEach((question) => {
                if (question.question_id && !seen.has(question.question_id)) {
                    const qid = String(question.question_id);
                    seen.add(qid);
                    const token = paletteLookup.get(qid) || { id: qid, label: findQuestionLabel(qid), source: 'bank' };
                    ensureToken(token);
                    state.initialQueue.push(token);
                }
            });
        });
        renderInitialList();
        updateWorkflowCounts();
    }

    function loadSurveyVersion(versionId) {
        sectionsContainer.innerHTML = '';
        state.assessment = { backlog: [], active: [], done: [] };
        state.scoring = [];
        state.routing = { conditions: [], targets: [] };
        state.business = { conditions: [], actions: [] };
        const structure = surveyStructures[versionId];
        if (structure) {
            structure.forEach((sectionData) => addSection(sectionData));
            seedInitialFromStructure(structure);
            renderAssessmentBoard();
            renderScoringList();
            renderRuleBuckets();
            updateWorkflowCounts();
        }
    }

    function collectSurvey() {
        const selectedVersionText = surveyVersionSelect?.selectedIndex >= 0
            ? surveyVersionSelect.options[surveyVersionSelect.selectedIndex]?.textContent?.trim()
            : '';
        const surveyTitle = selectedVersionText || untitledLabel;
        const sections = Array.from(sectionsContainer.querySelectorAll('.section-block')).map((sectionEl) => {
            const questions = Array.from(sectionEl.querySelectorAll('.question-block')).map((qEl) => {
                const isMatrix = qEl.classList.contains('matrix-question-block');
                const questionSelect = qEl.querySelector(isMatrix ? '.matrix-question-select' : '.question-select');
                const questionIds = questionSelect ? [questionSelect.value].filter(Boolean) : [];
                const questionData = {
                    question_ids: questionIds,
                    response_type: qEl.querySelector('.response-type')?.value,
                    required: qEl.querySelector('.question-required')?.checked || false,
                };

                if (isMatrix) {
                    questionData.matrix_group_id = qEl.querySelector('.matrix-group')?.value;
                } else {
                    questionData.response_group_id = qEl.querySelector('.response-group')?.value;
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

    function setupAssessmentDrops() {
        assessmentLists.forEach((listEl) => {
            listEl.addEventListener('dragover', (e) => {
                if (draggedAssessment) {
                    e.preventDefault();
                    listEl.classList.add('drop-active');
                }
            });
            listEl.addEventListener('dragleave', () => listEl.classList.remove('drop-active'));
            listEl.addEventListener('drop', (e) => {
                e.preventDefault();
                listEl.classList.remove('drop-active');
                const targetColumn = listEl.dataset.kanbanList;
                if (draggedAssessment?.from) {
                    moveAssessmentItem(draggedAssessment.id, draggedAssessment.from, targetColumn);
                    draggedAssessment = null;
                }
            });
        });
    }

    function setupRuleDropzones() {
        const zones = [
            { el: routingConditionsEl, bucket: state.routing.conditions, placeholder: builderLocale.routingConditions || 'اسحب شروط التوجيه هنا' },
            { el: routingTargetsEl, bucket: state.routing.targets, placeholder: builderLocale.routingTargets || 'ضع الأسئلة التالية هنا' },
            { el: businessConditionsEl, bucket: state.business.conditions, placeholder: builderLocale.businessConditions || 'اسحب شروط الأعمال هنا' },
            { el: businessActionsEl, bucket: state.business.actions, placeholder: builderLocale.businessActions || 'ضع الإجراءات هنا' },
        ];

        zones.forEach(({ el, bucket, placeholder }) => {
            if (!el) return;
            el.dataset.placeholder = placeholder;
            el.classList.toggle('empty', !bucket.length);
            el.addEventListener('dragover', (e) => {
                if (draggedRuleToken) {
                    e.preventDefault();
                    el.classList.add('drop-active');
                }
            });
            el.addEventListener('dragleave', () => el.classList.remove('drop-active'));
            el.addEventListener('drop', (e) => {
                e.preventDefault();
                el.classList.remove('drop-active');
                if (draggedRuleToken) {
                    addRuleToken(el, bucket, draggedRuleToken);
                    draggedRuleToken = null;
                }
            });
        });

        renderRuleBuckets();
    }

    function addRuleToken(container, bucket, token) {
        const exists = bucket.some((item) => item.id === token.id);
        if (!exists) {
            bucket.push(token);
            renderRuleBuckets();
            updateWorkflowCounts();
        }
    }

    function renderRuleBuckets() {
        const pairs = [
            { el: routingConditionsEl, bucket: state.routing.conditions },
            { el: routingTargetsEl, bucket: state.routing.targets },
            { el: businessConditionsEl, bucket: state.business.conditions },
            { el: businessActionsEl, bucket: state.business.actions },
        ];

        pairs.forEach(({ el, bucket }) => {
            if (!el) return;
            el.innerHTML = '';
            if (!bucket.length) {
                el.classList.add('empty');
                const placeholder = document.createElement('span');
                placeholder.className = 'drop-placeholder';
                placeholder.textContent = el.dataset.placeholder || '';
                el.appendChild(placeholder);
            } else {
                el.classList.remove('empty');
            }
            bucket.forEach((token) => {
                const pill = document.createElement('span');
                pill.className = 'drop-pill';
                pill.textContent = token.label;
                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.innerHTML = '&times;';
                removeBtn.addEventListener('click', () => {
                    const idx = bucket.findIndex((item) => item.id === token.id);
                    if (idx > -1) {
                        bucket.splice(idx, 1);
                        renderRuleBuckets();
                        updateWorkflowCounts();
                    }
                });
                pill.appendChild(removeBtn);
                el.appendChild(pill);
            });
        });
    }

    function setupSectionSorting() {
        sectionsContainer.addEventListener('dragstart', (e) => {
            const section = e.target.closest('.section-block');
            const question = e.target.closest('.question-block');
            if (section) {
                draggedSection = section;
                section.classList.add('dragging');
            } else if (question) {
                draggedQuestion = question;
                question.classList.add('dragging');
            }
        });

        sectionsContainer.addEventListener('dragend', (e) => {
            e.target.classList.remove('dragging');
            draggedSection = null;
            draggedQuestion = null;
        });

        sectionsContainer.addEventListener('dragover', (e) => {
            if (draggedSection) {
                e.preventDefault();
                const targetSection = e.target.closest('.section-block');
                if (targetSection && targetSection !== draggedSection) {
                    const rect = targetSection.getBoundingClientRect();
                    const after = (e.clientY - rect.top) > rect.height / 2;
                    sectionsContainer.insertBefore(draggedSection, after ? targetSection.nextSibling : targetSection);
                }
            } else if (draggedQuestion) {
                e.preventDefault();
                const targetList = e.target.closest('.question-list');
                if (targetList) {
                    const afterElement = (() => {
                        const blocks = Array.from(targetList.querySelectorAll('.question-block:not(.dragging)'));
                        for (const el of blocks) {
                            const midpoint = el.offsetTop + el.offsetHeight / 2;
                            if (e.clientY < midpoint) {
                                return el;
                            }
                        }
                        return null;
                    })();
                    if (isDropPositionUnchanged(targetList, afterElement, draggedQuestion)) return;
                    if (afterElement) {
                        targetList.insertBefore(draggedQuestion, afterElement);
                    } else {
                        targetList.appendChild(draggedQuestion);
                    }
                }
            }
        });
    }

    function isDropPositionUnchanged(targetList, afterElement, draggedItem) {
        return targetList === draggedItem?.parentElement && afterElement === draggedItem?.nextElementSibling;
    }

    addSectionBtn?.addEventListener('click', () => {
        addSection();
    });

    addBankQuestionBtn?.addEventListener('click', () => {
        const value = bankQuestionSelect?.value;
        if (!value) return;
        const label = findQuestionLabel(value);
        const token = { id: String(value), label, source: 'bank' };
        ensureToken(token);
        state.initialQueue.push(token);
        renderInitialList();
        updateWorkflowCounts();
        if (bankQuestionSelect.tomselect) {
            bankQuestionSelect.tomselect.clear(true);
        } else {
            bankQuestionSelect.value = '';
        }
    });

    addManualQuestionBtn?.addEventListener('click', () => {
        const text = manualQuestionInput?.value?.trim();
        if (!text) return;
        const token = { id: createManualId(), label: text, source: 'manual' };
        ensureToken(token);
        state.initialQueue.push(token);
        renderInitialList();
        updateWorkflowCounts();
        manualQuestionInput.value = '';
    });

    sendToAssessmentBtn?.addEventListener('click', () => {
        state.assessment.backlog = state.assessment.backlog.concat(state.initialQueue);
        state.initialQueue = [];
        renderInitialList();
        renderAssessmentBoard();
        updateWorkflowCounts();
    });

    sendToScoringBtn?.addEventListener('click', () => {
        state.scoring.push(...state.assessment.done.map((item) => ({ ...item, reviewed: false })));
        state.assessment.done = [];
        renderAssessmentBoard();
        renderScoringList();
        updateWorkflowCounts();
    });

    markReviewCompleteBtn?.addEventListener('click', () => {
        state.scoring = state.scoring.map((item) => ({ ...item, reviewed: true }));
        renderScoringList();
        updateWorkflowCounts();
    });

    surveyVersionSelect?.addEventListener('change', (e) => {
        const versionId = e.target.value;
        if (versionId) {
            loadSurveyVersion(versionId);
        }
    });

    assessmentLists.forEach((listEl) => {
        listEl.addEventListener('click', (e) => {
            const card = e.target.closest('.kanban-card');
            if (!card) return;
            const from = listEl.dataset.kanbanList;
            const order = ['backlog', 'active', 'done'];
            const toIndex = Math.min(order.indexOf(from) + 1, order.length - 1);
            moveAssessmentItem(card.dataset.tokenId, from, order[toIndex]);
        });
    });

    initializeTomSelect(surveyVersionSelect);
    initializeTomSelect(bankQuestionSelect);

    renderPalette();
    renderInitialList();
    renderAssessmentBoard();
    renderScoringList();
    setupAssessmentDrops();
    setupRuleDropzones();
    setupSectionSorting();
})(); 
