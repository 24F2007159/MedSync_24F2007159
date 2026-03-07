// admin.js - admin portal data and methods

const adminData = {
    adminTab: 'dashboard',
    adminStats: {},
    doctors: [],
    patients: [],
    allAppointments: [],
    departments: [],
    showAddDoctorModal: false,
    newDoctor: {
        username: '', email: '', name: '', specialization: '',
        qualification: '', experience: 0, consultation_fee: 0, phone: '', password: ''
    },
    doctorSearch: '',
    patientSearch: '',
};

const adminMethods = {
    async loadAdminDashboard() {
        const res = await api.getAdminDashboard();
        if (res.success) this.adminStats = res.data;
        const chartRes = await api.getAdminChartData();
        if (chartRes.success) {
            this.$nextTick(() => this.renderAdminCharts(chartRes.data));
        }
    },

    renderAdminCharts(data) {
        if (this._apptChart) this._apptChart.destroy();
        if (this._deptChart) this._deptChart.destroy();

        const apptCtx = document.getElementById('apptStatusChart');
        if (apptCtx) {
            this._apptChart = new Chart(apptCtx, {
                type: 'doughnut',
                data: {
                    labels: data.appointments_by_status.labels,
                    datasets: [{
                        data: data.appointments_by_status.values,
                        backgroundColor: ['#0d6efd', '#198754', '#dc3545'],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        }

        const deptCtx = document.getElementById('deptChart');
        if (deptCtx) {
            this._deptChart = new Chart(deptCtx, {
                type: 'bar',
                data: {
                    labels: data.doctors_per_dept.labels,
                    datasets: [{
                        label: 'Doctors',
                        data: data.doctors_per_dept.values,
                        backgroundColor: '#0d6efd',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
                }
            });
        }
    },

    async loadDoctors(search = '') {
        if (search === '') this.doctorSearch = '';
        const res = await api.getDoctors(search);
        if (res.success) this.doctors = res.data.doctors;
    },

    searchDoctors() {
        this.loadDoctors(this.doctorSearch);
    },

    async addDoctor() {
        const d = this.newDoctor;
        if (!d.username.trim() || !d.email.trim() || !d.name.trim() || !d.specialization.trim()) {
            this.showToast('Username, email, name and specialization are required', 'danger');
            return;
        }
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(d.email)) {
            this.showToast('Please enter a valid email address', 'danger');
            return;
        }
        const res = await api.addDoctor(d);
        if (res.success) {
            this.showToast('Doctor added successfully!');
            this.showAddDoctorModal = false;
            this.loadDoctors();
            this.newDoctor = {
                username: '', email: '', name: '', specialization: '',
                qualification: '', experience: 0, consultation_fee: 0, phone: '', password: ''
            };
        } else {
            this.showToast(res.message, 'danger');
        }
    },

    async toggleDoctorStatus(doc) {
        const res = await api.toggleDoctorStatus(doc.id);
        if (res.success) {
            this.showToast(res.message);
            this.loadDoctors();
        }
    },

    async loadPatients() {
        this.patientSearch = '';
        const res = await api.getPatients();
        if (res.success) this.patients = res.data.patients;
    },

    searchPatients() {
        this.loadPatientsFiltered(this.patientSearch);
    },

    async loadPatientsFiltered(search = '') {
        const res = await api.getPatients(search);
        if (res.success) this.patients = res.data.patients;
    },

    async togglePatientStatus(pat) {
        const res = await api.togglePatientStatus(pat.id);
        if (res.success) {
            this.showToast(res.message);
            this.loadPatients();
        }
    },

    async loadAllAppointments() {
        const res = await api.getAllAppointments();
        if (res.success) this.allAppointments = res.data.appointments;
    },

    async loadDepartments() {
        const isAdmin = this.currentUser.role === 'admin';
        const res = isAdmin ? await api.getDepartmentsAdmin() : await api.getDepartments();
        if (res.success) this.departments = res.data.departments;
    },
};
