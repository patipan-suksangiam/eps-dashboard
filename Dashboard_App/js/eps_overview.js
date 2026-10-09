// 📊 EPS Overview — FY 2026 (renderer loaded once; reacts to 'viewLoaded')
// Data: RAW_Data/0_EPS_Overview_2026.csv (KPIs + group actual vs plan — all derived by scripts/)
//       RAW_Data/3_SO_Data.csv           (monthly cumulative revenue, derived in-browser)
// No hardcoded business numbers: anything not present in the CSV is simply not shown.

document.addEventListener('viewLoaded', async (e) => {
    if (e.detail.viewId !== 'eps_overview') return;

    try {
        const [o, s] = await Promise.all([
            fetch(DATA_BASE + '0_EPS_Overview_2026.csv?t=' + Date.now()).then(x => x.text()),
            fetch(DATA_BASE + '3_SO_Data.csv?t=' + Date.now()).then(x => x.text()).catch(() => '')
        ]);

        const data = {};
        parseCSV(o).forEach(r => {
            data[r.metric] = {
                label: r.label,
                value: parseNum(r.value),
                target: (r.target === '-' || r.target === '') ? null : parseNum(r.target),
                unit: r.unit,
                trend: r.trend,
                trend_value: r.trend_value
            };
        });

        // cumulative revenue per month (derived from real orders)
        const monthly = {};
        if (s) {
            parseCSV(s).forEach(r => {
                const bd = r.booking_date || '';
                if (!bd.startsWith('2026-')) return;
                const d = bd.slice(0, 7);
                if (!/^\d{4}-\d{2}$/.test(d)) return;
                monthly[d] = (monthly[d] || 0) + parseNum(r.value_thb);
            });
        }

        renderEPSKpis(data);
        renderMonthlyChart(data, monthly);
        renderAIActionPlan(data);
        renderEPSCharts(data);
    } catch (err) {
        const box = document.getElementById('eps-kpi-container');
        if (box) box.innerHTML = '<div style="grid-column:1/-1;padding:20px;background:#FEF2F2;color:#991B1B;border:1px solid #FECACA;border-radius:8px;">'
            + '<strong>Could not load FY2026 data.</strong><br>' + err.message
            + '<br><br>Run the dashboard through a local server: <code>python3 -m http.server 8080</code> from the "AI Dashboard" folder.</div>';
    }
});

function cardHTML(title, big, unit, sub, color) {
    return '<div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow-sm);position:relative;overflow:hidden;">'
        + '<div style="position:absolute;top:0;left:0;width:4px;height:100%;background:' + color + ';"></div>'
        + '<div style="font-size:13px;font-weight:600;color:var(--text-muted);margin-bottom:8px;">' + title + '</div>'
        + '<div style="font-size:30px;font-weight:800;">' + big + '<span style="font-size:15px;color:var(--text-muted);font-weight:600;"> ' + unit + '</span></div>'
        + '<div style="font-size:12px;color:var(--text-muted);margin-top:10px;line-height:1.45;">' + sub + '</div></div>';
}

function renderEPSKpis(data) {
    const box = document.getElementById('eps-kpi-container');
    if (!box) return;

    const rev = data['FY2026_Revenue_YTD'];
    const ac = data['FY2026_Active_Customers'];
    const so = data['FY2026_Sales_Orders'];
    const hj = data['FY2026_Hot_Jobs'];
    let html = '';

    if (rev) {
        if (rev.target) {
            const pct = Math.round((rev.value / rev.target) * 100);
            const gap = (rev.target - rev.value).toFixed(2);
            html += cardHTML('EPS Revenue YTD (Plan: ' + rev.target.toFixed(2) + 'M THB)',
                rev.value.toFixed(2), 'M THB',
                '<div style="height:8px;background:#E2E8F0;border-radius:4px;overflow:hidden;margin-bottom:6px;">'
                + '<div style="width:' + Math.min(pct, 100) + '%;height:100%;background:#F59E0B;border-radius:4px;"></div></div>'
                + 'Achieved <b>' + pct + '%</b> of the FY2026 plan · gap remaining <b>' + gap + 'M THB</b>',
                '#F59E0B');
        } else {
            html += cardHTML('EPS Revenue YTD', rev.value.toFixed(2), 'M THB', 'Plan target not set', '#F59E0B');
        }
    }
    if (so) html += cardHTML('Sales Orders 2026', so.value, 'orders', 'Booked in CRM (year to date)', '#3B82F6');
    if (ac) html += cardHTML('Active Customers', ac.value, 'accounts', 'Accounts with at least one order in 2026', '#10B981');
    if (hj) {
        html += cardHTML(hj.label, hj.value.toFixed(2), 'M THB',
            '<b>' + parseNum(hj.trend_value) + ' live deals</b> · status Pending, chance ≥ 70%', '#8B5CF6');
    }

    box.innerHTML = html;
}

