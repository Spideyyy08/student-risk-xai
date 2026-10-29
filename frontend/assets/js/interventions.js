/**
 * Interventions Page Controller
 */
(function() {
  'use strict';

  let allInterventions = [];

  async function init() {
    // Check role guard (STUDENT cannot access)
    const user = window.Auth ? window.Auth.getUser() : null;
    if (user && user.role === 'STUDENT') {
      window.location.href = '/pages/dashboard.html';
      return;
    }

    // Set today's date
    const dateInput = document.getElementById('intDateInput');
    if (dateInput) {
      dateInput.value = new Date().toISOString().split('T')[0];
    }

    await loadStudentRoster();
    await loadInterventions();
    setupEvents();
  }

  let modStudent = null, modType = null, modStatus = null, modFilter = null;

  async function loadStudentRoster() {
    try {
      const select = document.getElementById('intStudentSelect');
      const allStudents = window.MockData ? window.MockData.STUDENTS : [];
      select.innerHTML = '<option value="">Select student...</option>';

      allStudents.forEach(st => {
        const opt = document.createElement('option');
        opt.value = st.id;
        opt.textContent = `${st.name} (${st.roll}) - Div ${st.division} [${st.risk_level} Risk]`;
        select.appendChild(opt);
      });

      if (window.ModernSelect) {
        modStudent = new window.ModernSelect(select);
        modType = new window.ModernSelect(document.getElementById('intTypeSelect'));
        modStatus = new window.ModernSelect(document.getElementById('intStatusSelect'));
        modFilter = new window.ModernSelect(document.getElementById('statusFilterSelect'));
      }
    } catch (err) {
      console.error('Failed to populate student roster:', err);
    }
  }

  async function loadInterventions() {
    const tbody = document.getElementById('interventionsTableBody');
    tbody.innerHTML = '<tr><td colspan="5" class="state-loading">Loading logged interventions...</td></tr>';

    try {
      allInterventions = await window.API.getInterventions();
      renderInterventionsTable();
    } catch (err) {
      console.error('Failed to load interventions:', err);
      tbody.innerHTML = '<tr><td colspan="5" class="state-error">Failed to load intervention records.</td></tr>';
    }
  }

  function renderInterventionsTable() {
    const filter = document.getElementById('statusFilterSelect').value;
    const tbody = document.getElementById('interventionsTableBody');

    let list = allInterventions;
    if (filter !== 'ALL') {
      list = list.filter(i => i.status.toLowerCase() === filter.toLowerCase());
    }

    const user = window.Auth ? window.Auth.getUser() : null;
    const isAdmin = user && user.role === 'ADMIN';

    if (isAdmin) {
      document.getElementById('interventionStatsSubtitle').textContent = `${list.length} department records (HOD Oversight: SEDA-A & SEDA-B)`;
    } else {
      document.getElementById('interventionStatsSubtitle').textContent = `${list.length} total records logged`;
    }

    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="state-empty">No interventions matching criteria.</td></tr>';
      return;
    }

    let html = '';
    list.forEach(i => {
      const advisor = i.division === 'SEDA-B' ? 'Prof. V. N. Joshi' : 'Prof. A. S. Sharma';
      html += `
        <tr>
          <td class="col-num" style="white-space: nowrap;">${window.Utils.formatDate(i.date)}</td>
          <td>
            <strong>${window.Utils.escapeHtml(i.student_name)}</strong>
            <div class="text-muted" style="font-size: 11px;">
              Div ${window.Utils.escapeHtml(i.division || 'SEDA-A')}
              ${isAdmin ? `&bull; <span style="color: var(--ink); font-weight: 500;">Advisor: ${advisor}</span>` : ''}
            </div>
          </td>
          <td>${window.Utils.escapeHtml(i.type)}</td>
          <td>${window.Utils.renderStatusBadge(i.status)}</td>
          <td>
            <div style="max-width: 380px; font-size: 12.5px; line-height: 1.4;">
              ${window.Utils.escapeHtml(i.notes)}
            </div>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  }

  function setupEvents() {
    const filterSelect = document.getElementById('statusFilterSelect');
    if (filterSelect) {
      filterSelect.addEventListener('change', renderInterventionsTable);
    }

    const form = document.getElementById('newInterventionForm');
    const msgBox = document.getElementById('intFormMessage');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      msgBox.style.display = 'none';

      const studentId = document.getElementById('intStudentSelect').value;
      const type = document.getElementById('intTypeSelect').value;
      const status = document.getElementById('intStatusSelect').value;
      const date = document.getElementById('intDateInput').value;
      const notes = document.getElementById('intNotesInput').value.trim();

      if (!studentId || !notes) {
        msgBox.className = 'form-error';
        msgBox.textContent = 'Please fill in all required fields.';
        msgBox.style.display = 'block';
        return;
      }

      try {
        const res = await window.API.createIntervention({
          student_id: studentId,
          type,
          status,
          date,
          notes
        });

        // Prepend to current list
        if (res.item) {
          allInterventions.unshift(res.item);
        }

        renderInterventionsTable();

        msgBox.className = 'footnote';
        msgBox.style.color = 'var(--risk-low)';
        msgBox.textContent = 'Intervention saved successfully.';
        msgBox.style.display = 'block';

        // Clear notes
        document.getElementById('intNotesInput').value = '';
      } catch (err) {
        msgBox.className = 'form-error';
        msgBox.textContent = err.message || 'Failed to save intervention.';
        msgBox.style.display = 'block';
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
