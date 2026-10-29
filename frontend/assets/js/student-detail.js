/**
 * Student Detail Page Controller
 */
(function() {
  'use strict';

  const urlParams = new URLSearchParams(window.location.search);
  const studentId = urlParams.get('id') || 'STU101';
  let currentStudent = null;
  let hasRenderedCharts = { subjects: false, trends: false };

  async function init() {
    try {
      const student = await window.API.getStudentById(studentId);
      currentStudent = student;
      renderHeader(student);
      renderOverviewTab(student);
      setupTabs();
      setupModal(student);
    } catch (err) {
      console.error('Failed to load student details:', err);
      document.body.innerHTML = `
        <div style="padding: 40px; text-align: center;">
          <p class="state-error">Student record not found or inaccessible.</p>
          <a href="/pages/students.html" class="btn btn-secondary" style="margin-top: 16px;">Back to Students</a>
        </div>
      `;
    }
  }

  function renderHeader(student) {
    document.getElementById('studentName').textContent = student.name;
    document.getElementById('studentRoll').textContent = student.roll;
    document.getElementById('studentDiv').textContent = student.division;
    document.getElementById('studentSem').textContent = student.semester;
    document.getElementById('studentUpdated').textContent = window.Utils.formatDate(student.updated_at);
    document.getElementById('studentRiskBadge').innerHTML = window.Utils.renderRiskBadge(student.risk_level);

    // Link simulator button
    const simBtn = document.getElementById('btnOpenSimulator');
    if (simBtn) {
      simBtn.href = `/pages/what-if.html?student_id=${encodeURIComponent(student.id)}`;
    }

    // Hide log intervention action for students
    const user = window.Auth ? window.Auth.getUser() : null;
    const intBtn = document.getElementById('btnLogIntervention');
    if (intBtn && user && user.role === 'STUDENT') {
      intBtn.style.display = 'none';
    }
  }

  async function renderOverviewTab(student) {
    // 1. Key indicators
    document.getElementById('indAttendance').textContent = `${student.attendance_pct}%`;
    document.getElementById('indQuiz').textContent = `${student.quiz_avg}/100`;
    document.getElementById('indAssignment').textContent = `${student.assignment_pct}%`;
    document.getElementById('indInternal').textContent = `${student.internal_marks}/30`;
    document.getElementById('indBacklogs').textContent = `${student.backlogs} course(s)`;

    // 2. Probabilities
    const probs = student.probabilities || { low: 0.1, medium: 0.2, high: 0.7 };
    const pLow = Math.round(probs.low * 100);
    const pMed = Math.round(probs.medium * 100);
    const pHigh = Math.round(probs.high * 100);

    document.getElementById('probLowBar').style.width = `${pLow}%`;
    document.getElementById('probLowVal').textContent = `${pLow}%`;
    document.getElementById('probMedBar').style.width = `${pMed}%`;
    document.getElementById('probMedVal').textContent = `${pMed}%`;
    document.getElementById('probHighBar').style.width = `${pHigh}%`;
    document.getElementById('probHighVal').textContent = `${pHigh}%`;

    // 3. SHAP factors
    try {
      const exp = await window.API.getExplanation(student.id);
      renderShapFactors(exp.factors);
    } catch (err) {
      console.error('Error fetching SHAP explanation:', err);
      document.getElementById('shapListContainer').innerHTML = '<div class="state-error">Unable to load SHAP factors.</div>';
    }
  }

  function renderShapFactors(factors) {
    const container = document.getElementById('shapListContainer');
    if (!container) return;

    if (!factors || factors.length === 0) {
      container.innerHTML = '<div class="state-empty">No explanation weights computed.</div>';
      return;
    }

    let html = '';
    factors.forEach(f => {
      const isPositive = f.shap >= 0; // positive pushes risk towards high
      const absVal = Math.min(100, Math.round(Math.abs(f.shap) * 200)); // normalized visual width
      const sign = isPositive ? '+' : '';

      html += `
        <div class="shap-item">
          <div class="shap-header">
            <span class="shap-feature">${window.Utils.escapeHtml(f.label)}: <strong class="mono">${window.Utils.escapeHtml(f.value)}</strong></span>
            <span class="shap-contribution-text ${isPositive ? 'positive' : 'negative'}">
              ${sign}${f.shap} impact
            </span>
          </div>
          <div class="shap-visual">
            <div class="shap-axis"></div>
            <div class="shap-bar-container">
              <div class="shap-bar-side-left">
                ${!isPositive ? `<div class="shap-bar-negative" style="width: ${absVal}%;"></div>` : ''}
              </div>
              <div class="shap-bar-side-right">
                ${isPositive ? `<div class="shap-bar-positive" style="width: ${absVal}%;"></div>` : ''}
              </div>
            </div>
          </div>
          <small class="text-muted">${window.Utils.escapeHtml(f.detail)}</small>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  async function renderSubjectsTab(student) {
    if (hasRenderedCharts.subjects) return;
    try {
      const subjects = await window.API.getSubjects(student.id);
      const tbody = document.getElementById('subjectsTableBody');

      let tableHtml = '';
      subjects.forEach(sub => {
        let statusBadge = '<span class="badge badge-risk-low">Satisfactory</span>';
        if (sub.status === 'Critical') {
          statusBadge = '<span class="badge badge-risk-high">Critical</span>';
        } else if (sub.status === 'Attention') {
          statusBadge = '<span class="badge badge-risk-medium">Needs Attention</span>';
        }

        tableHtml += `
          <tr>
            <td class="col-num">${window.Utils.escapeHtml(sub.subject_code)}</td>
            <td><strong>${window.Utils.escapeHtml(sub.subject_name)}</strong></td>
            <td class="col-num">${sub.attendance_pct}%</td>
            <td class="col-num">${sub.quiz_avg}/100</td>
            <td class="col-num">${sub.assignment_pct}%</td>
            <td class="col-num">${sub.internal_marks}/30</td>
            <td>${statusBadge}</td>
          </tr>
        `;
      });
      tbody.innerHTML = tableHtml;

      if (window.Charts) {
        window.Charts.renderSubjectBarChart('subjectBarCanvas', subjects);
      }
      hasRenderedCharts.subjects = true;
    } catch (err) {
      console.error('Error rendering subjects:', err);
    }
  }

  async function renderTrendsTab(student) {
    if (hasRenderedCharts.trends) return;
    try {
      const trends = await window.API.getTrends(student.id);
      if (window.Charts) {
        window.Charts.renderStudentTrendsChart('trendLineCanvas', trends);
        window.Charts.renderSgpaChart('sgpaBarCanvas', trends.past_sgpa);
      }
      hasRenderedCharts.trends = true;
    } catch (err) {
      console.error('Error rendering trends:', err);
    }
  }

  async function renderRecsTab(student) {
    const container = document.getElementById('recsContainer');
    try {
      const recs = await window.API.getRecommendations(student.id);
      if (!recs || recs.length === 0) {
        container.innerHTML = '<div class="state-empty">No active recommendations for this student.</div>';
        return;
      }

      let html = '';
      recs.forEach((rec, idx) => {
        html += `
          <div class="rec-card">
            <div class="rec-main">
              <div class="rec-header">
                ${window.Utils.renderPriorityBadge(rec.priority)}
                <span class="rec-subject">&bull; ${window.Utils.escapeHtml(rec.subject)}</span>
              </div>
              <div class="rec-action">${window.Utils.escapeHtml(rec.action)}</div>
              <div class="rec-reason">${window.Utils.escapeHtml(rec.reason)}</div>
            </div>
            <label class="rec-assign-box">
              <input type="checkbox" ${rec.assigned ? 'checked' : ''} data-rec-index="${idx}" />
              <span>Mark as assigned</span>
            </label>
          </div>
        `;
      });
      container.innerHTML = html;
    } catch (err) {
      console.error('Error rendering recommendations:', err);
      container.innerHTML = '<div class="state-error">Failed to load recommendations.</div>';
    }
  }

  function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.tab;

        // Active state on buttons
        tabBtns.forEach(b => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');

        // Toggle panels
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        const panel = document.getElementById(targetId);
        if (panel) panel.classList.add('active');

        // Trigger chart render when tabs become visible
        if (targetId === 'tabSubjects') renderSubjectsTab(currentStudent);
        if (targetId === 'tabTrends') renderTrendsTab(currentStudent);
        if (targetId === 'tabRecs') renderRecsTab(currentStudent);
      });
    });
  }

  function setupModal(student) {
    const modal = document.getElementById('interventionModal');
    const openBtn = document.getElementById('btnLogIntervention');
    const closeBtn = document.getElementById('btnCloseModal');
    const cancelBtn = document.getElementById('btnCancelModal');
    const form = document.getElementById('quickInterventionForm');
    const studentNameInput = document.getElementById('modalStudentName');
    const dateInput = document.getElementById('modalDate');

    if (!modal) return;

    studentNameInput.value = `${student.name} (${student.roll})`;
    dateInput.value = new Date().toISOString().split('T')[0];

    if (window.ModernSelect) {
      new window.ModernSelect(document.getElementById('modalInterventionType'));
    }

    const openModal = () => modal.classList.add('open');
    const closeModal = () => {
      modal.classList.remove('open');
      document.getElementById('modalError').style.display = 'none';
    };

    openBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const type = document.getElementById('modalInterventionType').value;
      const date = document.getElementById('modalDate').value;
      const notes = document.getElementById('modalNotes').value.trim();
      const errBox = document.getElementById('modalError');

      if (!notes) {
        errBox.textContent = 'Please enter intervention notes.';
        errBox.style.display = 'block';
        return;
      }

      try {
        await window.API.createIntervention({
          student_id: student.id,
          type,
          date,
          status: 'Planned',
          notes
        });
        closeModal();
        alert('Intervention logged successfully.');
      } catch (err) {
        errBox.textContent = err.message || 'Failed to save intervention.';
        errBox.style.display = 'block';
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
