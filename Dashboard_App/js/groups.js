// 📊 Group A/B/C/D/R — Group Overview renderer (Comment 20260924 & 20260928)
// Features: 3-year rep history (2024-2026), Top 10 accounts per sales rep,
// rolling-12m active accounts vs DBD>100M coverage, win rate, quote ageing,
// CapU-aware To-Do list, and drill-downs (clients green/red, SO lead time, rep performance).

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
function gSortable(id, headers, keys, align, data, labels, container) {
    const render = rows => {
        container.innerHTML = gSortTable(id, headers, keys, align,
            rows.map(d => labels(d)));
        gAttachSort(container);
    };
    GSORT[id] = { sortKey: keys[0], dir: -1, rows: data, render: render };
    render(data);
}

function gAttachSort(root) {
    const host = root || document;
    host.querySelectorAll('th[data-key]').forEach(th => {
        const key = th.getAttribute('data-key');
        if (!key || th._bound) return;
        th._bound = true;
        th.addEventListener('click', () => {
            const table = th.closest('table');
            const tid = table ? table.getAttribute('data-tid') : null;
            const store = tid ? GSORT[tid] : null;
            if (!store) return;
            if (store.sortKey === key) store.dir = -store.dir; else { store.sortKey = key; store.dir = -1; }
            const rows = store.rows.slice().sort((a, b) => {
                const va = a[key], vb = b[key];
                const na = parseFloat(va), nb = parseFloat(vb);
                if (!isNaN(na) && !isNaN(nb)) return (na - nb) * store.dir;
                return String(va).localeCompare(String(vb), 'th') * store.dir;
            });
            store.render(rows);
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

const GSTATE = {};

async function renderGroupPage(viewId) {
    const meta = GROUP_META[viewId];
    const host = document.getElementById('main-content');
    if (!meta || !host) return;
    const key = meta.key;

    let kpi = {}, ov = {}, reps = [], clients = [], so = [], todos = [];
    try {
        const [k, o, rp, cl, sr, td, oq] = await Promise.all([
            gFetch('12_Group_KPI.csv'), gFetch('0_EPS_Overview_2026.csv'),
            gFetch('13_Rep_Performance.csv'), gFetch('14_Client_Detail.csv'),
            gFetch('15_SO_Delivery.csv'), gFetch('16_Todo.csv'),
            gFetch('17_Open_Quotes.csv')
        ]);
        kpi = (k.find(x => x.group === key) || {});
        ov = (o.find(x => x.metric === meta.metric) || {});
        reps = rp.filter(x => x.group === key);
        clients = cl.filter(x => x.group === key);
        so = sr.filter(x => x.group === key);
        todos = td.filter(x => x.group === key);
        window.GROUP_OPEN_QUOTES = oq.filter(x => x.group === key);
    } catch (err) {
        host.insertAdjacentHTML('beforeend', '<div style="padding:20px;background:#FEF2F2;color:#991B1B;border:1px solid #FECACA;border-radius:8px;"><strong>Could not load group data.</strong><br>' + gEsc(err.message) + '</div>');
        return;
    }

    GSTATE[key] = { reps: reps, clients: clients, so: so, todos: todos };

    const actual = parseNum(ov.value), target = parseNum(ov.target);
    const pct = target ? Math.round((actual / target) * 100) : 0;
    const gap = target - actual;
    const active = parseNum(kpi.active_accounts_12m), total = parseNum(kpi.accounts_total);
    const dbdG = parseNum(kpi.dbd_factories_gt100m), dbdAll = parseNum(kpi.dbd_total_gt100m);
    const wrCnt = kpi.win_rate_count_pct || '0';
    const wrVal = kpi.win_rate_value_pct || '0';
    const qOpen = parseNum(kpi.quotes_open), qAll = parseNum(kpi.quotes_total);
    const oldest = parseNum(kpi.oldest_open_quote_days);

    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:20px;margin-bottom:24px;">';
    html += gCard('Revenue — rolling 12 months', fmtM(actual), 'M THB',
        '<div style="height:8px;background:#E2E8F0;border-radius:4px;overflow:hidden;margin-bottom:6px;">'
        + '<div style="width:' + Math.min(pct, 100) + '%;height:100%;background:' + meta.color + ';border-radius:4px;"></div></div>'
        + 'Plan ' + fmtM(target) + 'M · gap <b>' + fmtM(gap) + 'M</b> · <span style="color:#1E40AF;">click for accounts</span>', meta.color, 'clients');
    html += gCard('Active Accounts (rolling 12m)', active, 'of ' + total,
        'Ordered or visited in the last 12 months (green = active, red = idle)'
        + '<div style="margin-top:6px;"><b>' + dbdG + '</b> of <b>' + dbdAll + '</b> registered factories &gt;100M capital served</div>',
        '#0EA5E9', 'clients');
    html += gCard('Win Rate — by count &amp; by value', wrCnt + '% / ' + wrVal + '%', 'count / value',
        parseNum(kpi.quotes_won) + ' won · ' + parseNum(kpi.quotes_lost) + ' lost · ' + qAll + ' quotes incl. pending · <span style="color:#1E40AF;">click for team</span>', '#6366F1', 'reps');

    html += gCard('Open Quotations', qOpen, 'open',
        'Oldest open <b>' + oldest + ' days</b> · <span style="color:#1E40AF;">click for ageing list</span>', '#14B8A6', 'quotes');
    html += '</div>';

    html += '<div id="group-drill"></div>';

    // ---- Top 10 accounts per rep (each rep = its own sortable table) ----
    let top10Html = '';
    reps.forEach(rep => {
        const mine = clients.filter(c => (c.rep_name && c.rep_name === rep.name) || c.owner_id === rep.emp_id)
            .sort((a, b) => parseNum(b.so_value_12m_m) - parseNum(a.so_value_12m_m));
        if (!mine.length) return;
        const top = mine.slice(0, 10);
        const id = 'top_' + rep.emp_id;
        top10Html += '<div style="margin-bottom:18px;">'
            + '<h4 style="font-size:14px;font-weight:700;color:#1E3A8A;margin-bottom:8px;">👤 ' + gEsc(rep.name)
            + ' — Top ' + top.length + ' of ' + mine.length + ' accounts</h4>'
            + '<div id="' + id + '-host"></div></div>';
        const data = top.map(c => ({
            company: c.company_name || '-', province: c.province || '-', industry: c.industry_group || '-',
            orders: parseNum(c.so_count_12m), value: parseNum(c.so_value_12m_m), visits: parseNum(c.visits_12m),
            last: c.days_since_last_order === '' ? 99999 : parseNum(c.days_since_last_order),
            active: c.active_12m === 'Y' ? 1 : 0
        }));
        const labels = d => [gEsc(d.company), gEsc(d.province), gEsc(d.industry), d.orders, fmtM(d.value), d.visits,
            (d.last === 99999 ? '-' : d.last + 'd'), gBadge(d.active ? 'Y' : 'N')];
        const headers = ['Account', 'Province', 'Industry', 'Orders', 'Value (M THB)', 'Visits', 'Last order', 'Status'];
        const keys = ['company', 'province', 'industry', 'orders', 'value', 'visits', 'last', 'active'];
        html += '';
        setTimeout(((hostId, data2, labels2, headers2, keys2) => () => {
            const c = document.getElementById(hostId);
            if (c) gSortable(hostId, headers2, keys2, [null, null, null, 'right', 'right', 'right', 'right', null], data2, labels2, c);
        })(id + '-host', data, labels, headers, keys), 0);
    });

    html += gPanel('🏢 Top 10 Accounts per Sales Rep — Group ' + key,
        top10Html || '<p style="color:var(--text-muted);">No attributed top accounts for the reps in this group.</p>',
        'Top 10 / rep · sortable');

    // ---- Sales team with 3-year history ----
    html += gPanel('👤 Sales Team — 3-Year History (2024 · 2025 · 2026) — Group ' + key,
        gSortTable('reps', ['Rep', 'WR count %', 'WR value %', 'Won', 'Lost', 'Open', 'Oldest (d)', '2024 (M THB)', '2025 (M THB)', '2026 (M THB)', 'Total 3 yr (M THB)', 'Visits 12m'],
            ['name', 'wrc', 'wrv', 'won', 'lost', 'open', 'oldest', 'v24', 'v25', 'v26', 'vtot', 'visits'],
            [null, 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right'],
            reps.map(r => [
                '<a href="#" data-rep="' + gEsc(r.emp_id) + '" style="font-weight:700;color:var(--primary-light);text-decoration:none;">' + gEsc(r.name) + '</a>',
                (r.win_rate_count_pct || '0') + '%', (r.win_rate_value_pct || '0') + '%',
                parseNum(r.quotes_won), parseNum(r.quotes_lost), parseNum(r.quotes_open),
                parseNum(r.oldest_open_quote_days), fmtM(parseNum(r.so_value_2024_m)), fmtM(parseNum(r.so_value_2025_m)),
                fmtM(parseNum(r.so_value_2026_m)), fmtM(parseNum(r.so_value_3yr_total_m)), parseNum(r.visits_12m)
            ])),
        reps.length + ' reps · click a name for the personal page');

    // ---- Group Open Quotations Panel ----
    const gQuotes = window.GROUP_OPEN_QUOTES || [];
    gQuotes.sort((a, b) => parseInt(b.aging_days || 0) - parseInt(a.aging_days || 0));
    const gQuotesData = gQuotes.map(q => ({
        qid: q.quote_id || '-', company: q.company_name || '-', rep: q.rep_name || '-',
        val: parseNum(q.value_thb), chance: q.probability_pct || '-', exp: q.expected_order_date || '-',
        aging: parseInt(q.aging_days || 0)
    }));
    const gQuotesCells = gQuotesData.map(d => [
        '<b>' + gEsc(d.qid) + '</b>', gEsc(d.company), gEsc(d.rep), fmtM(d.val), d.chance, d.exp,
        (d.aging > 90 ? '<span style="color:#B91C1C;font-weight:700;">' + d.aging + ' d</span>' : d.aging + ' d')
    ]);
    html += gPanel('🧾 Open Quotations Pipeline — Group ' + key,
        gSortTable('g_quotes_' + key, ['Quote ID', 'Company Name', 'Sales Rep', 'Value (M THB)', 'Chance', 'Expected Order', 'Aging (Days)'],
            ['qid', 'company', 'rep', 'val', 'chance', 'exp', 'aging'],
            [null, null, null, 'right', 'center', null, 'right'],
            gQuotesCells),
        gQuotes.length + ' pending deals');

    // ---- To-Do ----
    html += gPanel('✅ To-Do List (generated from CRM + CapU signals) — Group ' + key,
        gSortTable('todo', ['Priority', 'Task', 'Insight / reason', 'Owner'], ['priority', 'task', 'reason', 'owner'], [null, null, null, null],
            todos.map(t => [
                '<span style="font-weight:700;color:' + (t.priority === 'High' ? '#B91C1C' : t.priority === 'Medium' ? '#B45309' : '#475569') + ';">' + gEsc(t.priority) + '</span>',
                gEsc(t.task), gEsc(t.reason), gEsc(t.owner)
            ])),
        todos.length + ' items');

    host.insertAdjacentHTML('beforeend', html);

    // ---- wiring ----
    gAttachSort(host);

    const soBtn = document.createElement('button');
    soBtn.className = 'btn-primary';
    soBtn.style.cssText = 'margin-bottom:24px;';
    soBtn.textContent = '📦 Sales Orders + delivery times (' + so.length + ' orders in this group)';
    const drillHost = document.getElementById('group-drill');

    const darkMini = (label, value) => '<div style="background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:12px;">'
        + '<div style="font-size:11px;color:#94A3B8;font-weight:700;text-transform:uppercase;">' + label + '</div>'
        + '<div style="font-size:18px;font-weight:800;color:#fff;margin-top:4px;">' + value + '</div></div>';

    const darkTable = (headers, rows, align) => {
        let h = '<div style="max-height:420px;overflow:auto;"><table style="width:100%;border-collapse:collapse;font-size:13px;">'
            + '<thead><tr style="color:#94A3B8;">';
        headers.forEach((x, i) => { h += '<th style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.15);text-align:left;' + ((align && align[i]) ? 'text-align:' + align[i] + ';' : '') + '">' + x + '</th>'; });
        h += '</tr></thead><tbody>';
        rows.forEach(c => { h += '<tr>' + c.map((v, i) => '<td style="padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.08);color:#E2E8F0;' + ((align && align[i]) ? 'text-align:' + align[i] + ';' : '') + '">' + v + '</td>').join('') + '</tr>'; });
        if (!rows.length) h += '<tr><td colspan="' + headers.length + '" style="padding:16px;color:#94A3B8;">No records</td></tr>';
        return h + '</tbody></table></div>';
    };

    const showDrill = (title, inner) => {
        drillHost.innerHTML = '<div style="background:#0F172A;color:white;padding:22px;border-radius:12px;margin-bottom:24px;">'
            + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
            + '<h3 style="font-size:16px;font-weight:800;">' + title + '</h3>'
            + '<button data-close="1" style="background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:700;cursor:pointer;">Close ✕</button></div>'
            + inner + '</div>';
        drillHost.scrollIntoView({ behavior: 'smooth', block: 'start' });
        const b = drillHost.querySelector('button[data-close]');
        if (b) b.addEventListener('click', () => { drillHost.innerHTML = ''; });
    };

    if (drillHost) drillHost.parentNode.insertBefore(soBtn, drillHost.nextSibling);

    soBtn.addEventListener('click', () => {
        const withLead = so.filter(x => (x.delivery_days || '') !== '');
        const avg = withLead.length ? Math.round(withLead.reduce((s, x) => s + parseNum(x.delivery_days), 0) / withLead.length) : 0;
        const totalVal = so.reduce((s, x) => s + parseNum(x.value_thb), 0);
        showDrill('📦 Sales Orders — Group ' + key + ' · ' + withLead.length + ' of ' + so.length + ' have a due date (avg lead time ' + avg + ' days)',
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:14px;">'
            + darkMini('Orders', so.length) + darkMini('Value (M THB)', fmtM(totalVal / 1e6)) + darkMini('Avg lead (days)', avg) + '</div>'
            + darkTable(['SO', 'Account', 'Value (THB)', 'Booking', 'Delivery', 'Lead (d)', 'Status'],
                so.slice(0, 400).map(x => [gEsc(x.so_id), gEsc(x.client_name) || gEsc(x.client_id), fmtM(parseNum(x.value_thb)), gEsc(x.booking_date), gEsc(x.delivery_date) || '-', x.delivery_days === '' ? '-' : x.delivery_days, gEsc(x.status)]),
                [null, null, 'right', null, null, 'right', null]));
    });

    host.querySelectorAll('[data-drill]').forEach(el => el.addEventListener('click', () => {
        const what = el.getAttribute('data-drill');
        if (what === 'clients') {
            const list = clients.slice().sort((a, b) => {
                if (a.active_12m !== b.active_12m) return a.active_12m === 'Y' ? -1 : 1;
                return parseNum(b.so_value_12m_m) - parseNum(a.so_value_12m_m);
            });
            showDrill('🔎 Accounts — active (green) vs non-active (red) · DBD matched: ' + clients.filter(c => c.in_dbd === 'Y').length + ' of ' + clients.length,
                darkTable(['Account', 'Province', 'Industry', 'Status', 'DBD', 'Capital (M)', 'Last order', 'Orders 12m', 'Value (M THB)'],
                    list.map(c => [gEsc(c.company_name), gEsc(c.province), gEsc(c.industry_group), gBadge(c.active_12m),
                        c.in_dbd === 'Y' ? '<span style="color:#34D399;font-weight:700;">✓ matched</span>' : '<span style="color:#94A3B8;">–</span>',
                        c.dbd_capital_m ? fmtM(parseNum(c.dbd_capital_m)) : '-',
                        c.last_order_date || '-', parseNum(c.so_count_12m), fmtM(parseNum(c.so_value_12m_m))]),
                    [null, null, null, null, null, 'right', null, 'right', 'right']));
        } else if (what === 'quotes') {
            const q = clients.filter(c => parseNum(c.quotes_open) > 0)
                .sort((a, b) => parseNum(b.oldest_open_quote_days) - parseNum(a.oldest_open_quote_days));
            showDrill('🧾 Open quotations by account (oldest first)',
                darkTable(['Account', 'Open quotes', 'All quotes', 'Oldest open (days)', 'Province'],
                    q.map(c => [gEsc(c.company_name), parseNum(c.quotes_open), parseNum(c.quotes_total), parseNum(c.oldest_open_quote_days), gEsc(c.province)]),
                    [null, 'right', 'right', 'right', null]));
        } else if (what === 'reps') {
            showDrill('👤 Team performance — Group ' + key,
                darkTable(['Rep', 'WR count %', 'WR value %', 'Won', 'Lost', 'Open', 'Oldest (d)', '2024 (M)', '2025 (M)', '2026 (M)', '3-yr total (M)'],
                    reps.map(r => [gEsc(r.name), (r.win_rate_count_pct || 0) + '%', (r.win_rate_value_pct || 0) + '%', parseNum(r.quotes_won), parseNum(r.quotes_lost),
                        parseNum(r.quotes_open), parseNum(r.oldest_open_quote_days), fmtM(parseNum(r.so_value_2024_m)),
                        fmtM(parseNum(r.so_value_2025_m)), fmtM(parseNum(r.so_value_2026_m)), fmtM(parseNum(r.so_value_3yr_total_m))]),
                    [null, 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right', 'right']));
        }
    }));

    host.querySelectorAll('a[data-rep]').forEach(a => a.addEventListener('click', ev => {
        ev.preventDefault();
        const id = a.getAttribute('data-rep');
        const r = reps.find(x => x.emp_id === id) || {};
        showDrill('👤 ' + gEsc(r.name) + ' — personal performance',
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:14px;">'
            + darkMini('WR count %', (r.win_rate_count_pct || 0) + '%') + darkMini('WR value %', (r.win_rate_value_pct || 0) + '%')
            + darkMini('Won / lost', parseNum(r.quotes_won) + ' / ' + parseNum(r.quotes_lost))
            + darkMini('Open quotes', parseNum(r.quotes_open)) + darkMini('Oldest open (d)', parseNum(r.oldest_open_quote_days))
            + darkMini('2024 (M THB)', fmtM(parseNum(r.so_value_2024_m))) + darkMini('2025 (M THB)', fmtM(parseNum(r.so_value_2025_m)))
            + darkMini('2026 (M THB)', fmtM(parseNum(r.so_value_2026_m))) + darkMini('3-yr total (M THB)', fmtM(parseNum(r.so_value_3yr_total_m)))
            + darkMini('Visits 12m', parseNum(r.visits_12m)) + '</div>'
            + '<div style="font-size:12px;color:#94A3B8;">Email: ' + gEsc(r.email) + '</div>');
    }));
}

document.addEventListener('viewLoaded', (e) => {
    if (GROUP_META[e.detail.viewId]) {
        renderGroupPage(e.detail.viewId).catch(err => {
            const host = document.getElementById('main-content');
            if (host) host.insertAdjacentHTML('beforeend', '<div style="padding:20px;background:#FEF2F2;color:#991B1B;border-radius:8px;">Group page error: ' + gEsc(err.message) + '</div>');
        });
    }
});
