const API_URL = "";

// State
let token = localStorage.getItem('access_token');
let currentPatientId = null;

// DOM Elements
const loginSection = document.getElementById('loginSection');
const registerSection = document.getElementById('registerSection');
const dashboardSection = document.getElementById('dashboardSection');
const logoutBtn = document.getElementById('logoutBtn');
const userInfo = document.getElementById('userInfo');
const patientList = document.getElementById('patientList');

// Init
function init() {
    if (token) {
        showDashboard();
    } else {
        showLogin();
    }
}

// Navigation
function showLogin() {
    loginSection.classList.remove('hidden');
    registerSection.classList.add('hidden');
    dashboardSection.classList.add('hidden');
    userInfo.classList.add('hidden');
}

function showDashboard() {
    loginSection.classList.add('hidden');
    registerSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
    userInfo.classList.remove('hidden');
    fetchPatients();
}

window.closeModal = (id) => {
    document.getElementById(id).classList.add('hidden');
};

document.getElementById('showRegister').onclick = (e) => { e.preventDefault(); loginSection.classList.add('hidden'); registerSection.classList.remove('hidden'); };
document.getElementById('showLogin').onclick = (e) => { e.preventDefault(); loginSection.classList.remove('hidden'); registerSection.classList.add('hidden'); };

document.getElementById('fillDemo').onclick = (e) => {
    e.preventDefault();
    document.getElementById('username').value = 'admin';
    document.getElementById('password').value = 'admin';
};

// Auth
document.getElementById('loginForm').onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
        const res = await fetch(`${API_URL}/token`, { method: 'POST', body: fd });
        if (!res.ok) throw new Error('Invalid credentials');
        const data = await res.json();
        token = data.access_token;
        localStorage.setItem('access_token', token);
        showDashboard();
    } catch (err) {
        document.getElementById('loginError').textContent = err.message;
    }
};

document.getElementById('registerForm').onsubmit = async (e) => {
    e.preventDefault();
    const u = document.getElementById('regUsername').value;
    const p = document.getElementById('regPassword').value;
    try {
        const res = await fetch(`${API_URL}/users/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: u, password: p })
        });
        if (!res.ok) throw new Error('Registration failed');
        alert('Registered! Please login.');
        showLogin();
    } catch (err) {
        document.getElementById('regError').textContent = err.message;
    }
};

logoutBtn.onclick = () => {
    token = null;
    localStorage.removeItem('access_token');
    showLogin();
};

// Patients
async function fetchPatients() {
    try {
        const res = await fetch(`${API_URL}/patients/`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.status === 401) return logoutBtn.click();
        const patients = await res.json();
        renderPatients(patients);
    } catch (err) { console.error(err); }
}

function renderPatients(patients) {
    patientList.innerHTML = '';
    patients.forEach(p => {
        const card = document.createElement('div');
        card.className = 'patient-card';
        card.innerHTML = `
            <div style="display:flex; justify-content:space-between;">
                <h3>${p.name}</h3>
                <span class="status-badge status-${p.status || 'Admitted'}">${p.status || 'Admitted'}</span>
            </div>
            <p><small>ID: ${p.patient_id}</small></p>
            <div class="patient-info">
                <p>Age: ${p.age} | ${p.gender}</p>
                <p>Loc: ${p.city}</p>
            </div>
            <div style="margin-top:10px; display:flex; gap:5px;">
                <button onclick="openDetails('${p.patient_id}')">Details</button>
                <button class="delete-btn" onclick="deletePatient('${p.patient_id}')" style="width:auto;">✕</button>
            </div>
        `;
        patientList.appendChild(card);
    });
}

// Add Patient
document.getElementById('addPatientBtn').onclick = () => document.getElementById('patientModal').classList.remove('hidden');
document.getElementById('patientForm').onsubmit = async (e) => {
    e.preventDefault();
    const statusEl = document.getElementById('modalStatus');
    statusEl.textContent = 'Saving...';

    const data = {
        patient_id: document.getElementById('pId').value,
        name: document.getElementById('pName').value,
        age: parseInt(document.getElementById('pAge').value),
        gender: document.getElementById('pGender').value,
        height: parseInt(document.getElementById('pHeight').value),
        weight: parseInt(document.getElementById('pWeight').value),
        phone: document.getElementById('pPhone').value,
        email: document.getElementById('pEmail').value,
        street: document.getElementById('pStreet').value,
        city: document.getElementById('pCity').value,
        state: document.getElementById('pState').value,
        zip_code: document.getElementById('pZip').value,
        country: document.getElementById('pCountry').value,
        // Status defaults to Admitted in backend
        // Appointments kept empty for standard flow (add via details later)
    };

    try {
        const res = await fetch(`${API_URL}/patients/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(data)
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(JSON.stringify(err.detail));
        }
        statusEl.textContent = 'Admitted!';
        statusEl.style.color = 'green';
        setTimeout(() => {
            closeModal('patientModal');
            statusEl.textContent = '';
            e.target.reset();
            fetchPatients();
        }, 800);
    } catch (err) {
        statusEl.textContent = err.message;
        statusEl.style.color = 'red';
    }
};

