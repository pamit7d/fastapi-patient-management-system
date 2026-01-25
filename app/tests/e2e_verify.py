import requests
import time
import sys
import os

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
# If running locally via uvicorn directly, it might be 8000. 
# If running via entrypoint.sh locally with default, it's 8000.
# If running on Render, use the deployed URL.

TIMESTAMP = int(time.time())

# Colors for Output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

class E2ETestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.doc_token = None
        self.pat_token = None
        self.doctor_id = None
        self.patient_id = None
        self.appt_id = None
        self.results = {"PASS": 0, "FAIL": 0}

    def log(self, test_id, name, status, message=""):
        color = GREEN if status == "PASS" else RED
        print(f"{color}[{status}] {test_id}: {name}{RESET} {message}")
        self.results[status] += 1

    def run(self):
        print(f"\n=== STARTING E2E VERIFICATION AGAINST {BASE_URL} ===\n")
        
        try:
            # 1. System Health
            self.test_health_check()

            # 2. Admin & Doctor Flow
            self.test_admin_login()
            self.test_admin_stats()
            self.test_create_doctor()
            self.test_search_doctor()
            self.test_doctor_availability()

            # 3. Patient Flow
            self.test_register_patient()
            self.test_patient_login()
            self.test_create_patient_profile()
            self.test_admin_search_patient()

            # 4. Appointment Flow
            self.test_book_appointment()
            self.test_view_appointments()
            self.test_update_appointment_status()
            
            # Summary
            print(f"\n=== TEST SUMMARY: {GREEN}{self.results['PASS']} PASSED{RESET}, {RED}{self.results['FAIL']} FAILED{RESET} ===")
            if self.results['FAIL'] > 0:
                sys.exit(1)
                
        except requests.exceptions.ConnectionError:
            print(f"{RED}CRITICAL: Could not connect to {BASE_URL}. Is the server running?{RESET}")
            sys.exit(1)
        except Exception as e:
            print(f"{RED}CRITICAL: Unexpected error: {e}{RESET}")
            sys.exit(1)

    # --- Tests ---

    def test_health_check(self):
        res = self.session.get(f"{BASE_URL}/")
        if res.status_code == 200:
            self.log("TC-00", "Health Check", "PASS")
        else:
            self.log("TC-00", "Health Check", "FAIL", f"Status: {res.status_code}")

    def test_admin_login(self):
        # Assumes admin/admin123 created by init_db
        res = self.session.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin123"})
        if res.status_code == 200:
            self.admin_token = res.json().get("access_token")
            self.log("TC-01", "Admin Login", "PASS")
        else:
            self.log("TC-01", "Admin Login", "FAIL", res.text)
            sys.exit(1) # Cannot proceed without admin

    def test_admin_stats(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        res = self.session.get(f"{BASE_URL}/admin/stats", headers=headers)
        if res.status_code == 200 and "patients" in res.json():
            self.log("TC-02", "Admin Stats", "PASS")
        else:
            self.log("TC-02", "Admin Stats", "FAIL", res.text)

    def test_create_doctor(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        username = f"dr_test_{TIMESTAMP}"
        payload = {
            "username": username,
            "password": "password",
            "full_name": "Dr. Test Strange",
            "specialization": "Magic"
        }
        # Note: The API might expect params or json depending on implementation. 
        # Audit showed query params for details in previous tests. Checking `test_suite.py`...
        # It used: json={"username", "password"}, params={"full_name", "specialization"} 
        # Let's try that to be safe based on audit.
        
        res = self.session.post(
            f"{BASE_URL}/admin/doctors",
            json={
                "username": username, 
                "password": "password",
                "full_name": "Dr. Test Strange", 
                "email": f"dr_{TIMESTAMP}@example.com",
                "phone": "5559998888",
                "role": "doctor"
            },
            params={"full_name": "Dr. Test Strange", "specialization": "Magic"},
            headers=headers
        )
        
        if res.status_code == 200:
            # Get token for doctor
            login = self.session.post(f"{BASE_URL}/token", data={"username": username, "password": "password"})
            self.doc_token = login.json().get("access_token")
            
            # Get real Doctor ID (Profile ID)
            search_res = self.session.get(f"{BASE_URL}/admin/doctors?search=Strange", headers=headers)
            if search_res.status_code == 200 and len(search_res.json()) > 0:
                self.doctor_id = search_res.json()[0]['id']
                self.log("TC-03", "Create Doctor", "PASS")
            else:
                 self.log("TC-03", "Create Doctor", "FAIL", "Created but not found")
        else:
            self.log("TC-03", "Create Doctor", "FAIL", res.text)

    def test_search_doctor(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        res = self.session.get(f"{BASE_URL}/admin/doctors?search=Strange", headers=headers)
        if res.status_code == 200 and len(res.json()) > 0:
            self.log("TC-04", "Search Doctor", "PASS")
        else:
            self.log("TC-04", "Search Doctor", "FAIL", res.text)

    def test_doctor_availability(self):
        if not self.doc_token: return self.log("TC-09", "Set Availability", "FAIL", "No doctor token")
        headers = {"Authorization": f"Bearer {self.doc_token}"}
        payload = {
            "weekly": {"Mon": ["09:00", "17:00"]},
            "specific_dates": {} 
        }
        res = self.session.post(f"{BASE_URL}/doctor/availability", json=payload, headers=headers)
        if res.status_code == 200:
            self.log("TC-09", "Set Availability", "PASS")
        else:
            self.log("TC-09", "Set Availability", "FAIL", res.text)

    def test_register_patient(self):
        self.pat_username = f"pat_{TIMESTAMP}"
        payload = {
            "username": self.pat_username, 
            "password": "password", 
            "role": "patient",
            "full_name": "Test Patient",
            "email": f"pat_{TIMESTAMP}@example.com",
            "phone": "5551234567",
            "age": 30,
            "gender": "Male",
            "city": "New York"
        }
        res = self.session.post(f"{BASE_URL}/users/", json=payload)
        if res.status_code == 200:
            self.log("TC-06", "Register Patient", "PASS")
        else:
            # Maybe schema is different? Audit showed /users/ only taking user/pass in `test_suite.py`...
            # `test_suite.py`: json={"username": self.pat_username, "password": "password"}
            # Let's default to what worked in `test_suite.py` but user request implied role might be needed.
            # We'll try basic auth based on previous success.
             self.log("TC-06", "Register Patient", "FAIL", res.text)

    def test_patient_login(self):
        res = self.session.post(f"{BASE_URL}/token", data={"username": self.pat_username, "password": "password"})
        if res.status_code == 200:
            self.pat_token = res.json().get("access_token")
            self.log("TC-01b", "Patient Login", "PASS")
        else:
            self.log("TC-01b", "Patient Login", "FAIL", res.text)

    def test_create_patient_profile(self):
        if not self.pat_token: return
        headers = {"Authorization": f"Bearer {self.pat_token}"}
        # Profile is created on registration. Verify it exists using /me
        res = self.session.get(f"{BASE_URL}/patients/me", headers=headers)
        if res.status_code == 200:
            self.patient_id = res.json().get("patient_id")
            self.log("TC-07", "Verify Profile Exists", "PASS")
        else:
            self.log("TC-07", "Verify Profile Exists", "FAIL", res.text)

    def test_admin_search_patient(self):
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        res = self.session.get(f"{BASE_URL}/patients/?search=Test", headers=headers)
        if res.status_code == 200 and len(res.json()) > 0:
            self.log("TC-08", "Admin Search Patient", "PASS")
        else:
            self.log("TC-08", "Admin Search Patient", "FAIL", res.text)

    def test_book_appointment(self):
        if not self.pat_token or not self.doctor_id: return self.log("TC-10", "Book Appointment", "FAIL", "Missing Context")
        headers = {"Authorization": f"Bearer {self.pat_token}"}
        # Future date
        payload = {"doctor_id": self.doctor_id, "date": "2030-01-01", "time": "09:00"}
        res = self.session.post(f"{BASE_URL}/appointments/book", json=payload, headers=headers)
        if res.status_code == 200:
            self.appt_id = res.json().get("id")
            self.log("TC-10", "Book Appointment", "PASS")
        else:
             self.log("TC-10", "Book Appointment", "FAIL", res.text)

    def test_view_appointments(self):
        if not self.pat_token: return
        headers = {"Authorization": f"Bearer {self.pat_token}"}
        res = self.session.get(f"{BASE_URL}/appointments/my", headers=headers)
        if res.status_code == 200:
            data = res.json()
            # Check if our appt is there
            found = any(a['id'] == self.appt_id for a in data)
            if found:
                self.log("TC-11", "View My Appointments", "PASS")
            else:
                 self.log("TC-11", "View My Appointments", "FAIL", "Created appt not found in list")
        else:
            self.log("TC-11", "View My Appointments", "FAIL", res.text)

    def test_update_appointment_status(self):
        if not self.doc_token or not self.appt_id: return
        headers = {"Authorization": f"Bearer {self.doc_token}"}
        res = self.session.put(f"{BASE_URL}/appointments/{self.appt_id}/status", json={"status": "Completed"}, headers=headers)
        if res.status_code == 200 and res.json().get("status") == "Completed":
            self.log("TC-13", "Update Status", "PASS")
        else:
            self.log("TC-13", "Update Status", "FAIL", res.text)

if __name__ == "__main__":
    runner = E2ETestRunner()
    runner.run()
