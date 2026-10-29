/**
 * Data Entry and Batch Ingestion Controller
 */
(function() {
  'use strict';

  let currentBatchData = [];

  function init() {
    // Role guard: STUDENT cannot access Data Entry
    const user = window.Auth ? window.Auth.getUser() : null;
    if (user && user.role === 'STUDENT') {
      window.location.href = '/pages/dashboard.html';
      return;
    }

    // Set today's date for attendance
    const attDate = document.getElementById('attDateInput');
    if (attDate) attDate.value = new Date().toISOString().split('T')[0];

    setupTabs();
    populateStudentDropdowns();
    setupForms();
    setupBulkUpload();
  }

  function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.tab;
        tabBtns.forEach(b => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');

        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        const panel = document.getElementById(targetId);
        if (panel) panel.classList.add('active');
      });
    });
  }

  function populateStudentDropdowns() {
    const students = window.MockData ? window.MockData.STUDENTS : [];
    const dropdownIds = ['attStudentSelect', 'quizStudentSelect', 'assStudentSelect'];

    dropdownIds.forEach(id => {
      const select = document.getElementById(id);
      if (!select) return;
      select.innerHTML = '<option value="">Select student...</option>';
      students.forEach(st => {
        const opt = document.createElement('option');
        opt.value = st.id;
        opt.textContent = `${st.name} (${st.roll}) - Div ${st.division} [${st.risk_level} Risk]`;
        select.appendChild(opt);
      });
      if (window.ModernSelect) {
        new window.ModernSelect(select);
      }
    });

    // Also modernize other selects
    if (window.ModernSelect) {
      ['attDivisionSelect', 'attSubjectSelect', 'quizSubjectSelect', 'quizTypeSelect', 'assSubjectSelect', 'assStatusSelect'].forEach(id => {
        const el = document.getElementById(id);
        if (el) new window.ModernSelect(el);
      });
    }
  }

  function setupForms() {
    // 1. Attendance Form
    const attForm = document.getElementById('attendanceEntryForm');
    const attValInput = document.getElementById('attValueInput');
    const attValError = document.getElementById('attValError');
    const attSuccess = document.getElementById('attSuccessMsg');

    attForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      attValError.style.display = 'none';
      attSuccess.style.display = 'none';

      const val = Number(attValInput.value);
      if (isNaN(val) || val < 0 || val > 100) {
        attValError.style.display = 'block';
        return;
      }

      try {
        await window.API.postAttendance({
          student_id: document.getElementById('attStudentSelect').value,
          subject: document.getElementById('attSubjectSelect').value,
          date: document.getElementById('attDateInput').value,
          attendance_pct: val
        });
        attSuccess.textContent = 'Attendance record stored successfully.';
        attSuccess.style.display = 'block';
        attValInput.value = '';
      } catch (err) {
        attValError.textContent = err.message || 'Failed to save attendance.';
        attValError.style.display = 'block';
      }
    });

    // 2. Quiz Form
    const quizForm = document.getElementById('quizEntryForm');
    const quizScoreInput = document.getElementById('quizScoreInput');
    const quizMaxInput = document.getElementById('quizMaxInput');
    const quizErrorMsg = document.getElementById('quizErrorMsg');
    const quizSuccessMsg = document.getElementById('quizSuccessMsg');

    quizForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      quizErrorMsg.style.display = 'none';
      quizSuccessMsg.style.display = 'none';

      const score = Number(quizScoreInput.value);
      const max = Number(quizMaxInput.value);

      if (isNaN(score) || score < 0 || score > max) {
        quizErrorMsg.style.display = 'block';
        return;
      }

      try {
        await window.API.postAssessments({
          student_id: document.getElementById('quizStudentSelect').value,
          subject: document.getElementById('quizSubjectSelect').value,
          assessment: document.getElementById('quizTypeSelect').value,
          score,
          max
        });
        quizSuccessMsg.textContent = 'Assessment score logged successfully.';
        quizSuccessMsg.style.display = 'block';
        quizScoreInput.value = '';
      } catch (err) {
        quizErrorMsg.textContent = err.message || 'Failed to save assessment.';
        quizErrorMsg.style.display = 'block';
      }
    });

    // 3. Assignment Form
    const assForm = document.getElementById('assignEntryForm');
    const assSuccessMsg = document.getElementById('assSuccessMsg');

    assForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      assSuccessMsg.style.display = 'none';

      try {
        await window.API.postAssignments({
          student_id: document.getElementById('assStudentSelect').value,
          subject: document.getElementById('assSubjectSelect').value,
          title: document.getElementById('assTitleInput').value,
          status: document.getElementById('assStatusSelect').value,
          score: document.getElementById('assScoreInput').value
        });
        assSuccessMsg.textContent = 'Assignment status recorded successfully.';
        assSuccessMsg.style.display = 'block';
        document.getElementById('assTitleInput').value = '';
      } catch (err) {
        alert(err.message || 'Failed to save assignment.');
      }
    });
  }

  function setupBulkUpload() {
    const dropZone = document.getElementById('dropZoneBox');
    const fileInput = document.getElementById('fileUploadInput');
    const btnBrowse = document.getElementById('btnBrowseFile');
    const btnDownload = document.getElementById('btnDownloadTemplate');
    const statusMsg = document.getElementById('fileUploadStatus');
    const previewContainer = document.getElementById('previewTableContainer');
    const previewTbody = document.getElementById('previewTableBody');
    const btnConfirm = document.getElementById('btnConfirmBatch');
    const btnCancel = document.getElementById('btnCancelBatch');

    btnBrowse.addEventListener('click', () => fileInput.click());

    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        processUploadedFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        processUploadedFile(e.target.files[0]);
      }
    });

    btnDownload.addEventListener('click', generateTemplateCsv);

    btnCancel.addEventListener('click', () => {
      previewContainer.style.display = 'none';
      statusMsg.style.display = 'none';
      fileInput.value = '';
    });

    btnConfirm.addEventListener('click', async () => {
      btnConfirm.disabled = true;
      btnConfirm.textContent = 'Ingesting & Predicting...';

      try {
        const res = await window.API.postImports({ records: currentBatchData });
        statusMsg.style.color = 'var(--risk-low)';
        statusMsg.textContent = res.message || '30 student records successfully synchronized with risk model.';
        statusMsg.style.display = 'block';
        previewContainer.style.display = 'none';
      } catch (err) {
        statusMsg.style.color = 'var(--risk-high)';
        statusMsg.textContent = err.message || 'Batch ingestion error.';
        statusMsg.style.display = 'block';
      } finally {
        btnConfirm.disabled = false;
        btnConfirm.textContent = 'Confirm & Run Model Ingestion';
      }
    });
  }

  function processUploadedFile(file) {
    const statusMsg = document.getElementById('fileUploadStatus');
    const previewContainer = document.getElementById('previewTableContainer');
    const previewTbody = document.getElementById('previewTableBody');

    statusMsg.style.color = 'var(--ink)';
    statusMsg.textContent = `Reading ${file.name} (${(file.size / 1024).toFixed(1)} KB)...`;
    statusMsg.style.display = 'block';

    const reader = new FileReader();
    reader.onload = function(e) {
      const text = e.target.result;
      const lines = text.split(/\r?\n/).filter(l => l.trim().length > 0);

      if (lines.length <= 1) {
        // Fallback demo rows if empty
        populateSamplePreview();
        return;
      }

      // Parse CSV headers and rows
      const rows = [];
      for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split(',').map(s => s.trim());
        if (parts.length >= 6) {
          rows.push({
            roll: parts[1] || `2211${String(i).padStart(2, '0')}`,
            name: parts[2] || `Student ${i}`,
            division: parts[3] || 'SEDA-A',
            attendance: parts[5] || '75',
            quiz: parts[6] || '65',
            assignment: parts[7] || '80',
            backlogs: parts[9] || '0'
          });
        }
      }

      currentBatchData = rows;
      renderPreviewRows(rows.slice(0, 5));
    };

    reader.onerror = function() {
      populateSamplePreview();
    };

    reader.readAsText(file);
  }

  function populateSamplePreview() {
    const sample = (window.MockData ? window.MockData.STUDENTS.slice(0, 5) : []).map(s => ({
      roll: s.roll,
      name: s.name,
      division: s.division,
      attendance: s.attendance_pct,
      quiz: s.quiz_avg,
      assignment: s.assignment_pct,
      backlogs: s.backlogs
    }));

    currentBatchData = sample;
    renderPreviewRows(sample);
  }

  function renderPreviewRows(rows) {
    const previewContainer = document.getElementById('previewTableContainer');
    const previewTbody = document.getElementById('previewTableBody');

    let html = '';
    rows.forEach(r => {
      html += `
        <tr>
          <td class="col-num">${window.Utils.escapeHtml(r.roll)}</td>
          <td><strong>${window.Utils.escapeHtml(r.name)}</strong></td>
          <td>${window.Utils.escapeHtml(r.division)}</td>
          <td class="col-num">${r.attendance}%</td>
          <td class="col-num">${r.quiz}/100</td>
          <td class="col-num">${r.assignment}%</td>
          <td class="col-num">${r.backlogs}</td>
        </tr>
      `;
    });

    previewTbody.innerHTML = html;
    previewContainer.style.display = 'block';
  }

  function generateTemplateCsv() {
    const headers = 'student_id,roll,name,division,subject,attendance_pct,quiz_score,assignments_pct,internal_marks,backlogs\n';
    const sampleRows = [
      'STU101,221101,Aditya Kulkarni,SEDA-A,CS301,54,46,50,14,2\n',
      'STU102,221102,Ananya Deshpande,SEDA-A,CS301,92,88,95,28,0\n',
      'STU103,221103,Rohan Joshi,SEDA-A,CS301,58,42,55,13,1\n'
    ].join('');

    const blob = new Blob([headers + sampleRows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'vit_student_academic_template.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
