# 🏗️ Nexus-ERP | Business & Operations Management System

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-Framework-092E20?style=for-the-badge&logo=django)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

**Nexus-ERP** is a comprehensive web-based Enterprise Resource Planning (ERP) and Business Management dashboard built with Django. It is designed to streamline project tracking, worker attendance, wage calculations, and financial reporting for construction and fabrication businesses.

---

## ✨ Key Features

* 🔐 **Role-Based Access Control:** Separate secure login portals for Administrators, Supervisors, and Workers.
* 📊 **Project Management:** Add, edit, and monitor ongoing projects with detailed status breakdowns.
* 👷 **Attendance & Payroll System:** Track daily worker attendance, manage supervisor roles, and calculate customized worker wages automatically.
* 📄 **Automated PDF Reporting:** Generate downloadable PDF expense reports, income breakdowns, and worker payslips.

---

## 🛠️ Tech Stack

* **Backend:** Python, Django
* **Frontend:** HTML5, CSS3, JavaScript (Django Templates)
* **Database:** SQLite3
* **Version Control:** Git & GitHub

---

## 🚀 Getting Started (Local Setup)

Follow these steps to run the project locally on your machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/VindithaKodithuwakku/Nexus-ERP.git](https://github.com/VindithaKodithuwakku/Nexus-ERP.git)
   cd Nexus-ERP
   ```

2. **Set up the Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install django
   ```

4. **Apply Database Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Run the Server:**
   ```bash
   python manage.py runserver
   ```
   Open your browser and go to `http://127.0.0.1:8000/`.

---

## 👨‍💻 Author

**Vinditha Kodithuwakku**  
* Computer Engineering Undergraduate, University of Peradeniya
* GitHub: [@VindithaKodithuwakku](https://github.com/VindithaKodithuwakku)
