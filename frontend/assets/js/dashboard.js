/**
 * Dynamic Dashboard Controller
 * Supports live division filtering, semester switching, view mode toggles,
 * and personalized student views.
 */
(function() {
  'use strict';

  let currentDivision = 'ALL';
  let chartAsPercentage = false;
  let shapOnlyDrivers = false;
  let cachedSummary = null;

  async function loadDashboard() {
    const user = window.Auth ? window.Auth.getUser() : { role: 'TEACHER' };
    const semester = sessionStorage.getItem('academic_semester') || 'sem5';

    // If Student role, render dedicated Student Advisory Dashboard
    if (user.role === 'STUDENT') {
      renderStudentPortal(user, semester);
      return;
    }

    // Otherwise render Faculty/Admin Dashboard
    document.getElementById('facultyDashboardContainer').style.display = 'block';
    document.getElementById('studentPortalContainer').style.display = 'none';

    // If Admin role, render Admin Special Overview Banner
    const adminBanner = document.getElementById('adminOverviewBanner');
    if (adminBanner) {
      if (user.role === 'ADMIN') {
        adminBanner.style.display = 'flex';
        adminBanner.className = 'admin-overview-banner';
        adminBanner.innerHTML = `
          <div>
            <div class="admin-banner-title">Department Administrative Overview — Computer Engineering</div>
            <div class="admin-banner-sub">HOD Control View &bull; 2 Divisions Active (SEDA-A: Prof. Sharma &bull; SEDA-B: Prof. Joshi) &bull; Model v2.1</div>
          </div>
          <div class="admin-banner-actions">
            <button type="button" class="btn-admin-export" id="btnExportDeptReport">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              <span>Export Dept Risk Audit (CSV)</span>
            </button>
          </div>
        `;
        const exportBtn = document.getElementById('btnExportDeptReport');
        if (exportBtn) {
          exportBtn.addEventListener('click', downloadDeptCsvReport);
        }
      } else {
        adminBanner.style.display = 'none';
      }
    }

    try {
      // 1. Fetch Class Summary with dynamic division & semester
      const summary = await window.API.getClassSummary({
        division: currentDivision,
        semester: semester
      });
      cachedSummary = summary;

      renderSummaryStrip(summary);
      renderCharts(summary);

      // 2. Fetch Students Needing Attention (filtered by active division & semester)
      const highRiskData = await window.API.getStudents({
        risk: 'HIGH',
        division: currentDivision,
        semester: semester,
        page: 1
      });
      renderAttentionTable(highRiskData.items ? highRiskData.items.slice(0, 8) : []);

      // 3. Fetch Recent Interventions
      const interventions = await window.API.getInterventions();
      let filteredInts = interventions.filter(i => (semester === 'sem4' ? i.semester === 'sem4' : i.semester !== 'sem4'));
      if (currentDivision !== 'ALL') {
        filteredInts = filteredInts.filter(i => i.division === currentDivision);
      }
      renderInterventionsList(filteredInts.slice(0, 5));
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  }

  function renderSummaryStrip(summary) {
    document.getElementById('totalStudentsCount').textContent = summary.total;
    document.getElementById('totalStudentsSub').textContent = currentDivision === 'ALL' ? 'across 2 divisions' : `in Div ${currentDivision}`;
    document.getElementById('highRiskCount').textContent = summary.high;
    document.getElementById('highRiskPct').textContent = `(${summary.high_pct}%)`;
    document.getElementById('mediumRiskCount').textContent = summary.medium;
    document.getElementById('mediumRiskPct').textContent = `(${summary.medium_pct}%)`;
    document.getElementById('lowRiskCount').textContent = summary.low;
    document.getElementById('lowRiskPct').textContent = `(${summary.low_pct}%)`;

    const scopeLabel = document.getElementById('cohortScopeLabel');
    if (scopeLabel) {
      scopeLabel.textContent = currentDivision === 'ALL'
        ? `Showing all ${summary.total} enrolled students`
        : `Showing Division ${currentDivision} (${summary.total} students)`;
    }

    const viewAllBtn = document.getElementById('btnViewAllFiltered');
    if (viewAllBtn) {
      viewAllBtn.href = `/pages/students.html?risk=HIGH&division=${encodeURIComponent(currentDivision)}`;
    }
  }

  function renderCharts(summary) {
    if (!window.Charts) return;

    // 1. Division Chart
    let divisionsData = summary.by_division;
    if (currentDivision !== 'ALL') {
      divisionsData = summary.by_division.filter(d => d.division === currentDivision);
    }
    window.Charts.renderStackedDivisionChart('divisionStackedCanvas', divisionsData, chartAsPercentage);

    // 2. SHAP Chart
    let factors = summary.top_factors;
    if (shapOnlyDrivers) {
      factors = factors.filter(f => f.direction === 'risk_raising');
    }
    window.Charts.renderClassShapChart('classShapCanvas', factors);
  }

  function renderAttentionTable(students) {
    const tbody = document.getElementById('attentionTableBody');
    if (!tbody) return;

    if (!students || students.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="state-empty">No high-risk students found in ${currentDivision === 'ALL' ? 'the selected cohort' : 'Division ' + currentDivision}.</td></tr>`;
      return;
    }

    let rowsHtml = '';
    students.forEach(st => {
      rowsHtml += `
        <tr>
          <td><strong>${window.Utils.escapeHtml(st.name)}</strong></td>
          <td class="col-num">${window.Utils.escapeHtml(st.roll)}</td>
          <td><span class="div-tag">${window.Utils.escapeHtml(st.division)}</span></td>
          <td>${window.Utils.renderRiskBadge(st.risk_level)}</td>
          <td class="col-num" style="${st.attendance_pct < 65 ? 'color: var(--risk-high); font-weight: 700;' : ''}">${st.attendance_pct}%</td>
          <td><span class="text-muted" style="font-size: 12.5px;">${window.Utils.escapeHtml(st.key_factor || 'Continuous evaluation deficit')}</span></td>
          <td>
            <a href="/pages/student-detail.html?id=${encodeURIComponent(st.id)}" class="btn btn-secondary btn-sm">View Profile</a>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = rowsHtml;
  }

  function renderInterventionsList(items) {
    const list = document.getElementById('recentInterventionsList');
    if (!list) return;

    if (!items || items.length === 0) {
      list.innerHTML = '<li class="state-empty">No interventions logged for this selection.</li>';
      return;
    }

    let itemsHtml = '';
    items.forEach(item => {
      itemsHtml += `
        <li class="intervention-feed-item">
          <div class="feed-item-top">
            <span class="feed-student-name">${window.Utils.escapeHtml(item.student_name)}</span>
            ${window.Utils.renderStatusBadge(item.status)}
          </div>
          <div class="feed-item-action">
            <strong>${window.Utils.escapeHtml(item.type)}:</strong> ${window.Utils.escapeHtml(item.notes)}
          </div>
          <div class="feed-item-meta">
            <span>${window.Utils.formatDate(item.date)}</span>
            <span>&bull;</span>
            <span>Div ${window.Utils.escapeHtml(item.division)}</span>
          </div>
        </li>
      `;
    });

    list.innerHTML = itemsHtml;
  }

  /**
   * Personalized Student Portal View
   */
  async function renderStudentPortal(user, semester) {
    document.getElementById('facultyDashboardContainer').style.display = 'none';
    const container = document.getElementById('studentPortalContainer');
    container.style.display = 'block';

    const pool = window.MockData.getStudentPool(semester);
    // Default to Aditya Kulkarni (STU101) for student login demo
    const student = pool[0];
    const exp = window.MockData.getStudentExplanations(student);
    const recs = window.MockData.getStudentRecommendations(student);

    container.innerHTML = `
      <div class="student-portal-banner">
        <div>
          <div class="student-portal-title">Welcome, ${window.Utils.escapeHtml(student.name)} (${student.roll})</div>
          <div class="student-portal-meta">Division ${student.division} &bull; ${student.semester} &bull; Academic Performance Health Check</div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
          ${window.Utils.renderRiskBadge(student.risk_level)}
          <a href="/pages/what-if.html?student_id=${student.id}" class="btn btn-primary btn-sm">Launch What-If Simulator</a>
        </div>
      </div>

      <div class="grid-7-5">
        <section class="card">
          <div class="card-header">
            <h2 class="card-title">My Personalized Learning Recovery Plan</h2>
          </div>
          <div class="card-body">
            ${recs.map(rec => `
              <div class="rec-card">
                <div class="rec-main">
                  <div class="rec-header">
                    ${window.Utils.renderPriorityBadge(rec.priority)}
                    <span class="rec-subject">&bull; ${window.Utils.escapeHtml(rec.subject)}</span>
                  </div>
                  <div class="rec-action">${window.Utils.escapeHtml(rec.action)}</div>
                  <div class="rec-reason">${window.Utils.escapeHtml(rec.reason)}</div>
                </div>
              </div>
            `).join('')}
          </div>
        </section>

        <section class="card">
          <div class="card-header">
            <h2 class="card-title">My Academic Metrics Summary</h2>
          </div>
          <div class="card-body">
            <dl class="indicator-dl">
              <dt>Attendance</dt>
              <dd style="${student.attendance_pct < 65 ? 'color: var(--risk-high);' : ''}">${student.attendance_pct}%</dd>
              <dt>Continuous Quiz Average</dt>
              <dd>${student.quiz_avg}/100</dd>
              <dt>Assignment Completion</dt>
              <dd>${student.assignment_pct}%</dd>
              <dt>Mid-Sem Internal Marks</dt>
              <dd>${student.internal_marks}/30</dd>
              <dt>Active Backlogs</dt>
              <dd>${student.backlogs} course(s)</dd>
            </dl>
          </div>
      </div>

      <!-- Student SHAP Breakdown -->
      <section class="card" style="margin-top: 20px;">
        <div class="card-header">
          <div>
            <h2 class="card-title">Why this risk prediction (Model SHAP Analysis)</h2>
            <div class="card-subtitle">Personal feature contributions explaining the model's prediction</div>
          </div>
        </div>
        <div class="card-body">
          <div class="shap-list">
            ${exp.factors.map(f => {
              const isRaising = f.direction === 'risk_raising';
              const sign = isRaising ? '+' : '-';
              const barWidth = Math.min(100, Math.abs(f.weight) * 220);
              return `
                <div class="shap-item">
                  <div class="shap-header">
                    <span class="shap-feature">${window.Utils.escapeHtml(f.feature)}</span>
                    <span class="shap-val">${window.Utils.escapeHtml(f.value)}</span>
                  </div>
                  <div class="shap-visual">
                    <div class="shap-axis"></div>
                    <div class="shap-bar-container">
                      <div class="shap-bar-side-left">
                        ${!isRaising ? `<div class="shap-bar-negative" style="width: ${barWidth}%;"></div>` : ''}
                      </div>
                      <div class="shap-bar-side-right">
                        ${isRaising ? `<div class="shap-bar-positive" style="width: ${barWidth}%;"></div>` : ''}
                      </div>
                    </div>
                    <span class="shap-contribution-text ${isRaising ? 'positive' : 'negative'}">
                      ${sign}${Math.abs(f.weight).toFixed(2)}
                    </span>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
          <p class="footnote" style="margin-top: 12px;">This analysis highlights the primary academic indicators driving your risk category to help you focus remediation efforts.</p>
        </div>
      </section>
    `;
  }

  function downloadDeptCsvReport() {
    const sem = sessionStorage.getItem('academic_semester') || 'sem5';
    const students = window.MockData ? window.MockData.getStudentPool(sem) : [];
    let csv = 'Roll_No,Student_Name,Division,Semester,Risk_Level,Attendance_Pct,Quiz_Average,Assignment_Pct,Internal_Marks,Backlogs\n';
    students.forEach(s => {
      csv += `${s.roll},"${s.name}",${s.division},${s.semester},${s.risk_level},${s.attendance_pct},${s.quiz_avg},${s.assignment_pct},${s.internal_marks},${s.backlogs}\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `vit_department_risk_audit_${sem}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function setupEventListeners() {
    // Division filter pills
    const pills = document.querySelectorAll('.filter-pill-btn');
    pills.forEach(pill => {
      pill.addEventListener('click', () => {
        pills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        currentDivision = pill.dataset.division;
        loadDashboard();
      });
    });

    // Chart mode toggle (Count vs %)
    const btnCount = document.getElementById('btnChartModeCount');
    const btnPct = document.getElementById('btnChartModePct');
    if (btnCount && btnPct) {
      btnCount.addEventListener('click', () => {
        btnCount.classList.add('active');
        btnPct.classList.remove('active');
        chartAsPercentage = false;
        if (cachedSummary) renderCharts(cachedSummary);
      });
      btnPct.addEventListener('click', () => {
        btnPct.classList.add('active');
        btnCount.classList.remove('active');
        chartAsPercentage = true;
        if (cachedSummary) renderCharts(cachedSummary);
      });
    }

    // SHAP factor filter (All vs Drivers)
    const btnShapAll = document.getElementById('btnShapAll');
    const btnShapDrivers = document.getElementById('btnShapDrivers');
    if (btnShapAll && btnShapDrivers) {
      btnShapAll.addEventListener('click', () => {
        btnShapAll.classList.add('active');
        btnShapDrivers.classList.remove('active');
        shapOnlyDrivers = false;
        if (cachedSummary) renderCharts(cachedSummary);
      });
      btnShapDrivers.addEventListener('click', () => {
        btnShapDrivers.classList.add('active');
        btnShapAll.classList.remove('active');
        shapOnlyDrivers = true;
        if (cachedSummary) renderCharts(cachedSummary);
      });
    }

    // Listen to Semester switch from topbar
    window.addEventListener('academicSemesterChanged', () => {
      loadDashboard();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setupEventListeners();
      loadDashboard();
    });
  } else {
    setupEventListeners();
    loadDashboard();
  }
})();
