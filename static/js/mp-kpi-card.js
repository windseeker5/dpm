/*
  MiniPass KPI Card — sparkline rendering + period-dropdown wiring for the
  .mp-kpi-card component (templates/macros/kpi_card.html).

  Registered on the shared window.mpBasecoat registry defined in
  mp-action-menu.js (must load before this file). The period dropdown
  itself is a real .mp-action-menu (see kpi_card.html), so its open/close/
  keyboard behavior is already handled by mp-action-menu.js — this file
  only listens for clicks on the period menu's [data-period-value] items
  and re-renders the chart.

  Chart tech: ApexCharts sparkline, same library/options already used by
  the real dashboard's KPI cards (templates/dashboard.html). Requires the
  ApexCharts script to be loaded before this file; if it isn't, the chart
  region is left empty rather than throwing.

  Period switching here has no backend behind it (this file has no page
  context) — it only re-renders whatever trend_data the caller supplies via
  root.refreshChart(). A page wiring this component to live data (e.g. a
  future dashboard.html migration) sets root.onPeriodChange itself; the
  style guide demo sets a stub that swaps in canned sample data.
*/
(() => {
  if (!window.mpBasecoat || typeof window.mpBasecoat.register !== 'function') {
    console.error('mp-kpi-card.js requires mp-action-menu.js to load first (window.mpBasecoat missing)');
    return;
  }

  // Matches templates/macros/kpi_card.html's kpi_period_short_labels — the
  // dropdown menu items show the full name (rendered server-side), but the
  // closed trigger shows this short code, so it has to be reapplied here
  // after a click swaps the selected period.
  const PERIOD_SHORT_LABELS = { '7d': '7D', '30d': '30D', '90d': '90D', fy: 'FY', all: 'All' };

  // Read from CSS rather than hardcoding a hex, so a future per-tenant
  // brand color only needs to override --mp-chart-1 (e.g. inline on
  // <body>) with no JS changes.
  const getChartColor = () =>
    getComputedStyle(document.documentElement).getPropertyValue('--mp-chart-1').trim() || '#206bc4';

  const buildChartOptions = (root, trendData) => {
    const chartType = root.dataset.kpiChartType === 'bar' ? 'bar' : 'area';
    const isCurrency = root.dataset.kpiFormat === 'currency';

    const options = {
      // background:'transparent' matters here — ApexCharts' area fill
      // stops ~1.5px short of the container's full height (room reserved
      // for the line stroke), and without this the gap shows ApexCharts'
      // own default SVG background (#fefefe, slightly off-white) instead
      // of blending into the card, which reads as a stray white line
      // under the chart.
      chart: { type: chartType, height: 40, sparkline: { enabled: true }, toolbar: { show: false }, background: 'transparent' },
      series: [{ data: trendData }],
      colors: [getChartColor()],
      grid: { show: false, padding: { top: 0, right: 0, bottom: 0, left: 0 } },
      dataLabels: { enabled: false },
      // Strip ApexCharts' default tooltip chrome (the data-point index
      // header and the auto-generated "series-1" label) down to just the
      // formatted value — neither of those carries real information here.
      tooltip: {
        x: { show: false },
        marker: { show: false },
        y: {
          title: { formatter: () => '' },
          formatter: (val) => (isCurrency ? '$' + Number(val).toLocaleString() : Number(val).toLocaleString()),
        },
      },
    };

    if (chartType === 'area') {
      options.stroke = { width: 1.5, curve: 'smooth' };
      options.fill = { opacity: 0.15 };
    } else {
      options.plotOptions = { bar: { borderRadius: 2, columnWidth: '60%' } };
    }

    return options;
  };

  const renderChart = (root, trendData) => {
    const chartEl = document.getElementById(root.id + '-chart');
    if (!chartEl) return;
    if (typeof ApexCharts === 'undefined') {
      console.warn('mp-kpi-card: ApexCharts not loaded, skipping chart render for #' + root.id);
      return;
    }
    if (root._apexChart) {
      root._apexChart.destroy();
      root._apexChart = null;
    }
    chartEl.innerHTML = '';
    root._apexChart = new ApexCharts(chartEl, buildChartOptions(root, trendData));
    root._apexChart.render();
  };

  const wirePeriodMenu = (root) => {
    const menu = root.querySelector('.mp-kpi-card__period [role="menu"]');
    if (!menu) return;

    const handleClick = (event) => {
      const item = event.target.closest('[data-period-value]');
      if (!item) return;

      const period = item.dataset.periodValue;
      root.dataset.kpiPeriod = period;

      const labelEl = document.getElementById(root.id + '-period-label');
      if (labelEl) labelEl.textContent = PERIOD_SHORT_LABELS[period] || item.textContent;

      menu.querySelectorAll('[role="menuitem"]').forEach((mi) => mi.classList.remove('active'));
      item.classList.add('active');

      if (typeof root.onPeriodChange === 'function') root.onPeriodChange(period);
    };

    menu.addEventListener('click', handleClick);
    root._destroyPeriodMenu = () => menu.removeEventListener('click', handleClick);
  };

  const initKpiCard = (root) => {
    const chartEl = document.getElementById(root.id + '-chart');
    if (chartEl) {
      let trendData = [];
      try {
        trendData = JSON.parse(chartEl.dataset.trend || '[]');
      } catch (error) {
        console.error('mp-kpi-card: invalid data-trend JSON on #' + root.id, error);
      }
      renderChart(root, trendData);
    }

    root.refreshChart = (trendData) => renderChart(root, trendData);
    wirePeriodMenu(root);

    root._destroy = () => {
      if (root._apexChart) {
        root._apexChart.destroy();
        root._apexChart = null;
      }
      if (typeof root._destroyPeriodMenu === 'function') root._destroyPeriodMenu();
      delete root.refreshChart;
      delete root.onPeriodChange;
    };

    root.dataset.mpKpiCardInitialized = 'true';
  };

  window.mpBasecoat.register('mp-kpi-card', {
    selector: '.mp-kpi-card:not([data-mp-kpi-card-initialized])',
    init: initKpiCard,
  });
})();
