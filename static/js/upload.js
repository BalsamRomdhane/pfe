/*
  upload.js provides a drag & drop upload experience and allows running compliance audits.
*/

(function () {
  const uploadEndpoint = '/api/documents/upload/';
  const auditEndpoint = '/api/compliance/audit/';
  const STANDARDS_API_ENDPOINT = '/api/standards/';

  function initUpload() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const status = document.getElementById('uploadStatus');
    const progressBar = document.getElementById('uploadProgress');
    const uploadedList = document.getElementById('uploadedList');
    const runAuditBtn = document.getElementById('runAuditBtn');
    const standardSelect = document.getElementById('standardSelect');

  let uploadedDocumentIds = [];

  const updateStatus = (message, type = 'info') => {
    if (!status) return;
    status.innerHTML = `<div class="text-${type}">${message}</div>`;
  };

  const setProgress = (percent) => {
    if (!progressBar) return;
    progressBar.style.width = `${Math.min(100, Math.max(0, percent))}%`;
    progressBar.setAttribute('aria-valuenow', Math.round(percent));
  };

  const renderUploadedList = (items) => {
    if (!uploadedList) return;
    uploadedList.innerHTML = '';

    if (!items.length) {
      uploadedList.innerHTML = '<li class="list-group-item text-muted">No files uploaded yet.</li>';
      return;
    }

    items.forEach((item) => {
      const li = document.createElement('li');
      li.className = 'list-group-item d-flex justify-content-between align-items-center';
      li.innerHTML = `${item.name} <span class="badge bg-info text-dark">Uploaded</span>`;
      uploadedList.appendChild(li);
    });
  };

  const fetchStandards = async () => {
    if (!standardSelect) return;
    standardSelect.innerHTML = '<option>Loading standards...</option>';

    const resp = await fetch(STANDARDS_API_ENDPOINT);
    if (!resp.ok) {
      standardSelect.innerHTML = '<option>Failed to load standards</option>';
      return;
    }

    const standards = await resp.json();
    standardSelect.innerHTML = '<option value="" selected disabled>Choose a standard</option>';

    standards.forEach((standard) => {
      const opt = document.createElement('option');
      opt.value = standard.id;
      opt.textContent = standard.name;
      standardSelect.appendChild(opt);
    });
  };

  const sendFiles = async (files) => {
    if (!files || files.length === 0) {
      updateStatus('No files selected.', 'warning');
      return;
    }

    const formData = new FormData();
    for (const file of files) {
      formData.append('file', file);
    }

    // Include the selected standard when uploading documents.
    const standardId = standardSelect?.value;
    if (standardId) {
      formData.append('standard', standardId);
    }

    updateStatus('Uploading files...', 'info');
    setProgress(10);

    const headers = typeof addCsrfHeader === 'function'
      ? addCsrfHeader({})
      : {};

    // Fetch with credentials ensures cookies are sent (required for CSRF validation)
    const response = await fetch(uploadEndpoint, {
      method: 'POST',
      headers,
      body: formData,
      credentials: 'same-origin',
    });

    setProgress(100);

    if (!response.ok) {
      updateStatus('Upload failed. Please try again.', 'danger');
      return;
    }

    try {
      const json = await response.json();
      const uploaded = Array.isArray(json) ? json : [json];

      const newIds = uploaded
        .filter((item) => item && item.id)
        .map((item) => item.id);

      uploadedDocumentIds = [...new Set([...uploadedDocumentIds, ...newIds])];

      renderUploadedList(uploaded.map((item) => ({ name: item.file || item.filename || 'Unknown file' })));
      updateStatus('Upload completed.', 'success');
      runAuditBtn.disabled = false;
    } catch (err) {
      updateStatus('Upload succeeded but response could not be parsed.', 'warning');
    }
  };

  const runAudit = async () => {
    if (!uploadedDocumentIds.length) {
      updateStatus('Please upload at least one document before running an audit.', 'warning');
      return;
    }

    const standardId = standardSelect?.value;
    if (!standardId) {
      updateStatus('Please select a standard before running the audit.', 'warning');
      return;
    }

    updateStatus('Running compliance audit...', 'info');
    setProgress(0);

    const payload = { document_ids: uploadedDocumentIds, standard_id: parseInt(standardId, 10) };
    const headers = typeof addCsrfHeader === 'function'
      ? addCsrfHeader({ 'Content-Type': 'application/json' })
      : { 'Content-Type': 'application/json' };

    const response = await fetch(auditEndpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      credentials: 'same-origin',
    });

    if (!response.ok) {
      updateStatus('Audit failed. Please check the selected standard and try again.', 'danger');
      return;
    }

    updateStatus('Audit completed. Redirecting to results...', 'success');
    window.location.href = '/audit-results/';
  };

  // Event bindings
  dropzone.addEventListener('click', () => fileInput.click());
  runAuditBtn?.addEventListener('click', runAudit);

  fileInput.addEventListener('change', (e) => {
    if (e.target.files) {
      sendFiles(Array.from(e.target.files));
    }
  });

  dropzone.addEventListener('dragover', (event) => {
    event.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (event) => {
    event.preventDefault();
    dropzone.classList.remove('dragover');
    const files = Array.from(event.dataTransfer.files || []);
    sendFiles(files);
  });

  // Initial load
  fetchStandards();
  renderUploadedList([]);
  setProgress(0);
}

window.initUpload = initUpload;
})();
