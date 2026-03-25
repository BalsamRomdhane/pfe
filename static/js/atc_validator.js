/*
  atc_validator.js

  Provides the UI interactions for the ATC Document Name Validator page.
*/

const atcEndpoint = '/api/atc/validate-name/';

async function validateAtcFilename(filename) {
  const resp = await fetch(atcEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': window.CSRF_TOKEN || '',
    },
    body: JSON.stringify({ filename }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`API request failed: ${resp.status} ${text}`);
  }

  return await resp.json();
}

function renderValidationResult(result) {
  const container = document.getElementById('validation-result');
  if (!container) return;

  container.classList.remove('hidden');

  const status = (result.status || '').toUpperCase();
  const isCompliant = status === 'COMPLIANT';
  const icon = isCompliant ? '✔' : '✖';
  const statusText = isCompliant ? 'COMPLIANT' : 'NON COMPLIANT';

  const cardBg = isCompliant ? 'bg-emerald-50' : 'bg-red-50';
  const cardBorder = isCompliant ? 'border-emerald-200' : 'border-red-200';
  const textColor = isCompliant ? 'text-emerald-700' : 'text-red-700';

  container.innerHTML = `
    <div class="${cardBg} border ${cardBorder} p-4 rounded-lg">
      <span class="${textColor} font-semibold">${icon} ${statusText}</span>
      <p class="text-sm text-gray-600 mt-1">${result.reason || ''}</p>
    </div>
  `;
}

function showError(error) {
  const errorEl = document.getElementById('atc-error');
  if (!errorEl) return;
  errorEl.textContent = error?.message ? error.message : String(error);
  errorEl.classList.remove('hidden');
}

function initATCValidator() {
  const validateBtn = document.getElementById('validate-atc-btn');
  const filenameInput = document.getElementById('filename-input');
  const fileInput = document.getElementById('atc-file');

  if (!validateBtn || !filenameInput) return;

  const runValidation = async () => {
    const filename = filenameInput.value.trim();
    if (!filename) {
      showError(new Error('Please enter a document filename.'));
      return;
    }

    try {
      const result = await validateAtcFilename(filename);
      renderValidationResult(result);
    } catch (err) {
      showError(err);
    }
  };

  validateBtn.addEventListener('click', (e) => {
    e.preventDefault();
    runValidation();
  });

  if (fileInput) {
    fileInput.addEventListener('change', (event) => {
      const file = event.target.files?.[0];
      if (file) {
        filenameInput.value = file.name;
      }
    });
  }
}

window.initATCValidator = initATCValidator;
