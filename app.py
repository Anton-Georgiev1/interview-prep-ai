#!/usr/bin/env python3
"""
Interview Prep AI Web Application
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

# In-memory storage for interview sessions
SAVED_SESSIONS = []
# Dynamic remembered model - stays on the successfully answered model until unavailable
ACTIVE_GEMINI_MODEL = "gemini-3.5-flash"
ALL_GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]

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
                <!-- Theme Toggle -->
                <button onclick="toggleTheme()" class="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" title="Toggle Theme">
                    <i id="theme-icon" class="fa-solid fa-sun"></i>
                </button>

                <!-- Language Toggle (EN / BG) -->
                <button onclick="toggleLang()" class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-700 dark:text-slate-300">
                    <i class="fa-solid fa-globe"></i>
                    <span id="lang-code">EN</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 flex flex-col">
        <!-- API Setup Page -->
        <div id="view-setup" class="hidden bg-white dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-4">
            <h2 id="setup-title" class="text-sm font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400">Gemini API Key Configuration</h2>
            <p class="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Provide your Google Gemini API Key. It will be stored securely in your browser's LocalStorage and used directly for generating questions, instant answer checking, hints, and fast evaluations.
            </p>
            <div class="space-y-2">
                <input type="password" id="api-key-input" placeholder="AIzaSy..." class="w-full p-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500">
            </div>
            <div class="flex items-center gap-3">
                <button onclick="saveApiKey()" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl shadow-md transition-all">Save Key</button>
                <span id="api-status" class="text-xs text-emerald-600 dark:text-emerald-400 font-medium"></span>
            </div>
        </div>

        <!-- New Interview Session Form -->
        <div id="view-new" class="bg-white dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-6">
            <div class="border-b border-slate-100 dark:border-slate-700/60 pb-4">
                <h2 id="new-title" class="text-xs font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400">New Interview Session</h2>
            </div>

            <div class="space-y-4">
                <div>
                    <label id="label-role" class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">Target Role / Position</label>
                    <input type="text" id="job-title" placeholder="e.g. Project Manager, Senior Python Engineer, Data Analyst, Product Owner" class="w-full p-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500">
                </div>

                <div>
                    <div class="flex items-center justify-between mb-1.5">
                        <label id="label-context" class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">Job Posting URL or Description (Optional)</label>
                        <span id="tag-context" class="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">AI Scans & Tailors 10 Questions</span>
                    </div>
                    <textarea id="job-context" rows="3" placeholder="Paste a job URL (e.g. https://company.com/job/123) or copy/paste the full job description text here..." class="w-full p-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"></textarea>
                </div>

                <div>
                    <label id="label-type" class="block text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400 mb-1.5">Interview Type</label>
                    <select id="interview-type" class="w-full p-3 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500">
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
            <!-- Top Bar with Navigator & Abandon Option -->
            <div class="px-6 py-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex flex-wrap justify-between items-center gap-3">
                <div class="flex items-center gap-3">
                    <span id="active-meta" class="text-xs font-mono font-bold text-slate-700 dark:text-slate-200 uppercase">Question 1 of 10</span>
                    <span id="active-status-badge" class="px-2 py-0.5 text-[11px] font-bold rounded-md bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">Unanswered</span>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="abandonInterview()" id="btn-abandon" class="px-3 py-1 text-xs font-semibold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg border border-rose-200 dark:border-rose-900/50 transition-all flex items-center gap-1.5" title="Quit and discard current interview">
                        <i class="fa-solid fa-arrow-right-from-bracket"></i>
                        <span id="btn-abandon-text">Abandon Interview</span>
                    </button>
                </div>
            </div>

            <!-- Question Numbers Quick Navigator Bar -->
            <div class="px-6 py-2 border-b border-slate-100 dark:border-slate-800 bg-slate-100/50 dark:bg-slate-900/30 flex items-center gap-1.5 overflow-x-auto" id="question-nav-dots">
                <!-- Filled dynamically with Q1, Q2, Q3... buttons -->
            </div>

            <div class="p-6 space-y-5 flex-1 overflow-y-auto">
                <div class="flex justify-between items-start gap-4">
                    <h3 id="question-text" class="text-base sm:text-lg font-semibold text-slate-900 dark:text-white leading-relaxed flex-1">Loading question...</h3>
                </div>

                <!-- Multiple Choice Container -->
                <div id="mcq-container" class="space-y-3 hidden"></div>

                <!-- Text Area / Free Writing -->
                <div id="text-container" class="space-y-2">
                    <textarea id="answer-text" rows="6" oninput="saveCurrentTextAnswer()" placeholder="Type your answer or response here..." class="w-full p-4 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-sm font-mono text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"></textarea>
                </div>

                <!-- Interactive Helpers: Hint & Suggested Model Answer Toggle Buttons -->
                <div class="flex flex-wrap items-center gap-2 pt-1">
                    <button onclick="toggleHint()" id="btn-hint" class="px-3.5 py-1.5 bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20 border border-amber-500/30 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5">
                        <i class="fa-regular fa-lightbulb"></i>
                        <span id="btn-hint-text">Show Hint</span>
                    </button>

                    <button onclick="toggleSuggestedAnswer()" id="btn-suggested" class="px-3.5 py-1.5 bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-500/20 border border-indigo-500/30 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-wand-magic-sparkles"></i>
                        <span id="btn-suggested-text">AI Suggested Answer</span>
                    </button>
                </div>

                <!-- Hint Content Box -->
                <div id="hint-box" class="p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/40 rounded-xl hidden">
                    <div class="flex items-center gap-2 text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider mb-1">
                        <i class="fa-solid fa-lightbulb"></i>
                        <span id="hint-heading">Question Hint</span>
                    </div>
                    <div id="hint-content" class="text-xs text-amber-900 dark:text-amber-200 leading-relaxed"></div>
                </div>

                <!-- Suggested Model Answer Box -->
                <div id="suggested-box" class="p-4 bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-200 dark:border-indigo-900/40 rounded-xl hidden">
                    <div class="flex items-center gap-2 text-xs font-bold text-indigo-700 dark:text-indigo-400 uppercase tracking-wider mb-1">
                        <i class="fa-solid fa-star"></i>
                        <span id="suggested-heading">AI Model / Reference Answer</span>
                    </div>
                    <div id="suggested-content" class="text-xs text-indigo-950 dark:text-indigo-200 leading-relaxed whitespace-pre-wrap"></div>
                </div>

                <!-- MCQ Validation Feedback Banner -->
                <div id="validation-banner" class="p-4 rounded-xl hidden border"></div>
            </div>

            <!-- Bottom Navigation Bar (Previous, Next / Skip, Finish Interview) -->
            <div class="p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex flex-wrap justify-between items-center gap-3">
                <div class="flex items-center gap-2">
                    <button onclick="prevQuestion()" id="btn-prev-question" class="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-200 font-semibold text-xs rounded-xl transition-all flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed">
                        <i class="fa-solid fa-arrow-left"></i>
                        <span id="btn-prev-text">Previous</span>
                    </button>
                </div>

                <div class="flex items-center gap-2">
                    <button onclick="nextQuestion(true)" id="btn-skip-question" class="px-4 py-2 bg-slate-200/80 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold text-xs rounded-xl transition-all flex items-center gap-1.5">
                        <span id="btn-skip-text">Skip</span>
                        <i class="fa-solid fa-forward-step"></i>
                    </button>

                    <button onclick="nextQuestion(false)" id="btn-next-question" class="px-5 py-2 bg-slate-800 dark:bg-slate-700 hover:bg-slate-700 dark:hover:bg-slate-600 text-white font-semibold text-xs rounded-xl transition-all flex items-center gap-1.5">
                        <span id="btn-next-text">Next Question</span>
                        <i class="fa-solid fa-arrow-right"></i>
                    </button>

                    <button onclick="finishInterview()" id="btn-finish-interview" class="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-md shadow-emerald-600/20 transition-all flex items-center gap-1.5">
                        <i class="fa-solid fa-circle-check"></i>
                        <span id="btn-finish-text">Finish & Final Evaluation</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Saved Results / Summary Report Page -->
        <div id="view-saved" class="hidden bg-white dark:bg-slate-800/80 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden flex-1 flex flex-col">
            <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
                <h2 id="saved-title" class="text-xs font-bold uppercase tracking-widest text-emerald-600 dark:text-emerald-400">Saved Interview Session History & Evaluations</h2>
                <button onclick="clearHistory()" id="clear-history-btn" class="text-xs text-red-500 hover:text-red-600 font-semibold flex items-center gap-1">
                    <i class="fa-solid fa-trash-can"></i>
                    <span>Clear History</span>
                </button>
            </div>
            <div id="saved-list" class="p-6 space-y-4 flex-1 overflow-y-auto">
                <div id="empty-saved-msg" class="text-center py-12 text-slate-400 text-xs">No saved interview sessions found yet. Complete an interview to see your overall evaluation!</div>
            </div>
        </div>
    </main>

    <!-- Evaluating Modal Overlay -->
    <div id="eval-modal" class="fixed inset-0 bg-slate-900/70 backdrop-blur-sm z-50 flex items-center justify-center hidden">
        <div class="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl text-center space-y-4">
            <div class="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center mx-auto text-xl animate-spin">
                <i class="fa-solid fa-circle-notch"></i>
            </div>
            <div>
                <h4 id="eval-modal-title" class="font-bold text-sm text-slate-900 dark:text-white">Evaluating Complete Interview...</h4>
                <p id="eval-modal-desc" class="text-xs text-slate-500 dark:text-slate-400 mt-1">AI is calculating your final score, analyzing all answers, and preparing comprehensive feedback report.</p>
            </div>
        </div>
    </div>

    <script>
        let currentTheme = 'dark';
        let currentLang = 'EN';
        let activeSession = null;
        let currentQIdx = 0;
        let userAnswers = {};
        let shownHints = {};
        let shownSuggested = {};

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
                rolePlaceholder: "e.g. Project Manager, Senior Python Engineer, Data Analyst, Product Owner",
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
                questionText: "Question",
                ofText: "of",
                unanswered: "Unanswered",
                answered: "Answered",
                skipped: "Skipped",
                correct: "Correct Answer!",
                incorrect: "Incorrect Answer",
                btnAbandon: "Abandon Interview",
                abandonConfirm: "Are you sure you want to abandon this interview session? Your progress will not be saved.",
                btnHint: "Show Hint",
                btnHideHint: "Hide Hint",
                hintHeading: "Question Hint",
                noHintAvailable: "Consider the key responsibilities, industry best practices, and core objectives for this specific scenario.",
                btnSuggested: "AI Suggested Answer",
                btnHideSuggested: "Hide AI Suggested Answer",
                suggestedHeading: "AI Model / Reference Answer",
                btnPrev: "Previous",
                btnNext: "Next Question",
                btnSkip: "Skip",
                btnFinish: "Finish & Final Evaluation",
                savedTitle: "Saved Interview Session History & Evaluations",
                clearHistoryBtn: "Clear History",
                clearConfirm: "Clear all saved interview sessions?",
                emptySavedMsg: "No saved interview sessions found yet. Complete an interview to see your overall evaluation!",
                evaluatingModalTitle: "Evaluating Complete Interview...",
                evaluatingModalDesc: "AI is calculating your final score, analyzing all answers, and generating comprehensive feedback summary.",
                overallScoreLabel: "Overall Score",
                comprehensiveSummary: "Comprehensive AI Evaluation Report",
                individualBreakdown: "Question-by-Question Review",
                yourAnswer: "Your Answer",
                correctAnswerLabel: "Correct Answer",
                aiFeedbackLabel: "AI Feedback",
                idealAnswerLabel: "Ideal Reference Answer"
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
                contextTag: "AI Анализира и Генерира 10 Въпроса",
                contextPlaceholder: "Залепете URL линк към обява за работа (напр. https://company.com/job/123) или копирайте текста на обявата...",
                typeLabel: "Тип на Интервюто",
                typeOptions: {
                    multiple_choice: "Тест с Избор на Отговор (Quiz)",
                    free_writing: "Писмена Оценка",
                    technical_interview: "Техническо Интервю",
                    hr_interview: "HR Интервю"
                },
                startBtn: "Генерирай Въпроси и Започни",
                generatingBtn: "Генериране на Въпроси от AI...",
                answerPlaceholder: "Въведете вашия отговор или решение тук...",
                questionText: "Въпрос",
                ofText: "от",
                unanswered: "Няма отговор",
                answered: "Отговорен",
                skipped: "Пропуснат",
                correct: "Верен отговор!",
                incorrect: "Грешен отговор",
                btnAbandon: "Прекрати Интервюто",
                abandonConfirm: "Сигурни ли сте, че искате да прекратите това интервю? Прогресът ви няма да бъде запазен.",
                btnHint: "Покажи Подсказка",
                btnHideHint: "Скрий Подсказката",
                hintHeading: "Подсказка към Въпроса",
                noHintAvailable: "Помислете за основните отговорности, добрите практики в индустрията и ключовите цели за тази ситуация.",
                btnSuggested: "Препоръчан Отговор от AI",
                btnHideSuggested: "Скрий Препоръчания Отговор",
                suggestedHeading: "Примерен / Препоръчан Отговор от AI",
                btnPrev: "Предишен",
                btnNext: "Следващ Въпрос",
                btnSkip: "Пропусни",
                btnFinish: "Приключи и Оцени Интервюто",
                savedTitle: "История на Запазените Сесии и Оценки",
                clearHistoryBtn: "Изчисти Историята",
                clearConfirm: "Изчистване на всички запазени интервю сесии?",
                emptySavedMsg: "Все още няма запазени сесии. Завършете интервю, за да видите пълния доклад с оценка!",
                evaluatingModalTitle: "Оценяване на цялото интервю...",
                evaluatingModalDesc: "AI изчислява общия ви резултат, анализира отговорите и изготвя пълен обобщен доклад с обратна връзка.",
                overallScoreLabel: "Краен Резултат",
                comprehensiveSummary: "Пълен Доклад с AI Оценка и Препоръки",
                individualBreakdown: "Преглед по отделни въпроси",
                yourAnswer: "Вашият Отговор",
                correctAnswerLabel: "Верен Отговор",
                aiFeedbackLabel: "AI Обратна Връзка",
                idealAnswerLabel: "Препоръчан Отговор"
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
            document.getElementById('btn-abandon-text').innerText = t.btnAbandon;
            document.getElementById('hint-heading').innerText = t.hintHeading;
            document.getElementById('suggested-heading').innerText = t.suggestedHeading;
            document.getElementById('btn-prev-text').innerText = t.btnPrev;
            document.getElementById('btn-next-text').innerText = t.btnNext;
            document.getElementById('btn-skip-text').innerText = t.btnSkip;
            document.getElementById('btn-finish-text').innerText = t.btnFinish;
            document.getElementById('saved-title').innerText = t.savedTitle;
            document.getElementById('clear-history-btn').innerHTML = `<i class="fa-solid fa-trash-can"></i> <span>${t.clearHistoryBtn}</span>`;
            
            const emptyMsg = document.getElementById('empty-saved-msg');
            if (emptyMsg) emptyMsg.innerText = t.emptySavedMsg;

            if (activeSession) renderQuestion();
        }

        function toggleLang() {
            currentLang = currentLang === 'EN' ? 'BG' : 'EN';
            updateLangUI();
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
            setTimeout(() => { document.getElementById('api-status').innerText = ''; }, 3500);
        }

        async function startInterview() {
            const jobTitle = document.getElementById('job-title').value.trim() || 'General Professional';
            const jobContext = document.getElementById('job-context').value.trim();
            const type = document.getElementById('interview-type').value;
            const btn = document.getElementById('btn-start');
            const apiKey = localStorage.getItem('GEMINI_API_KEY') || '';

            btn.disabled = true;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> ' + i18n[currentLang].generatingBtn;

            try {
                const res = await fetch('/api/generate-questions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ jobTitle, jobContext, type, lang: currentLang, apiKey })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.error || `HTTP error ${res.status}`);
                }

                const data = await res.json();
                if (!data.questions || data.questions.length === 0) {
                    throw new Error('No interview questions returned by AI.');
                }

                activeSession = {
                    id: 'session_' + Date.now(),
                    jobTitle,
                    type,
                    questions: data.questions,
                    date: new Date().toISOString()
                };

                currentQIdx = 0;
                userAnswers = {};
                shownHints = {};
                shownSuggested = {};

                const navActive = document.getElementById('nav-active');
                navActive.disabled = false;
                navActive.classList.remove('cursor-not-allowed', 'text-slate-400', 'dark:text-slate-500');
                
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
            if (!activeSession || !activeSession.questions) return;
            const q = activeSession.questions[currentQIdx];
            const t = i18n[currentLang];
            const totalQ = activeSession.questions.length;

            document.getElementById('active-meta').innerText = `${activeSession.jobTitle} • ${t.questionText} ${currentQIdx + 1} ${t.ofText} ${totalQ}`;
            document.getElementById('question-text').innerText = `${currentQIdx + 1}. ${q.text}`;

            // Update question navigator dots/buttons
            const navDots = document.getElementById('question-nav-dots');
            navDots.innerHTML = activeSession.questions.map((item, idx) => {
                const ans = userAnswers[item.id];
                const isCurrent = idx === currentQIdx;
                let statusBg = 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-400';
                
                if (ans) {
                    if (item.type === 'multiple_choice' && item.correctAnswer) {
                        statusBg = ans === item.correctAnswer ? 'bg-emerald-500 text-white font-bold' : 'bg-rose-500 text-white font-bold';
                    } else {
                        statusBg = 'bg-emerald-600 text-white font-bold';
                    }
                }
                
                const ringStyle = isCurrent ? 'ring-2 ring-emerald-500 ring-offset-2 dark:ring-offset-slate-900' : '';
                return `
                    <button onclick="jumpToQuestion(${idx})" class="px-2.5 py-1 text-[11px] font-mono font-semibold rounded-lg transition-all ${statusBg} ${ringStyle}">
                        Q${idx + 1}
                    </button>
                `;
            }).join('');

            // Status Badge
            const currentAns = userAnswers[q.id];
            const statusBadge = document.getElementById('active-status-badge');
            if (currentAns) {
                statusBadge.innerText = t.answered + (q.type === 'multiple_choice' ? ` (${currentAns})` : '');
                statusBadge.className = 'px-2 py-0.5 text-[11px] font-bold rounded-md bg-emerald-100 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400';
            } else {
                statusBadge.innerText = t.unanswered;
                statusBadge.className = 'px-2 py-0.5 text-[11px] font-bold rounded-md bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300';
            }

            const mcqBox = document.getElementById('mcq-container');
            const txtBox = document.getElementById('text-container');
            const valBanner = document.getElementById('validation-banner');

            valBanner.classList.add('hidden');

            if (q.type === 'multiple_choice' && q.options) {
                txtBox.classList.add('hidden');
                mcqBox.classList.remove('hidden');
                mcqBox.innerHTML = '';

                q.options.forEach((opt, idx) => {
                    const char = String.fromCharCode(65 + idx);
                    const isSel = userAnswers[q.id] === char;
                    const isCorrect = q.correctAnswer === char;

                    let optCardClass = 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:border-emerald-500';
                    let charBadgeClass = 'border-slate-300 dark:border-slate-600 text-slate-600 dark:text-slate-300';
                    let iconHtml = '';

                    if (userAnswers[q.id]) {
                        // User has selected an answer: validate immediately
                        if (isSel) {
                            if (isCorrect) {
                                optCardClass = 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 text-emerald-900 dark:text-emerald-200 shadow-sm';
                                charBadgeClass = 'bg-emerald-500 text-white border-emerald-500';
                                iconHtml = `<span class="ml-auto text-emerald-600 dark:text-emerald-400 text-xs font-bold flex items-center gap-1"><i class="fa-solid fa-circle-check"></i> ${t.correct}</span>`;
                            } else {
                                optCardClass = 'bg-rose-50 dark:bg-rose-950/40 border-rose-500 text-rose-900 dark:text-rose-200 shadow-sm';
                                charBadgeClass = 'bg-rose-500 text-white border-rose-500';
                                iconHtml = `<span class="ml-auto text-rose-600 dark:text-rose-400 text-xs font-bold flex items-center gap-1"><i class="fa-solid fa-circle-xmark"></i> ${t.incorrect}</span>`;
                            }
                        } else if (isCorrect) {
                            // Highlight the correct answer if the user picked the wrong one
                            optCardClass = 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-400/60 text-emerald-900 dark:text-emerald-300';
                            charBadgeClass = 'border-emerald-500 text-emerald-600 dark:text-emerald-400 font-bold';
                            iconHtml = `<span class="ml-auto text-emerald-600 dark:text-emerald-400 text-xs font-semibold">${t.correctAnswerLabel}</span>`;
                        }
                    }

                    mcqBox.innerHTML += `
                        <div onclick="selectMCQ('${q.id}', '${char}')" class="p-4 border rounded-xl cursor-pointer flex items-center gap-3 transition-all ${optCardClass}">
                            <span class="w-8 h-8 rounded-lg border flex items-center justify-center font-bold text-xs ${charBadgeClass}">${char}</span>
                            <span class="text-sm font-medium flex-1">${opt}</span>
                            ${iconHtml}
                        </div>
                    `;
                });

                if (userAnswers[q.id]) {
                    valBanner.classList.remove('hidden');
                    const isRight = userAnswers[q.id] === q.correctAnswer;
                    if (isRight) {
                        valBanner.className = 'p-3 rounded-xl border bg-emerald-50 dark:bg-emerald-950/30 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 text-xs flex items-center gap-2';
                        valBanner.innerHTML = `<i class="fa-solid fa-check-circle text-emerald-500 text-sm"></i> <div><strong>${t.correct}</strong> Option ${q.correctAnswer} is right.</div>`;
                    } else {
                        valBanner.className = 'p-3 rounded-xl border bg-rose-50 dark:bg-rose-950/30 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200 text-xs flex items-center gap-2';
                        valBanner.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-500 text-sm"></i> <div><strong>${t.incorrect}:</strong> You selected ${userAnswers[q.id]}. The correct answer is <strong>Option ${q.correctAnswer}</strong>.</div>`;
                    }
                }
            } else {
                mcqBox.classList.add('hidden');
                txtBox.classList.remove('hidden');
                document.getElementById('answer-text').value = userAnswers[q.id] || '';
            }

            // Hint state
            const hintBox = document.getElementById('hint-box');
            const hintBtn = document.getElementById('btn-hint');
            if (shownHints[q.id]) {
                hintBox.classList.remove('hidden');
                document.getElementById('hint-content').innerText = q.hint || t.noHintAvailable;
                hintBtn.innerHTML = `<i class="fa-solid fa-lightbulb"></i> <span>${t.btnHideHint}</span>`;
            } else {
                hintBox.classList.add('hidden');
                hintBtn.innerHTML = `<i class="fa-regular fa-lightbulb"></i> <span>${t.btnHint}</span>`;
            }

            // Suggested answer state
            const suggestedBox = document.getElementById('suggested-box');
            const suggestedBtn = document.getElementById('btn-suggested');
            if (shownSuggested[q.id]) {
                suggestedBox.classList.remove('hidden');
                document.getElementById('suggested-content').innerText = q.suggestedAnswer || (q.correctAnswer ? `Option ${q.correctAnswer}: ${q.options ? q.options[q.correctAnswer.charCodeAt(0) - 65] : ''}` : 'No model answer provided.');
                suggestedBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> <span>${t.btnHideSuggested}</span>`;
            } else {
                suggestedBox.classList.add('hidden');
                suggestedBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> <span>${t.btnSuggested}</span>`;
            }

            // Navigation Button States
            document.getElementById('btn-prev-question').disabled = currentQIdx === 0;
            const isLast = currentQIdx === totalQ - 1;
            document.getElementById('btn-next-question').classList.toggle('hidden', isLast);
            document.getElementById('btn-skip-question').classList.toggle('hidden', isLast);
        }

        function selectMCQ(qId, choice) {
            userAnswers[qId] = choice;
            renderQuestion();
        }

        function saveCurrentTextAnswer() {
            if (!activeSession) return;
            const q = activeSession.questions[currentQIdx];
            if (q.type !== 'multiple_choice') {
                userAnswers[q.id] = document.getElementById('answer-text').value;
            }
        }

        function toggleHint() {
            if (!activeSession) return;
            const q = activeSession.questions[currentQIdx];
            shownHints[q.id] = !shownHints[q.id];
            renderQuestion();
        }

        function toggleSuggestedAnswer() {
            if (!activeSession) return;
            const q = activeSession.questions[currentQIdx];
            shownSuggested[q.id] = !shownSuggested[q.id];
            renderQuestion();
        }

        function prevQuestion() {
            saveCurrentTextAnswer();
            if (currentQIdx > 0) {
                currentQIdx--;
                renderQuestion();
            }
        }

        function nextQuestion(isSkip = false) {
            saveCurrentTextAnswer();
            if (currentQIdx < activeSession.questions.length - 1) {
                currentQIdx++;
                renderQuestion();
            }
        }

        function jumpToQuestion(idx) {
            saveCurrentTextAnswer();
            if (idx >= 0 && idx < activeSession.questions.length) {
                currentQIdx = idx;
                renderQuestion();
            }
        }

        function abandonInterview() {
            if (confirm(i18n[currentLang].abandonConfirm)) {
                activeSession = null;
                const navActive = document.getElementById('nav-active');
                navActive.disabled = true;
                navActive.classList.add('cursor-not-allowed', 'text-slate-400', 'dark:text-slate-500');
                switchView('new');
            }
        }

        async function finishInterview() {
            saveCurrentTextAnswer();
            const modal = document.getElementById('eval-modal');
            modal.classList.remove('hidden');

            const apiKey = localStorage.getItem('GEMINI_API_KEY') || '';

            try {
                const res = await fetch('/api/evaluate-interview', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session: activeSession,
                        userAnswers,
                        lang: currentLang,
                        apiKey
                    })
                });

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.error || `Evaluation error ${res.status}`);
                }

                const result = await res.json();
                activeSession.overallScore = result.overallScore;
                activeSession.summaryFeedback = result.summaryFeedback;
                activeSession.questionReviews = result.questionReviews || [];
                activeSession.userAnswers = userAnswers;
                activeSession.completed = true;

                await fetch('/api/save-session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(activeSession)
                });

                const navActive = document.getElementById('nav-active');
                navActive.disabled = true;
                navActive.classList.add('cursor-not-allowed', 'text-slate-400', 'dark:text-slate-500');

                switchView('saved');
            } catch (err) {
                alert('Error during final evaluation: ' + err.message);
            } finally {
                modal.classList.add('hidden');
            }
        }

        async function loadSavedSessions() {
            const list = document.getElementById('saved-list');
            const t = i18n[currentLang];

            try {
                const res = await fetch('/api/saved-sessions');
                const sessions = await res.json();

                if (!sessions || sessions.length === 0) {
                    list.innerHTML = `<div class="text-center py-12 text-slate-400 text-xs">${t.emptySavedMsg}</div>`;
                    return;
                }

                list.innerHTML = sessions.map((s, sIdx) => {
                    const score = s.overallScore || 0;
                    let scoreBadgeColor = score >= 75 ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : (score >= 50 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' : 'bg-rose-500/20 text-rose-400 border-rose-500/30');

                    const reviewsHtml = (s.questionReviews || []).map((rev, rIdx) => `
                        <div class="p-3.5 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700/80 space-y-2 text-xs">
                            <div class="flex justify-between items-start gap-2">
                                <span class="font-bold text-slate-900 dark:text-white">Q${rIdx + 1}: ${rev.questionText}</span>
                                <span class="font-mono font-bold px-2 py-0.5 rounded ${rev.score >= 70 ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-rose-500/20 text-rose-600 dark:text-rose-400'}">${rev.score}/100</span>
                            </div>
                            <div class="text-slate-600 dark:text-slate-300">
                                <strong>${t.yourAnswer}:</strong> <span class="font-mono">${rev.userAnswer || '<em>Skipped / None</em>'}</span>
                            </div>
                            ${rev.correctAnswer ? `<div class="text-emerald-600 dark:text-emerald-400"><strong>${t.correctAnswerLabel}:</strong> Option ${rev.correctAnswer}</div>` : ''}
                            <div class="text-slate-500 dark:text-slate-400 leading-relaxed">
                                <strong>${t.aiFeedbackLabel}:</strong> ${rev.feedback}
                            </div>
                            ${rev.suggestedAnswer ? `
                                <div class="p-2.5 bg-slate-50 dark:bg-slate-900 rounded-lg text-slate-600 dark:text-slate-300 font-mono text-[11px]">
                                    <strong>${t.idealAnswerLabel}:</strong> ${rev.suggestedAnswer}
                                </div>
                            ` : ''}
                        </div>
                    `).join('');

                    return `
                        <div class="p-5 bg-slate-50 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-700 rounded-2xl space-y-4">
                            <div class="flex flex-wrap justify-between items-center gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
                                <div>
                                    <h3 class="font-bold text-base text-slate-900 dark:text-white">${s.jobTitle}</h3>
                                    <div class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">${new Date(s.date).toLocaleString()} • <span class="uppercase font-semibold">${s.type}</span></div>
                                </div>
                                <div class="px-4 py-1.5 border rounded-xl font-bold text-sm ${scoreBadgeColor}">
                                    ${t.overallScoreLabel}: ${score}/100
                                </div>
                            </div>

                            ${s.summaryFeedback ? `
                                <div class="p-4 bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/50 rounded-xl space-y-1">
                                    <h4 class="text-xs font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5">
                                        <i class="fa-solid fa-chart-pie"></i> ${t.comprehensiveSummary}
                                    </h4>
                                    <p class="text-xs text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">${s.summaryFeedback}</p>
                                </div>
                            ` : ''}

                            ${reviewsHtml ? `
                                <div class="space-y-2">
                                    <h4 class="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">${t.individualBreakdown}</h4>
                                    <div class="space-y-2 max-h-96 overflow-y-auto pr-1">
                                        ${reviewsHtml}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    `;
                }).join('');
            } catch (err) {
                list.innerHTML = `<div class="text-center py-6 text-red-400 text-xs">Failed to load saved sessions: ${err.message}</div>`;
            }
        }

        async function clearHistory() {
            if (confirm(i18n[currentLang].clearConfirm)) {
                await fetch('/api/clear-sessions', { method: 'POST' });
                loadSavedSessions();
            }
        }

        // Initialize UI on page load
        document.addEventListener('DOMContentLoaded', () => {
            const savedKey = localStorage.getItem('GEMINI_API_KEY');
            if (savedKey) {
                document.getElementById('api-key-input').value = savedKey;
            }
            updateLangUI();
        });
    </script>
</body>
</html>"""

