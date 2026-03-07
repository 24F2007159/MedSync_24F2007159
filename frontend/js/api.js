// api.js - handles all API calls to backend
const API_BASE = '/api';

function getToken() {
    return localStorage.getItem('medsync_token');
}

function getHeaders() {
    const token = getToken();
    return {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
}

async function apiCall(method, endpoint, data = null) {
    const options = {
        method,
        headers: getHeaders()
    };
    if (data) {
        options.body = JSON.stringify(data);
    }
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    return response.json();
}

const api = {
    // auth
    login: (data) => apiCall('POST', '/auth/login', data),
    register: (data) => apiCall('POST', '/auth/register', data),
    
    // admin
    getAdminDashboard: () => apiCall('GET', '/admin/dashboard'),
    getDoctors: (search='') => apiCall('GET', `/admin/doctors?search=${search}`),
    addDoctor: (data) => apiCall('POST', '/admin/doctors', data),
    toggleDoctorStatus: (id) => apiCall('PUT', `/admin/doctors/${id}/blacklist`),
    getPatients: () => apiCall('GET', '/admin/patients'),
    togglePatientStatus: (id) => apiCall('PUT', `/admin/patients/${id}/blacklist`),
    getAllAppointments: () => apiCall('GET', '/admin/appointments'),
    getDepartmentsAdmin: () => apiCall('GET', '/admin/departments'),
    
    // doctor
    getDoctorDashboard: () => apiCall('GET', '/doctor/dashboard'),
    getDoctorAppointments: () => apiCall('GET', '/doctor/appointments'),
    updateAppointmentStatus: (id, status) => apiCall('PUT', `/doctor/appointments/${id}/status`, {status}),
    addTreatment: (id, data) => apiCall('POST', `/doctor/appointments/${id}/treatment`, data),
    getDoctorPatients: () => apiCall('GET', '/doctor/patients'),
    getAvailability: () => apiCall('GET', '/doctor/availability'),
    setAvailability: (data) => apiCall('POST', '/doctor/availability', data),
    
    // patient
    getPatientDashboard: () => apiCall('GET', '/patient/dashboard'),
    getDepartments: () => apiCall('GET', '/patient/departments'),
    getDoctorsByDepartment: (deptId) => apiCall('GET', `/patient/departments/${deptId}/doctors`),
    getAvailableSlots: (doctorId, date) => apiCall('GET', `/patient/available-slots?doctor_id=${doctorId}&date=${date}`),
    bookAppointment: (data) => apiCall('POST', '/patient/appointments', data),
    getPatientAppointments: () => apiCall('GET', '/patient/appointments'),
    cancelAppointment: (id) => apiCall('PUT', `/patient/appointments/${id}/cancel`),
    rescheduleAppointment: (id, data) => apiCall('PUT', `/patient/appointments/${id}/reschedule`, data),
    getPatientHistory: () => apiCall('GET', '/patient/history'),
    updatePatientProfile: (data) => apiCall('PUT', '/patient/profile', data),
    exportHistory: () => apiCall('POST', '/patient/export'),
};