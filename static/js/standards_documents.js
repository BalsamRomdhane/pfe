/*
  standards_documents.js provides a small embedded documents browser within the Standards page.
*/

(function () {
  const documentsEndpoint = '/api/documents/';
  let currentPage = 1;
  let pageSize = 10;
  let totalPages = 1;
  let searchTerm = '';

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      const dt = new Date(dateString);
      return dt.toLocaleString();
    } catch (e) {
      return dateString;
    }
  };

  const showStatus = (message, type = 'info') => {
    const el = document.getElementById('standards-documents-status');
    if (!el) return;
    el.innerHTML = `<div class="text-${type}">${message}</div>`;
  };

  const buildRow = (doc) => {
    const tr = document.createElement('tr');

    const fileName = doc.file_name || doc.file || '—';
    const standard = doc.standard_name || '—';

    tr.innerHTML = `
      <td>${doc.id}</td>
      <td>${fileName}</td>
      <td>${standard}</td>
      <td>${formatDate(doc.uploaded_at)}</td>
      <td class="text-end">
        <button class="btn btn-sm btn-outline-danger" data-doc-id="${doc.id}">Supprimer</button>
      </td>
    `;

    const deleteBtn = tr.querySelector('button');
    deleteBtn.addEventListener('click', async () => {
      await deleteDocument(doc.id, tr);
    });

    return tr;
  };

  const deleteDocument = async (id, row) => {
    if (!confirm('Supprimer ce document ? Cette action ne peut pas être annulée.')) {
      return;
    }

    showStatus('Suppression en cours…', 'info');

    const headers = typeof addCsrfHeader === 'function' ? addCsrfHeader({}) : {};

    const resp = await fetch(`${documentsEndpoint}${id}/`, {
      method: 'DELETE',
      headers,
      credentials: 'same-origin',
    });

    if (!resp.ok) {
      showStatus('Impossible de supprimer le document. Rafraîchissez et réessayez.', 'danger');
      return;
    }

    if (row && row.remove) {
      row.remove();
    }

    showStatus('Document supprimé.', 'success');
    loadDocuments();
  };

  const buildPagination = () => {
    const container = document.getElementById('standards-documents-pagination');
    if (!container) return;

    container.innerHTML = '';

    if (totalPages <= 1) {
      return;
    }

    const createButton = (label, page, disabled = false) => {
      const btn = document.createElement('button');
      btn.className = `btn btn-sm btn-outline-secondary me-1${disabled ? ' disabled' : ''}`;
      btn.type = 'button';
      btn.textContent = label;
      if (!disabled) {
        btn.addEventListener('click', () => {
          currentPage = page;
          loadDocuments();
        });
      }
      return btn;
    };

    container.appendChild(createButton('«', 1, currentPage === 1));
    container.appendChild(createButton('‹', Math.max(1, currentPage - 1), currentPage === 1));

    const pageInfo = document.createElement('span');
    pageInfo.className = 'mx-2 text-muted';
    pageInfo.textContent = `Page ${currentPage} / ${totalPages}`;
    container.appendChild(pageInfo);

    container.appendChild(createButton('›', Math.min(totalPages, currentPage + 1), currentPage === totalPages));
    container.appendChild(createButton('»', totalPages, currentPage === totalPages));
  };

  const loadDocuments = async () => {
    const tbody = document.querySelector('#standards-documents-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Chargement…</td></tr>';

    const params = new URLSearchParams();
    if (searchTerm) params.set('search', searchTerm);
    params.set('page', currentPage);
    params.set('page_size', pageSize);

    const resp = await fetch(`${documentsEndpoint}?${params.toString()}`, {
      credentials: 'same-origin',
    });

    if (!resp.ok) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Impossible de charger les documents.</td></tr>';
      return;
    }

    const data = await resp.json();
    const docs = data.results || [];
    totalPages = data.total_pages || 1;

    if (!docs.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Aucun document trouvé.</td></tr>';
      buildPagination();
      return;
    }

    tbody.innerHTML = '';
    docs.forEach((doc) => {
      tbody.appendChild(buildRow(doc));
    });

    buildPagination();
    showStatus(`Affichage de ${docs.length} document(s).`, 'success');
  };

  const initStandardsDocuments = () => {
    const searchInput = document.getElementById('standards-documents-search');
    const searchBtn = document.getElementById('standards-documents-search-btn');

    if (!searchInput || !searchBtn) return;

    const applySearch = () => {
      searchTerm = searchInput.value.trim();
      currentPage = 1;
      loadDocuments();
    };

    searchBtn.addEventListener('click', applySearch);
    searchInput.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') {
        applySearch();
      }
    });

    loadDocuments();
  };

  window.initStandardsDocuments = initStandardsDocuments;
})();
