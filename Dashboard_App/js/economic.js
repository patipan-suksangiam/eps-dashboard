// 📈 Economic & BOI — renderer
// Data: RAW_Data/6_Macroeconomic_Data.csv (OIE MPI / CapU / BOT policy rate)
//       RAW_Data/7_BOI_Data.csv           (BOI approved projects)
//       RAW_Data/8_DBD_Data.csv           (DIW/DBD factory register match)

function eCard(title, big, unit, sub, color) {
    return '<div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow-sm);position:relative;overflow:hidden;min-width:0;">'
        + '<div style="position:absolute;top:0;left:0;width:4px;height:100%;background:' + color + ';"></div>'
        + '<div style="font-size:13px;font-weight:600;color:var(--text-muted);margin-bottom:8px;">' + title + '</div>'
        + '<div style="font-size:28px;font-weight:800;">' + big + '<span style="font-size:14px;color:var(--text-muted);font-weight:600;"> ' + unit + '</span></div>'
        + '<div style="font-size:12px;color:var(--text-muted);margin-top:10px;line-height:1.45;">' + sub + '</div></div>';
}

function ePanel(title, inner, badge) {
    return '<div style="background:white;padding:22px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow-sm);margin-bottom:24px;">'
        + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;border-bottom:1px solid var(--border-subtle);padding-bottom:12px;">'
        + '<h3 style="font-size:16px;font-weight:700;">' + title + '</h3>'
        + '<span style="font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;background:#F1F5F9;color:#475569;">' + (badge || '') + '</span>'
        + '</div>' + inner + '</div>';
}

function eTable(headers, rows, align) {
    let h = '<div style="max-height:420px;overflow-y:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;text-align:left;">'
        + '<thead><tr style="background:#F8FAFC;color:#475569;position:sticky;top:0;">';
    headers.forEach((x, i) => {
        h += '<th style="padding:10px 14px;border-bottom:1px solid var(--border);' + ((align && align[i]) ? 'text-align:' + align[i] + ';' : '') + '">' + x + '</th>';
    });
    h += '</tr></thead><tbody>';
    if (!rows.length) {
        h += '<tr><td colspan="' + headers.length + '" style="padding:20px;text-align:center;color:var(--text-muted);">No records</td></tr>';
    } else {
        rows.forEach(cells => {
            h += '<tr>';
            cells.forEach((c, i) => {
                h += '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);' + ((align && align[i]) ? 'text-align:' + align[i] + ';' : '') + '">' + c + '</td>';
            });
            h += '</tr>';
        });
    }
    return h + '</tbody></table></div>';
}

