// 🧩 Minimal RFC4180-ish CSV parser (no external dependency, works offline & on GitHub Pages)
// Handles: quoted fields, embedded commas, embedded newlines, escaped quotes ("")
// Usage: const rows = parseCSV(text);   // rows = array of objects keyed by header row

function parseCSV(text) {
    // Normalize line endings, strip BOM
    text = text.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    const rows = [];
    let row = [];
    let field = '';
    let inQuotes = false;

    for (let i = 0; i < text.length; i++) {
        const c = text[i];

        if (inQuotes) {
            if (c === '"') {
                if (text[i + 1] === '"') { field += '"'; i++; }   // escaped quote
                else { inQuotes = false; }
            } else {
                field += c;
            }
        } else {
            if (c === '"') {
                inQuotes = true;
            } else if (c === ',') {
                row.push(field); field = '';
            } else if (c === '\n') {
                row.push(field); field = '';
                rows.push(row); row = [];
            } else {
                field += c;
            }
        }
    }
    // flush last field/row
    if (field !== '' || row.length > 0) { row.push(field); rows.push(row); }

    if (rows.length === 0) return [];

    // First row = header; trim and de-duplicate empty header names
    const header = rows[0].map(h => h.trim());
    const out = [];
    for (let r = 1; r < rows.length; r++) {
        const cells = rows[r];
        // skip fully empty lines
        if (cells.length === 1 && cells[0].trim() === '') continue;
        const obj = {};
        header.forEach((key, idx) => {
            if (!key) return;
            obj[key] = (cells[idx] !== undefined ? cells[idx] : '').trim();
        });
        out.push(obj);
    }
    return out;
}

// Helper: parse a number that may contain thousands separators / quotes
function parseNum(v) {
    if (v === null || v === undefined) return 0;
    const cleaned = String(v).replace(/[",\s]/g, '');
    const n = parseFloat(cleaned);
    return isNaN(n) ? 0 : n;
}
