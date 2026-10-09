// 🧾 Open Quotes Pipeline — Role-Restricted Renderer (Robust Sortable)
document.addEventListener('viewLoaded', async (e) => {
    if (e.detail.viewId !== 'open_quotes') return;

    const container = document.getElementById('oq-table-container');
    const kpiHost = document.getElementById('oq-kpi-container');
    const groupSelect = document.getElementById('oq-group-select');
    const searchInput = document.getElementById('oq-search');
    const badge = document.getElementById('oq-user-badge');

    const currentUser = auth.getCurrentUser() || {};
    let lockedGroup = null;

    if (currentUser.roleId && currentUser.roleId.startsWith('group_')) {
        lockedGroup = currentUser.roleId.replace('group_', '').toUpperCase();
        groupSelect.value = lockedGroup;
        groupSelect.disabled = true;
        badge.innerText = 'Group ' + lockedGroup + ' (Locked)';
        badge.style.background = '#ECFDF5'; badge.style.color = '#065F46'; badge.style.borderColor = '#A7F3D0';
    } else {
        badge.innerText = 'Administrator (All Groups)';
    }

    let quotes = [];
    try {
        const res = await fetch(DATA_BASE + '17_Open_Quotes.csv?t=' + Date.now());
        if (!res.ok) throw new Error('HTTP ' + res.status);
        quotes = parseCSV(await res.text());
    } catch (err) {
        container.innerHTML = '<div style="padding:20px;color:#B91C1C;text-align:center;">Failed to load open quotes: ' + err.message + '</div>';
        return;
    }

    const fmtM = v => (v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    let currentSortKey = 'aging_days';
    let currentSortDir = -1; // desc

    const render = () => {
        let filterGrp = lockedGroup || groupSelect.value;
        const query = searchInput.value.toLowerCase().trim();

        let list = quotes;
        if (filterGrp !== 'all') {
            list = list.filter(q => q.group === filterGrp);
        }
        if (query) {
            list = list.filter(q => (q.company_name || '').toLowerCase().includes(query) || (q.quote_id || '').toLowerCase().includes(query) || (q.rep_name || '').toLowerCase().includes(query));
        }

        const totalCnt = list.length;
        const totalVal = list.reduce((s, x) => s + parseFloat(x.value_thb || 0), 0);
        const stalled = list.filter(x => parseInt(x.aging_days || 0) > 90).length;

        kpiHost.innerHTML = '<div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow-sm);"><div style="font-size:13px;font-weight:600;color:var(--text-muted);margin-bottom:8px;">Open Quotations Count</div><div style="font-size:30px;font-weight:800;">' + totalCnt.toLocaleString() + ' <span style="font-size:15px;color:var(--text-muted);">deals</span></div><div style="font-size:12px;color:var(--success);font-weight:600;margin-top:8px;">Active pipeline</div></div>'
            + '<div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow-sm);"><div style="font-size:13px;font-weight:600;color:var(--text-muted);margin-bottom:8px;">Total Pipeline Value</div><div style="font-size:30px;font-weight:800;">' + fmtM(totalVal / 1e6) + ' <span style="font-size:15px;color:var(--text-muted);">M THB</span></div><div style="font-size:12px;color:var(--text-muted);margin-top:8px;">Pending conversion</div></div>'
            + '<div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow-sm);"><div style="font-size:13px;font-weight:600;color:var(--text-muted);margin-bottom:8px;">Stalled Quotes (>90 Days)</div><div style="font-size:30px;font-weight:800;color:var(--danger);">' + stalled.toLocaleString() + ' <span style="font-size:15px;color:var(--text-muted);">deals</span></div><div style="font-size:12px;color:var(--text-muted);margin-top:8px;">Requires immediate follow-up</div></div>';

        // Sort list
        list.sort((a, b) => {
            let va = a[currentSortKey], vb = b[currentSortKey];
            if (currentSortKey === 'value_thb' || currentSortKey === 'aging_days') {
                va = parseFloat(va || 0); vb = parseFloat(vb || 0);
            }
            if (va < vb) return -1 * currentSortDir;
            if (va > vb) return 1 * currentSortDir;
            return 0;
        });

        const headers = [
            { label: 'Quote ID', key: 'quote_id', align: 'left' },
            { label: 'Company Name', key: 'company_name', align: 'left' },
            { label: 'Sales Rep', key: 'rep_name', align: 'left' },
            { label: 'Value (THB)', key: 'value_thb', align: 'right' },
            { label: 'Chance', key: 'probability_pct', align: 'center' },
            { label: 'Expected Order', key: 'expected_order_date', align: 'left' },
            { label: 'Aging (Days)', key: 'aging_days', align: 'right' }
        ];

        let h = '<table style="width:100%;border-collapse:collapse;font-size:13px;text-align:left;">'
            + '<thead><tr style="background:#F8FAFC;color:#475569;position:sticky;top:0;cursor:pointer;user-select:none;">';
        headers.forEach(hd => {
            const arrow = currentSortKey === hd.key ? (currentSortDir === 1 ? ' ▲' : ' ▼') : ' ↕';
            h += '<th data-sort-key="' + hd.key + '" style="padding:10px 14px;border-bottom:1px solid var(--border);text-align:' + hd.align + ';white-space:nowrap;">' + hd.label + '<span style="opacity:.5;font-size:10px;">' + arrow + '</span></th>';
        });
        h += '</tr></thead><tbody>';

        list.slice(0, 300).forEach(q => {
            const age = parseInt(q.aging_days || 0);
            const ageBadge = age > 90 
                ? '<span style="background:#FEF2F2;color:#B91C1C;padding:2px 6px;border-radius:4px;font-weight:700;">' + age + ' d</span>'
                : '<span>' + age + ' d</span>';
            h += '<tr>'
                + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);font-family:monospace;font-weight:bold;">' + (q.quote_id || '-') + '</td>'
                + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);font-weight:600;">' + (q.company_name || '-') + '</td>'
                + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);">' + (q.rep_name || '-') + '</td>'
                + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);text-align:right;font-weight:bold;">' + fmtM(parseFloat(q.value_thb || 0)) + '</td>'
                + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);text-align:center;">' + (q.probability_pct || '-') + '</td>'
                + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);">' + (q.expected_order_date || '-') + '</td>'
                + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);text-align:right;">' + ageBadge + '</td>'
                + '</tr>';
        });

        if (!list.length) h += '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-muted);">No open quotes found for this filter.</td></tr>';
        h += '</tbody></table>';
        container.innerHTML = h;

        // Attach sort click handlers
        container.querySelectorAll('th[data-sort-key]').forEach(th => {
            th.addEventListener('click', () => {
                const k = th.getAttribute('data-sort-key');
                if (currentSortKey === k) {
                    currentSortDir = -currentSortDir;
                } else {
                    currentSortKey = k;
                    currentSortDir = (k === 'value_thb' || k === 'aging_days') ? -1 : 1;
                }
                render();
            });
        });
    };

    render();
    groupSelect.addEventListener('change', render);
    searchInput.addEventListener('input', render);
});
