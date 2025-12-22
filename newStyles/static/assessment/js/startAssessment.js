function startAssessment(pathContainer, assessmentPath) {
    pathContainer.innerHTML = '';
    assessmentPath.length = 0;
    const firstQuestion = document.querySelector('.question-card');
    showQuestion(firstQuestion ? firstQuestion.dataset.questionId : null);
}
