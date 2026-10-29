/**
 * Chart.js Integration Module
 * Enhanced modern dataviz with refined palettes, rounded bar geometries,
 * interactive percentage toggles, threshold reference lines, and responsive layouts.
 */
(function(window) {
  'use strict';

  const PALETTE = {
    ink: '#1B2B4B',
    inkLight: '#3D5174',
    accent: '#8A6D2F',
    riskLow: '#10B981',      // Modern clean emerald
    riskMedium: '#F59E0B',   // Modern warm amber
    riskHigh: '#EF4444',     // Modern vibrant ruby
    grid: '#EAEFF5',
    text: '#1E293B',
    textMuted: '#64748B'
  };

  const chartInstances = {};

  function destroyExisting(canvasId) {
    if (chartInstances[canvasId]) {
      chartInstances[canvasId].destroy();
      delete chartInstances[canvasId];
    }
  }

  /**
   * 1. Stacked Bar Chart: Risk distribution by division
   * Supports both count mode and percentage mode
   */
  function renderStackedDivisionChart(canvasId, divisions, asPercentage = false) {
    if (!window.Chart) return;
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    destroyExisting(canvasId);

    const labels = divisions.map(d => d.division);

    let lowData, medData, highData;
    if (asPercentage) {
      lowData = divisions.map(d => Math.round((d.low / d.total) * 100));
      medData = divisions.map(d => Math.round((d.medium / d.total) * 100));
      highData = divisions.map(d => Math.round((d.high / d.total) * 100));
    } else {
      lowData = divisions.map(d => d.low);
      medData = divisions.map(d => d.medium);
      highData = divisions.map(d => d.high);
    }

    chartInstances[canvasId] = new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Low Risk',
            data: lowData,
            backgroundColor: PALETTE.riskLow,
            borderRadius: 6,
            maxBarThickness: 44
          },
          {
            label: 'Medium Risk',
            data: medData,
            backgroundColor: PALETTE.riskMedium,
            borderRadius: 6,
            maxBarThickness: 44
          },
          {
            label: 'High Risk',
            data: highData,
            backgroundColor: PALETTE.riskHigh,
            borderRadius: 6,
            maxBarThickness: 44
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            align: 'end',
            labels: {
              boxWidth: 8,
              boxHeight: 8,
              usePointStyle: true,
              pointStyle: 'circle',
              font: { family: 'IBM Plex Sans', size: window.innerWidth < 440 ? 10 : 12, weight: '500' },
              color: PALETTE.text,
              padding: window.innerWidth < 440 ? 8 : 14
            }
          },
          tooltip: {
            backgroundColor: 'rgba(19, 30, 53, 0.95)',
            padding: 10,
            cornerRadius: 6,
            titleFont: { family: 'IBM Plex Sans', size: 12, weight: '600' },
            bodyFont: { family: 'IBM Plex Sans', size: 11 },
            callbacks: {
              label: (ctx) => {
                if (asPercentage) {
                  return ` ${ctx.dataset.label}: ${ctx.raw}% of division`;
                }
                const divObj = divisions[ctx.dataIndex];
                const pct = divObj && divObj.total ? Math.round((ctx.raw / divObj.total) * 100) : 0;
                return ` ${ctx.dataset.label}: ${ctx.raw} students (${pct}%)`;
              }
            }
          }
        },
        scales: {
          x: {
            stacked: true,
            grid: { display: false },
            ticks: {
              font: { family: 'IBM Plex Sans', size: window.innerWidth < 440 ? 11 : 13, weight: '600' },
              color: PALETTE.ink
            }
          },
          y: {
            stacked: true,
            beginAtZero: true,
            max: asPercentage ? 100 : undefined,
            grid: { color: PALETTE.grid },
            ticks: {
              font: { family: 'IBM Plex Mono', size: window.innerWidth < 440 ? 9 : 11 },
              color: PALETTE.textMuted,
              callback: (val) => asPercentage ? `${val}%` : val,
              precision: 0
            }
          }
        }
      }
    });
  }

  /**
   * 2. Horizontal Bar Chart: Class-wide Top SHAP Contributing Factors
   */
  function renderClassShapChart(canvasId, factors) {
    if (!window.Chart) return;
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    destroyExisting(canvasId);

    const labels = factors.map(f => f.factor);
    const data = factors.map(f => f.importance);
    const colors = factors.map(f => {
      if (f.direction === 'risk_raising') return PALETTE.riskHigh;
      if (f.direction === 'risk_lowering') return PALETTE.riskLow;
      return PALETTE.inkLight;
    });

    chartInstances[canvasId] = new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors,
          borderRadius: 4,
          maxBarThickness: 18
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(19, 30, 53, 0.95)',
            padding: 10,
            cornerRadius: 6,
            callbacks: {
              label: (ctx) => {
                const f = factors[ctx.dataIndex];
                const dir = f.direction === 'risk_raising' ? 'Increases Risk' : (f.direction === 'risk_lowering' ? 'Protective Factor' : 'Neutral Factor');
                return ` Relative Importance: ${(ctx.raw * 100).toFixed(0)}% (${dir})`;
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            max: 0.40,
            grid: { color: PALETTE.grid },
            ticks: {
              font: { family: 'IBM Plex Mono', size: 11 },
              color: PALETTE.textMuted,
              callback: (val) => `${(val * 100).toFixed(0)}%`
            }
          },
          y: {
            grid: { display: false },
            ticks: {
              font: { family: 'IBM Plex Sans', size: window.innerWidth < 440 ? 10 : 12, weight: '500' },
              color: PALETTE.text,
              callback: function(val) {
                const label = this.getLabelForValue(val);
                if (window.innerWidth < 440 && typeof label === 'string' && label.length > 15) {
                  return label.substring(0, 13) + '...';
                }
                return label;
              }
            }
          }
        }
      }
    });
  }

  /**
   * 3. Trend Line Chart: 6 Months Attendance (%) & Quiz Score
   * With smooth curves and 75% attendance threshold line
   */
  function renderStudentTrendsChart(canvasId, trends) {
    if (!window.Chart) return;
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    destroyExisting(canvasId);

    // 75% threshold guideline array
    const thresholdLine = trends.months.map(() => 75);

    chartInstances[canvasId] = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels: trends.months,
        datasets: [
          {
            label: 'Attendance %',
            data: trends.attendance,
            borderColor: PALETTE.ink,
            backgroundColor: 'rgba(27, 43, 75, 0.08)',
            fill: true,
            borderWidth: 2.5,
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: PALETTE.ink,
            pointHoverRadius: 6
          },
          {
            label: 'Quiz Avg (out of 100)',
            data: trends.quiz_scores,
            borderColor: PALETTE.accent,
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [4, 4],
            tension: 0.35,
            pointRadius: 4,
            pointBackgroundColor: PALETTE.accent,
            pointHoverRadius: 6
          },
          {
            label: 'Institute Guideline (75%)',
            data: thresholdLine,
            borderColor: 'rgba(239, 68, 68, 0.45)',
            borderWidth: 1.5,
            borderDash: [3, 3],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              boxWidth: 12,
              usePointStyle: true,
              font: { family: 'IBM Plex Sans', size: 12 },
              color: PALETTE.text
            }
          },
          tooltip: {
            backgroundColor: 'rgba(19, 30, 53, 0.95)',
            cornerRadius: 6
          }
        },
        scales: {
          x: {
            grid: { color: PALETTE.grid },
            ticks: { font: { family: 'IBM Plex Sans', size: 11.5 }, color: PALETTE.text }
          },
          y: {
            min: 20,
            max: 100,
            grid: { color: PALETTE.grid },
            ticks: {
              font: { family: 'IBM Plex Mono', size: 11 },
              color: PALETTE.textMuted,
              callback: (val) => `${val}%`
            }
          }
        }
      }
    });
  }

  /**
   * 4. Bar Chart: Past Semester SGPA
   */
  function renderSgpaChart(canvasId, pastSgpa) {
    if (!window.Chart) return;
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    destroyExisting(canvasId);

    chartInstances[canvasId] = new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: pastSgpa.map(p => p.semester),
        datasets: [{
          label: 'SGPA',
          data: pastSgpa.map(p => p.sgpa),
          backgroundColor: PALETTE.ink,
          borderRadius: 4,
          maxBarThickness: 42
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(19, 30, 53, 0.95)',
            cornerRadius: 6,
            callbacks: {
              label: (ctx) => ` SGPA: ${ctx.raw} / 10.0`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { family: 'IBM Plex Sans', size: 12 }, color: PALETTE.text }
          },
          y: {
            min: 0,
            max: 10,
            grid: { color: PALETTE.grid },
            ticks: { font: { family: 'IBM Plex Mono', size: 11 }, color: PALETTE.textMuted }
          }
        }
      }
    });
  }

  /**
   * 5. Subject Comparison Bar Chart
   */
  function renderSubjectBarChart(canvasId, subjects) {
    if (!window.Chart) return;
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    destroyExisting(canvasId);

    chartInstances[canvasId] = new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: subjects.map(s => s.subject_short),
        datasets: [
          {
            label: 'Attendance %',
            data: subjects.map(s => s.attendance_pct),
            backgroundColor: PALETTE.ink,
            borderRadius: 4,
            maxBarThickness: 24
          },
          {
            label: 'Quiz Avg %',
            data: subjects.map(s => s.quiz_avg),
            backgroundColor: PALETTE.accent,
            borderRadius: 4,
            maxBarThickness: 24
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              boxWidth: 12,
              font: { family: 'IBM Plex Sans', size: 12 },
              color: PALETTE.text
            }
          },
          tooltip: {
            backgroundColor: 'rgba(19, 30, 53, 0.95)',
            cornerRadius: 6
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { font: { family: 'IBM Plex Sans', size: 12 }, color: PALETTE.text }
          },
          y: {
            min: 0,
            max: 100,
            grid: { color: PALETTE.grid },
            ticks: {
              font: { family: 'IBM Plex Mono', size: 11 },
              color: PALETTE.textMuted,
              callback: (val) => `${val}%`
            }
          }
        }
      }
    });
  }

  /**
   * 6. SHAP Horizontal Bars for Simulator
   */
  function renderShapChart(canvasId, factors) {
    if (!window.Chart) return;
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    destroyExisting(canvasId);

    const labels = factors.map(f => f.label);
    const data = factors.map(f => f.shap);
    const colors = factors.map(f => f.shap >= 0 ? PALETTE.riskHigh : PALETTE.riskLow);

    chartInstances[canvasId] = new window.Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: colors,
          borderRadius: 4,
          maxBarThickness: 16
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(19, 30, 53, 0.95)',
            cornerRadius: 6,
            callbacks: {
              label: (ctx) => ` SHAP Impact: ${ctx.raw >= 0 ? '+' : ''}${ctx.raw}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: PALETTE.grid },
            ticks: {
              font: { family: 'IBM Plex Mono', size: 11 },
              color: PALETTE.textMuted
            }
          },
          y: {
            grid: { display: false },
            ticks: { font: { family: 'IBM Plex Sans', size: 12 }, color: PALETTE.text }
          }
        }
      }
    });
  }

  window.Charts = {
    renderStackedDivisionChart,
    renderClassShapChart,
    renderStudentTrendsChart,
    renderSgpaChart,
    renderSubjectBarChart,
    renderShapChart
  };
})(window);
