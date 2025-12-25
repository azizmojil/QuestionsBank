document.addEventListener('DOMContentLoaded', function () {
    const assessmentContainer = document.getElementById('assessment-container');
    const selectRequiredMessage = assessmentContainer?.dataset?.selectRequired || "Please select at least one option.";
    const assessmentLocaleEl = document.getElementById('assessment-locale');
    const assessmentLocale = assessmentLocaleEl ? JSON.parse(assessmentLocaleEl.textContent) : {
        completedTitle: "Assessment Completed",
        submitButton: "Submit"
    };
    let multiSelectStore = {};

    assessmentContainer.addEventListener('click', function (e) {
        // Handle Question Box Expansion
        const questionBox = e.target.closest('.question-box');
        if (!questionBox) return;

        // Only expand if clicking the header/collapsed area, not buttons inside
        if (questionBox.classList.contains('collapsed') && !e.target.closest('button') && !e.target.closest('.selected-answer')) {
            expandQuestion(questionBox);
            return;
        }

        // Handle Option Button Click (Single Choice)
        const optionBtn = e.target.closest('.option-btn');
        if (optionBtn) {
            handleSingleChoice(optionBtn);
            return;
        }

        // Handle Confirm Button Click (Multi Choice)
        const confirmBtn = e.target.closest('.confirm-btn');
        if (confirmBtn) {
            handleMultiChoiceContinue(confirmBtn);
            return;
        }

        // Handle Submit Assessment Button
        const submitBtn = e.target.closest('.submit-assessment-btn');
        if (submitBtn) {
            submitAssessment();
            return;
        }

        // Handle Dropdown Items
        if (e.target.classList.contains('searchable-dropdown-item')) {
            if (e.target.classList.contains('multi-select-item')) {
                handleMultiSelectDropdown(e.target);
            } else {
                handleDropdownSelect(e.target);
            }
        }
    });

    function handleSingleChoice(button) {
        const questionBox = button.closest('.question-box');
        resetSubsequentState(questionBox).then(() => {
            collapseQuestion(questionBox, [button.innerText]);
            fetchNextQuestion(questionBox.dataset.questionId, [button.dataset.optionId]);
        });
    }

    function handleMultiChoiceContinue(button) {
        const questionBox = button.closest('.question-box');
        const questionId = questionBox.dataset.questionId;
        let optionIds = [];
        let selectedTexts = [];

        if (questionBox.querySelector('.multi-select-dropdown-container')) {
            optionIds = multiSelectStore[questionId] || [];
            const tags = questionBox.querySelectorAll('.selected-item-tag');
            selectedTexts = Array.from(tags).map(tag => tag.innerText.replace('x', '').trim());
        } else {
            const selectedCheckboxes = questionBox.querySelectorAll('input[type="checkbox"]:checked');
            optionIds = Array.from(selectedCheckboxes).map(cb => cb.value);
            selectedTexts = Array.from(selectedCheckboxes).map(cb => cb.parentElement.innerText.trim());
        }

        if (optionIds.length > 0) {
            resetSubsequentState(questionBox).then(() => {
                collapseQuestion(questionBox, selectedTexts);
                fetchNextQuestion(questionId, optionIds);
            });
        } else {
            alert(selectRequiredMessage);
        }
    }

    function handleDropdownSelect(item) {
        const questionBox = item.closest('.question-box');
        resetSubsequentState(questionBox).then(() => {
            collapseQuestion(questionBox, [item.innerText]);
            fetchNextQuestion(questionBox.dataset.questionId, [item.dataset.optionId]);
        });
    }

    function handleMultiSelectDropdown(item) {
        const questionBox = item.closest('.question-box');
        const questionId = questionBox.dataset.questionId;
        const optionId = item.dataset.optionId;
        const optionText = item.dataset.optionText;

        if (!multiSelectStore[questionId]) {
            multiSelectStore[questionId] = [];
        }

        if (!multiSelectStore[questionId].includes(optionId)) {
            multiSelectStore[questionId].push(optionId);

            const selectedItemsContainer = questionBox.querySelector('.selected-items-container');
            const tag = document.createElement('span');
            tag.className = 'selected-item-tag';
            tag.innerText = optionText;

            const removeBtn = document.createElement('span');
            removeBtn.className = 'remove-tag';
            removeBtn.innerText = 'x';
            removeBtn.onclick = () => {
                const index = multiSelectStore[questionId].indexOf(optionId);
                if (index > -1) {
                    multiSelectStore[questionId].splice(index, 1);
                }
                tag.remove();
            };

            tag.appendChild(removeBtn);
            selectedItemsContainer.appendChild(tag);
        }

        const container = item.closest('.searchable-dropdown-container');
        container.querySelector('.searchable-dropdown-input').value = '';
        container.querySelector('.searchable-dropdown-list').classList.remove('show');
    }

    function collapseQuestion(questionBox, selectedTexts) {
        questionBox.classList.add('collapsed');
        const placeholder = questionBox.querySelector('.selected-answer-placeholder');

        placeholder.innerHTML = '';
        selectedTexts.forEach(text => {
            const answerDiv = document.createElement('div');
            answerDiv.className = 'selected-answer';
            answerDiv.innerText = text;
            placeholder.appendChild(answerDiv);
        });
    }

    function expandQuestion(questionBox) {
        // Just expand UI, don't rewind yet
        questionBox.classList.remove('collapsed');
        questionBox.querySelector('.selected-answer-placeholder').innerHTML = '';
        questionBox.querySelectorAll('button, input').forEach(el => el.disabled = false);
    }

    function resetSubsequentState(questionBox) {
        const questionId = questionBox.dataset.questionId;
        
        // Remove subsequent questions from DOM
        let nextSibling = questionBox.nextElementSibling;
        while (nextSibling) {
            let toRemove = nextSibling;
            nextSibling = nextSibling.nextElementSibling;
            toRemove.remove();
        }

        // Rewind server-side state
        return fetch(`/assessment/rewind/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ question_id: questionId }),
        });
    }

    function fetchNextQuestion(questionId, optionIds) {
        const url = `/assessment/next_question/`;
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ question_id: questionId, option_ids: optionIds }),
        })
        .then(response => response.status === 204 ? null : response.text())
        .then(html => {
            if (html) {
                const newQuestionContainer = document.createElement('div');
                newQuestionContainer.innerHTML = html;
                assessmentContainer.appendChild(newQuestionContainer);
                newQuestionContainer.scrollIntoView({ behavior: 'smooth' });
            } else {
                renderCompletionBox();
            }
        })
        .catch(error => console.error('Error fetching next question:', error));
    }

    function renderCompletionBox() {
        const completionBox = document.createElement('div');
        completionBox.className = 'card question-box';
        completionBox.innerHTML = `
            <h3 class="text-center">${assessmentLocale.completedTitle}</h3>
            <div class="options flex-center">
                <button class="btn btn-secondary submit-assessment-btn">${assessmentLocale.submitButton}</button>
            </div>
        `;
        assessmentContainer.appendChild(completionBox);
        completionBox.scrollIntoView({ behavior: 'smooth' });
    }

    function submitAssessment() {
        window.location.href = '/assessment/complete/';
    }

    // --- Event listeners for UI interactions ---
    assessmentContainer.addEventListener('input', e => {
        if (e.target.classList.contains('searchable-dropdown-input')) filterDropdown(e.target);
    });
    assessmentContainer.addEventListener('change', e => {
        if (e.target.type === 'checkbox') e.target.closest('.multi-choice-option').classList.toggle('selected', e.target.checked);
    });
    assessmentContainer.addEventListener('focus', e => {
        if (e.target.classList.contains('searchable-dropdown-input')) e.target.nextElementSibling.classList.add('show');
    }, true);
    document.addEventListener('click', e => {
        document.querySelectorAll('.searchable-dropdown-list.show').forEach(dropdown => {
            if (!dropdown.parentElement.contains(e.target)) dropdown.classList.remove('show');
        });
    });

    function filterDropdown(input) {
        const filter = input.value.toUpperCase();
        const items = input.nextElementSibling.getElementsByClassName('searchable-dropdown-item');
        for (let i = 0; i < items.length; i++) {
            items[i].style.display = items[i].innerText.toUpperCase().indexOf(filter) > -1 ? "" : "none";
        }
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
});
