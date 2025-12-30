(() => {
    console.log('Builder Initial script initialized');
    const surveyVersionSelect = document.getElementById('survey-version-select');
    const bankQuestionSelect = document.getElementById('bank-question-select');
    const manualQuestionInput = document.getElementById('manual-question-text');
    const initialQuestionsBody = document.getElementById('initial-questions-body');
    const sendToAssessmentBtn = document.getElementById('send-to-assessment-btn');
    const builderLocaleEl = document.getElementById('builder-locale');
    const builderLocale = builderLocaleEl ? JSON.parse(builderLocaleEl.textContent) : {};
    const untitledLabel = builderLocale.untitled || 'Untitled survey';

    // Modal elements
    const confirmationModal = document.getElementById('confirmation-modal');
    const cancelSubmitBtn = document.getElementById('cancel-submit');
    const confirmSubmitBtn = document.getElementById('confirm-submit');
    
    const successModal = document.getElementById('success-modal');
    const goToAssessmentBtn = document.getElementById('go-to-assessment-btn');

    const availableQuestionsDataEl = document.getElementById('available-questions-data');
    const availableQuestions = availableQuestionsDataEl ? JSON.parse(availableQuestionsDataEl.textContent) : [];

    const surveyStructuresEl = document.getElementById('survey-structures-data');
    const surveyStructures = surveyStructuresEl ? JSON.parse(surveyStructuresEl.textContent) : {};

    const paletteLookup = new Map();
    availableQuestions.forEach((q) => {
        paletteLookup.set(String(q.id), {
            id: String(q.id),
            label_ar: q.label_ar,
            label_en: q.label_en,
            label: q.label, // Fallback
            source: 'bank',
        });
    });

    const state = {
        initialQueue: [],
    };

    let manualCounter = 0;

    // --- State Persistence ---
    const storageKey = 'initialBuilderState';

    function saveState() {
        const dataToSave = {
            version: surveyVersionSelect.value,
            queue: state.initialQueue,
        };
        sessionStorage.setItem(storageKey, JSON.stringify(dataToSave));
    }

    function restoreState() {
        const savedData = sessionStorage.getItem(storageKey);
        if (savedData) {
            try {
                const parsed = JSON.parse(savedData);
                if (parsed.version) {
                    surveyVersionSelect.value = parsed.version;
                }
                if (parsed.queue && Array.isArray(parsed.queue)) {
                    state.initialQueue = parsed.queue;
                }
            } catch (e) {
                console.error("Failed to parse saved state:", e);
            }
            sessionStorage.removeItem(storageKey);
        }
    }

    window.addEventListener('beforeunload', saveState);
    // --- End State Persistence ---

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

    function getQuestionLabel(questionId) {
        const token = paletteLookup.get(String(questionId));
        if (!token) return untitledLabel;
        const currentLang = document.documentElement.lang.slice(0, 2);
        const label = currentLang === 'ar' ? token.label_ar : token.label_en;
        return label || token.label;
    }

    function ensureToken(token) {
        if (!paletteLookup.has(token.id)) {
            paletteLookup.set(token.id, token);
        }
    }

    function createManualId() {
        let candidate;
        do {
            manualCounter += 1;
            candidate = `manual-${Date.now()}-${manualCounter}-${Math.random().toString(16).slice(2)}`;
        } while (paletteLookup.has(candidate));
        return candidate;
    }

    function renderInitialList() {
        if (!initialQuestionsBody) return;
        initialQuestionsBody.innerHTML = '';
        state.initialQueue.forEach((item) => {
            const row = document.createElement('tr');
            row.className = 'table-row';
            
            const questionCell = document.createElement('td');
            questionCell.textContent = item.source === 'bank' ? getQuestionLabel(item.id) : item.label;
            
            const sourceCell = document.createElement('td');
            sourceCell.textContent = item.source === 'bank' ? 'بنك الأسئلة' : 'إدخال يدوي';
            
            const actionCell = document.createElement('td');
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn btn-secondary';
            removeBtn.textContent = 'حذف';
            removeBtn.addEventListener('click', () => {
                state.initialQueue = state.initialQueue.filter((q) => q.id !== item.id);
                renderInitialList();

                // Add back to dropdown if it is a valid bank question
                if (paletteLookup.has(item.id) && item.source === 'bank') {
                     if (bankQuestionSelect.tomselect) {
                        bankQuestionSelect.tomselect.addOption({ value: item.id, text: getQuestionLabel(item.id) });
                        bankQuestionSelect.tomselect.refreshOptions(false);
                    } else {
                        const opt = document.createElement('option');
                        opt.value = item.id;
                        opt.textContent = getQuestionLabel(item.id);
                        bankQuestionSelect.appendChild(opt);
                    }
                }
            });
            actionCell.appendChild(removeBtn);
            
            row.append(questionCell, sourceCell, actionCell);
            initialQuestionsBody.appendChild(row);
        });

        if (!state.initialQueue.length) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 3;
            cell.className = 'text-center';
            cell.textContent = 'لا توجد أسئلة مبدئية بعد';
            row.appendChild(cell);
            initialQuestionsBody.appendChild(row);
        }
    }

    function filterAvailableQuestions() {
        state.initialQueue.forEach(item => {
            if (item.source === 'bank') {
                if (bankQuestionSelect.tomselect) {
                    bankQuestionSelect.tomselect.removeOption(item.id);
                } else {
                    const option = bankQuestionSelect.querySelector(`option[value="${item.id}"]`);
                    if (option) option.remove();
                }
            }
        });
        if (bankQuestionSelect.tomselect) {
            bankQuestionSelect.tomselect.refreshOptions(false);
        }
    }

    function seedInitialFromStructure(structure) {
        const seen = new Set();
        state.initialQueue = [];
        structure.forEach((sectionData) => {
            (sectionData.questions || []).forEach((question) => {
                if (question.question_id && !seen.has(question.question_id)) {
                    const qid = String(question.question_id);
                    seen.add(qid);
                    const token = paletteLookup.get(qid) || { id: qid, label: getQuestionLabel(qid), source: 'bank' };
                    ensureToken(token);
                    state.initialQueue.push(token);
                }
            });
        });
        renderInitialList();
        filterAvailableQuestions();
    }

    function loadSurveyVersion(versionId) {
        const structure = surveyStructures[versionId];
        if (structure) {
            seedInitialFromStructure(structure);
        }
        updateInputState();
    }

    function updateInputState() {
        const versionSelected = !!surveyVersionSelect.value;
        if (bankQuestionSelect.tomselect) {
            if (versionSelected) {
                bankQuestionSelect.tomselect.enable();
            } else {
                bankQuestionSelect.tomselect.disable();
            }
        } else {
            bankQuestionSelect.disabled = !versionSelected;
        }
        
        manualQuestionInput.disabled = !versionSelected;
    }

    bankQuestionSelect?.addEventListener('change', (e) => {
        const value = e.target.value;
        if (!value) return;
        
        // Prevent duplicates
        if (state.initialQueue.some(q => q.id === String(value))) {
             if (bankQuestionSelect.tomselect) {
                bankQuestionSelect.tomselect.clear(true);
                bankQuestionSelect.tomselect.removeOption(value);
            }
            return;
        }

        const label = getQuestionLabel(value);
        const token = { id: String(value), label, source: 'bank' };
        ensureToken(token);
        state.initialQueue.push(token);
        renderInitialList();

        // Remove from dropdown
        if (bankQuestionSelect.tomselect) {
            bankQuestionSelect.tomselect.clear(true);
            bankQuestionSelect.tomselect.removeOption(value);
        } else {
            bankQuestionSelect.value = '';
            const option = bankQuestionSelect.querySelector(`option[value="${value}"]`);
            if (option) option.remove();
        }
    });

    manualQuestionInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission if inside a form
            const text = manualQuestionInput.value.trim();
            if (!text) return;
            const token = { id: createManualId(), label: text, source: 'manual' };
            ensureToken(token);
            state.initialQueue.push(token);
            renderInitialList();
            manualQuestionInput.value = '';
        }
    });

    // Modal Logic
    function showModal(modal) {
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
    }

    function hideModal(modal) {
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
    }

    sendToAssessmentBtn?.addEventListener('click', () => {
        const versionId = surveyVersionSelect.value;
        if (!versionId) {
            alert('Please select a survey version.');
            return;
        }
        showModal(confirmationModal);
    });

    cancelSubmitBtn?.addEventListener('click', () => hideModal(confirmationModal));

    confirmSubmitBtn?.addEventListener('click', () => {
        const versionId = surveyVersionSelect.value;
        const payload = {
            version_id: versionId,
            questions: state.initialQueue.map(q => ({
                id: q.id,
                label: q.label,
                source: q.source
            }))
        };

        fetch('/surveys/builder/initial/submit/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            hideModal(confirmationModal);
            if (data.status === 'success') {
                showModal(successModal);
            } else {
                alert('Error submitting questions: ' + data.message);
            }
        })
        .catch(error => {
            hideModal(confirmationModal);
            console.error('Error:', error);
            alert('An error occurred.');
        });
    });
    
    goToAssessmentBtn?.addEventListener('click', () => {
        const versionId = surveyVersionSelect.value;
        if (versionId) {
            window.location.href = `/assessment/version/${versionId}/`;
        }
    });

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

    surveyVersionSelect?.addEventListener('change', (e) => {
        const versionId = e.target.value;
        if (versionId) {
            loadSurveyVersion(versionId);
        } else {
            updateInputState();
        }
    });

    // --- Initial Load ---
    restoreState();
    initializeTomSelect(surveyVersionSelect);
    initializeTomSelect(bankQuestionSelect);
    renderInitialList();
    filterAvailableQuestions(); // Ensure restored questions are removed from dropdown
    updateInputState();
})();
