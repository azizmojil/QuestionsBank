document.addEventListener('DOMContentLoaded', function () {
  function bindWhenReady() {
    if (!window.assessmentApp || !window.assessmentApp.pathContainer) {
      requestAnimationFrame(bindWhenReady);
      return;
    }

    const { assessmentPath, pathContainer, surveyQuestionId } = window.assessmentApp;

    function syncSelectAppearance($select) {
      const $container = $select.next('.select2-container');
      const rawVal = $select.val();
      const texts = $select.find(':selected').map(function () {
        return ($(this).text() || '').trim();
      }).get();

      const hasValue = Array.isArray(rawVal) ? rawVal.length > 0 : !!rawVal;
      $container.toggleClass('has-value', hasValue);

      const $wrapper = $select.parent();
      const $label = $wrapper.find('.select2-floating-label');
      if ($label.length) {
        if (hasValue) {
          $label.text(texts.join('\n')).removeClass('hidden');
        } else {
          $label.text('').addClass('hidden');
        }
      }
    }

    function attachFloatingLabel($select) {
      const $wrapper = $select.parent();
      if ($wrapper.find('.select2-floating-label').length === 0) {
        $wrapper.prepend('<div class="select2-floating-label text-sm mb-1 hidden"></div>');
      }
      setTimeout(() => syncSelectAppearance($select), 0);
      $select.on('change', function () {
        syncSelectAppearance($select);
      });
    }

    function formatOptionWithIcon(option) {
      if (!option.id) {
        return option.text;
      }
      const $option = $(option.element);
      const explanation = $option.data('explanation');
      
      if (explanation) {
        const iconHtml = '<span class="info-icon" title="' + explanation + '">ⓘ</span>';
        return $('<span>' + option.text + ' ' + iconHtml + '</span>');
      }
      return option.text;
    }

    $('.dropdown-wrapper.s2-scope .searchable-dropdown, .multi-select-container.s2-scope .searchable-dropdown').each(function () {
      const $select = $(this);
      const $wrapper = $select.parent();
      $select
        .select2({
          placeholder: "Select an option",
          allowClear: true,
          dropdownParent: $wrapper,
          templateResult: formatOptionWithIcon,
          templateSelection: formatOptionWithIcon
        })
        .off('select2:select.assessment')
        .on('select2:select.assessment', function (e) {
          handleDropdownSelection(e, assessmentPath, pathContainer, surveyQuestionId);
        });

      attachFloatingLabel($select);
    });

    $('.dynamic-survey-question-wrapper.s2-scope .dynamic-survey-question-dropdown').each(function () {
      const $select = $(this);
      const $wrapper = $select.parent();
      $select.select2({
        placeholder: "Select an option",
        allowClear: true,
        dropdownParent: $wrapper
      });
      attachFloatingLabel($select);
    });
  }

  bindWhenReady();
});
