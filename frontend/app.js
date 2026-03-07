// app.js - main Vue application entry point
// Depends on: js/api.js, js/auth.js, js/admin.js, js/doctor.js, js/patient.js

const { createApp } = Vue;

createApp({
    data() {
        return {
            ...authData,
            ...adminData,
            ...doctorData,
            ...patientData,
        };
    },

    mounted() {
        const token = localStorage.getItem('medsync_token');
        const role = localStorage.getItem('medsync_role');
        const username = localStorage.getItem('medsync_username');
        if (token && role) {
            this.currentUser = { username, role };
            this.currentPage = role;
            this.loadInitialData(role);
        }
    },

    methods: {
        ...authMethods,
        ...adminMethods,
        ...doctorMethods,
        ...patientMethods,
    }
}).mount('#app');
