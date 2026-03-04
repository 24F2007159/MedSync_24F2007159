const { createApp } = Vue;

createApp({
    data() {
        return {
            // page state
            currentPage: 'login',
            loading: false,
            error: null,
            
            // toast notification
            toast: { show: false, message: '', type: 'success' },
            
            // current user
            currentUser: {},
            
            // forms
            loginForm: { username: '', password: '' },
            registerForm: { username: '', email: '', password: '', name: '', phone: '', age: null, gender: '', blood_group: '' },
            
            // patient data
            patientTab: 'dashboard',
            patientStats: { upcoming_appointments: 0, total_appointments: 0, doctors_visited: 0 },
            patientAppointments: [],
            patientHistory: [],
            patientProfile: {},
            
            // booking flow
            bookingStep: 1,
            selectedDept: null,
            selectedDoctor: null,
            selectedDate: '',
            selectedSlot: null,
            timeSlots: [],
            bookingNotes: '',
            minDate: new Date().toISOString().split('T')[0],
            deptDoctors: [],
            departments: [],
        };
    },

    mounted() {
        // check if user is already logged in
        const token = localStorage.getItem('medsync_token');
        const role = localStorage.getItem('medsync_role');
        const username = localStorage.getItem('medsync_username');
        
        if (token && role === 'patient') {
            this.currentUser = { username, role };
            this.currentPage = 'patient';
            this.loadPatientDashboard();
            this.loadDepartments();
        }
    },

    methods: {
        // show toast notification
        showToast(message, type = 'success') {
            this.toast = { show: true, message, type };
            setTimeout(() => { this.toast.show = false; }, 3000);
        },

        // login
        async login() {
            if (!this.loginForm.username || !this.loginForm.password) {
                this.error = 'Please enter username and password';
                return;
            }
            this.loading = true;
            this.error = null;
            try {
                const res = await api.login(this.loginForm);
                if (res.success) {
                    // Check if user is a patient
                    if (res.data.role !== 'patient') {
                        this.error = 'This portal is for patients only. Please use the appropriate login.';
                        this.loading = false;
                        return;
                    }
                    
                    localStorage.setItem('medsync_token', res.data.token);
                    localStorage.setItem('medsync_role', res.data.role);
                    localStorage.setItem('medsync_username', res.data.username);
                    this.currentUser = { username: res.data.username, role: res.data.role };
                    this.currentPage = 'patient';
                    this.loginForm = { username: '', password: '' };
                    this.loadPatientDashboard();
                    this.loadDepartments();
                    this.showToast(`Welcome back, ${res.data.username}!`);
                } else {
                    this.error = res.message || 'Login failed';
                }
            } catch (e) {
                this.error = 'Connection error. Please try again.';
                console.error(e);
            }
            this.loading = false;
        },

        // register
        async register() {
            if (!this.registerForm.name || !this.registerForm.username || !this.registerForm.email || !this.registerForm.password) {
                this.error = 'Please fill in all required fields';
                return;
            }
            this.loading = true;
            this.error = null;
            try {
                const res = await api.register(this.registerForm);
                if (res.success) {
                    this.showToast('Registration successful! Please login.');
                    this.currentPage = 'login';
                    this.registerForm = { username: '', email: '', password: '', name: '', phone: '', age: null, gender: '', blood_group: '' };
                } else {
                    this.error = res.message || 'Registration failed';
                }
            } catch (e) {
                this.error = 'Connection error. Please try again.';
                console.error(e);
            }
            this.loading = false;
        },

        // logout
        logout() {
            localStorage.clear();
            this.currentUser = {};
            this.currentPage = 'login';
            this.loginForm = { username: '', password: '' };
            this.patientTab = 'dashboard';
            this.bookingStep = 1;
            this.selectedDept = null;
            this.selectedDoctor = null;
            this.selectedDate = '';
            this.selectedSlot = null;
            this.showToast('Logged out successfully');
        },

        // ===== PATIENT METHODS =====
        async loadPatientDashboard() {
            try {
                const res = await api.getPatientDashboard();
                if (res.success) {
                    this.patientStats = res.data;
                    this.patientProfile = res.data.patient;
                }
            } catch (e) {
                console.error('Error loading dashboard:', e);
            }
        },

        async loadDepartments() {
            try {
                const res = await api.getDepartments();
                if (res.success) {
                    this.departments = res.data.departments;
                }
            } catch (e) {
                console.error('Error loading departments:', e);
            }
        },

        async selectDepartment(dept) {
            this.selectedDept = dept;
            this.selectedDoctor = null;
            this.deptDoctors = [];
            
            try {
                const res = await api.getDoctorsByDepartment(dept.id);
                if (res.success) {
                    this.deptDoctors = res.data.doctors;
                    this.bookingStep = 2;
                } else {
                    this.showToast('Failed to load doctors: ' + res.message, 'danger');
                }
            } catch (e) {
                this.showToast('Error loading doctors', 'danger');
                console.error(e);
            }
        },

        selectDoctor(doc) {
            this.selectedDoctor = doc;
            this.selectedDate = '';
            this.selectedSlot = null;
            this.timeSlots = [];
            this.bookingStep = 3;
        },

        async loadTimeSlots() {
            if (!this.selectedDate) return;
            
            try {
                const res = await api.getAvailableSlots(this.selectedDoctor.id, this.selectedDate);
                if (res.success) {
                    this.timeSlots = res.data.slots || [];
                    this.selectedSlot = null;
                } else {
                    this.showToast('No slots available for this date', 'danger');
                }
            } catch (e) {
                this.showToast('Error loading time slots', 'danger');
                console.error(e);
            }
        },

        selectSlot(slot) {
            this.selectedSlot = slot;
        },

        async confirmBooking() {
            if (!this.selectedDoctor || !this.selectedDate || !this.selectedSlot) {
                this.showToast('Please select all required fields', 'danger');
                return;
            }

            this.loading = true;
            try {
                const res = await api.bookAppointment({
                    doctor_id: this.selectedDoctor.id,
                    appointment_date: this.selectedDate,
                    appointment_time: this.selectedSlot.time,
                    notes: this.bookingNotes
                });
                
                if (res.success) {
                    this.showToast('Appointment booked successfully!');
                    this.bookingStep = 1;
                    this.selectedDept = null;
                    this.selectedDoctor = null;
                    this.selectedDate = '';
                    this.selectedSlot = null;
                    this.bookingNotes = '';
                    this.deptDoctors = [];
                    this.timeSlots = [];
                    this.loadPatientDashboard();
                } else {
                    this.showToast(res.message || 'Booking failed', 'danger');
                }
            } catch (e) {
                this.showToast('Error booking appointment', 'danger');
                console.error(e);
            }
            this.loading = false;
        },

        async loadPatientAppointments() {
            try {
                const res = await api.getPatientAppointments();
                if (res.success) {
                    this.patientAppointments = res.data.appointments || [];
                }
            } catch (e) {
                this.showToast('Error loading appointments', 'danger');
                console.error(e);
            }
        },

        async cancelAppointment(id) {
            const confirm = window.confirm('Are you sure you want to cancel this appointment?');
            if (!confirm) return;

            try {
                const res = await api.cancelAppointment(id);
                if (res.success) {
                    this.showToast('Appointment cancelled');
                    this.loadPatientAppointments();
                    this.loadPatientDashboard();
                } else {
                    this.showToast(res.message || 'Cancellation failed', 'danger');
                }
            } catch (e) {
                this.showToast('Error cancelling appointment', 'danger');
                console.error(e);
            }
        },

        async loadPatientHistory() {
            try {
                const res = await api.getPatientHistory();
                if (res.success) {
                    this.patientHistory = res.data.treatments || [];
                }
            } catch (e) {
                this.showToast('Error loading history', 'danger');
                console.error(e);
            }
        },
    }
}).mount('#app');
