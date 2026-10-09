// 🌐 EPS Dashboard - Bilingual i18n (Thai / English)
const i18n = {
    currentLang: localStorage.getItem('eps_lang') || 'th',

    dict: {
        th: {
            brandSub: 'Performance Cockpit',
            loginTitle: 'เข้าสู่ระบบแดชบอร์ด',
            username: 'ชื่อผู้ใช้ (Username)',
            password: 'รหัสผ่าน (Password)',
            signIn: 'เข้าสู่ระบบ',
            logout: 'ออกจากระบบ',
            fiscalYear: 'ปีงบประมาณ',
            loading: 'กำลังโหลดข้อมูล...',
            dataSources: 'แหล่งข้อมูล',
            role: 'สิทธิ์การใช้งาน',
            errorUser: 'กรุณากรอกชื่อผู้ใช้',
            errorLogin: 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง',
            navOverview: 'ภาพรวม (Overview)',
            navGroupA: 'กลุ่ม A (Energy & Petrochem)',
            navGroupB: 'กลุ่ม B (Water & Municipal)',
            navGroupC: 'กลุ่ม C (Renewable & Agri)',
            navGroupD: 'กลุ่ม D (Industrial & EPC)',
            navGroupR: 'กลุ่ม R (Rayon / Eastern)',
            navStock: 'คลังสินค้า & Dead Stock',
            navEconomic: 'เศรษฐกิจมหภาค & BOI/DBD',
            navQuotes: 'ใบเสนอราคาค้าง (Open Quotes)'
        },
        en: {
            brandSub: 'Performance Cockpit',
            loginTitle: 'Access Dashboard',
            username: 'Username',
            password: 'Password',
            signIn: 'Sign In',
            logout: 'Logout',
            fiscalYear: 'Fiscal Year',
            loading: 'Loading data...',
            dataSources: 'Data Sources',
            role: 'Role',
            errorUser: 'Please enter a username.',
            errorLogin: 'Invalid username or password.',
            navOverview: 'Overview',
            navGroupA: 'Group A (Energy & Petrochem)',
            navGroupB: 'Group B (Water & Municipal)',
            navGroupC: 'Group C (Renewable & Agri)',
            navGroupD: 'Group D (Industrial & EPC)',
            navGroupR: 'Group R (Rayon / Eastern)',
            navStock: 'Inventory & Dead Stock',
            navEconomic: 'Macro & BOI/DBD',
            navQuotes: 'Open Quotations'
        }
    },

    t(key) {
        return this.dict[this.currentLang][key] || this.dict['th'][key] || key;
    },

    setLang(lang) {
        this.currentLang = lang;
        localStorage.setItem('eps_lang', lang);
        window.location.reload();
    },

    toggleLang() {
        this.setLang(this.currentLang === 'th' ? 'en' : 'th');
    }
};
