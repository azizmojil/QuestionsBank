async function saveResult(finalLabel, surveyQuestionId, assessmentPath) {
  try {
    const container = document.getElementById('assessment-container');
    if (!container) return false;

    const saveUrl = container.dataset.saveUrl;
    if (!saveUrl) return false;

    const payload = {
      final_label: finalLabel ?? null,
      survey_question_id: surveyQuestionId,
      assessment_path: assessmentPath,
    };

    const resp = await fetch(saveUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(payload),
      credentials: 'same-origin',
    });

    const data = await resp.json();

    const finalCard = document.getElementById('final-result-card');
    const finalText = document.getElementById('final-result-text');
    const actions = document.getElementById('result-actions');

    function finishView() {
      document.querySelectorAll('.question-card').forEach(q => q.classList.add('hidden'));
      if (finalCard) finalCard.classList.remove('hidden');
      try { finalCard.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch(_) {}
    }

    function setFinalText(labelFromServer) {
      const label = (labelFromServer ?? finalLabel ?? '').toString().trim();
      if (!finalText) return;
    }

    if (data.status === 'redirect' && data.url) {
      setFinalText(data.final_label);
      if (actions) {
        actions.innerHTML = '';
        const uploadBtn = document.createElement('a');
        uploadBtn.href = data.url;
        uploadBtn.className = 'btn-primary';
        uploadBtn.textContent = 'رفع الشواهد المطلوبة';

        const backBtn = document.createElement('a');
        backBtn.href = actions.dataset.backHref || '#';
        backBtn.className = 'btn-secondary ml-3';
        backBtn.textContent = actions.dataset.backText || 'العودة';

        actions.appendChild(uploadBtn);
        if (backBtn.getAttribute('href') !== '#') {
          actions.appendChild(backBtn);
        }
      }
      finishView();
      return true;
    }

    if (data.status === 'success') {
      setFinalText(data.final_label);
      finishView();
      return true;
    }

    if (data.status === 'error') {
      console.error('Save error:', data.message);
      alert(data.message || 'حدث خطأ أثناء الحفظ.');
      return false;
    }

    setFinalText();
    finishView();
    return true;

  } catch (err) {
    console.error('saveResult exception:', err);
    alert('تعذر حفظ النتيجة. حاول مرة أخرى.');
    return false;
  }
}

function getCsrfToken() {
  const name = 'csrftoken';
  const cookies = document.cookie ? document.cookie.split(';') : [];
  for (let i = 0; i < cookies.length; i++) {
    const c = cookies[i].trim();
    if (c.substring(0, name.length + 1) === (name + '=')) {
      return decodeURIComponent(c.substring(name.length + 1));
    }
  }
  return '';
}
