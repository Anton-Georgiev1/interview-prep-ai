#!/usr/bin/env python3
"""
Python Technical Interview Prep Web Application
Multi-threaded HTTP Server running on standard Python 3 library.
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.error
import os
import sys
import re

PORT = 3000
HOST = "0.0.0.0"

# Memory storage for interview sessions
SAVED_SESSIONS = []

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interview Prep AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        brand: {
                            50: '#f0fdf4',
                            100: '#dcfce7',
                            500: '#22c55e',
                            600: '#16a34a',
                            700: '#15803d',
                        }
                    }
                }
            }
        }
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        code, pre { font-family: 'JetBrains Mono', monospace; }
    </style>
</head>
<body class="bg-slate-50 dark:bg-[#0F172A] text-slate-900 dark:text-slate-50 min-h-screen flex flex-col transition-colors duration-200">

    <!-- Header -->
    <header class="sticky top-0 z-50 bg-white/80 dark:bg-[#1E293B]/80 backdrop-blur border-b border-slate-200 dark:border-slate-800 px-6 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div>
                <h1 class="text-base font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
                    <span id="title-text">Interview Prep AI</span>
                </h1>
            </div>
        </div>

        <div class="flex items-center gap-3 sm:gap-6">
            <nav class="hidden sm:flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs font-medium border border-slate-200 dark:border-slate-700">
                <button onclick="switchView('setup')" id="nav-setup" class="px-3 py-1.5 rounded-md transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">API Setup</button>
                <button onclick="switchView('new')" id="nav-new" class="px-3 py-1.5 rounded-md transition-all bg-white dark:bg-slate-700 text-emerald-600 dark:text-white shadow-sm font-semibold">New Interview</button>
                <button onclick="switchView('active')" id="nav-active" class="px-3 py-1.5 rounded-md transition-all text-slate-400 dark:text-slate-500 cursor-not-allowed" disabled>Active</button>
                <button onclick="switchView('saved')" id="nav-saved" class="px-3 py-1.5 rounded-md transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white">Saved Results</button>
            </nav>

            <div class="flex items-center gap-2">
                <button onclick="toggleTheme()" class="w-9 h-9 flex items-center justify-center rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                    <i id="theme-icon" class="fa-solid fa-sun"></i>
                </button>
                <button onclick="toggleLang()" class="px-3 py-1.5 flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                    <i class="fa-solid fa-globe"></i>
                    <span id="lang-code">EN</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 flex flex-col space-y-6">

        <!-- Setup Page -->
        <div id="view-setup" class="hidden bg-white dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden flex-1 flex flex-col">
            <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
                <h2 class="text-xs font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400" id="setup-title">Gemini API Key Configuration</h2>
            </div>
            <div class="p-6 space-y-6 flex-1">
                <div class="p-4 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 text-xs leading-relaxed text-slate-600 dark:text-slate-300">
                    <p class="font-semibold text-slate-900 dark:text-slate-100 mb-2" id="setup-instructions">How to set up your API Key:</p>
                    <ol class="list-decimal list-inside space-y-1.5 ml-1 text-slate-600 dark:text-slate-400">
                        <li>Get a free Gemini API key from Google AI Studio.</li>
                        <li>Paste your key in the field below to customize or override default server environment keys.</li>
                        <li>Your key is saved securely in your browser's local storage.</li>
                    </ol>
                </div>

                <div class="space-y-2">
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">API Key</label>
                    <input type="password" id="api-key-input" placeholder="AIzaSy..." class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl px-4 py-3 text-sm font-mono text-emerald-600 dark:text-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-500">
                </div>
                
                <div class="flex items-center gap-3">
                    <button onclick="saveApiKey()" class="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition-all">Save API Key</button>
                    <span id="api-status" class="text-xs font-medium text-slate-500"></span>
                </div>
            </div>
        </div>

        <!-- New Interview Page -->
        <div id="view-new" class="bg-white dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden flex-1 flex flex-col">
            <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
                <h2 class="text-xs font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400" id="new-title">New Interview Session</h2>
            </div>

            <div class="p-6 space-y-6 flex-1">
                <div class="space-y-2">
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400" id="label-role">Target Role / Position</label>
                    <div>
                        <input type="text" id="job-title" value="Project Manager" placeholder="e.g. Senior Software Engineer, Project Manager, Data Analyst, Marketing Lead" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500">
                    </div>
                </div>

                <div class="space-y-2">
                    <div class="flex items-center justify-between">
                        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400" id="label-context">Job Posting URL or Description (Optional)</label>
                        <span class="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium" id="tag-context">AI Scans & Tailors 10 Questions</span>
                    </div>
                    <textarea id="job-context" rows="3" placeholder="Paste a job URL (e.g. https://company.com/job/123) or copy/paste the full job description text here..." class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl p-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"></textarea>
                </div>

                <div class="space-y-2">
                    <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400" id="label-type">Interview Type</label>
                    <select id="interview-type" class="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500">
                        <option value="multiple_choice">Multiple Choice Quiz</option>
                        <option value="free_writing">Written Assessment</option>
                        <option value="technical_interview">Technical Interview</option>
                        <option value="hr_interview">HR Interview</option>
                    </select>
                </div>

                <div class="pt-4">
                    <button onclick="startInterview()" id="btn-start" class="px-8 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm rounded-xl shadow-lg shadow-emerald-600/20 transition-all flex items-center gap-2">
                        <i class="fa-solid fa-play"></i>
                        <span id="btn-start-text">Generate Questions & Start</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Active Interview Page -->
        <div id="view-active" class="hidden bg-white dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden flex-1 flex flex-col">
            <div class="px-6 py-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
                <span id="active-meta" class="text-xs font-mono font-medium text-slate-600 dark:text-slate-300 uppercase">Question 1 of 3</span>
                <span id="active-score-badge" class="px-2.5 py-1 bg-emerald-100 text-emerald-800 dark:bg-emerald-500/20 dark:text-emerald-400 text-xs font-bold rounded-lg hidden">Score: 0/100</span>
            </div>

            <div class="p-6 space-y-6 flex-1 overflow-y-auto">
                <h3 id="question-text" class="text-base sm:text-lg font-semibold text-slate-900 dark:text-white leading-relaxed">Loading question...</h3>

                <!-- Multiple Choice Container -->
                <div id="mcq-container" class="space-y-3 hidden"></div>

                <!-- Text Area / Free Writing -->
                <div id="text-container" class="space-y-2">
                    <textarea id="answer-text" rows="7" placeholder="Type your answer or response here..." class="w-full p-4 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-sm font-mono text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"></textarea>
                </div>

                <!-- Feedback & Best Answer Boxes -->
                <div id="evaluation-box" class="space-y-4 hidden">
                    <div class="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
                        <div id="feedback-heading" class="text-[11px] font-bold text-blue-700 dark:text-blue-400 uppercase tracking-wider mb-1">AI Feedback & Scoring</div>
                        <div id="feedback-content" class="text-xs text-blue-900 dark:text-blue-200 leading-relaxed whitespace-pre-wrap"></div>
                    </div>

                    <div class="p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl">
                        <div id="best-answer-heading" class="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider mb-1">Ideal Model Answer</div>
                        <div id="best-answer-content" class="text-xs font-mono text-emerald-900 dark:text-emerald-200 leading-relaxed whitespace-pre-wrap"></div>
                    </div>
                </div>
            </div>

            <div class="p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex justify-between items-center">
                <div id="current-score-display" class="text-xs font-semibold text-slate-500 dark:text-slate-400">
                    Submit answer for instant AI grading
                </div>
                <div class="flex items-center gap-3">
                    <button onclick="submitAnswer()" id="btn-submit-answer" class="px-6 py-2 bg-slate-800 dark:bg-slate-700 hover:bg-slate-700 dark:hover:bg-slate-600 text-white font-semibold text-xs rounded-xl transition-all">
                        Submit Answer
                    </button>
                    <button onclick="nextQuestion()" id="btn-next-question" class="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition-all hidden">
                        <span id="btn-next-text">Next Question</span> <i class="fa-solid fa-arrow-right ml-1"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Saved Results Page -->
        <div id="view-saved" class="hidden bg-white dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden flex-1 flex flex-col">
            <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
                <h2 id="saved-title" class="text-xs font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400">Saved Interview Session History</h2>
                <button onclick="clearHistory()" id="clear-history-btn" class="text-xs text-red-500 hover:text-red-600 font-semibold">Clear History</button>
            </div>
            <div id="saved-list" class="p-6 space-y-4 flex-1 overflow-y-auto">
                <div id="empty-saved-msg" class="text-center py-12 text-slate-400 text-xs">No saved interview sessions found yet. Complete an interview to save your progress!</div>
            </div>
        </div>

    </main>

    <script>
        let currentLang = 'EN';
        let currentTheme = 'dark';
        let activeSession = null;
        let currentQIdx = 0;
        let userAnswers = {};
        let evaluations = {};
        let bestAnswers = {};

        const i18n = {
            EN: {
                title: "Interview Prep AI",
                navSetup: "API Setup",
                navNew: "New Interview",
                navActive: "Active",
                navSaved: "Saved Results",
                setupTitle: "Gemini API Key Configuration",
                newTitle: "New Interview Session",
                roleLabel: "Target Role / Position",
                rolePlaceholder: "e.g. Senior Software Engineer, Project Manager, Data Analyst, Marketing Lead",
                contextLabel: "Job Posting URL or Description (Optional)",
                contextTag: "AI Scans & Tailors 10 Questions",
                contextPlaceholder: "Paste a job URL (e.g. https://company.com/job/123) or copy/paste the full job description text here...",
                typeLabel: "Interview Type",
                typeOptions: {
                    multiple_choice: "Multiple Choice Quiz",
                    free_writing: "Written Assessment",
                    technical_interview: "Technical Interview",
                    hr_interview: "HR Interview"
                },
                startBtn: "Generate Questions & Start",
                generatingBtn: "Generating AI Questions...",
                answerPlaceholder: "Type your answer or response here...",
                feedbackHeading: "AI Feedback & Scoring",
                bestAnswerHeading: "Ideal Model Answer",
                submitAnswerBtn: "Submit Answer",
                nextQuestionBtn: "Next Question",
                evaluatingBtn: "Evaluating with Gemini...",
                gradingMsg: "Submit answer for instant AI grading",
                savedTitle: "Saved Interview Session History",
                clearHistoryBtn: "Clear History",
                emptySavedMsg: "No saved interview sessions found yet. Complete an interview to save your progress!",
                questionText: "Question",
                ofText: "of"
            },
            BG: {
                title: "Подготовка за Интервю AI",
                navSetup: "API Настройки",
                navNew: "Ново Интервю",
                navActive: "Активно",
                navSaved: "Запазени Резултати",
                setupTitle: "Конфигурация на Gemini API Ключ",
                newTitle: "Нова Сесия за Интервю",
                roleLabel: "Заемана Длъжност / Роля",
                rolePlaceholder: "напр. Проект Мениджър, Софтуерен Инженер, Анализатор на Данни, Маркетинг Мениджър",
                contextLabel: "URL Линк или Описание на Обявата за Работа (По избор)",
                contextTag: "AI Анализира и Генерира Въпроси",
                contextPlaceholder: "Залепете URL линк към обява за работа (напр. https://company.com/job/123) или копирайте текста на обявата. AI ще я сканира и ще създаде персонализирани въпроси...",
                typeLabel: "Тип на Интервюто",
                typeOptions: {
                    multiple_choice: "Тест с Избор на Отговор",
                    free_writing: "Писмена Оценка",
                    technical_interview: "Техническо Интервю",
                    hr_interview: "HR Интервю"
                },
                startBtn: "Генерирай Въпроси и Започни",
                generatingBtn: "Генериране на Въпроси от AI...",
                answerPlaceholder: "Въведете вашия отговор или решение тук...",
                feedbackHeading: "AI Обратна Връзка и Оценка",
                bestAnswerHeading: "Примерен Идеален Отговор",
                submitAnswerBtn: "Изпрати Отговор",
                nextQuestionBtn: "Следващ Въпрос",
                evaluatingBtn: "Оценяване от Gemini...",
                gradingMsg: "Изпратете отговор за незабавна AI оценка",
                savedTitle: "История на Запазените Сесии",
                clearHistoryBtn: "Изчисти Историята",
                emptySavedMsg: "Все още няма запазени сесии. Завършете интервю, за да запазите резултатите си!",
                questionText: "Въпрос",
                ofText: "от"
            }
        };

        function toggleTheme() {
            currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.className = currentTheme;
            document.getElementById('theme-icon').className = currentTheme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }

        function updateLangUI() {
            document.getElementById('lang-code').innerText = currentLang;
            const t = i18n[currentLang];
            document.getElementById('title-text').innerText = t.title;
            document.getElementById('nav-setup').innerText = t.navSetup;
            document.getElementById('nav-new').innerText = t.navNew;
            document.getElementById('nav-active').innerText = t.navActive;
            document.getElementById('nav-saved').innerText = t.navSaved;
            document.getElementById('setup-title').innerText = t.setupTitle;
            document.getElementById('new-title').innerText = t.newTitle;
            document.getElementById('label-role').innerText = t.roleLabel;
            document.getElementById('job-title').placeholder = t.rolePlaceholder;
            document.getElementById('label-context').innerText = t.contextLabel;
            document.getElementById('tag-context').innerText = t.contextTag;
            document.getElementById('job-context').placeholder = t.contextPlaceholder;
            document.getElementById('label-type').innerText = t.typeLabel;

            const typeSelect = document.getElementById('interview-type');
            const selectedVal = typeSelect.value || 'multiple_choice';
            typeSelect.innerHTML = `
                <option value="multiple_choice">${t.typeOptions.multiple_choice}</option>
                <option value="free_writing">${t.typeOptions.free_writing}</option>
                <option value="technical_interview">${t.typeOptions.technical_interview}</option>
                <option value="hr_interview">${t.typeOptions.hr_interview}</option>
            `;
            typeSelect.value = selectedVal;

            document.getElementById('btn-start-text').innerText = t.startBtn;
            document.getElementById('answer-text').placeholder = t.answerPlaceholder;
            document.getElementById('feedback-heading').innerText = t.feedbackHeading;
            document.getElementById('best-answer-heading').innerText = t.bestAnswerHeading;
            document.getElementById('btn-submit-answer').innerText = t.submitAnswerBtn;
            document.getElementById('btn-next-text').innerText = t.nextQuestionBtn;
            document.getElementById('current-score-display').innerText = t.gradingMsg;
            document.getElementById('saved-title').innerText = t.savedTitle;
            document.getElementById('clear-history-btn').innerText = t.clearHistoryBtn;
            const emptyMsg = document.getElementById('empty-saved-msg');
            if (emptyMsg) emptyMsg.innerText = t.emptySavedMsg;
        }

        function toggleLang() {
            currentLang = currentLang === 'EN' ? 'BG' : 'EN';
            updateLangUI();
            if (activeSession) renderQuestion();
        }

        function switchView(viewName) {
            ['setup', 'new', 'active', 'saved'].forEach(v => {
                document.getElementById('view-' + v).classList.add('hidden');
                const navBtn = document.getElementById('nav-' + v);
                if (navBtn) {
                    navBtn.className = 'px-3 py-1.5 rounded-md transition-all text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white';
                }
            });
            document.getElementById('view-' + viewName).classList.remove('hidden');
            const activeNav = document.getElementById('nav-' + viewName);
            if (activeNav) {
                activeNav.className = 'px-3 py-1.5 rounded-md transition-all bg-white dark:bg-slate-700 text-emerald-600 dark:text-white shadow-sm font-semibold';
            }
            if (viewName === 'saved') loadSavedSessions();
        }

        function saveApiKey() {
            const key = document.getElementById('api-key-input').value.trim();
            localStorage.setItem('GEMINI_API_KEY', key);
            document.getElementById('api-status').innerText = 'API Key saved to browser local storage!';
            setTimeout(() => document.getElementById('api-status').innerText = '', 3000);
        }

        window.onload = function() {
            const savedKey = localStorage.getItem('GEMINI_API_KEY') || '';
            if (savedKey) document.getElementById('api-key-input').value = savedKey;
            updateLangUI();
        };

        async function startInterview() {
            const jobTitle = document.getElementById('job-title').value.trim();
            const jobContext = document.getElementById('job-context').value.trim();
            const type = document.getElementById('interview-type').value;
            const btn = document.getElementById('btn-start');
            const t = i18n[currentLang];
            btn.disabled = true;
            btn.innerText = t.generatingBtn;

            const apiKey = localStorage.getItem('GEMINI_API_KEY') || '';

            try {
                const res = await fetch('/api/generate-questions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ jobTitle, jobContext, type, apiKey, lang: currentLang })
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);

                activeSession = {
                    id: 'session_' + Date.now(),
                    jobTitle,
                    type,
                    questions: data.questions,
                    date: new Date().toISOString()
                };
                currentQIdx = 0;
                userAnswers = {};
                evaluations = {};
                bestAnswers = {};

                document.getElementById('nav-active').disabled = false;
                switchView('active');
                renderQuestion();
            } catch (err) {
                alert('Error generating interview questions: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa-solid fa-play"></i> <span id="btn-start-text">' + i18n[currentLang].startBtn + '</span>';
            }
        }

        function renderQuestion() {
            const q = activeSession.questions[currentQIdx];
            const t = i18n[currentLang];
            document.getElementById('active-meta').innerText = `${activeSession.jobTitle} • ${t.questionText} ${currentQIdx + 1} ${t.ofText} ${activeSession.questions.length}`;
            document.getElementById('question-text').innerText = q.text;

            const mcqBox = document.getElementById('mcq-container');
            const txtBox = document.getElementById('text-container');
            const evalBox = document.getElementById('evaluation-box');

            evalBox.classList.add('hidden');
            document.getElementById('btn-next-question').classList.add('hidden');
            document.getElementById('btn-submit-answer').classList.remove('hidden');
            document.getElementById('answer-text').value = userAnswers[q.id] || '';

            if (q.type === 'multiple_choice' && q.options) {
                txtBox.classList.add('hidden');
                mcqBox.classList.remove('hidden');
                mcqBox.innerHTML = '';
                q.options.forEach((opt, idx) => {
                    const char = String.fromCharCode(65 + idx);
                    const isSel = userAnswers[q.id] === char;
                    mcqBox.innerHTML += `
                        <div onclick="selectMCQ('${q.id}', '${char}')" class="p-4 border rounded-xl cursor-pointer flex items-center gap-3 transition-all ${isSel ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 text-emerald-900 dark:text-emerald-200' : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:border-emerald-500'}">
                            <span class="w-7 h-7 rounded-lg border flex items-center justify-center font-bold text-xs ${isSel ? 'bg-emerald-500 text-white border-emerald-500' : 'border-slate-300 dark:border-slate-600'}">${char}</span>
                            <span class="text-sm font-medium">${opt}</span>
                        </div>
                    `;
                });
            } else {
                mcqBox.classList.add('hidden');
                txtBox.classList.remove('hidden');
            }

            if (evaluations[q.id]) {
                showEvaluation(q.id);
            }
        }

        function selectMCQ(qId, choice) {
            userAnswers[qId] = choice;
            renderQuestion();
        }

        async function submitAnswer() {
            const q = activeSession.questions[currentQIdx];
            if (q.type !== 'multiple_choice') {
                userAnswers[q.id] = document.getElementById('answer-text').value.trim();
            }

            if (!userAnswers[q.id]) {
                alert('Please provide an answer before submitting.');
                return;
            }

            const btn = document.getElementById('btn-submit-answer');
            btn.disabled = true;
            btn.innerText = 'Evaluating with Gemini...';

            const apiKey = localStorage.getItem('GEMINI_API_KEY') || '';

            try {
                const res = await fetch('/api/evaluate-answer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        question: q,
                        answer: userAnswers[q.id],
                        jobTitle: activeSession.jobTitle,
                        apiKey,
                        lang: currentLang
                    })
                });
                const data = await res.json();
                evaluations[q.id] = { score: data.score, feedback: data.feedback };
                bestAnswers[q.id] = data.bestAnswer;

                showEvaluation(q.id);
            } catch (err) {
                alert('Evaluation error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = 'Submit Answer';
            }
        }

        function showEvaluation(qId) {
            document.getElementById('feedback-content').innerText = evaluations[qId].feedback;
            document.getElementById('best-answer-content').innerText = bestAnswers[qId];
            document.getElementById('evaluation-box').classList.remove('hidden');
            document.getElementById('btn-submit-answer').classList.add('hidden');
            document.getElementById('btn-next-question').classList.remove('hidden');
        }

        async function nextQuestion() {
            if (currentQIdx < activeSession.questions.length - 1) {
                currentQIdx++;
                renderQuestion();
            } else {
                // Calculate overall score
                let total = 0;
                let count = 0;
                Object.values(evaluations).forEach(e => {
                    total += e.score;
                    count++;
                });
                const overallScore = count > 0 ? Math.round(total / count) : 0;
                activeSession.overallScore = overallScore;
                activeSession.completed = true;
                activeSession.userAnswers = userAnswers;
                activeSession.evaluations = evaluations;
                activeSession.bestAnswers = bestAnswers;

                await fetch('/api/save-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(activeSession)
                });

                alert(`Interview Complete! Your overall score is ${overallScore}/100.`);
                switchView('saved');
            }
        }

        async function loadSavedSessions() {
            const list = document.getElementById('saved-list');
            try {
                const res = await fetch('/api/saved-sessions');
                const sessions = await res.json();
                if (sessions.length === 0) {
                    list.innerHTML = '<div class="text-center py-12 text-slate-400 text-xs">No saved interview sessions found yet. Complete an interview to save your progress!</div>';
                    return;
                }
                list.innerHTML = sessions.map(s => `
                    <div class="p-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2">
                        <div class="flex justify-between items-center">
                            <div>
                                <h4 class="font-bold text-sm text-slate-900 dark:text-white">${s.jobTitle}</h4>
                                <div class="text-xs text-slate-500 mt-0.5">Score: <span class="font-bold text-emerald-600 dark:text-emerald-400">${s.overallScore || 0}/100</span> • ${new Date(s.date).toLocaleDateString()}</div>
                            </div>
                            <span class="px-2.5 py-1 bg-slate-200 dark:bg-slate-800 text-xs font-semibold rounded-lg uppercase">${s.type}</span>
                        </div>
                    </div>
                `).join('');
            } catch (err) {
                list.innerHTML = '<div class="text-center py-6 text-red-400 text-xs">Failed to load saved sessions.</div>';
            }
        }

        async function clearHistory() {
            if (confirm('Clear all saved interview sessions?')) {
                await fetch('/api/clear-sessions', { method: 'POST' });
                loadSavedSessions();
            }
        }
    </script>
</body>
</html>
"""

