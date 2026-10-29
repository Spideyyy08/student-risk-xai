/**
 * What-If Academic Risk Simulator Controller
 */
(function() {
  'use strict';

  let currentStudent = null;
  let activeStudentId = null;
  let simulatedBacklogs = 0;

  // 300ms debounced simulation runner
  const debouncedSimulate = window.Utils.debounce(runSimulation, 300);

  async function init() {
    try {
      const urlParams = new URLSearchParams(window.location.search);
      const user = window.Auth ? window.Auth.getUser() : null;

      if (user && user.role === 'STUDENT') {
        activeStudentId = 'STU101';
        const selectorEl = document.querySelector('.selector-left');
        if (selectorEl) {
          selectorEl.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
              <span class="badge badge-risk-high">High Risk</span>
              <strong style="color: var(--ink); font-size: 14px;">Aditya Kulkarni (221101) &bull; Div SEDA-A</strong>
              <span class="text-muted" style="font-size: 12.5px;">&mdash; Self-Remediation Goal Simulator</span>
              <span class="recalculating-indicator" id="recalcStatus" aria-live="polite">Recalculating...</span>
            </div>
          `;
        }
      } else {
        activeStudentId = urlParams.get('student_id') || 'STU101';

        // Load all students for the dropdown
        const studentsData = await window.API.getStudents({ page: 1 });
        const select = document.getElementById('studentSelect');
        const allStudents = window.MockData ? window.MockData.STUDENTS : (studentsData.items || []);

        if (select) {
          select.innerHTML = '';
          allStudents.forEach(st => {
            const opt = document.createElement('option');
            opt.value = st.id;
            opt.textContent = `${st.name} (${st.roll}) - Div ${st.division} [${st.risk_level} Risk]`;
            if (st.id === activeStudentId) opt.selected = true;
            select.appendChild(opt);
          });

          select.addEventListener('change', (e) => {
            activeStudentId = e.target.value;
            loadStudentData(activeStudentId);
          });

          // Initialize modern rich dropdown
          if (window.ModernSelect) {
            new window.ModernSelect(select);
          }
        }
      }

      setupControls();
      await loadStudentData(activeStudentId);
    } catch (err) {
      console.error('Failed to init simulator:', err);
    }
  }

  async function loadStudentData(studentId) {
    showRecalc(true);
    try {
      const student = await window.API.getStudentById(studentId);
      currentStudent = student;
      simulatedBacklogs = student.backlogs;

      // Set baselines and slider values
      setSliderState('Attendance', student.attendance_pct, '%');
      setSliderState('Quiz', student.quiz_avg, '');
      setSliderState('Assignment', student.assignment_pct, '%');
      setSliderState('Internal', student.internal_marks, '');
      setSliderState('Practical', student.practical_marks, '');

      // Stepper
      document.getElementById('baseBacklogs').textContent = `was ${student.backlogs}`;
      document.getElementById('valBacklogs').textContent = student.backlogs;

      // Trigger initial simulation call
      await runSimulation();
    } catch (err) {
      console.error('Error loading student for simulator:', err);
    } finally {
      showRecalc(false);
    }
  }

  function setSliderState(name, val, unit) {
    const slider = document.getElementById(`slider${name}`);
    const baseline = document.getElementById(`base${name}`);
    const readout = document.getElementById(`val${name}`);

    slider.value = val;
    baseline.textContent = `was ${val}${unit}`;
    readout.textContent = `${val}${unit}`;
  }

  function setupControls() {
    const sliderNames = [
      { name: 'Attendance', unit: '%' },
      { name: 'Quiz', unit: '' },
      { name: 'Assignment', unit: '%' },
      { name: 'Internal', unit: '' },
      { name: 'Practical', unit: '' }
    ];

    sliderNames.forEach(cfg => {
      const slider = document.getElementById(`slider${cfg.name}`);
      const readout = document.getElementById(`val${cfg.name}`);
      slider.addEventListener('input', () => {
        readout.textContent = `${slider.value}${cfg.unit}`;
        showRecalc(true);
        debouncedSimulate();
      });
    });

    // Backlog Stepper buttons
    const valBacklogs = document.getElementById('valBacklogs');
    document.getElementById('btnBacklogDec').addEventListener('click', () => {
      if (simulatedBacklogs > 0) {
        simulatedBacklogs--;
        valBacklogs.textContent = simulatedBacklogs;
        showRecalc(true);
        debouncedSimulate();
      }
    });

    document.getElementById('btnBacklogInc').addEventListener('click', () => {
      if (simulatedBacklogs < 6) {
        simulatedBacklogs++;
        valBacklogs.textContent = simulatedBacklogs;
        showRecalc(true);
        debouncedSimulate();
      }
    });

    // Reset button
    document.getElementById('btnResetSimulation').addEventListener('click', () => {
      if (currentStudent) {
        loadStudentData(currentStudent.id);
      }
    });
  }

  function showRecalc(visible) {
    const el = document.getElementById('recalcStatus');
    if (el) {
      if (visible) el.classList.add('visible');
      else el.classList.remove('visible');
    }
  }

  async function runSimulation() {
    if (!currentStudent) return;
    showRecalc(true);

    const overrides = {
      attendance_pct: Number(document.getElementById('sliderAttendance').value),
      quiz_avg: Number(document.getElementById('sliderQuiz').value),
      assignment_pct: Number(document.getElementById('sliderAssignment').value),
      internal_marks: Number(document.getElementById('sliderInternal').value),
      practical_marks: Number(document.getElementById('sliderPractical').value),
      backlogs: simulatedBacklogs
    };

    try {
      const result = await window.API.simulateWhatIf(currentStudent.id, overrides);
      renderSimulationResult(result);
    } catch (err) {
      console.error('Simulation calculation failed:', err);
    } finally {
      showRecalc(false);
    }
  }

  function renderSimulationResult(result) {
    const curr = result.current;
    const sim = result.simulated;

    // Badges
    document.getElementById('currentRiskBadge').innerHTML = window.Utils.renderRiskBadge(curr.risk_level);
    document.getElementById('simulatedRiskBadge').innerHTML = window.Utils.renderRiskBadge(sim.risk_level);

    // Banner logic
    const banner = document.getElementById('shiftSummaryText');
    banner.className = 'shift-summary-banner';

    const riskRank = { 'High': 3, 'Medium': 2, 'Low': 1 };
    const currRank = riskRank[curr.risk_level];
    const simRank = riskRank[sim.risk_level];

    if (simRank < currRank) {
      banner.classList.add('improved');
      banner.textContent = `Risk improved from ${curr.risk_level} to ${sim.risk_level}`;
    } else if (simRank > currRank) {
      banner.classList.add('worsened');
      banner.textContent = `Warning: Risk elevated from ${curr.risk_level} to ${sim.risk_level}`;
    } else {
      banner.classList.add('unchanged');
      banner.textContent = `Risk maintained at ${sim.risk_level}`;
    }

    // Probabilities
    renderProbSet('curr', curr.probabilities);
    renderProbSet('sim', sim.probabilities);

    // Simulated SHAP Factors
    renderSimShap(sim.factors);
  }

  function renderProbSet(prefix, probs) {
    const pLow = Math.round((probs.low || 0) * 100);
    const pMed = Math.round((probs.medium || 0) * 100);
    const pHigh = Math.round((probs.high || 0) * 100);

    document.getElementById(`${prefix}ProbLowBar`).style.width = `${pLow}%`;
    document.getElementById(`${prefix}ProbLowVal`).textContent = `${pLow}%`;

    document.getElementById(`${prefix}ProbMedBar`).style.width = `${pMed}%`;
    document.getElementById(`${prefix}ProbMedVal`).textContent = `${pMed}%`;

    document.getElementById(`${prefix}ProbHighBar`).style.width = `${pHigh}%`;
    document.getElementById(`${prefix}ProbHighVal`).textContent = `${pHigh}%`;
  }

  function renderSimShap(factors) {
    const container = document.getElementById('simShapContainer');
    if (!container) return;

    if (!factors || factors.length === 0) {
      container.innerHTML = '<div class="state-empty">No feature weights computed.</div>';
      return;
    }

    let html = '';
    factors.forEach(f => {
      const isPositive = f.shap >= 0;
      const absVal = Math.min(100, Math.round(Math.abs(f.shap) * 200));
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
        </div>
      `;
    });

    container.innerHTML = html;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
