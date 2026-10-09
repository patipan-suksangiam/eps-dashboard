import os

js = r'''// 📊 Group A/B/C/D/R — Group Overview renderer (Comment 20260924 & 20260928)
// Features: 3-year rep history (2024-2026), Top 10 accounts per sales rep,
// active rolling-12m accounts vs DBD>100M coverage, win rate, quotes aging, CapU To-Do, drill-downs.

const GROUP_META = {
    group_a: { key: 'A', title: '📊 Group A Overview', sector: 'Animal Feed & Agricultural Processing', color: '#10B981', metric: 'Group_A_Revenue' },
    group_b: { key: 'B', title: '📊 Group B Overview', sector: 'Chemicals & Wastewater Treatment', color: '#3B82F6', metric: 'Group_B_Revenue' },
    group_c: { key: 'C', title: '📊 Group C Overview', sector: 'Cosmetics, Pharma & Rubber', color: '#8B5CF6', metric: 'Group_C_Revenue' },
    group_d: { key: 'D', title: '📊 Group D Overview', sector: 'Oil & Gas, Power Plants', color: '#F59E0B', metric: 'Group_D_Revenue' },
    group_r: { key: 'R', title: '📊 Group R Overview', sector: 'Rayong / Eastern Region Hub', color: '#EF4444', metric: 'Group_R_Revenue' }
};

const gEsc = s => String(s == null ? '' : s);
const fmtM = v => (v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function gCard(title, big, unit, sub, color, clickId) {
    return '<div' + (clickId ? ' data-drill="' + clickId + '" style="cursor:pointer;"' : '') +
        ' style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow-sm);position:relative;overflow:hidden;min-width:0;">'
        + '<div style="position:absolute;top:0;left:0;width:4px;height:100%;background:' + color + ';"></div>'
        + '<div style="font-size:13px;font-weight:600;color:var(--text-muted);margin-bottom:8px;">' + title + '</div>'
        + '<div style="font-size:28px;font-weight:800;">' + big + '<span style="font-size:14px;color:var(--text-muted);font-weight:600;"> ' + unit + '</span></div>'
        + '<div style="font-size:12px;color:var(--text-muted);margin-top:10px;line-height:1.45;">' + sub + '</div></div>';
}

function gPanel(title, inner, badge) {
    return '<div style="background:white;padding:22px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow-sm);margin-bottom:24px;">'
        + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;border-bottom:1px solid var(--border-subtle);padding-bottom:12px;">'
        + '<h3 style="font-size:16px;font-weight:700;">' + title + '</h3>'
        + '<span style="font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;background:#F1F5F9;color:#475569;">' + (badge || '') + '</span>'
        + '</div>' + inner + '</div>';
}

function gSortTable(id, headers, keys, align, rows) {
    let h = '<div style="max-height:460px;overflow:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;" data-tid="' + id + '">'
        + '<thead><tr style="background:#F8FAFC;color:#475569;position:sticky;top:0;z-index:1;">';
    headers.forEach((x, i) => {
        const a = (align && align[i]) ? 'text-align:' + align[i] + ';' : '';
        const clickable = keys[i] ? 'cursor:pointer;user-select:none;' : '';
        h += '<th data-key="' + (keys[i] || '') + '" style="padding:10px 14px;border-bottom:1px solid var(--border);white-space:nowrap;' + a + clickable + '">'
            + x + (keys[i] ? ' <span style="opacity:.45;font-size:10px;">↕</span>' : '') + '</th>';
    });
    h += '</tr></thead><tbody>';
    rows.forEach(cells => {
        h += '<tr>';
        cells.forEach((c, i) => {
            const a = (align && align[i]) ? 'text-align:' + align[i] + ';' : '';
            h += '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);' + a + '">' + c + '</td>';
        });
        h += '</tr>';
    });
    if (!rows.length) h += '<tr><td colspan="' + headers.length + '" style="padding:20px;text-align:center;color:var(--text-muted);">No records</td></tr>';
    return h + '</tbody></table></div>';
}

const GSORT = {};
function gAttachSort(host) {
    host.querySelectorAll('th[data-key]').forEach(th => {
        const key = th.getAttribute('data-key');
        if (!key) return;
        th.addEventListener('click', () => {
            const table = th.closest('table');
            const tid = table.getAttribute('data-tid');
            const store = GSORT[tid];
            if (!store) return;
            if (store.sortKey === key) store.dir = -store.dir; else { store.sortKey = key; store.dir = -1; }
            const rows = store.rows.slice().sort((a, b) => {
                const va = a[key], vb = b[key];
                const na = parseFloat(va), nb = parseFloat(vb);
                if (!isNaN(na) && !isNaN(nb)) return (na - nb) * store.dir;
                return String(va).localeCompare(String(vb), 'th') * store.dir;
            });
            store.render(rows);
            gAttachSort(host);
        });
    });
}

function gBadge(active) {
    return active === 'Y'
        ? '<span style="background:#ECFDF5;color:#065F46;border:1px solid #A7F3D0;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;">Active</span>'
        : '<span style="background:#FEF2F2;color:#B91C1C;border:1px solid #FECACA;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;">Non-Active</span>';
}

async function gFetch(name) {
    const r = await fetch(DATA_BASE + name + '?t=' + Date.now());
    if (!r.ok) return [];
    return parseCSV(await r.text());
}

async function renderGroupPage(viewId) {
    const meta = GROUP_META[viewId];
    const host = document.getElementById('main-content');
    if (!meta || !host) return;
    const key = meta.key;

    let kpi = {}, ov = {}, reps = [], clients = [], so = [], todos = [];
    try {
        const [k, o, rp, cl, sr, td] = await Promise.all([
            gFetch('12_Group_KPI.csv'), gFetch('0_EPS_Overview_2026.csv'),
            gFetch('13_Rep_Performance.csv'), gFetch('14_Client_Detail.csv'),
            gFetch('15_SO_Delivery.csv'), gFetch('16_Todo.csv')
        ]);
        kpi = (k.find(x => x.group === key) || {});
        ov = (o.find(x => x.metric === meta.metric) || {});
        reps = rp.filter(x => x.group === key);
        clients = cl.filter(x => x.group === key);
        so = sr.filter(x => x.group === key);
        todos = td.filter(x => x.group === key);
    } catch (err) {
        host.insertAdjacentHTML('beforeend', '<div style="padding:20px;background:#FEF2F2;color:#991B1B;border:1px solid #FECACA;border-radius:8px;"><strong>Could not load group data.</strong><br>' + gEsc(err.message) + '</div>');
        return;
    }

    const actual = parseNum(ov.value), target = parseNum(ov.target);
    const pct = target ? Math.round((actual / target) * 100) : 0;
    const gap = target - actual;
    const active = parseNum(kpi.active_accounts_12m), total = parseNum(kpi.accounts_total);
    const dbdG = parseNum(kpi.dbd_factories_gt100m), dbdAll = parseNum(kpi.dbd_total_gt100m);
    const wr = kpi.win_rate_pct || '0';
    const qOpen = parseNum(kpi.quotes_open), qAll = parseNum(kpi.quotes_total);
    const oldest = parseNum(kpi.oldest_open_quote_days);

    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;margin-bottom:24px;">';
    html += gCard('Revenue YTD vs Plan (' + meta.key + ')', fmtM(actual), 'M THB',
        '<div style="height:8px;background:#E2E8F0;border-radius:4px;overflow:hidden;margin-bottom:6px;">'
        + '<div style="width:' + Math.min(pct, 100) + '%;height:100%;background:' + meta.color + ';border-radius:4px;"></div></div>'
        + 'Achieved <b>' + pct + '%</b> of plan (' + fmtM(target) + 'M) · gap <b>' + fmtM(gap) + 'M</b>', meta.color, 'clients');
    html += gCard('Active Accounts (rolling 12m)', active, 'of ' + total,
        'Accounts with order or visit in last 12 months'
        + '<div style="margin-top:6px;"><b>' + dbdG + '</b> of <b>' + dbdAll + '</b> DBD factories &gt;100M covered</div>',
        '#0EA5E9', 'clients');
    html += gCard('Win Rate (quotes decided)', wr, '%',
        parseNum(kpi.quotes_won) + ' won · ' + parseNum(kpi.quotes_lost) + ' lost of ' + qAll + ' quotes', '#6366F1', 'reps');
    html += gCard('Open Quotations', qOpen, 'open',
        qAll + ' total · oldest open <b>' + oldest + ' days</b>', '#14B8A6', 'quotes');
    html += '</div>';

    html += '<div id="group-drill"></div>';

    // Top Accounts: Top 10 per rep in this group
    let top10Html = '';
    reps.forEach(rep => {
        const repClients = clients.filter(c => c.owner_id === rep.emp_id || c.rep_name === rep.name)
            .sort((a, b) => parseNum(b.so_value_12m_m) - parseNum(a.so_value_12m_m))
            .slice(0, 10);
        if (repClients.length === 0) return;

        const mk = c => ({
            company: c.company_name || '-', province: c.province || '-', industry: c.industry_group || '-',
            orders: parseNum(c.so_count_12m), value: parseNum(c.so_value_12m_m), visits: parseNum(c.visits_12m),
            last: c.days_since_last_order === '' ? 99999 : parseNum(c.days_since_last_order),
            active: c.active_12m === 'Y' ? 1 : 0
        });
        const data = repClients.map(mk);
        const cells = data.map(d => [
            '<b>' + gEsc(d.company) + '</b>', d.province, d.industry, d.orders, fmtM(d.value), d.visits,
            (d.last === 99999 ? '-' : d.last + 'd'), gBadge(d.active ? 'Y' : 'N')
        ]);
        top10Html += '<div style="margin-bottom:16px;"><h4 style="font-size:14px;font-weight:700;color:#1E3A8A;margin-bottom:8px;">👤 Rep: ' + gEsc(rep.name) + ' (Top ' + repClients.length + ' Accounts)</h4>'
            + gSortTable('top_' + rep.emp_id, ['Account', 'Province', 'Industry', 'Orders', 'Value (M THB)', 'Visits', 'Last order', 'Status'], ['company', 'province', 'industry', 'orders', 'value', 'visits', 'last', 'active'], [null, null, null, 'right', 'right', 'right', 'right', null], cells)
            + '</div>';
    });

    html += gPanel('🏢 Top 10 Accounts per Sales Rep — Group ' + key,
        top10Html || '<p style="color:var(--text-muted);">No attributed top accounts found for reps in this group.</p>',
        'Top 10 / Rep');

    // Sales Team table (3-year history: 2024, 2025, 2026)
    html += gPanel('👤 Sales Team (3-Year History) — Group ' + key,
        gSortTable('reps', ['Rep', 'Win rate', 'Won', 'Lost', 'Open', 'Oldest (d)', '2024 (M)', '2025 (M)', '2026 (M)', 'Total 3Yr (M)', 'Visits 12m'],
            ['name', 'wr', 'won', 'lost', 'open', 'oldest', 'v24', 'v25', 'v26', 'vtot', 'visits'],
            [null, 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
            reps.map(r => [
                '<a href="#" data-rep="' + gEsc(r.emp_id) + '" style="font-weight:700;color:var(--primary-light);text-decoration:none;">' + gEsc(r.name) + '</a>',
                (r.win_rate_pct || '0') + '%', parseNum(r.quotes_won), parseNum(r.quotes_lost), parseNum(r.quotes_open),
                parseNum(r.oldest_open_quote_days), fmtM(parseNum(r.so_value_2024_m)), fmtM(parseNum(r.so_value_2025_m)),
                fmtM(parseNum(r.so_value_2026_m)), fmtM(parseNum(r.so_value_3yr_total_m)), parseNum(r.visits_12m)
            ])),
        reps.length + ' reps');

    // To-Do list with CapU insights
    html += gPanel('✅ To-Do List (CapU Analyzed) — Group ' + key,
        gSortTable('todo', ['Priority', 'Task', 'Insight / Reason', 'Owner'], ['priority', 'task', 'reason', 'owner'], [null, null, null, null],
            todos.map(t => [
                '<span style="font-weight:700;color:' + (t.priority === 'High' ? '#B91C1C' : t.priority === 'Medium' ? '#B45309' : '#475569') + ';">' + gEsc(t.priority) + '</span>',
                gEsc(t.task), gEsc(t.reason), gEsc(t.owner)
            ])),
        todos.length + ' items');

    host.insertAdjacentHTML('beforeend', html);
    gAttachSort(host);

    // Drill-downs
    const drill = document.getElementById('group-drill');
    const showDrill = (title, inner) => {
        drill.innerHTML = '<div style="background:#0F172A;color:white;padding:22px;border-radius:12px;margin-bottom:24px;">'
            + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
            + '<h3 style="font-size:16px;font-weight:800;">' + title + '</h3>'
            + '<button data-close="1" style="background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;cursor:pointer;">Close ✕</button></div>'
            + inner + '</div>';
        drill.scrollIntoView({ behavior: 'smooth', block: 'start' });
        const btn = drill.querySelector('button[data-close]');
        if (btn) btn.addEventListener('click', () => { drill.innerHTML = ''; });
    };
    const darkTable = (headers, rows, align) => {
        let h = '<div style="max-height:420px;overflow:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
            + '<thead><tr style="color:#94A3B8;">';
        headers.forEach((x, i) => { h += '<th style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.15);text-align:left;' + ((align && align[i]) ? 'text-align:' + align[i] + ';' : '') + '">' + x + '</th>'; });
        h += '</tr></thead><tbody>';
        rows.forEach(c => { h += '<tr>' + c.map((v, i) => '<td style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.08);color:#E2E8F0;' + ((align && align[i]) ? 'text-align:' + align[i] + ';' : '') + '">' + v + '</td>').join('') + '</tr>'; });
        if (!rows.length) h += '<tr><td colspan="' + headers.length + '" style="padding:16px;color:#94A3B8;">No records</td></tr>';
        return h + '</tbody></table></div>';
    };

    host.querySelectorAll('[data-drill]').forEach(el => el.addEventListener('click', () => {
        const what = el.getAttribute('data-drill');
        if (what === 'clients') {
            const list = clients.slice().sort((a, b) => (a.active_12m === 'Y' ? -1 : 1) - (b.active_12m === 'Y' ? -1 : 1));
            showDrill('🔎 Accounts — Active vs Non-Active (DBD matched = ' + clients.filter(c => c.in_dbd === 'Y').length + ' / Total DBD >100M: ' + dbdG + ' factories)',
                darkTable(['Account', 'Province', 'Industry', 'Status', 'DBD?', 'Capital (M)', 'Last order', 'Orders 12m', 'Value (M THB)'],
                    list.map(c => [
                        gEsc(c.company_name), gEsc(c.province), gEsc(c.industry_group), gBadge(c.active_12m),
                        c.in_dbd === 'Y' ? '<span style="color:#34D399;font-weight:700;">✓</span>' : '<span style="color:#94A3B8;">–</span>',
                        c.dbd_capital_m ? fmtM(parseNum(c.dbd_capital_m)) : '-',
                        c.last_order_date || '-', parseNum(c.so_count_12m), fmtM(parseNum(c.so_value_12m_m))
                    ])));
        } else if (what === 'quotes') {
            const q = clients.filter(c => parseNum(c.quotes_open) > 0).sort((a, b) => parseNum(b.oldest_open_quote_days) - parseNum(a.oldest_open_quote_days));
            showDrill('🧾 Open Quotations by account (oldest first)',
                darkTable(['Account', 'Open quotes', 'All quotes', 'Oldest open (days)', 'Province'],
                    q.map(c => [gEsc(c.company_name), parseNum(c.quotes_open), parseNum(c.quotes_total), parseNum(c.oldest_open_quote_days), gEsc(c.province)])));
        } else if (what === 'reps') {
            showDrill('👤 Team performance',
                darkTable(['Rep', 'Win rate', 'Won', 'Lost', 'Open', 'Oldest open (d)', '3Yr Total (M THB)', 'Visits 12m'],
                    reps.map(r => [gEsc(r.name), (r.win_rate_pct || 0) + '%', parseNum(r.quotes_won), parseNum(r.quotes_lost), parseNum(r.quotes_open), parseNum(r.oldest_open_quote_days), fmtM(parseNum(r.so_value_3yr_total_m)), parseNum(r.visits_12m)])));
        }
    }));

    // sales-order drill button
    const soBtn = document.createElement('button');
    soBtn.className = 'btn-primary';
    soBtn.style.cssText = 'margin-bottom:24px;';
    soBtn.textContent = '📦 View Sales Orders + delivery times (' + so.length + ')';
    soBtn.addEventListener('click', () => {
        const withLead = so.filter(x => (x.delivery_days || '') !== '');
        const avg = withLead.length ? Math.round(withLead.reduce((s, x) => s + parseNum(x.delivery_days), 0) / withLead.length) : 0;
        showDrill('📦 Sales Orders — Group ' + key + ' (avg lead time ' + avg + ' days, ' + withLead.length + ' with due date)',
            darkTable(['SO', 'Account', 'Value (THB)', 'Booking', 'Delivery', 'Lead (d)', 'Status'],
                so.slice(0, 400).map(x => [gEsc(x.so_id), gEsc(x.client_name) || gEsc(x.client_id), fmtM(parseNum(x.value_thb)), gEsc(x.booking_date), gEsc(x.delivery_date) || '-', x.delivery_days === '' ? '-' : x.delivery_days, gEsc(x.status)]),
                [null, null, 'right', null, null, 'right', null]));
    });
    const drillHost = document.getElementById('group-drill');
    if (drillHost) drillHost.parentNode.insertBefore(soBtn, drillHost.nextSibling);

    // per-rep drill from table links
    host.querySelectorAll('a[data-rep]').forEach(a => a.addEventListener('click', ev => {
        ev.preventDefault();
        const id = a.getAttribute('data-rep');
        const r = reps.find(x => x.emp_id === id) || {};
        showDrill('👤 ' + gEsc(r.name) + ' — personal performance (3-year history)',
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:14px;">'
            + darkKpi('Win rate', (r.win_rate_pct || 0) + '%') + darkKpi('Quotes won', parseNum(r.quotes_won)) + darkKpi('Quotes lost', parseNum(r.quotes_lost))
            + darkKpi('Open quotes', parseNum(r.quotes_open)) + darkKpi('Oldest open (d)', parseNum(r.oldest_open_quote_days))
            + darkKpi('2024 SO (M)', fmtM(parseNum(r.so_value_2024_m))) + darkKpi('2025 SO (M)', fmtM(parseNum(r.so_value_2025_m)))
            + darkKpi('2026 SO (M)', fmtM(parseNum(r.so_value_2026_m))) + darkKpi('3Yr Total (M)', fmtM(parseNum(r.so_value_3yr_total_m)))
            + darkKpi('Visits 12m', parseNum(r.visits_12m)) + '</div>'
            + '<div style="font-size:12px;color:#94A3B8;">Email: ' + gEsc(r.email) + '</div>');
    }));
}

function darkKpi(label, value) {
    return '<div style="background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:12px;">'
        + '<div style="font-size:11px;color:#94A3B8;font-weight:700;text-transform:uppercase;">' + label + '</div>'
        + '<div style="font-size:18px;font-weight:800;color:#fff;margin-top:4px;">' + value + '</div></div>';
}

document.addEventListener('viewLoaded', (e) => {
    if (GROUP_META[e.detail.viewId]) {
        renderGroupPage(e.detail.viewId).catch(err => {
            const host = document.getElementById('main-content');
            if (host) host.insertAdjacentHTML('beforeend', '<div style="padding:20px;background:#FEF2F2;color:#991B1B;border-radius:8px;">Group page error: ' + gEsc(err.message) + '</div>');
        });
    }
});
'''

path = "/home/jom/SynologyDrive/AI Dashboard/Dashboard_App/js/groups.js"
with open(path, "w", encoding="utf-8") as f:
    f.write(js_code)
print("groups.js written successfully")
EOF
python3 /home/jom/SynologyDrive/AI Dashboard/scripts/write_groups_file.py
cd "/home/jom/SynologyDrive/AI Dashboard/Dashboard_App"
node --check js/groups.js && echo "groups.js syntax OK"
sed -i "s/APP_VERSION = '20260924d';/APP_VERSION = '20260924e';/g" js/app.js
sed -i 's/v=20260924d/v=20260924e/g' index.html
echo "bumped to e"