window.deletePatient = async (id) => {
    if (!confirm('Discharge and remove record?')) return;
    await fetch(`${API_URL}/patients/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` } });
    fetchPatients();
};

// Details & Appointments
window.openDetails = async (id) => {
    currentPatientId = id;
    const modal = document.getElementById('detailsModal');
    // Fetch fresh data
    const res = await fetch(`${API_URL}/patients/${id}`, { headers: { 'Authorization': `Bearer ${token}` } });
    const p = await res.json();

    document.getElementById('dName').textContent = p.name;
    document.getElementById('dId').textContent = `Patient ID: ${p.patient_id} | BMI: ${p.bmi}`;
    document.getElementById('dStatus').value = p.status || 'Admitted';

    // Fetch appointments
    loadAppointments(id);

    document.getElementById('apptForm').classList.add('hidden');
    modal.classList.remove('hidden');
};

async function loadAppointments(id) {
    const list = document.getElementById('dAppointments');
    list.innerHTML = 'Loading...';

    // First check nested appointments from patient object, or fetch independent if we changed router interaction
    // Since we created independent appointment router, let's fetch from there or use the relationship if loaded
    // Current Patient read fetches appointments relationship eagerly? Let's assume yes or fetch via new endpoint

    const res = await fetch(`${API_URL}/appointments/${id}`, { headers: { 'Authorization': `Bearer ${token}` } });
    const appts = await res.json();

    list.innerHTML = '';
    if (appts.length === 0) {
        list.innerHTML = '<p style="color:#777;">No appointments scheduled.</p>';
        return;
    }

    appts.forEach(a => {
        const item = document.createElement('div');
        item.className = 'appointment-item';
        item.innerHTML = `
            <span><strong>${a.date}</strong> @ ${a.time}</span>
            <span>${a.doctor} (${a.department})</span>
        `;
        list.appendChild(item);
    });
}

window.updateStatus = async () => {
    const newStatus = document.getElementById('dStatus').value;
    const msg = document.getElementById('statusMsg');

    try {
        const res = await fetch(`${API_URL}/patients/${currentPatientId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            msg.textContent = 'Updated';
            msg.style.color = 'green';
            setTimeout(() => msg.textContent = '', 2000);
            fetchPatients(); // Update background list
        } else {
            throw new Error('Failed');
        }
    } catch (e) {
        msg.textContent = 'Error';
    }
};

window.showApptForm = () => document.getElementById('apptForm').classList.remove('hidden');

document.getElementById('apptForm').onsubmit = async (e) => {
    e.preventDefault();
    const data = {
        patient_id: currentPatientId,
        date: document.getElementById('apptDate').value,
        time: document.getElementById('apptTime').value,
        // Since input type=time gives HH:MM (24h), we might just send that and rely on loose validation or format it.
        // Let's trust it for now or simple format.
        time: formatTime(document.getElementById('apptTime').value),
        doctor: document.getElementById('apptDoctor').value,
        department: document.getElementById('apptDept').value,
        appointment_id: "A-" + Date.now() // Generated client side or server? Server schema implies client provides it?
        // Schema AppointmentBase has appointment_id. Planner said new CRUD auto-increments? 
        // Ah, Planner said CRUD: new_id = f"A{1000 + count + 1}". 
        // But Schema might require it? AppointmentCreateIndependent inherits AppointmentBase which HAS appointment_id.
        // Let's generate it here to be safe and satisfy schema validation.
    };

    try {
        const res = await fetch(`${API_URL}/appointments/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            loadAppointments(currentPatientId);
            e.target.reset();
            document.getElementById('apptForm').classList.add('hidden');
        } else {
            const err = await res.json();
            alert('Error: ' + JSON.stringify(err));
        }
    } catch (e) { console.error(e); }
};

function formatTime(val) {
    if (!val) return "09:00 AM"; // default
    const [h, m] = val.split(':');
    const hours = parseInt(h);
    const suffix = hours >= 12 ? 'PM' : 'AM';
    const adjHours = ((hours + 11) % 12 + 1);
    return `${adjHours.toString().padStart(2, '0')}:${m} ${suffix}`;
}

init();
