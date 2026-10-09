// 🔒 EPS Dashboard - Authentication & Roles
const auth = {
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
            return { success: true, user: user };
        } else {
            return { success: false, message: 'Invalid username or password.' };
        }
    },

    logout() {
        sessionStorage.removeItem('eps_user');
        window.location.reload();
    },

    getCurrentUser() {
        const userData = sessionStorage.getItem('eps_user');
        return userData ? JSON.parse(userData) : null;
    }
};
