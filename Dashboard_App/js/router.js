// 🛣️ EPS Dashboard - Role-Based Router
const router = {
    pageDefinitions: {
        'eps_overview': { id: 'eps_overview', file: 'eps_overview.html', titleTh: '🏢 ภาพรวม EPS', titleEn: '🏢 EPS Overview' },
        'group_a': { id: 'group_a', file: 'group_a.html', titleTh: '📊 ภาพรวมกลุ่ม A', titleEn: '📊 Group A Overview' },
        'group_b': { id: 'group_b', file: 'group_b.html', titleTh: '📊 ภาพรวมกลุ่ม B', titleEn: '📊 Group B Overview' },
        'group_c': { id: 'group_c', file: 'group_c.html', titleTh: '📊 ภาพรวมกลุ่ม C', titleEn: '📊 Group C Overview' },
        'group_d': { id: 'group_d', file: 'group_d.html', titleTh: '📊 ภาพรวมกลุ่ม D', titleEn: '📊 Group D Overview' },
        'group_r': { id: 'group_r', file: 'group_r.html', titleTh: '📊 ภาพรวมกลุ่ม R', titleEn: '📊 Group R Overview' },
        'stock':   { id: 'stock', file: 'stock.html', titleTh: '📦 คลังสินค้า & Dead Stock', titleEn: '📦 Inventory & Dead Stock' },
        'economic':{ id: 'economic', file: 'economic.html', titleTh: '📈 เศรษฐกิจมหภาค & BOI/DBD', titleEn: '📈 Macro & BOI/DBD' }
    },

    init(user) {
        this.currentUser = user;
        this.renderNav();
        if (user.pages && user.pages.length > 0) this.navigate(user.pages[0]);
    },

    renderNav() {
        const navContainer = document.getElementById('nav-tabs-container');
        navContainer.innerHTML = '';
        this.currentUser.pages.forEach(pageId => {
            const pageDef = this.pageDefinitions[pageId];
            if (!pageDef) return;
            const btn = document.createElement('button');
            btn.className = 'nav-tab';
            btn.id = 'tab-' + pageId;
            btn.onclick = () => this.navigate(pageId);
            const title = (i18n.currentLang === 'en') ? pageDef.titleEn : pageDef.titleTh;
            btn.innerHTML = '<span>' + title + '</span>';
            navContainer.appendChild(btn);
        });
    },

    async navigate(pageId) {
        document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
        const activeTab = document.getElementById('tab-' + pageId);
        if (activeTab) activeTab.classList.add('active');

        const mainContent = document.getElementById('main-content');
        mainContent.innerHTML = '<div class="loading-spinner">Loading view...</div>';

        const pageDef = this.pageDefinitions[pageId];
        try {
            // Absolute URL so it works whether opened at / or /Dashboard_App/
            const fileResp = await fetch(APP_BASE + 'views/' + pageDef.file + '?v=' + APP_VERSION);
            if (!fileResp.ok) throw new Error('view HTTP ' + fileResp.status);
            mainContent.innerHTML = await fileResp.text();
            // let the view renderer (already loaded globally) react
            setTimeout(() => document.dispatchEvent(new CustomEvent('viewLoaded', { detail: { viewId: pageId } })), 0);
        } catch (error) {
            mainContent.innerHTML = '<div class="form-error" style="text-align:left; padding: 20px; background:#FEF2F2; color:#991B1B; border:1px solid #FECACA; border-radius:8px;">'
                + '<strong>Error loading view:</strong> ' + error.message + '<br><br>'
                + 'Please open the dashboard through a local web server (not by double-clicking the file):<br>'
                + '<code>cd "/home/jom/SynologyDrive/AI Dashboard" &amp;&amp; python3 -m http.server 8080</code><br>'
                + 'then go to <a href="http://localhost:8080/Dashboard_App/index.html">http://localhost:8080/Dashboard_App/index.html</a>'
                + '</div>';
        }
    }
};