const eNum = v => (v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

async function renderEconomicPage() {
    const host = document.getElementById('main-content');
    if (!host) return;

    let macro = [], boi = [], dbd = [];
    try {
        const [m, b, d, v] = await Promise.all([
            fetch(DATA_BASE + '6_Macroeconomic_Data.csv?t=' + Date.now()).then(x => x.text()),
            fetch(DATA_BASE + '7_BOI_Data.csv?t=' + Date.now()).then(x => x.text()),
            fetch(DATA_BASE + '8_DBD_Data.csv?t=' + Date.now()).then(x => x.text()),
            fetch(DATA_BASE + '4_Visit_Report.csv?t=' + Date.now()).then(x => x.text()).catch(() => '')
        ]);
        macro = parseCSV(m); boi = parseCSV(b); dbd = parseCSV(d);
        window.VISITED_CIDS = new Set();
        if (v) { parseCSV(v).forEach(r => { if (r.client_id) window.VISITED_CIDS.add(r.client_id); }); }
    } catch (err) {
        host.insertAdjacentHTML('beforeend',
            '<div style="padding:20px;background:#FEF2F2;color:#991B1B;border:1px solid #FECACA;border-radius:8px;">'
            + '<strong>Could not load economic data.</strong><br>' + err.message + '</div>');
        return;
    }

    // latest overall period
    const periods = Array.from(new Set(macro.map(r => r.date_period).filter(Boolean))).sort();
    const latest = periods[periods.length - 1] || '';
    const overall = macro.find(r => r.date_period === latest && r.industry_sector === 'ALL_INDUSTRY') || {};
    const sectors = macro
        .filter(r => r.date_period === latest && r.industry_sector !== 'ALL_INDUSTRY' && parseNum(r.cap_u_pct) > 0)
        .sort((a, b) => parseNum(b.cap_u_pct) - parseNum(a.cap_u_pct));

    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;margin-bottom:24px;">';
    html += eCard('MPI Index (' + latest + ')', eNum(parseNum(overall.mpi_index)), 'index',
        'YoY <b>' + eNum(parseNum(overall.mpi_yoy_pct)) + '%</b> · source: OIE', '#0EA5E9');
    html += eCard('Capacity Utilization', eNum(parseNum(overall.cap_u_pct)), '%',
        'All-industry average across ' + sectors.length + ' sectors', '#F59E0B');
    html += eCard('BOT Policy Rate', eNum(parseNum(overall.bot_policy_rate)), '%',
        'Bank of Thailand MPC', '#10B981');
    html += eCard('Private Capex Growth', eNum(parseNum(overall.private_capex_growth)), '%',
        'Private investment growth indicator', '#8B5CF6');
    html += '</div>';

    // capacity utilization chart
    const chartData = sectors.slice(0, 12);
    html += ePanel('🏭 Capacity Utilization by Sector — ' + latest,
        '<div style="height:320px;"><canvas id="capuChart"></canvas></div>', chartData.length + ' sectors');

    // BOI projects
    const projects = boi.slice().sort((a, b) => parseNum(b.investment_value_m) - parseNum(a.investment_value_m));
    const boiTotal = projects.reduce((s, x) => s + parseNum(x.investment_value_m), 0);
    html += ePanel('🏗️ BOI Investment Radar — ' + (projects.length) + ' projects',
        eTable(['Company', 'Industry', 'Zone', 'Period', 'Status', 'Investment (M THB)'],
            projects.slice(0, 25).map(x => [
                '<b>' + (x.company_name || '-') + '</b>',
                x.industry_type || '-',
                x.zone || '-',
                x.approval_period || '-',
                x.status || '-',
                eNum(parseNum(x.investment_value_m))
            ]), [null, null, null, null, null, 'right']),
        'total ' + eNum(boiTotal) + ' M THB');

    // DBD / DIW match
    const matched = dbd.filter(r => (r.match_source || '').trim()).length;
    const withCapital = dbd.filter(r => parseNum(r.registered_capital_m) > 0).length;
    const indCount = {};
    dbd.forEach(r => { 
        const ind = (r.industry_type || r.tsic_code || 'Other').trim(); 
        if (ind) indCount[ind] = (indCount[ind] || 0) + 1; 
    });
    const topInd = Object.entries(indCount).sort((a, b) => b[1] - a[1]).slice(0, 15);

    html += ePanel('🏢 Factory Register Match by Industry Type (DIW / DBD)',
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:16px;">'
        + '<div style="padding:14px;background:#F8FAFC;border-radius:8px;"><div style="font-size:12px;color:var(--text-muted);font-weight:600;">Clients checked</div><div style="font-size:22px;font-weight:800;">' + dbd.length.toLocaleString() + '</div></div>'
        + '<div style="padding:14px;background:#F8FAFC;border-radius:8px;"><div style="font-size:12px;color:var(--text-muted);font-weight:600;">Matched to factory register</div><div style="font-size:22px;font-weight:800;">' + matched.toLocaleString() + ' <span style="font-size:13px;color:var(--text-muted);">(' + (dbd.length ? Math.round(matched / dbd.length * 100) : 0) + '%)</span></div></div>'
        + '<div style="padding:14px;background:#F8FAFC;border-radius:8px;"><div style="font-size:12px;color:var(--text-muted);font-weight:600;">With registered capital</div><div style="font-size:22px;font-weight:800;">' + withCapital.toLocaleString() + '</div></div>'
        + '</div>'
        + '<p style="font-size:12.5px;color:var(--text-muted);margin:0 0 10px;">Click any Industry Type below to inspect the factory list and details.</p>'
        + eTable(['Industry Type / TSIC', 'Factories matched'],
            topInd.map(([i, n]) => ['<a href="#" data-ind-drill="' + i + '" style="font-weight:700;color:var(--primary-light);text-decoration:none;">' + i + '</a>', n.toLocaleString()]), [null, 'right']),
        'top 15 industries · clickable')
        + '<div id="economic-drill"></div>';

    setTimeout(() => {
        const drillHost = document.getElementById('economic-drill');
        if (drillHost) {
            host.querySelectorAll('a[data-ind-drill]').forEach(a => {
                a.addEventListener('click', ev => {
                    ev.preventDefault();
                    const ind = a.getAttribute('data-ind-drill');
                    const matchedRows = dbd.filter(r => (r.industry_type || r.tsic_code || 'Other').trim() === ind);
                    
                    const renderDrillTable = (rowsData, sortKey = 'capital', sortDir = -1) => {
                        const sorted = rowsData.slice().sort((a, b) => {
                            let va = a[sortKey], vb = b[sortKey];
                            if (sortKey === 'capital') {
                                va = parseFloat(a.registered_capital_m || 0);
                                vb = parseFloat(b.registered_capital_m || 0);
                            }
                            if (va < vb) return -1 * sortDir;
                            if (va > vb) return 1 * sortDir;
                            return 0;
                        });

                        let h = '<div style="background:#0F172A;color:white;padding:22px;border-radius:12px;margin-bottom:24px;">'
                            + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
                            + '<h3 style="font-size:16px;font-weight:800;">🏭 Factories in Industry: ' + ind + ' (' + matchedRows.length + ' factories) <span style="font-size:12px;color:#34D399;font-weight:normal;margin-left:12px;">🟢 Green = Visited</span></h3>'
                            + '<button data-close="1" style="background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;cursor:pointer;">Close ✕</button></div>'
                            + '<p style="font-size:12px;color:#94A3B8;margin:0 0 10px;">Click column headers (Company / Province / Capital) to sort.</p>'
                            + '<div style="max-height:420px;overflow:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
                            + '<thead><tr style="color:#94A3B8;cursor:pointer;user-select:none;">'
                            + '<th data-dsort="company" style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.15);text-align:left;">Company Name ↕</th>'
                            + '<th data-dsort="province" style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.15);text-align:left;">Province ↕</th>'
                            + '<th data-dsort="capital" style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.15);text-align:right;">Registered Capital (M) ↕</th>'
                            + '<th style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.15);text-align:left;">Status / Visit</th>'
                            + '</tr></thead><tbody>';

                        sorted.forEach(r => {
                            const isVisited = window.VISITED_CIDS && window.VISITED_CIDS.has(r.client_id);
                            const nameColor = isVisited ? '#34D399' : '#E2E8F0';
                            const visitBadge = isVisited ? '<span style="color:#34D399;font-weight:700;">✓ Visited</span>' : '<span style="color:#64748B;">Not visited</span>';
                            h += '<tr>'
                                + '<td style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.08);color:' + nameColor + ';"><b>' + (r.company_name || '-') + '</b></td>'
                                + '<td style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.08);color:#E2E8F0;">' + (r.province || '-') + '</td>'
                                + '<td style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.08);color:#E2E8F0;text-align:right;">' + (r.registered_capital_m ? parseFloat(r.registered_capital_m).toLocaleString(undefined, {minimumFractionDigits:2}) : '-') + '</td>'
                                + '<td style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.08);">' + visitBadge + '</td>'
                                + '</tr>';
                        });
                        if (!sorted.length) h += '<tr><td colspan="4" style="padding:16px;color:#94A3B8;">No factories found</td></tr>';
                        h += '</tbody></table></div></div>';
                        drillHost.innerHTML = h;

                        drillHost.querySelectorAll('th[data-dsort]').forEach(th => {
                            th.addEventListener('click', () => {
                                const k = th.getAttribute('data-dsort');
                                const nextDir = (sortKey === k) ? -sortDir : -1;
                                renderDrillTable(rowsData, k, nextDir);
                            });
                        });
                        const b = drillHost.querySelector('button[data-close]');
                        if (b) b.addEventListener('click', () => { drillHost.innerHTML = ''; });
                    };

                    renderDrillTable(matchedRows, 'capital', -1);
                    drillHost.innerHTML = h;
                    drillHost.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    const b = drillHost.querySelector('button[data-close]');
                    if (b) b.addEventListener('click', () => { drillHost.innerHTML = ''; });
                });
            });
        }
    }, 50);

    host.insertAdjacentHTML('beforeend', html);

    // ---- chart ----
    if (typeof Chart !== 'undefined') {
        const el = document.getElementById('capuChart');
        if (el) {
            const old = Chart.getChart(el); if (old) old.destroy();
            new Chart(el, {
                type: 'bar',
                data: {
                    labels: chartData.map(x => (x.industry_sector || '').slice(0, 28)),
                    datasets: [{
                        label: 'Capacity utilization (%) @ ' + latest,
                        data: chartData.map(x => parseNum(x.cap_u_pct)),
                        backgroundColor: '#F59E0B',
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { x: { beginAtZero: true, max: 100 } },
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        }
    }
}

document.addEventListener('viewLoaded', (e) => {
    if (e.detail.viewId === 'economic') {
        renderEconomicPage().catch(err => {
            const host = document.getElementById('main-content');
            if (host) host.insertAdjacentHTML('beforeend',
                '<div style="padding:20px;background:#FEF2F2;color:#991B1B;border-radius:8px;">Economic page error: ' + err.message + '</div>');
        });
    }
});
