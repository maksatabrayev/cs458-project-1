# ARES — AI-Driven Resilient & Evolutionary Authentication System

**CS458 Software Verification & Validation — Project 1**

## Overview

ARES is an autonomous self-healing authentication system built with:
1. **Login Portal** — Modern web login with Email/Phone + Password and Social Auth (Google/Facebook)
2. **Context-Aware Security** — Risk score engine + Gemini LLM fraud analysis
3. **Self-Healing Selenium Framework** — Tests that auto-recover from broken selectors using heuristic scoring and LLM-based repair
4. **5 Advanced Test Scenarios** — Dynamic ID recovery, multimodal failure, cross-browser, social auth, rate limiting

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (React), Vanilla CSS |
| Auth | NextAuth.js (Google, Facebook, Credentials) |
| LLM | Google Gemini 2.0 Flash API |
| Testing | Python 3.9+ / Selenium / pytest |
| Database | In-memory (no external DB needed) |

## Project Structure

```
ares-auth/
├── app/                              # Next.js App (Frontend + API)
│   ├── page.js                       # Login page
│   ├── layout.js                     # Root layout with SessionProvider
│   ├── providers.js                  # NextAuth SessionProvider wrapper
│   ├── globals.css                   # Global styles (dark theme, glassmorphism)
│   ├── dashboard/page.js             # Post-login dashboard
│   └── api/
│       ├── auth/[...nextauth]/route.js  # NextAuth config
│       ├── login/route.js               # Login with risk assessment
│       ├── heal/route.js                # Self-healing selector repair
│       ├── risk-assessment/route.js     # Risk scoring API
│       └── reset-account/route.js       # Reset locked accounts
├── lib/                              # Shared libraries
│   ├── users.js                      # User store & account state machine
│   ├── riskEngine.js                 # Risk score calculation (5 factors)
│   └── llmClient.js                  # Gemini LLM client
├── tests/                            # Self-Healing Selenium Tests (Python)
│   ├── conftest.py                   # Pytest fixtures
│   ├── self_healing.py               # Core SelfHealingDriver
│   ├── llm_repair.py                 # LLM selector repair module
│   ├── heuristic_scorer.py           # Heuristic element matching
│   ├── shadow_dom.py                 # Shadow DOM MutationObserver
│   ├── requirements.txt              # Python dependencies
│   ├── test_dynamic_id.py            # Test 1: Dynamic ID Recovery
│   ├── test_multimodal_failure.py    # Test 2: Popup obscuring elements
│   ├── test_cross_browser.py         # Test 3: CSS breakage resilience
│   ├── test_social_auth.py           # Test 4: OAuth handshake flow
│   └── test_rate_limiting.py         # Test 5: Brute force simulation
├── .env.example                      # Environment variable template
├── .gitignore                        # Git ignore rules
└── package.json                      # Node.js dependencies
```

## Quick Start

### Prerequisites
- **Node.js 18+** — [Download](https://nodejs.org/)
- **Python 3.9+** — [Download](https://www.python.org/)
- **Google Chrome** — [Download](https://www.google.com/chrome/)
- **Gemini API Key** — [Get one free](https://aistudio.google.com/apikey)

### 1. Clone and Install

```bash
git clone https://github.com/maksatabrayev/cs458-project-1.git
cd cs458-project-1/ares-auth
npm install
```

### 2. Configure Environment Variables

```bash
cp .env.example .env.local
```

Edit `.env.local` and fill in your API keys:

```env
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=any-random-string-at-least-32-characters-long
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLIENT_ID=your_google_oauth_id       # Optional for now
GOOGLE_CLIENT_SECRET=your_google_secret      # Optional for now
FACEBOOK_CLIENT_ID=your_facebook_id          # Optional for now
FACEBOOK_CLIENT_SECRET=your_facebook_secret  # Optional for now
```

> **Note:** Social login buttons will redirect to NextAuth's default page if OAuth credentials aren't configured. The Gemini API key is required for the self-healing framework and fraud analysis.

### 3. Run the Web App

```bash
npm run dev
```

Open **http://localhost:3000** in your browser.

### 4. Run Selenium Tests

```bash
cd tests
pip install -r requirements.txt
```

Run tests **one file at a time** (to avoid Gemini free tier rate limits):

```bash
pytest test_rate_limiting.py -v          # API tests (no browser needed)
pytest test_dynamic_id.py -v             # Self-healing ID changes
pytest test_social_auth.py -v            # OAuth redirect flow
pytest test_cross_browser.py -v          # CSS breakage resilience
pytest test_multimodal_failure.py -v     # Popup handling
```

> **Important:** Gemini free tier has a rate limit of ~15 requests/minute. Wait **1-2 minutes** between test files. Tests that change element IDs use the LLM to find new selectors — if rate limited, those specific sub-tests will fail with `429 Too Many Requests`. The heuristic scorer handles most cases without LLM, but when 3+ elements change simultaneously, the LLM is needed.

## Test Accounts

| Email | Password | Role |
|-------|----------|------|
| testuser@ares.com | Test@1234 | Regular User |
| admin@ares.com | Admin@5678 | Admin User |

## Account State Machine

```
Active → (5 fails) → Challenged → (10 fails) → Locked → (15 fails) → Suspended
```

To reset a locked account, restart the server (`Ctrl+C` + `npm run dev`), or POST:
```bash
curl -X POST http://localhost:3000/api/reset-account -H "Content-Type: application/json" -d '{"email":"testuser@ares.com"}'
```

## Self-Healing Mechanism

```
findElement("login-btn") → NOT FOUND
  ↓
1. Heuristic Scoring (no LLM call)
   Compare tag, text, position, size, parent → score > 0.6? → USE IT
  ↓ (if below threshold)
2. LLM Repair (Gemini API)
   Send DOM + old selector → get new CSS/XPath → validate → USE IT
  ↓
3. Log healing event for developer review
```

## Risk Assessment Factors

| Factor | Weight | Trigger |
|--------|--------|---------|
| Unknown IP | +25 | IP not in user's known list |
| Failed Attempts | +8/attempt | Cumulative failed logins |
| IP Rate Limit | +15 | >10 attempts from same IP |
| Unusual Time | +10 | Login between 2-5 AM |
| Account Status | +20 | Non-active account state |

Risk > 60 triggers LLM fraud analysis via Gemini.

## Team

CS458 — Group Project, Bilkent University
