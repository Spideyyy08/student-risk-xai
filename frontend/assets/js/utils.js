/**
 * Utility functions for formatting, sanitization, and UI helpers
 */
(function(window) {
  'use strict';

  /**
   * Escape HTML to prevent XSS injections
   */
  function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Format date into DD Mon YYYY (e.g., 28 Oct 2026)
   */
  function formatDate(dateInput) {
    if (!dateInput) return '-';
    const d = new Date(dateInput);
    if (isNaN(d.getTime())) return String(dateInput);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const day = String(d.getDate()).padStart(2, '0');
    const mon = months[d.getMonth()];
    const yr = d.getFullYear();
    return `${day} ${mon} ${yr}`;
  }

  /**
   * Format number as percentage
   */
  function formatPct(val, decimals = 0) {
    if (val === null || val === undefined || isNaN(val)) return '0%';
    return Number(val).toFixed(decimals) + '%';
  }

  /**
   * Generate HTML for a risk badge (Low / Medium / High)
   */
  function renderRiskBadge(riskLevel) {
    const raw = (riskLevel || '').toUpperCase();
    let cls = 'badge-risk-low';
    let label = 'Low';
    if (raw.includes('HIGH')) {
      cls = 'badge-risk-high';
      label = 'High';
    } else if (raw.includes('MED')) {
      cls = 'badge-risk-medium';
      label = 'Medium';
    } else {
      cls = 'badge-risk-low';
      label = 'Low';
    }
    return `<span class="badge ${cls}">${escapeHtml(label)}</span>`;
  }

  /**
   * Generate priority badge
   */
  function renderPriorityBadge(priority) {
    const raw = (priority || '').toLowerCase();
    let cls = 'badge-priority-low';
    let label = 'Low';
    if (raw === 'high') {
      cls = 'badge-priority-high';
      label = 'High';
    } else if (raw === 'medium') {
      cls = 'badge-priority-medium';
      label = 'Medium';
    }
    return `<span class="badge ${cls}">${escapeHtml(label)}</span>`;
  }

  /**
   * Generate status badge
   */
  function renderStatusBadge(status) {
    const raw = (status || '').toLowerCase();
    let cls = 'badge-status-planned';
    let label = status;
    if (raw.includes('comp')) {
      cls = 'badge-status-completed';
      label = 'Completed';
    } else if (raw.includes('prog')) {
      cls = 'badge-status-progress';
      label = 'In progress';
    } else {
      cls = 'badge-status-planned';
      label = 'Planned';
    }
    return `<span class="badge ${cls}">${escapeHtml(label)}</span>`;
  }

  /**
   * Debounce function for inputs/sliders
   */
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  window.Utils = {
    escapeHtml,
    formatDate,
    formatPct,
    renderRiskBadge,
    renderPriorityBadge,
    renderStatusBadge,
    debounce
  };
})(window);
