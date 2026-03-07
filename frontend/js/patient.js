// patient.js - patient portal data and methods

const patientData = {
    patientTab: 'book',
    patientStats: { upcoming_appointments: 0, total_appointments: 0, doctors_visited: 0 },
    patientAppointments: [],
    patientHistory: [],
    patientProfile: {},
    bookingStep: 1,
    selectedDept: null,
    selectedDoctor: null,
    selectedDate: '',
    selectedSlot: null,
    timeSlots: [],
    bookingNotes: '',
    minDate: new Date().toISOString().split('T')[0],
    showRescheduleModal: false,
    rescheduleTarget: null,
    rescheduleDate: '',
    rescheduleSlot: null,
    rescheduleSlots: [],
};

const patientMethods = {
    async loadPatientDashboard() {
        const res = await api.getPatientDashboard();
        if (res.success) {
            this.patientStats = res.data;
            this.patientProfile = res.data.patient;
        }
    },

    selectDepartment(dept) {
        this.selectedDept = dept;
        this.bookingStep = 2;
    },

    selectDoctor(doc) {
        this.selectedDoctor = doc;
        this.bookingStep = 3;
    },

    async loadTimeSlots() {
        if (!this.selectedDate) return;
        const res = await api.getAvailableSlots(this.selectedDoctor.id, this.selectedDate);
        if (res.success) {
            this.timeSlots = res.data.slots;
            this.selectedSlot = null;
        }
    },

    selectSlot(slot) {
        this.selectedSlot = slot;
    },

    async confirmBooking() {
        if (!this.selectedDate || !this.selectedSlot) {
            this.showToast('Please select a date and time slot', 'danger');
            return;
        }
        this.loading = true;
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
            this.loadPatientDashboard();
        } else {
            this.showToast(res.message, 'danger');
        }
        this.loading = false;
    },

    async loadPatientAppointments() {
        const res = await api.getPatientAppointments();
        if (res.success) this.patientAppointments = res.data.appointments;
    },

    async cancelAppointment(id) {
        const res = await api.cancelAppointment(id);
        if (res.success) {
            this.showToast('Appointment cancelled');
            this.loadPatientAppointments();
            this.loadPatientDashboard();
        }
    },

    openRescheduleModal(apt) {
        this.rescheduleTarget = apt;
        this.rescheduleDate = '';
        this.rescheduleSlot = null;
        this.rescheduleSlots = [];
        this.showRescheduleModal = true;
    },

    async loadRescheduleSlots() {
        if (!this.rescheduleDate) return;
        const res = await api.getAvailableSlots(this.rescheduleTarget.doctor.id, this.rescheduleDate);
        if (res.success) {
            this.rescheduleSlots = res.data.slots.filter(s => s.status === 'available');
            this.rescheduleSlot = null;
        }
    },

    async confirmReschedule() {
        if (!this.rescheduleDate || !this.rescheduleSlot) {
            this.showToast('Please select a new date and time slot', 'danger');
            return;
        }
        const res = await api.rescheduleAppointment(this.rescheduleTarget.id, {
            appointment_date: this.rescheduleDate,
            appointment_time: this.rescheduleSlot.time
        });
        if (res.success) {
            this.showToast('Appointment rescheduled successfully!');
            this.showRescheduleModal = false;
            this.loadPatientAppointments();
            this.loadPatientDashboard();
        } else {
            this.showToast(res.message, 'danger');
        }
    },

    async loadPatientHistory() {
        const res = await api.getPatientHistory();
        if (res.success) this.patientHistory = res.data.treatments;
    },

    async updateProfile() {
        const res = await api.updatePatientProfile(this.patientProfile);
        if (res.success) {
            this.showToast('Profile updated successfully!');
        }
    },

    async exportHistory() {
        const res = await api.exportHistory();
        if (res.success) {
            this.showToast('Export started! You will be notified when ready.');
        } else {
            this.showToast('Export failed - Celery may not be running', 'danger');
        }
    },
};
