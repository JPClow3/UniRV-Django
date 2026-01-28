// Edital create/update forms: autosave, loading state, date validation, delete confirm
(function () {
  const editalForm = document.querySelector('form#edital-form');
  if (!editalForm) return;

  // ========================================
  // FORM AUTOSAVE & UNSAVED CHANGES WARNING
  // ========================================
  const AUTOSAVE_KEY = 'edital_form_autosave';
  const AUTOSAVE_INTERVAL = 10000;
  let formChanged = false;
  let autosaveInterval;

  const formFields = editalForm.querySelectorAll('input, textarea, select');

  window.addEventListener('DOMContentLoaded', function () {
    const savedData = localStorage.getItem(AUTOSAVE_KEY);
    if (!savedData) return;

    try {
      const data = JSON.parse(savedData);
      const savedDate = new Date(data.timestamp);
      const now = new Date();
      const hoursSince = (now - savedDate) / (1000 * 60 * 60);

      if (hoursSince < 24) {
        // eslint-disable-next-line no-alert
        if (confirm(`Encontramos um rascunho salvo em ${savedDate.toLocaleString()}. Deseja restaurá-lo?`)) {
          restoreFormData(data.fields);
          if (typeof window.showToast === 'function') window.showToast('Rascunho restaurado com sucesso!');
        } else {
          localStorage.removeItem(AUTOSAVE_KEY);
        }
      }
    } catch {
      localStorage.removeItem(AUTOSAVE_KEY);
    }
  });

  formFields.forEach(function (field) {
    field.addEventListener('input', function () {
      formChanged = true;
    });
    field.addEventListener('change', function () {
      formChanged = true;
    });
  });

  function autosaveForm() {
    if (!formChanged) return;

    const data = {};
    formFields.forEach(function (field) {
      if (field.type !== 'password' && field.name) {
        data[field.name] = field.value;
      }
    });

    const saveData = {
      fields: data,
      timestamp: new Date().toISOString(),
    };

    try {
      const jsonString = JSON.stringify(saveData);
      if (jsonString.length > 4.5 * 1024 * 1024) {
        if (typeof window.showToast === 'function') window.showToast('Rascunho muito grande para salvar automaticamente', 'warning');
        return;
      }
      localStorage.setItem(AUTOSAVE_KEY, jsonString);
      showAutosaveIndicator();
    } catch (e) {
      if (e && e.name === 'QuotaExceededError') {
        if (typeof window.showToast === 'function') window.showToast('Armazenamento local cheio. Rascunho não salvo.', 'error');
        Object.keys(localStorage).forEach((key) => {
          if (key.startsWith('edital_form_autosave')) localStorage.removeItem(key);
        });
      }
    }
  }

  function restoreFormData(data) {
    Object.keys(data).forEach(function (name) {
      const field = editalForm.querySelector(`[name="${name}"]`);
      if (field) field.value = data[name];
    });
  }

  function showAutosaveIndicator() {
    let indicator = document.querySelector('.autosave-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.className = 'autosave-indicator';
      indicator.innerHTML = '<i class="fas fa-check-circle"></i> Rascunho salvo';
      document.body.appendChild(indicator);
    }

    indicator.classList.add('visible');
    setTimeout(function () {
      indicator.classList.remove('visible');
    }, 2000);
  }

  autosaveInterval = setInterval(autosaveForm, AUTOSAVE_INTERVAL);

  window.addEventListener('beforeunload', function (e) {
    if (formChanged) {
      e.preventDefault();
      e.returnValue = 'Você tem alterações não salvas. Tem certeza que deseja sair?';
      return e.returnValue;
    }
    return undefined;
  });

  editalForm.addEventListener('submit', function () {
    formChanged = false;
    clearInterval(autosaveInterval);
    localStorage.removeItem(AUTOSAVE_KEY);
  });

  const manualSaveBtn = document.getElementById('manual-save-draft');
  if (manualSaveBtn) {
    manualSaveBtn.addEventListener('click', function (e) {
      e.preventDefault();
      autosaveForm();
      if (typeof window.showToast === 'function') window.showToast('Rascunho salvo manualmente!');
    });
  }

  // ========================================
  // FORM LOADING STATES
  // ========================================
  editalForm.addEventListener('submit', function () {
    const submitBtn = editalForm.querySelector('#submit-btn');
    if (!editalForm.checkValidity()) return;
    if (submitBtn && !submitBtn.classList.contains('loading')) {
      submitBtn.classList.add('loading');
      submitBtn.disabled = true;
      const btnText = submitBtn.querySelector('.btn-text');
      const btnLoading = submitBtn.querySelector('.btn-loading');
      if (btnText) btnText.style.display = 'none';
      if (btnLoading) btnLoading.style.display = 'inline-block';
    }
  });

  // ========================================
  // DATE VALIDATION (Frontend)
  // ========================================
  const startDateInput = document.getElementById('id_start_date');
  const endDateInput = document.getElementById('id_end_date');

  if (startDateInput && endDateInput) {
    function validateDates() {
      if (startDateInput.value && endDateInput.value) {
        const start = new Date(startDateInput.value);
        const end = new Date(endDateInput.value);

        if (end < start) {
          endDateInput.setCustomValidity('A data de encerramento deve ser posterior à data de abertura.');
          endDateInput.classList.add('has-date-error');
          return false;
        }
        endDateInput.setCustomValidity('');
        endDateInput.classList.remove('has-date-error');
        return true;
      }
      endDateInput.setCustomValidity('');
      endDateInput.classList.remove('has-date-error');
      return true;
    }

    startDateInput.addEventListener('change', validateDates);
    endDateInput.addEventListener('change', validateDates);
    startDateInput.addEventListener('input', validateDates);
    endDateInput.addEventListener('input', validateDates);

    editalForm.addEventListener('submit', function (e) {
      if (!validateDates()) {
        e.preventDefault();
        endDateInput.focus();
        if (typeof window.showToast === 'function') {
          window.showToast('A data de encerramento deve ser posterior à data de abertura.', 'error');
        }
      }
    });
  }
})();

