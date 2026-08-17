# 🎯 Interview Prep AI

[![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Zero Dependency](https://img.shields.io/badge/Dependencies-Zero--External-brightgreen)](#zero-dependency-architecture)
[![Gemini](https://img.shields.io/badge/AI--Engine-Google%20Gemini-orange?logo=google-gemini&logoColor=white)](#intelligent-multi-model-fallback)
[![Localization](https://img.shields.io/badge/Languages-EN%20%7C%20BG-purple)](#localization--dual-language-support)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An elegant, **zero-dependency**, AI-powered interview preparation companion designed to help professionals confidently ace their next job interview. By combining a multi-threaded Python backend with the state-of-the-art **Google Gemini API**, Interview Prep AI generates highly personalized questions, analyzes real-time responses, and delivers deep diagnostic feedback tailored to your exact target role.

---

## 🌟 Why Interview Prep AI?

Preparing for interviews is often a generic experience-practicing with stale question banks that do not align with the actual job description. **Interview Prep AI** changes that by acting as a highly specialized executive interviewer. 

Whether you are preparing for a Senior Python Engineer role, a Product Owner position, or a creative design role, this application scans the actual job description (or webpage), tailors a customized 10-question evaluation, and acts as your personal coach.

---

## ✨ Key Features

### 🚀 Zero-Dependency Architecture
The backend is powered entirely by the Python **standard library**. Using `http.server`, `socketserver`, and `urllib`, the application starts instantly without needing a single third-party framework or package.

### 🌐 Localization & Dual-Language Support
Switch seamlessly between **English (EN)** and **Bulgarian (BG)**. All system flows, user interfaces, questions, hints, and final AI evaluations adapt dynamically to your selected language.

### 🧠 Intelligent Multi-Model Fallback
To ensure high availability and robust API interactions, the server utilizes a **Dynamic Remembered Model** framework. It attempts calls on a primary model and, in case of rate limits or service disruptions, automatically falls back across a pool of Gemini models, promoting the first successful model as the new default.

### 📋 Custom Interview Types
* **Multiple Choice Quiz (MCQ):** Dynamic 4-option quizzes with instant answer validation, feedback banners, and automated grading.
* **Written Assessment:** Open problem-solving and scenario-based assignments.
* **Technical Interview:** Deep technical and domain-specific knowledge evaluations.
* **HR / Behavioral Interview:** Situational, behavioral, and culture-fit reviews.

### 🛠️ Interactive Preparation Aids
* **Tailored Scraper:** Provide a Job Posting URL or paste a raw description. The backend automatically fetches, strips, and sanitizes the description to contextualize and focus the questions.
* **Adaptive Hints:** Stuck on a question? Toggle a conceptual hint designed to steer you in the right direction without giving away the answer.
* **Reference Model Answers:** Learn as you go. Access comprehensive, AI-formulated model answers to understand what interviewers are looking for.
* **Comprehensive AI Report:** Complete your interview to generate an overall score (0-100), a detailed executive summary, and a question-by-question breakdown.

---

## 📸 User Interface Showcase

Designed with a modern, fully responsive dark-first aesthetic, the UI uses **Tailwind CSS**, **Plus Jakarta Sans**, and **JetBrains Mono** to deliver a gorgeous desktop and mobile experience.

* **API Configuration Dashboard:** Set your Gemini API key securely in browser `LocalStorage` so it never leaks.
* **Unified SPA Navigation:** Clean transitions between API Setup, New Session, Active Interview, and Saved Reports.
* **Interactive Quick Navigator:** jump freely between questions using the responsive Q1–Q10 dashboard.
* **Persistent History:** Clear and persistent storage of all completed interview reports.

---

## 🛠️ Technical Deep-Dive

```
               [ User Browser (SPA HTML/CSS/JS) ]
                 │                            ▲
                 ▼ (REST API / Fetch)         │ (HTML / JSON)
        ┌──────────────────────────────────────────────┐
        │       Python Multi-Threaded HTTP Server      │
        │                  (app.py)                    │
        └──────────────────────┬───────────────────────┘
                               │
               (JSON HTTP POST)│ (Fallback Chain)
                               ▼
                   [ Google Gemini API Engine ]
```

### Server Architecture
The server is built with `socketserver.ThreadingTCPServer` and handles concurrent requests gracefully. It serves static assets (the HTML/JS bundle) and hosts several REST endpoints:
* `GET /` - Serves the Single Page Application.
* `POST /api/generate-questions` - Prepares custom tailored questions.
* `POST /api/evaluate-interview` - Scores, validates, and evaluates responses.
* `GET /api/saved-sessions` / `POST /api/save-session` / `POST /api/clear-sessions` - In-memory historical logging.
* `GET /api/active-model` - Retrieves the active API model state.

### Dynamic Model Fallback Chain
If a Gemini model becomes overloaded, the server evaluates available alternatives. It sequentially cycles through:
1. `gemini-3.5-flash` (Default)
2. `gemini-3.5-flash-lite`
3. `gemini-3.7-flash`
4. `gemini-3.6-flash`
5. `gemini-3.1-flash-lite`
6. `gemini-flash-latest`
7. `gemini-pro-latest`
8. `gemini-2.5-flash`
9. `gemini-2.5-pro`

Upon finding an operational model, that model is promoted to the **Active Default Model** to optimize subsequent latency and success rates.

---

## ⚡ Quick Start

### Prerequisites
* **Python 3.12+**
* A Google Gemini API Key ([Get one here](https://aistudio.google.com/))

### Method A: Start with Pure Python (Recommended)
No package managers, build steps, or installations are required:

```bash
# Run the server
python app.py
```

### Method B: Start with Node.js / NPM
If your environment utilizes standard package runners:

```bash
# Install development scripts & tools
npm install

# Run the server
npm run dev
```

Once running, navigate to **`http://localhost:3000`** in your browser.

---

## ⚙️ Configuration & Usage

1. Open **`http://localhost:3000`**.
2. Go to the **API Setup** tab.
3. Paste your Google Gemini API Key and click **Save Key**. (This is stored client-side in LocalStorage, keeping your keys private and secure).
4. Head over to **New Interview**, enter your target position, optionally paste a job posting link, choose your interview type, and click **Generate Questions & Start**.
5. Work through your questions. You can toggle hints or reference answers whenever you need them.
6. When finished, hit **Finish & Final Evaluation** to review your diagnostic scorecard.

---

## 🧪 Automated Testing Suite

The repository includes a comprehensive `unittest` test suite validating crucial aspects of the server, including:
* Server home-page rendering with proper DOM elements.
* Historical session persistence, saving, and retrieval.
* Active model endpoints and API response schemas.
* Dynamic model memory, prioritization, and fallback ordering logic.
* HTTP 500 error reporting and validation for invalid API key configurations.

### Running the Tests

To execute the test suite locally:

```bash
# Using Python Standard Library Unittest
python -m unittest discover tests

# Or using the NPM script alias
npm run lint
```

---

## 📄 License

This project is licensed under the MIT License. Feel free to use, modify, and distribute it to boost your preparation!

---
