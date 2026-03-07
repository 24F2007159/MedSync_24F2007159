// doctor.js - doctor portal data and methods

const doctorData = {
    doctorTab: 'dashboard',
    doctorStats: {},
    doctorAppointments: [],
    doctorPatients: [],
    availabilitySlots: [],
    showTreatmentModal: false,
    selectedAppointment: null,
    treatmentForm: { diagnosis: '', prescription: '', notes: '', next_visit: '' },
    showPatientHistoryModal: false,
    selectedPatient: null,
    patientHistoryRecords: [],
};

const doctorMethods = {
    async loadDoctorDashboard() {
        const res = await api.getDoctorDashboard();
        if (res.success) this.doctorStats = res.data;
    },

    async loadDoctorAppointments() {
        const res = await api.getDoctorAppointments();
        if (res.success) this.doctorAppointments = res.data.appointments;
    },

    async updateAppointmentStatus(id, status) {
        const res = await api.updateAppointmentStatus(id, status);
        if (res.success) {
            this.showToast(`Appointment marked as ${status}`);
            this.loadDoctorAppointments();
        }
    },

    openTreatmentModal(apt) {
        this.selectedAppointment = apt;
        this.treatmentForm = { diagnosis: '', prescription: '', notes: '', next_visit: '' };
        this.showTreatmentModal = true;
    },

    async saveTreatment() {
        if (!this.treatmentForm.diagnosis) {
            this.showToast('Diagnosis is required', 'danger');
            return;
        }
        const res = await api.addTreatment(this.selectedAppointment.id, this.treatmentForm);
        if (res.success) {
            this.showToast('Treatment saved successfully!');
            this.showTreatmentModal = false;
            this.loadDoctorAppointments();
        } else {
            this.showToast(res.message, 'danger');
        }
    },

    async loadDoctorPatients() {
        const res = await api.getDoctorPatients();
        if (res.success) this.doctorPatients = res.data.patients;
    },

    async openPatientHistory(patient) {
        this.selectedPatient = patient;
        this.patientHistoryRecords = [];
        this.showPatientHistoryModal = true;
        const res = await api.getPatientHistory(patient.id);
        if (res.success) {
            const records = [];
            for (const apt of res.data.appointments) {
                if (apt.treatment) {
                    records.push({
                        id: apt.id,
                        appointment_date: apt.appointment_date,
                        appointment_time: apt.appointment_time,
                        diagnosis: apt.treatment.diagnosis,
                        prescription: apt.treatment.prescription,
                        notes: apt.treatment.notes,
                        next_visit: apt.treatment.next_visit
                    });
                }
            }
            this.patientHistoryRecords = records;
        }
    },

    async loadAvailability() {
        const res = await api.getAvailability();
        const slots = [];
        for (let i = 0; i < 7; i++) {
            const d = new Date();
            d.setDate(d.getDate() + i);
            const dateStr = d.toISOString().split('T')[0];
            const morningSlot = res.success ? res.data.availability.find(
                a => a.availability_date === dateStr && a.slot_type === 'morning'
            ) : null;
            const eveningSlot = res.success ? res.data.availability.find(
                a => a.availability_date === dateStr && a.slot_type === 'evening'
            ) : null;
            slots.push({
                date: dateStr,
                morning: morningSlot ? morningSlot.is_available : false,
                evening: eveningSlot ? eveningSlot.is_available : false
            });
        }
        this.availabilitySlots = slots;
    },

    async saveAvailability() {
        const res = await api.setAvailability({ availability: this.availabilitySlots });
        if (res.success) {
            this.showToast('Availability saved successfully!');
        }
    },
};
