# FNOL Claims Intelligence

AI-powered First Notice of Loss (FNOL) Claims Processing System built using Flask, Groq LLaMA 3.3, HTML, CSS, and JavaScript.

---

# Overview

FNOL Claims Intelligence is an intelligent insurance claims dashboard that automates:

- FNOL document analysis
- Field extraction
- Risk assessment
- Fraud detection
- Smart claim routing
- Interactive analytics visualization

---

# Features

## AI Claim Processing
- Upload PDF or TXT claims
- Paste FNOL text directly
- AI-powered extraction using Groq API

## Intelligent Routing
- Fast-track low-risk claims
- Manual review recommendations
- Specialist escalation
- Fraud investigation detection

## Interactive Dashboard
- Dashboard navigation
- History section
- Analytics section
- Settings section
- Smooth scrolling
- Responsive UI

## Theme Support
- Dark Mode
- Blue-White Light Mode

---

# Tech Stack

## Frontend
- HTML5
- CSS3
- JavaScript

## Backend
- Flask
- Python

## AI Integration
- Groq API
- LLaMA 3.3

---

# Project Structure

```bash
fnol-agent/
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
│
├── templates/
│   └── index.html
│
├── uploads/
│
├── sample_docs/
│
└── README.md
```

---

# How to Run the Project

## 1. Clone Repository

```bash
git clone https://github.com/kruthi349/fnol-claims-intelligence.git
cd fnol-claims-intelligence
```

---

## 2. Create Virtual Environment

### Windows

```bash
python -m venv venv
```

### Mac/Linux

```bash
python3 -m venv venv
```

---

## 3. Activate Virtual Environment

### Windows PowerShell

```bash
venv\Scripts\activate
```

### Mac/Linux

```bash
source venv/bin/activate
```

---

## 4. Install Required Packages

```bash
pip install -r requirements.txt
```

---

## 5. Create `.env` File

Create a `.env` file in the project root folder and add:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## 6. Run Flask Application

```bash
python app.py
```

---

## 7. Open Browser

```text
http://localhost:5000
```

---

## 8. Stop Server

Press:

```text
CTRL + C
```

in the terminal.

---

# Dashboard Sections

## Dashboard
Main AI FNOL processing interface.

## History
Displays previous claim records and processing details.

## Analytics
Shows claim metrics, fraud statistics, and risk indicators.

## Settings
Theme switching and dashboard configuration controls.

---

# Future Improvements

- User authentication
- Database integration
- OCR support
- Real-time analytics
- Claim export system
- Admin dashboard
- Email notifications
- Multi-user support

---

# Security Notes

- Never upload `.env`
- Never expose API keys publicly
- Use `.gitignore`
- Store secrets securely

---

# Author

Developed as an AI-powered insurance claims intelligence project using Flask and Groq LLM integration.

---

# License

This project is for educational and demonstration purposes.
