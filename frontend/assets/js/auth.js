/**
 * Authentication and Role Guard Module
 * Uses sessionStorage for secure session lifetime token retention
 */
(function(window) {
  'use strict';

  function isAuthenticated() {
    return Boolean(sessionStorage.getItem('access_token'));
  }

  function getUser() {
    return {
      token: sessionStorage.getItem('access_token'),
      role: sessionStorage.getItem('user_role') || 'TEACHER',
      name: sessionStorage.getItem('user_name') || 'Faculty Member'
    };
  }

  function setSession(authData) {
    sessionStorage.setItem('access_token', authData.access_token);
    sessionStorage.setItem('user_role', authData.role);
    sessionStorage.setItem('user_name', authData.name);
  }

  function logout() {
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user_role');
    sessionStorage.removeItem('user_name');
    window.location.href = '/index.html';
  }

  /**
   * Guard protected pages. If unauthenticated, redirect to login.
   * If authenticated but trying to access index.html, redirect to dashboard.
   */
  function guard() {
    const path = window.location.pathname;
    const isLoginPage = path.endsWith('index.html') || path === '/' || path.endsWith('/frontend/');

    if (!isAuthenticated()) {
      if (!isLoginPage) {
        window.location.href = '/index.html';
      }
      return;
    }

    if (isLoginPage && isAuthenticated()) {
      window.location.href = '/pages/dashboard.html';
      return;
    }

    // Role-based route guard: Students cannot access Data Entry, Interventions, or the full Student Directory
    const user = getUser();
    if (user.role === 'STUDENT') {
      if (path.includes('data-entry.html') || path.includes('interventions.html') || path.includes('students.html')) {
        window.location.href = '/pages/student-detail.html?id=STU101';
      }
    }
  }

  window.Auth = {
    isAuthenticated,
    getUser,
    setSession,
    logout,
    guard
  };
})(window);