class PythonInterviewServer(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format%args))

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == "/api/saved-sessions":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(SAVED_SESSIONS).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if self.path == "/api/generate-questions":
            self.handle_generate_questions(data)
        elif self.path == "/api/evaluate-answer":
            self.handle_evaluate_answer(data)
        elif self.path == "/api/save-session":
            SAVED_SESSIONS.insert(0, data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        elif self.path == "/api/clear-sessions":
            SAVED_SESSIONS.clear()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def call_gemini_api(self, prompt, user_key=None):
        api_key = (user_key or os.environ.get("GEMINI_API_KEY", "")).strip()
        if not api_key:
            raise Exception("No Gemini API key provided. Please enter your API key in the 'API Setup' tab.")

        models_to_try = [
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash"
        ]
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        last_error = None
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    res_body = resp.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    candidates = res_json.get('candidates', [])
                    if not candidates:
                        raise Exception("Gemini API returned an empty response.")
                    text_result = candidates[0]['content']['parts'][0]['text'].strip()
                    # Strip any markdown code fences if returned
                    if text_result.startswith("```json"):
                        text_result = text_result[7:]
                    elif text_result.startswith("```"):
                        text_result = text_result[3:]
                    if text_result.endswith("```"):
                        text_result = text_result[:-3]
                    return text_result.strip()
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8', errors='ignore')
                try:
                    err_json = json.loads(err_body)
                    msg = err_json.get('error', {}).get('message', str(e))
                except Exception:
                    msg = str(e)
                # If model is not found (404), try the next model in our list
                if e.code == 404:
                    last_error = f"Model {model} 404: {msg}"
                    continue
                # For auth errors, quota, or parameter issues, fail immediately with clear explanation
                raise Exception(f"Gemini API Error ({e.code}): {msg}")
            except Exception as e:
                last_error = str(e)
                continue

        raise Exception(f"Failed to connect to Gemini API: {last_error}")

    def handle_generate_questions(self, data):
        import time
        import random
        job_title = data.get('jobTitle', 'Professional Candidate')
        job_context = data.get('jobContext', '').strip()
        interview_type = data.get('type', 'technical_interview')
        lang = data.get('lang', 'EN')
        api_key = data.get('apiKey', '')
        seed = int(time.time() * 1000) + random.randint(1000, 9999)

        context_prompt_part = ""
        if job_context:
            if job_context.startswith("http://") or job_context.startswith("https://"):
                try:
                    req = urllib.request.Request(
                        job_context,
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        raw_html = resp.read().decode('utf-8', errors='ignore')
                        clean_text = re.sub(r'<script[^>]*>.*?</script>', '', raw_html, flags=re.DOTALL)
                        clean_text = re.sub(r'<style[^>]*>.*?</style>', '', clean_text, flags=re.DOTALL)
                        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
                        clean_text = ' '.join(clean_text.split())[:3000]
                        context_prompt_part = f"\nJOB POSTING WEBPAGE CONTENT ({job_context}):\n{clean_text}\n"
                except Exception as ex:
                    context_prompt_part = f"\nJOB POSTING URL PROVIDED: {job_context} (Fetch Note: {str(ex)})\n"
            else:
                context_prompt_part = f"\nJOB POSTING / DESCRIPTION PROVIDED BY CANDIDATE:\n{job_context[:3000]}\n"

        type_descriptions = {
            "multiple_choice": "Multiple Choice Quiz with 4 options (A, B, C, D) per question.",
            "free_writing": "Written Assessment & Open Problem Solving Exercises.",
            "technical_interview": "Technical & Domain Expertise Knowledge Interview.",
            "hr_interview": "HR, Behavioral, Situational & Culture Fit Interview."
        }
        type_desc = type_descriptions.get(interview_type, "Standard Interview")

        if lang == "BG":
            lang_instruction = """
STRICT LANGUAGE REQUIREMENT: EVERYTHING MUST BE WRITTEN IN BULGARIAN (български език).
All 10 question texts, option choices (Choice A, Choice B, Choice C, Choice D), and explanations MUST be written 100% in natural, fluent Bulgarian language.
Do NOT output English text or English options when language is set to BG.
"""
        else:
            lang_instruction = """
STRICT LANGUAGE REQUIREMENT: EVERYTHING MUST BE WRITTEN IN PROFESSIONAL ENGLISH.
"""

        prompt = f"""You are an executive interviewer conducting a professional interview for a candidate applying for '{job_title}'.
Interview Category: {interview_type} ({type_desc})
Random Variation Seed: {seed}
{context_prompt_part}
{lang_instruction}

CRITICAL REQUIREMENTS:
1. Generate EXACTLY 10 high-quality, relevant, and realistic interview questions tailored specifically for the position of '{job_title}'.
2. If job posting text or URL content is provided above, analyze it thoroughly and generate questions directly testing the specific duties, skills, tools, and requirements mentioned in that posting.
3. The questions MUST be randomly selected, diverse, non-repetitive, and unique every time. Do NOT repeat previous standard templates.
4. For 'multiple_choice' interview type, every question MUST include an 'options' array containing exactly 4 realistic choices.
5. For other interview types ('free_writing', 'technical_interview', 'hr_interview'), do NOT include an 'options' array.

Return ONLY a valid JSON object matching this exact schema:
{{
  "questions": [
    {{
      "id": "q1",
      "text": "Detailed question text...",
      "type": "{interview_type}",
      "options": ["Choice A", "Choice B", "Choice C", "Choice D"]
    }}
  ]
}}
"""
        try:
            raw_text = self.call_gemini_api(prompt, api_key)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(raw_text.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def handle_evaluate_answer(self, data):
        question = data.get('question', {})
        answer = data.get('answer', '')
        job_title = data.get('jobTitle', 'Candidate')
        lang = data.get('lang', 'EN')
        api_key = data.get('apiKey', '')

        if lang == "BG":
            lang_instruction = """
STRICT LANGUAGE REQUIREMENT:
The evaluation feedback ("feedback") and ideal model answer ("bestAnswer") MUST be written 100% in fluent, professional BULGARIAN (български език).
Do NOT reply in English when language is set to BG.
"""
        else:
            lang_instruction = """
STRICT LANGUAGE REQUIREMENT:
Write evaluation feedback and model answers in clear professional English.
"""

        prompt = f"""You are a senior hiring manager grading a candidate's answer for the position of '{job_title}'.
Question: "{question.get('text', '')}"
Candidate's Answer: "{answer}"
{lang_instruction}

Grade the answer objectively from 0 to 100 based on accuracy, depth, relevance, and professional competency for a '{job_title}'.
Return ONLY a valid JSON object matching this schema:
{{
  "score": 85,
  "feedback": "Detailed constructive feedback explaining strengths, weaknesses, and key missing insights...",
  "bestAnswer": "Clear, exemplary response illustrating an ideal top-tier candidate answer..."
}}
"""
        try:
            raw_text = self.call_gemini_api(prompt, api_key)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(raw_text.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer((HOST, PORT), PythonInterviewServer)
    print(f"★ Interview Prep AI Server running on http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    run_server()
