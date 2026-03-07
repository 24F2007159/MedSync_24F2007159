// auth.js - authentication and shared data/methods

const authData = {
    currentPage: 'home',
    loading: false,
    error: null,
    toast: { show: false, message: '', type: 'success' },
    currentUser: {},
    loginForm: { username: '', password: '' },
    registerForm: {
        username: '', email: '', password: '', name: '',
        phone: '', age: null, gender: '', blood_group: ''
    },
};

const authMethods = {
    showToast(message, type = 'success') {
        this.toast = { show: true, message, type };
        setTimeout(() => { this.toast.show = false; }, 3000);
    },

    async login() {
        if (!this.loginForm.username.trim() || !this.loginForm.password.trim()) {
            this.error = 'Username and password are required';
            return;
        }
        this.loading = true;
        this.error = null;
        try {
            const res = await api.login(this.loginForm);
            if (res.success) {
                localStorage.setItem('medsync_token', res.data.token);
                localStorage.setItem('medsync_role', res.data.role);
                localStorage.setItem('medsync_username', res.data.username);
                this.currentUser = { username: res.data.username, role: res.data.role };
                this.currentPage = res.data.role;
                this.loadInitialData(res.data.role);
                this.showToast(`Welcome back, ${res.data.username}!`);
            } else {
                this.error = res.message;
            }
        } catch (e) {
            this.error = 'Connection error. Please try again.';
        }
        this.loading = false;
    },

    async register() {
        const f = this.registerForm;
        if (!f.name.trim() || !f.username.trim() || !f.email.trim() || !f.password.trim()) {
            this.error = 'Name, username, email and password are required';
            return;
        }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(f.email)) {
            this.error = 'Please enter a valid email address';
            return;
        }
        if (f.password.length < 6) {
            this.error = 'Password must be at least 6 characters';
            return;
        }
        this.loading = true;
        this.error = null;
        try {
            const res = await api.register(f);
            if (res.success) {
                this.showToast('Registration successful! Please login.');
                this.currentPage = 'login';
            } else {
                this.error = res.message;
            }
        } catch (e) {
            this.error = 'Connection error. Please try again.';
        }
        this.loading = false;
    },

    logout() {
        localStorage.clear();
        this.currentUser = {};
        this.currentPage = 'home';
        this.showToast('Logged out successfully');
    },

    loadInitialData(role) {
        if (role === 'admin') {
            this.loadAdminDashboard();
        } else if (role === 'doctor') {
            this.loadDoctorDashboard();
        } else if (role === 'patient') {
            this.loadPatientDashboard();
            this.loadDepartments();
        }
    },
};