// 💡 Action plan — every figure comes from the data, nothing is invented
function renderAIActionPlan(data) {
    const container = document.getElementById('ai-action-plan-container');
    if (!container) return;

    const rev = data['FY2026_Revenue_YTD'] || { value: 0, target: 0 };
    const actual = rev.value, target = rev.target || 0;
    const gap = target ? (target - actual) : 0;
    const pct = target ? Math.round((actual / target) * 100) : 0;

    const groups = ['Group_A_Revenue', 'Group_B_Revenue', 'Group_C_Revenue', 'Group_D_Revenue', 'Group_R_Revenue']
        .map(k => data[k]).filter(Boolean);
    let topGroup = null;
    groups.forEach(g => {
        if (!g.target) return;
        const gapVal = g.target - g.value;
        if (!topGroup || gapVal > topGroup.gap) topGroup = { label: g.label, gap: gapVal, value: g.value, target: g.target };
    });

    let html = '<div style="background:#F8FAFC;border:1px solid #CBD5E1;border-radius:8px;padding:16px;margin-bottom:16px;">'
        + '<div style="font-size:14px;font-weight:700;color:#1E3A8A;margin-bottom:4px;">🎯 Diagnostic Summary</div>'
        + '<p style="font-size:13px;color:#334155;line-height:1.5;">Actual revenue YTD is <b>' + actual.toFixed(2) + 'M THB</b>'
        + (target ? ' against the FY2026 plan of <b>' + target.toFixed(2) + 'M THB</b> (' + pct + '% attained), leaving a gap of <b style="color:#B91C1C;">' + gap.toFixed(2) + 'M THB</b>' : ' (plan target not set)')
        + '. ' + (topGroup ? 'Largest absolute gap: <b>' + topGroup.label + '</b> (' + topGroup.gap.toFixed(2) + 'M THB).' : '')
        + '</p></div>';

    html += '<table style="width:100%;border-collapse:collapse;font-size:13px;text-align:left;">'
        + '<thead><tr style="background:#F1F5F9;color:#475569;">'
        + '<th style="padding:10px 14px;border-bottom:1px solid var(--border);">Focus</th>'
        + '<th style="padding:10px 14px;border-bottom:1px solid var(--border);">Closing the gap — where to act</th>'
        + '<th style="padding:10px 14px;border-bottom:1px solid var(--border);">Current position</th></tr></thead><tbody>';

    groups.slice().sort((a, b) => (b.target || 0) - (a.target || 0)).forEach(g => {
        const gGap = g.target ? (g.target - g.value) : null;
        const line = gGap === null
            ? 'Plan target not set for this group'
            : (gGap > 0 ? 'Gap ' + gGap.toFixed(2) + 'M THB to plan' : 'Ahead of plan by ' + Math.abs(gGap).toFixed(2) + 'M THB');
        html += '<tr>'
            + '<td style="padding:12px 14px;border-bottom:1px solid var(--border-subtle);font-weight:700;">' + g.label + '</td>'
            + '<td style="padding:12px 14px;border-bottom:1px solid var(--border-subtle);">Concentrate senior capacity on live tenders and plant revamps; review stalled bids weekly.</td>'
            + '<td style="padding:12px 14px;border-bottom:1px solid var(--border-subtle);">' + g.value.toFixed(2) + 'M booked' + (g.target ? ' / ' + g.target.toFixed(2) + 'M plan — ' + line : '') + '</td></tr>';
    });
    html += '</tbody></table>';

    container.innerHTML = html;
}

// cumulative revenue by month (real orders) vs straight-line plan
function renderMonthlyChart(data, monthly) {
    if (typeof Chart === 'undefined') return;
    const el = document.getElementById('epsRevenueChart');
    if (!el) return;
    const old = Chart.getChart(el); if (old) old.destroy();

    const months = Object.keys(monthly).sort();
    if (!months.length) return;

    let run = 0;
    const cumulative = months.map(m => (run += monthly[m]) / 1e6);
    const labels = months.map(m => m.slice(5) + '/' + m.slice(2, 4));
    const rev = data['FY2026_Revenue_YTD'] || {};
    const plan = rev.target || 0;
    const planLine = plan ? months.map((_, i) => plan * (i + 1) / months.length) : null;

    const datasets = [{
        label: 'Actual cumulative (M THB)',
        data: cumulative,
        borderColor: '#3B82F6', backgroundColor: 'rgba(59,130,246,0.12)',
        fill: true, tension: 0.3, pointRadius: 4
    }];
    if (planLine) {
        datasets.push({
            label: 'Plan trajectory (' + plan.toFixed(2) + 'M)',
            data: planLine, borderColor: '#F59E0B', borderDash: [6, 6], pointRadius: 0, fill: false
        });
    }

    new Chart(el, {
        type: 'line',
        data: { labels: labels, datasets: datasets },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } }, plugins: { legend: { position: 'bottom' } } }
    });
}

function renderEPSCharts(data) {
    if (typeof Chart === 'undefined') return;

    const g = document.getElementById('epsGroupChart');
    if (g) {
        const old = Chart.getChart(g); if (old) old.destroy();
        const keys = ['Group_A_Revenue', 'Group_B_Revenue', 'Group_C_Revenue', 'Group_D_Revenue', 'Group_R_Revenue'];
        const labels = ['Group A', 'Group B', 'Group C', 'Group D', 'Group R'];
        new Chart(g, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    { label: 'Actual YTD (M THB)', data: keys.map(k => data[k] ? data[k].value : 0), backgroundColor: '#3B82F6', borderRadius: 4 },
                    { label: 'FY 2026 Plan (M THB)', data: keys.map(k => data[k] ? (data[k].target || 0) : 0), backgroundColor: '#E2E8F0', borderRadius: 4 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } }, plugins: { legend: { position: 'bottom' } } }
        });
    }
}