class PythonInterviewServer(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

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
        elif self.path == "/api/active-model":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "active_model": ACTIVE_GEMINI_MODEL,
                "available_models": ALL_GEMINI_MODELS
            }).encode('utf-8'))
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
        elif self.path == "/api/evaluate-interview":
            self.handle_evaluate_interview(data)
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

    def call_gemini_api(self, prompt, user_key=None, max_output_tokens=4096):
        global ACTIVE_GEMINI_MODEL
        api_key = (user_key or os.environ.get("GEMINI_API_KEY", "")).strip()
        if not api_key:
            raise Exception("No Gemini API key provided. Please enter your API key in the 'API Setup' tab.")

        # Build prioritized models list: try active remembered model first, then fallback to others
        models_to_try = [ACTIVE_GEMINI_MODEL] + [m for m in ALL_GEMINI_MODELS if m != ACTIVE_GEMINI_MODEL]

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": max_output_tokens,
                "temperature": 0.4
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
                        raise Exception(f"Model {model} returned an empty candidates list.")
                    
                    finish_reason = candidates[0].get('finishReason', '')
                    text_result = candidates[0]['content']['parts'][0]['text'].strip()
                    
                    if text_result.startswith("```json"):
                        text_result = text_result[7:]
                    elif text_result.startswith("```"):
                        text_result = text_result[3:]
                    if text_result.endswith("```"):
                        text_result = text_result[:-3]
                    text_result = text_result.strip()

                    # Verify it's valid JSON
                    try:
                        json.loads(text_result)
                        # Remember this successful model as default for future calls
                        if ACTIVE_GEMINI_MODEL != model:
                            print(f"[Gemini Model Switch] Successfully answered with {model}. Saving as default remembered model.")
                            ACTIVE_GEMINI_MODEL = model
                        return text_result
                    except json.JSONDecodeError:
                        # If truncated by token limit, try next model or raise
                        if finish_reason == "MAX_TOKENS":
                            print(f"[Gemini Fallback] Model {model} exceeded token limit. Trying next model...")
                            last_error = f"Model {model} hit token limit ({finish_reason})"
                            continue
                        raise
            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8', errors='ignore')
                try:
                    err_json = json.loads(err_body)
                    msg = err_json.get('error', {}).get('message', str(e))
                except Exception:
                    msg = str(e)

                if "API_KEY_INVALID" in msg or "API key not valid" in msg:
                    raise Exception(f"Invalid Gemini API Key: {msg}")

                print(f"[Gemini Fallback] Model {model} failed with HTTP {e.code}: {msg}. Trying next available model...")
                last_error = f"{model} ({e.code}): {msg}"
                continue
            except Exception as e:
                print(f"[Gemini Fallback] Model {model} exception: {e}. Trying next available model...")
                last_error = f"{model}: {str(e)}"
                continue

        raise Exception(f"All Gemini models were busy or unavailable. Last response: {last_error}")

    def handle_generate_questions(self, data):
        import time
        import random

        job_title = data.get('jobTitle', 'Professional Candidate')
        job_context = data.get('jobContext', '').strip()
        interview_type = data.get('type', 'multiple_choice')
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
            "multiple_choice": "Multiple Choice Quiz with 4 options (A, B, C, D) per question, exactly 1 right answer, a helpful hint, and a suggested model answer.",
            "free_writing": "Written Assessment & Open Problem Solving Exercises with helpful hints and suggested model answers.",
            "technical_interview": "Technical & Domain Knowledge Interview with hints and suggested model answers.",
            "hr_interview": "HR, Behavioral, Situational & Culture Fit Interview with hints and suggested model answers."
        }
        type_desc = type_descriptions.get(interview_type, "Standard Interview")

        if lang == "BG":
            lang_instruction = """STRICT LANGUAGE REQUIREMENT: EVERYTHING MUST BE WRITTEN IN BULGARIAN (български език).
All 10 question texts, option choices (Choice A, Choice B, Choice C, Choice D), hints ("hint"), and suggested model answers ("suggestedAnswer") MUST be written 100% in natural, professional Bulgarian language."""
        else:
            lang_instruction = """STRICT LANGUAGE REQUIREMENT: EVERYTHING MUST BE WRITTEN IN PROFESSIONAL ENGLISH."""

        prompt = f"""You are an executive interviewer conducting a professional interview for a candidate applying for '{job_title}'.
Interview Category: {interview_type} ({type_desc})
Random Variation Seed: {seed}
{context_prompt_part}
{lang_instruction}

CRITICAL REQUIREMENTS:
1. Generate EXACTLY 10 high-quality, relevant, and realistic interview questions tailored specifically for '{job_title}'.
2. If job posting text or URL is provided, analyze it thoroughly and generate questions directly testing those specific skills.
3. For EVERY question include:
   - "hint": A concise guiding hint (1-2 sentences).
   - "suggestedAnswer": A concise model answer (2-3 sentences).
4. For 'multiple_choice' type:
   - Include "options" array with exactly 4 choices (A, B, C, D).
   - Include "correctAnswer": String ("A", "B", "C", or "D") indicating the single correct choice.
5. For other types ('free_writing', 'technical_interview', 'hr_interview'), omit "options" and "correctAnswer".

Return ONLY a valid JSON object matching this schema:
{{
  "questions": [
    {{
      "id": "q1",
      "text": "Question text...",
      "type": "{interview_type}",
      "options": ["Choice A text", "Choice B text", "Choice C text", "Choice D text"],
      "correctAnswer": "A",
      "hint": "Guiding hint...",
      "suggestedAnswer": "Concise model answer..."
    }}
  ]
}}"""

        try:
            raw_text = self.call_gemini_api(prompt, api_key, max_output_tokens=3000)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(raw_text.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def handle_evaluate_interview(self, data):
        session = data.get('session', {})
        user_answers = data.get('userAnswers', {})
        lang = data.get('lang', 'EN')
        api_key = data.get('apiKey', '')

        job_title = session.get('jobTitle', 'Candidate')
        questions = session.get('questions', [])
        interview_type = session.get('type', 'multiple_choice')

        # Fast Instant Pre-Scoring for Multiple Choice Quiz
        is_all_mcq = (interview_type == 'multiple_choice') or all(q.get('type') == 'multiple_choice' for q in questions)
        
        if is_all_mcq:
            # Deterministic, ultra-fast 0ms exact calculation for MCQ
            question_reviews = []
            correct_count = 0
            total_count = len(questions)

            for idx, q in enumerate(questions):
                q_id = q.get('id', f'q{idx+1}')
                user_ans = user_answers.get(q_id, '')
                correct_ans = q.get('correctAnswer', 'A')
                is_correct = (user_ans == correct_ans) and (user_ans != '')

                if is_correct:
                    score = 100
                    correct_count += 1
                    feedback = "Правилен отговор! Избрахте точния верен вариант." if lang == "BG" else "Correct! You selected the accurate choice."
                elif not user_ans:
                    score = 0
                    feedback = f"Въпросът беше пропуснат. Верният отговор е Опция {correct_ans}." if lang == "BG" else f"Question was skipped. Correct answer is Option {correct_ans}."
                else:
                    score = 0
                    feedback = f"Неточен избор. Избрахте {user_ans}, а верният отговор е Опция {correct_ans}." if lang == "BG" else f"Incorrect choice. You selected {user_ans}; the correct option is {correct_ans}."

                question_reviews.append({
                    "id": q_id,
                    "questionText": q.get('text', ''),
                    "userAnswer": user_ans or ('Пропуснат' if lang == 'BG' else 'Skipped'),
                    "correctAnswer": correct_ans,
                    "score": score,
                    "feedback": feedback,
                    "suggestedAnswer": q.get('suggestedAnswer', '')
                })

            overall_score = round((correct_count / total_count) * 100) if total_count > 0 else 0

            # Generate concise executive summary in under 1 second
            if lang == "BG":
                summary_prompt = f"""Напиши кратко, структурирано обобщение (3-4 изречения) за представянето на кандидат за позиция '{job_title}'.
Общ резултат от теста: {overall_score}/100 ({correct_count} от {total_count} верни въпроса).
Върни САМО JSON: {{"summaryFeedback": "Обобщен текст с препоръки..."}}"""
            else:
                summary_prompt = f"""Write a concise, professional executive summary (3-4 sentences) evaluating a candidate applying for '{job_title}'.
Quiz Score: {overall_score}/100 ({correct_count} out of {total_count} correct questions).
Return ONLY JSON: {{"summaryFeedback": "Summary feedback and key recommendations..."}}"""

            try:
                raw_summary = self.call_gemini_api(summary_prompt, api_key, max_output_tokens=500)
                summary_data = json.loads(raw_summary)
                summary_text = summary_data.get('summaryFeedback', '')
            except Exception:
                if lang == "BG":
                    summary_text = f"Кандидатът завърши теста за позиция '{job_title}' с резултат {overall_score}/100 ({correct_count} от {total_count} верни отговора). Препоръчва се преговор на сгрешените въпроси за затвърждаване на знанията."
                else:
                    summary_text = f"Candidate completed the assessment for '{job_title}' with a score of {overall_score}/100 ({correct_count} of {total_count} correct). Review incorrect responses to reinforce core concepts."

            response_payload = {
                "overallScore": overall_score,
                "summaryFeedback": summary_text,
                "questionReviews": question_reviews
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_payload, ensure_ascii=False).encode('utf-8'))
            return

        # For Free Writing / Open Technical Interviews
        qa_pairs = []
        for idx, q in enumerate(questions):
            ans = user_answers.get(q.get('id', f'q{idx+1}'), 'Skipped')
            qa_pairs.append({
                "number": idx + 1,
                "id": q.get('id', f'q{idx+1}'),
                "question": q.get('text', ''),
                "userAnswer": ans[:400]
            })

        if lang == "BG":
            prompt = f"""Оцени следното писмено интервю за '{job_title}'. Бъди кратък и прецизен.
Всичко на БЪЛГАРСКИ.
Данни: {json.dumps(qa_pairs, ensure_ascii=False)}
Върни САМО валиден JSON:
{{
  "overallScore": 80,
  "summaryFeedback": "Кратко обобщение (3-4 изречения)...",
  "questionReviews": [
    {{
      "id": "q1",
      "questionText": "Въпрос...",
      "userAnswer": "Отговор...",
      "score": 85,
      "feedback": "Кратка обратна връзка (1-2 изречения)...",
      "suggestedAnswer": "Примерен верен отговор..."
    }}
  ]
}}"""
        else:
            prompt = f"""Evaluate this written interview for '{job_title}'. Be concise and direct.
Interview Data: {json.dumps(qa_pairs, ensure_ascii=False)}
Return ONLY valid JSON:
{{
  "overallScore": 80,
  "summaryFeedback": "Concise summary evaluation (3-4 sentences)...",
  "questionReviews": [
    {{
      "id": "q1",
      "questionText": "Question...",
      "userAnswer": "Answer...",
      "score": 85,
      "feedback": "Concise feedback (1-2 sentences)...",
      "suggestedAnswer": "Model ideal answer..."
    }}
  ]
}}"""

        try:
            raw_text = self.call_gemini_api(prompt, api_key, max_output_tokens=2500)
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

if __name__ == '__main__':
    run_server()
