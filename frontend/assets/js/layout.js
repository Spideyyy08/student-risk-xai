/**
 * Application Shell Injector
 * Dynamically injects consistent sidebar, topbar, and drawer into all protected pages
 */
(function(window) {
  'use strict';

  // SVG Icons (16px, 1.5px stroke, inline)
  const ICONS = {
    dashboard: '<svg class="nav-icon" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>',
    students: '<svg class="nav-icon" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    simulator: '<svg class="nav-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 3v18"/><path d="M3 12h18"/><path d="m18 15-6-6-6 6"/></svg>',
    interventions: '<svg class="nav-icon" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    dataEntry: '<svg class="nav-icon" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
    logout: '<svg style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:1.5" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
    menu: '<svg style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2" viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>'
  };

  function initLayout() {
    // Check authentication first
    if (window.Auth) {
      window.Auth.guard();
    }

    const path = window.location.pathname;
    const isLoginPage = path.endsWith('index.html') || path === '/' || path.endsWith('/frontend/');
    if (isLoginPage) return;

    const user = window.Auth ? window.Auth.getUser() : { name: 'Faculty Member', role: 'TEACHER' };
    const pageTitle = document.body.dataset.pageTitle || 'Academic Dashboard';

    // Build Role-Specific Navigation
    let navItems = [];
    if (user.role === 'STUDENT') {
      navItems = [
        { id: 'dashboard', label: 'My Advisory Portal', href: '/pages/dashboard.html', icon: ICONS.dashboard },
        { id: 'myProfile', label: 'My Academic Profile', href: '/pages/student-detail.html?id=STU101', icon: ICONS.students },
        { id: 'simulator', label: 'What-If Remediation', href: '/pages/what-if.html?student_id=STU101', icon: ICONS.simulator }
      ];
    } else if (user.role === 'ADMIN') {
      navItems = [
        { id: 'dashboard', label: 'Department Overview', href: '/pages/dashboard.html', icon: ICONS.dashboard },
        { id: 'students', label: 'Student Cohorts', href: '/pages/students.html', icon: ICONS.students },
        { id: 'simulator', label: 'What-If Policy Lab', href: '/pages/what-if.html', icon: ICONS.simulator },
        { id: 'interventions', label: 'Faculty Interventions', href: '/pages/interventions.html', icon: ICONS.interventions },
        { id: 'dataEntry', label: 'Data & Model Ingestion', href: '/pages/data-entry.html', icon: ICONS.dataEntry }
      ];
    } else {
      // TEACHER (Faculty)
      navItems = [
        { id: 'dashboard', label: 'Class Overview', href: '/pages/dashboard.html', icon: ICONS.dashboard },
        { id: 'students', label: 'Students Directory', href: '/pages/students.html', icon: ICONS.students },
        { id: 'simulator', label: 'What-If Simulator', href: '/pages/what-if.html', icon: ICONS.simulator },
        { id: 'interventions', label: 'Interventions Log', href: '/pages/interventions.html', icon: ICONS.interventions },
        { id: 'dataEntry', label: 'Data Entry', href: '/pages/data-entry.html', icon: ICONS.dataEntry }
      ];
    }

    let navListHtml = '';
    navItems.forEach(item => {
      const isActive = path === item.href || (item.id === 'students' && path.includes('students.html')) || (item.id === 'myProfile' && path.includes('student-detail.html'));
      navListHtml += `
        <li class="nav-item">
          <a href="${item.href}" class="nav-link ${isActive ? 'active' : ''}" data-nav-id="${item.id}">
            ${item.icon}
            <span>${item.label}</span>
          </a>
        </li>
      `;
    });

    let roleBadgeText = user.role;
    if (user.role === 'ADMIN') roleBadgeText = 'HOD / ADMIN';
    else if (user.role === 'TEACHER') roleBadgeText = 'FACULTY';
    else if (user.role === 'STUDENT') roleBadgeText = 'STUDENT';

    const sidebarHtml = `
      <aside class="app-sidebar" id="appSidebar">
        <div class="sidebar-header">
          <img src="/assets/img/logo.svg" alt="VIT Logo" class="sidebar-logo" />
          <div class="sidebar-brand">
            <span class="sidebar-brand-title">VIT Pune</span>
            <span class="sidebar-brand-sub">Computer Engineering</span>
          </div>
        </div>
        <ul class="sidebar-nav">
          ${navListHtml}
        </ul>
        <div class="sidebar-footer">
          <div class="user-profile-summary">
            <span class="user-name">${window.Utils.escapeHtml(user.name)}</span>
            <span class="user-role-badge">${roleBadgeText}</span>
          </div>
          <button type="button" class="btn-sidebar-logout" id="btnLogout">
            ${ICONS.logout}
            <span>Sign out</span>
          </button>
        </div>
      </aside>
      <div class="sidebar-backdrop" id="sidebarBackdrop"></div>
    `;

    const topbarHtml = `
      <header class="app-topbar">
        <div class="topbar-left">
          <button type="button" class="mobile-menu-btn" id="mobileMenuBtn" aria-label="Toggle navigation drawer">
            ${ICONS.menu}
          </button>
          <h1 class="page-title">${window.Utils.escapeHtml(pageTitle)}</h1>
        </div>
        <div class="topbar-right">
          <label for="semSelect" class="sr-only" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);">Semester Select</label>
          <select id="semSelect" class="academic-period-select" aria-label="Academic Semester">
            <option value="sem5" selected>Sem 5 (AY 2026-27)</option>
            <option value="sem4">Sem 4 (AY 2025-26)</option>
          </select>
        </div>
      </header>
    `;

    // Wrap page content into app-wrapper and app-main
    const existingContent = document.body.innerHTML;
    document.body.innerHTML = `
      <div class="app-wrapper">
        ${sidebarHtml}
        <div class="app-main">
          ${topbarHtml}
          <main class="app-content">
            ${existingContent}
          </main>
        </div>
      </div>
    `;

    // Attach Logout Event
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
      btnLogout.addEventListener('click', () => {
        if (window.Auth) window.Auth.logout();
      });
    }

    // Attach Semester Switcher
    const semSelect = document.getElementById('semSelect');
    if (semSelect) {
      const activeSem = sessionStorage.getItem('academic_semester') || 'sem5';
      semSelect.value = activeSem;
      semSelect.addEventListener('change', (e) => {
        sessionStorage.setItem('academic_semester', e.target.value);
        window.dispatchEvent(new CustomEvent('academicSemesterChanged', { detail: { semester: e.target.value } }));
      });
    }

    // Attach Mobile Drawer Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const appSidebar = document.getElementById('appSidebar');
    const sidebarBackdrop = document.getElementById('sidebarBackdrop');

    if (mobileMenuBtn && appSidebar && sidebarBackdrop) {
      mobileMenuBtn.addEventListener('click', () => {
        appSidebar.classList.toggle('open');
        sidebarBackdrop.classList.toggle('active');
      });

      sidebarBackdrop.addEventListener('click', () => {
        appSidebar.classList.remove('open');
        sidebarBackdrop.classList.remove('active');
      });
    }
  }

  // Auto-init on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLayout);
  } else {
    initLayout();
  }
})(window);
