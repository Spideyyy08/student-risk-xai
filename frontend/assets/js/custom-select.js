/**
 * Modern Custom Dropdown Component
 * Replaces archaic native OS selects with a polished, searchable, rich dropdown
 * displaying student details, division chips, and risk badges.
 */
(function(window) {
  'use strict';

  class ModernSelect {
    constructor(selectElement, options = {}) {
      if (!selectElement) return;
      this.originalSelect = selectElement;
      this.options = options;
      this.isOpen = false;
      this.init();
    }

    init() {
      // Hide original select visually but keep accessible
      this.originalSelect.style.display = 'none';

      // Create modern wrapper
      this.wrapper = document.createElement('div');
      this.wrapper.className = 'modern-select-wrapper ' + (this.options.customClass || '');
      this.wrapper.tabIndex = 0;

      // Trigger button
      this.trigger = document.createElement('div');
      this.trigger.className = 'modern-select-trigger';
      this.trigger.innerHTML = `
        <div class="modern-select-selected-content">
          <span class="selected-main-text">Loading...</span>
        </div>
        <svg class="modern-select-chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      `;

      // Dropdown panel
      this.panel = document.createElement('div');
      this.panel.className = 'modern-select-panel';

      // Search input if enabled (default true for lists > 6 items)
      this.enableSearch = this.options.searchable !== false && this.originalSelect.options.length > 5;
      if (this.enableSearch) {
        this.searchContainer = document.createElement('div');
        this.searchContainer.className = 'modern-select-search-box';
        this.searchContainer.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="search-icon">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input type="text" class="modern-select-search-input" placeholder="Type to filter..." />
        `;
        this.panel.appendChild(this.searchContainer);
        this.searchInput = this.searchContainer.querySelector('.modern-select-search-input');
      }

      // Options list
      this.list = document.createElement('div');
      this.list.className = 'modern-select-list';
      this.panel.appendChild(this.list);

      this.wrapper.appendChild(this.trigger);
      this.wrapper.appendChild(this.panel);

      this.originalSelect.parentNode.insertBefore(this.wrapper, this.originalSelect);

      this.populateOptions();
      this.updateTriggerContent();
      this.bindEvents();
    }

    populateOptions(filterText = '') {
      this.list.innerHTML = '';
      const filter = (filterText || '').toLowerCase().trim();
      let matchCount = 0;

      Array.from(this.originalSelect.options).forEach((opt, idx) => {
        const text = opt.textContent;
        const val = opt.value;
        const isSelected = opt.selected;

        if (filter && !text.toLowerCase().includes(filter) && !val.toLowerCase().includes(filter)) {
          return;
        }

        matchCount++;
        const item = document.createElement('div');
        item.className = 'modern-select-item ' + (isSelected ? 'selected' : '');
        item.dataset.value = val;
        item.dataset.index = idx;

        // Rich formatting for student options: e.g. "Aditya Kulkarni (221101) - Div SEDA-A [High Risk]"
        if (text.includes('(') && text.includes('Risk')) {
          item.innerHTML = this.formatStudentOption(text);
        } else {
          item.innerHTML = `
            <span class="item-text">${window.Utils.escapeHtml(text)}</span>
            ${isSelected ? '<svg class="item-check" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>' : ''}
          `;
        }

        item.addEventListener('click', (e) => {
          e.stopPropagation();
          this.selectOption(val);
        });

        this.list.appendChild(item);
      });

      if (matchCount === 0) {
        this.list.innerHTML = '<div class="modern-select-empty">No matching options</div>';
      }
    }

    formatStudentOption(rawText) {
      // Regex parsing: "Aditya Kulkarni (221101) - Div SEDA-A [High Risk]"
      const match = rawText.match(/^(.*?)\s*\((.*?)\)\s*-\s*Div\s*(.*?)\s*\[(.*?)\]/);
      if (match) {
        const name = match[1];
        const roll = match[2];
        const div = match[3];
        const risk = match[4];

        let riskCls = 'badge-risk-low';
        if (risk.toLowerCase().includes('high')) riskCls = 'badge-risk-high';
        else if (risk.toLowerCase().includes('med')) riskCls = 'badge-risk-medium';

        return `
          <div class="student-item-main">
            <span class="student-item-name">${window.Utils.escapeHtml(name)}</span>
            <div class="student-item-meta">
              <span class="mono">${window.Utils.escapeHtml(roll)}</span>
              <span class="div-tag">${window.Utils.escapeHtml(div)}</span>
            </div>
          </div>
          <span class="badge ${riskCls}">${window.Utils.escapeHtml(risk)}</span>
        `;
      }
      return `<span class="item-text">${window.Utils.escapeHtml(rawText)}</span>`;
    }

    updateTriggerContent() {
      const selectedOpt = this.originalSelect.options[this.originalSelect.selectedIndex];
      if (!selectedOpt) return;

      const text = selectedOpt.textContent;
      const contentEl = this.trigger.querySelector('.modern-select-selected-content');

      if (text.includes('(') && text.includes('Risk')) {
        const match = text.match(/^(.*?)\s*\((.*?)\)\s*-\s*Div\s*(.*?)\s*\[(.*?)\]/);
        if (match) {
          const name = match[1];
          const roll = match[2];
          const div = match[3];
          const risk = match[4];

          let riskCls = 'badge-risk-low';
          if (risk.toLowerCase().includes('high')) riskCls = 'badge-risk-high';
          else if (risk.toLowerCase().includes('med')) riskCls = 'badge-risk-medium';

          contentEl.innerHTML = `
            <span class="selected-name">${window.Utils.escapeHtml(name)}</span>
            <span class="selected-roll mono">(${window.Utils.escapeHtml(roll)})</span>
            <span class="selected-div-pill">${window.Utils.escapeHtml(div)}</span>
            <span class="badge ${riskCls}" style="margin-left:auto; flex-shrink: 0;">${window.Utils.escapeHtml(risk)}</span>
          `;
          return;
        }
      }

      contentEl.innerHTML = `<span class="selected-main-text">${window.Utils.escapeHtml(text)}</span>`;
    }

    selectOption(val) {
      this.originalSelect.value = val;
      // Trigger native change event so listeners update!
      this.originalSelect.dispatchEvent(new Event('change', { bubbles: true }));
      this.updateTriggerContent();
      this.close();
    }

    open() {
      // Close other open modern-selects
      document.querySelectorAll('.modern-select-wrapper.open').forEach(el => {
        if (el !== this.wrapper) el.classList.remove('open');
      });

      this.populateOptions();
      this.wrapper.classList.add('open');
      this.isOpen = true;

      if (this.searchInput) {
        this.searchInput.value = '';
        setTimeout(() => this.searchInput.focus(), 50);
      }
    }

    close() {
      this.wrapper.classList.remove('open');
      this.isOpen = false;
    }

    toggle() {
      if (this.isOpen) this.close();
      else this.open();
    }

    refresh() {
      this.populateOptions();
      this.updateTriggerContent();
    }

    bindEvents() {
      this.trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggle();
      });

      if (this.searchInput) {
        this.searchInput.addEventListener('input', (e) => {
          this.populateOptions(e.target.value);
        });
        this.searchInput.addEventListener('click', (e) => e.stopPropagation());
      }

      document.addEventListener('click', (e) => {
        if (!this.wrapper.contains(e.target)) {
          this.close();
        }
      });

      this.wrapper.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.close();
        }
      });
    }
  }

  window.ModernSelect = ModernSelect;
})(window);
