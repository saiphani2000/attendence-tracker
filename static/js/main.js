(function() {
  function compareValues(a, b, type) {
    if (type === 'int') {
      return parseInt(a, 10) - parseInt(b, 10);
    }
    if (type === 'float' || type === 'pct') {
      const av = parseFloat((a || '').toString().replace('%','')) || 0;
      const bv = parseFloat((b || '').toString().replace('%','')) || 0;
      return av - bv;
    }
    const as = (a || '').toString().toLowerCase();
    const bs = (b || '').toString().toLowerCase();
    if (as < bs) return -1;
    if (as > bs) return 1;
    return 0;
  }

  function makeTableSortable(table) {
    const thead = table.querySelector('thead');
    if (!thead) return;
    const headers = Array.from(thead.querySelectorAll('th'));
    headers.forEach((th, idx) => {
      const sortType = th.getAttribute('data-sort');
      if (!sortType) return;
      th.addEventListener('click', () => {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const asc = th.dataset.order !== 'desc';
        rows.sort((r1, r2) => {
          const t1 = (r1.children[idx] || {}).innerText || '';
          const t2 = (r2.children[idx] || {}).innerText || '';
          const cmp = compareValues(t1.trim(), t2.trim(), sortType);
          return asc ? cmp : -cmp;
        });
        // Update order state
        headers.forEach(h => delete h.dataset.order);
        th.dataset.order = asc ? 'asc' : 'desc';
        // Re-append
        rows.forEach(r => tbody.appendChild(r));
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('table[data-sortable]').forEach(makeTableSortable);
  });
})();
