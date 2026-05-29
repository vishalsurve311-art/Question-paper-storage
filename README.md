# Question Paper Storage Web Application

A premium, glassmorphism-themed web application for teachers to upload and students to search/download question papers.

## Features
- **Teacher Portal**: Secure login (pass: `1234`), file upload with metadata, and management of uploaded papers.
- **Student Portal**: Advanced search filtering by year, semester, branch, subject, etc.
- **Modern UI**: Responsive design with glassmorphism effects and smooth animations.

## Tech Stack
- **Backend**: Python (Flask)
- **Database**: MySQL
- **Frontend**: Vanilla HTML, CSS (Inter font), JavaScript

---

## Setup Instructions

### 1. Database Setup
Create a MySQL database named `question_bank` and run the following SQL command:

```sql
CREATE DATABASE question_bank;
USE question_bank;

CREATE TABLE papers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year VARCHAR(10),
    semester VARCHAR(10),
    branch VARCHAR(50),
    subject VARCHAR(100),
    exam_type VARCHAR(20),
    month VARCHAR(20),
    file_path VARCHAR(255),
    original_filename VARCHAR(255)
);
```

### 2. Installation
1. Clone or download this project.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and update your database credentials.

### 3. Run Locally
```bash
python app.py
```
Visit `http://localhost:5000` for the student portal and `http://localhost:5000/teacher` for the teacher portal.

---

## Deployment (Render / Railway)
1. Push this code to a GitHub repository.
2. Connect the repository to Render/Railway.
3. Add the environment variables from `.env` in the platform's dashboard.
4. Set the build command to `pip install -r requirements.txt` and start command to `gunicorn app:app`.
