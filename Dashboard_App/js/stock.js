// 📦 Stock & Product Management renderer (with Filter Dropdowns & Search)
document.addEventListener('viewLoaded', async (e) => {
    if (e.detail.viewId !== 'stock') return;

    const tbody = document.getElementById('inventory-tbody');
    try {
        const res = await fetch(DATA_BASE + '5_Inventory_Supplier.csv?t=' + Date.now());
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const rows = parseCSV(await res.text());

        let totalValuation = 0, deadStockVal = 0;
        const items = [];
        const brandsSet = new Set();

        rows.forEach(r => {
            const brand = (r['Products'] || r['Brand'] || '').trim();
            const code = (r['CODE'] || '').trim();
            const desc = (r['Description'] || '').trim();
            const qty = parseInt(String(r['Qty'] || '0').replace(/,/g, '')) || 0;
            const price = parseNum(r['Total price'] || r['Total Price'] || 0);
            const type = (r['TYPE'] || 'Spare Part').trim();
            const status = (r['Status'] || '').trim();

            totalValuation += price;
            if (status.toLowerCase().indexOf('dead') !== -1) deadStockVal += price;

            if (code) {
                items.push({ brand, code, desc, qty, price, type, status });
                if (brand) brandsSet.add(brand);
            }
        });

        // Update KPIs
        const inv = document.getElementById('kpi-total-inv');
        const dead = document.getElementById('kpi-dead-stock');
        if (inv) inv.innerText = (totalValuation / 1000000).toFixed(2) + 'M THB';
        if (dead) dead.innerText = (deadStockVal / 1000000).toFixed(2) + 'M THB';

        // Update Last-Modified stamp
        const stamp = document.getElementById('inv-last-updated');
        if (stamp) {
            const lm = res.headers && res.headers.get ? res.headers.get('last-modified') : null;
            stamp.innerText = lm ? ('Data updated: ' + new Date(lm).toLocaleString()) : ('Total items: ' + items.length);
        }

        // Populate Brand Dropdown
        const brandSelect = document.getElementById('filter-brand');
        if (brandSelect) {
            const sortedBrands = Array.from(brandsSet).sort();
            let bHtml = '<option value="all">All Brands (' + sortedBrands.length + ' brands)</option>';
            sortedBrands.forEach(b => {
                bHtml += '<option value="' + b + '">' + b + '</option>';
            });
            brandSelect.innerHTML = bHtml;
        }

        // Render function
        const renderTable = (list) => {
            const badge = (s) => {
                const t = (s || '').toLowerCase();
                let bg = '#F1F5F9', fg = '#475569';
                if (t.indexOf('dead') !== -1) { bg = '#FEF2F2'; fg = '#B91C1C'; }
                else if (t.indexOf('stock') !== -1 || t.indexOf('available') !== -1) { bg = '#ECFDF5'; fg = '#065F46'; }
                return '<span style="background:' + bg + ';color:' + fg + ';padding:2px 6px;border-radius:4px;font-size:11px;font-weight:700;">' + (s || '-') + '</span>';
            };

            let html = '';
            list.slice(0, 400).forEach(it => {
                html += '<tr>'
                    + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);font-weight:600;">' + (it.brand || '-') + '</td>'
                    + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);font-family:monospace;font-size:11px;">' + it.code + '</td>'
                    + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);">' + it.desc + '</td>'
                    + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);">' + it.qty + '</td>'
                    + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);font-weight:700;text-align:right;">' + it.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + '</td>'
                    + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);">' + it.type + '</td>'
                    + '<td style="padding:10px 14px;border-bottom:1px solid var(--border-subtle);">' + badge(it.status) + '</td>'
                    + '</tr>';
            });

            if (tbody) {
                tbody.innerHTML = html || '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-muted);">No matching inventory records found.</td></tr>';
            }
        };

        // Initial render
        renderTable(items);

        // Filter event listeners
        const applyFilters = () => {
            const bVal = document.getElementById('filter-brand').value;
            const sVal = document.getElementById('filter-status').value;
            const qVal = document.getElementById('search-input').value.toLowerCase().trim();

            const filtered = items.filter(it => {
                if (bVal !== 'all' && it.brand !== bVal) return false;
                if (sVal === 'dead' && it.status.toLowerCase().indexOf('dead') === -1) return false;
                if (qVal) {
                    const matchCode = it.code.toLowerCase().includes(qVal);
                    const matchDesc = it.desc.toLowerCase().includes(qVal);
                    if (!matchCode && !matchDesc) return false;
                }
                return true;
            });
            renderTable(filtered);
        };

        document.getElementById('filter-brand').addEventListener('change', applyFilters);
        document.getElementById('filter-status').addEventListener('change', applyFilters);
        document.getElementById('search-input').addEventListener('input', applyFilters);

    } catch (err) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#B91C1C;padding:20px;">Failed to load inventory CSV: ' + err.message + '</td></tr>';
    }
});
