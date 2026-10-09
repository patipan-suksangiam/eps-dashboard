// 🔒 EPS Dashboard - Authentication & Roles
const auth = {
    // ผู้ใช้ที่เข้าโดยอัตโนมัติเมื่อยังไม่ล็อกอิน — ทีมใช้รหัสกลางของเซิร์ฟเวอร์อยู่แล้ว
    // จึงไม่ต้องล็อกอินซ้ำ (หัวหน้ากลุ่มที่อยากเห็นเฉพาะกลุ่มตัวเอง: กด "ออกจากระบบ" แล้วใช้บัญชี group_*)
    SHARED_USER: 'admin',
    LOGOUT_FLAG: 'eps_logged_out',

    users: {
        'admin':   { name: 'System Administrator', roleId: 'admin', roleName: 'Admin', pages: ['eps_overview', 'group_a', 'group_b', 'group_c', 'group_d', 'group_r', 'stock', 'economic'] },
        'group_a': { name: 'Manager Group A', roleId: 'group_a', roleName: 'Head of Group A', pages: ['group_a', 'stock', 'economic'] },
        'group_b': { name: 'Manager Group B', roleId: 'group_b', roleName: 'Head of Group B', pages: ['group_b', 'stock', 'economic'] },
        'group_c': { name: 'Manager Group C', roleId: 'group_c', roleName: 'Head of Group C', pages: ['group_c', 'stock', 'economic'] },
        'group_d': { name: 'Manager Group D', roleId: 'group_d', roleName: 'Head of Group D', pages: ['group_d', 'stock', 'economic'] },
        'group_r': { name: 'Manager Group R', roleId: 'group_r', roleName: 'Head of Group R', pages: ['group_r', 'stock', 'economic'] }
    },

    passwords: {
        'admin': 'admin123',
        'group_a': 'eps2026_a',
        'group_b': 'eps2026_b',
        'group_c': 'eps2026_c',
        'group_d': 'eps2026_d',
        'group_r': 'eps2026_r'
    },

    login(username, password) {
        const uid = username.toLowerCase();
        const user = this.users[uid];
        
        if (user && this.passwords[uid] === password) {
            sessionStorage.setItem('eps_user', JSON.stringify(user));
            sessionStorage.removeItem(this.LOGOUT_FLAG);   // ล็อกอินเองแล้ว → เปิด autoLogin อีกครั้ง
            return { success: true, user: user };
        } else {
            return { success: false, message: 'Invalid username or password.' };
        }
    },

    logout() {
        sessionStorage.removeItem('eps_user');
        sessionStorage.setItem(this.LOGOUT_FLAG, '1');   // กัน autoLogin ดึงกลับเข้าทันที
        window.location.reload();
    },

    // ผู้ใช้เริ่มต้นสำหรับทีม (ถ้าเพิ่งกด "ออกจากระบบ" จะคืน null → แสดงหน้า login ปกติ)
    autoLogin() {
        if (sessionStorage.getItem(this.LOGOUT_FLAG)) return null;
        const u = this.users[this.SHARED_USER];
        if (!u) return null;
        sessionStorage.setItem('eps_user', JSON.stringify(u));
        return u;
    },

    getCurrentUser() {
        const userData = sessionStorage.getItem('eps_user');
        return userData ? JSON.parse(userData) : null;
    }
};
