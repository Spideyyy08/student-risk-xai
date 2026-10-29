/**
 * Students Directory Page Controller
 */
(function() {
  'use strict';

  let currentPage = 1;
  const pageSize = 10;
  let currentSort = { field: 'roll', direction: 'asc' };

  // Parse URL query params
  const urlParams = new URLSearchParams(window.location.search);
  const initialRisk = urlParams.get('risk') || 'ALL';
  const initialDiv = urlParams.get('division') || 'ALL';

  async function loadStudents() {
    const q = document.getElementById('searchInput').value.trim();
    const division = document.getElementById('divisionSelect').value;
    const risk = document.getElementById('riskSelect').value;

    const tbody = document.getElementById('studentsTableBody');
    tbody.innerHTML = '<tr><td colspan="10" class="state-loading">Loading student records...</td></tr>';

    try {
      // Fetch full matching set to allow custom client sorting and exact pagination
      const data = await window.API.getStudents({
        q: q,
        division: division,
        risk: risk,
        page: 1
      });

      // Fetch all items without page limit for accurate sorting & pagination
      let allItems = (window.MockData ? window.MockData.STUDENTS : []).filter(s => {
        if (division !== 'ALL' && s.division !== division) return false;
        if (risk !== 'ALL' && s.risk_level.toUpperCase() !== risk.toUpperCase()) return false;
        if (q) {
          const match = s.name.toLowerCase().includes(q.toLowerCase()) ||
                        s.roll.toLowerCase().includes(q.toLowerCase());
          if (!match) return false;
        }
        return true;
      });

      // Apply sorting
      allItems.sort((a, b) => {
        let valA = a[currentSort.field];
        let valB = b[currentSort.field];

        if (currentSort.field === 'risk') {
          const riskRank = { 'High': 3, 'Medium': 2, 'Low': 1 };
          valA = riskRank[a.risk_level] || 0;
          valB = riskRank[b.risk_level] || 0;
        } else if (currentSort.field === 'att') {
          valA = a.attendance_pct;
          valB = b.attendance_pct;
        } else if (currentSort.field === 'quiz') {
          valA = a.quiz_avg;
          valB = b.quiz_avg;
        }

        if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
        if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
      });

      // Pagination slice
      const total = allItems.length;
      const totalPages = Math.ceil(total / pageSize) || 1;
      if (currentPage > totalPages) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      const startIndex = (currentPage - 1) * pageSize;
      const pageItems = allItems.slice(startIndex, startIndex + pageSize);

      renderTableRows(pageItems);
      renderPagination(total, totalPages, startIndex, pageItems.length);
      updateSortIndicators();
    } catch (err) {
      console.error('Error loading students:', err);
      tbody.innerHTML = '<tr><td colspan="10" class="state-error">Failed to load student records.</td></tr>';
    }
  }

  function renderTableRows(students) {
    const tbody = document.getElementById('studentsTableBody');
    if (!tbody) return;

    if (students.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" class="state-empty">No students match the selected criteria.</td></tr>';
      return;
    }

    let html = '';
    students.forEach(st => {
      html += `
        <tr>
          <td class="col-num">${window.Utils.escapeHtml(st.roll)}</td>
          <td><strong>${window.Utils.escapeHtml(st.name)}</strong></td>
          <td>${window.Utils.escapeHtml(st.division)}</td>
          <td>${window.Utils.renderRiskBadge(st.risk_level)}</td>
          <td class="col-num">${st.attendance_pct}%</td>
          <td class="col-num">${st.quiz_avg}/100</td>
          <td class="col-num">${st.assignment_pct}%</td>
          <td class="col-num">${st.internal_marks}/30</td>
          <td class="col-num">${st.backlogs}</td>
          <td>
            <a href="/pages/student-detail.html?id=${encodeURIComponent(st.id)}" class="btn btn-secondary btn-sm">
              View Profile
            </a>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  }

  function renderPagination(total, totalPages, start, count) {
    const summary = document.getElementById('paginationSummary');
    const indicator = document.getElementById('pageIndicator');
    const prevBtn = document.getElementById('btnPrevPage');
    const nextBtn = document.getElementById('btnNextPage');
    const recordCount = document.getElementById('tableRecordCount');

    if (total === 0) {
      summary.textContent = 'Showing 0 records';
      indicator.textContent = 'Page 0 of 0';
      prevBtn.disabled = true;
      nextBtn.disabled = true;
      recordCount.textContent = '0 total records';
      return;
    }

    summary.textContent = `Showing ${start + 1} to ${start + count} of ${total} students`;
    indicator.textContent = `Page ${currentPage} of ${totalPages}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    recordCount.textContent = `${total} matching records`;
  }

  function updateSortIndicators() {
    ['Roll', 'Name', 'Risk', 'Att', 'Quiz', 'Backlogs'].forEach(col => {
      const el = document.getElementById(`sort${col}`);
      if (el) el.textContent = '';
    });

    const activeMap = {
      roll: 'sortRoll',
      name: 'sortName',
      risk: 'sortRisk',
      att: 'sortAtt',
      quiz: 'sortQuiz',
      backlogs: 'sortBacklogs'
    };

    const targetId = activeMap[currentSort.field];
    if (targetId) {
      const el = document.getElementById(targetId);
      if (el) {
        el.textContent = currentSort.direction === 'asc' ? '▲' : '▼';
      }
    }
  }

  function setupEvents() {
    const filterForm = document.getElementById('filterForm');
    const resetBtn = document.getElementById('btnResetFilters');
    const prevBtn = document.getElementById('btnPrevPage');
    const nextBtn = document.getElementById('btnNextPage');

    // Preset initial dropdown values if specified in URL
    if (initialRisk !== 'ALL') {
      document.getElementById('riskSelect').value = initialRisk;
    }
    if (initialDiv !== 'ALL') {
      document.getElementById('divisionSelect').value = initialDiv;
    }

    // Initialize ModernSelect dropdowns
    let modDiv = null, modRisk = null, modSub = null;
    if (window.ModernSelect) {
      modDiv = new window.ModernSelect(document.getElementById('divisionSelect'));
      modRisk = new window.ModernSelect(document.getElementById('riskSelect'));
      modSub = new window.ModernSelect(document.getElementById('subjectSelect'));
    }

    // Auto-filter on select change
    ['divisionSelect', 'riskSelect', 'subjectSelect'].forEach(id => {
      document.getElementById(id).addEventListener('change', () => {
        currentPage = 1;
        loadStudents();
      });
    });

    // Real-time search with debounce
    document.getElementById('searchInput').addEventListener('input', window.Utils.debounce(() => {
      currentPage = 1;
      loadStudents();
    }, 250));

    filterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      currentPage = 1;
      loadStudents();
    });

    resetBtn.addEventListener('click', () => {
      document.getElementById('searchInput').value = '';
      document.getElementById('divisionSelect').value = 'ALL';
      document.getElementById('riskSelect').value = 'ALL';
      document.getElementById('subjectSelect').value = 'ALL';
      if (modDiv) modDiv.refresh();
      if (modRisk) modRisk.refresh();
      if (modSub) modSub.refresh();
      currentPage = 1;
      loadStudents();
    });

    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        loadStudents();
      }
    });

    nextBtn.addEventListener('click', () => {
      currentPage++;
      loadStudents();
    });

    // Export cohort CSV
    const btnExport = document.getElementById('btnExportStudentsCsv');
    if (btnExport) {
      btnExport.addEventListener('click', () => {
        const sem = sessionStorage.getItem('academic_semester') || 'sem5';
        const students = window.MockData ? window.MockData.getStudentPool(sem) : [];
        let csv = 'Roll_No,Student_Name,Division,Semester,Risk_Level,Attendance_Pct,Quiz_Average,Assignment_Pct,Internal_Marks,Backlogs\n';
        students.forEach(s => {
          csv += `${s.roll},"${s.name}",${s.division},${s.semester},${s.risk_level},${s.attendance_pct},${s.quiz_avg},${s.assignment_pct},${s.internal_marks},${s.backlogs}\n`;
        });
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vit_students_cohort_${sem}.csv`;
        a.click();
      });
    }

    // Column sorting clicks
    document.querySelectorAll('#studentsTable th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const field = th.dataset.sort;
        if (currentSort.field === field) {
          currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
          currentSort.field = field;
          currentSort.direction = 'asc';
        }
        loadStudents();
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setupEvents();
      loadStudents();
    });
  } else {
    setupEvents();
    loadStudents();
  }
})();
