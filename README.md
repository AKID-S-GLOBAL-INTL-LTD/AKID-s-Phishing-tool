# AKID Phishing Simulation Toolkit
### AKID Global Cybersecurity Portfolio Tool

---

## Legal Notice
This tool is for **authorized security testing only**.  
Only use against systems you own or have explicit written permission to test.  
Every cloned page includes a visible AKID simulation banner.

---

## Features
- Campaign Manager — create, launch, pause campaigns
- Email Templates — write, import (.html/.txt/.eml), manage templates
- Page Cloner — clone any web page with asset rewriting + injection
- Link Tracking — unique /sim/<id> URL per campaign logs every click
- Form Capture — JS injection captures form field names on cloned pages
- Live Dashboard — real-time stats: clicks, submissions, click-rate
- Event Log — full filterable log with IP hash + user agent

---

## Setup

```bash
pip install flask
cd akid-phishing-tool
python app.py
# Open http://localhost:5050
```

---

## Workflow

1. **Clone** — Page Cloner tab, enter URL, click Clone Page
2. **Campaign** — New Campaign, fill details, paste clone filename
3. **Launch** — Click ▶ Launch, copy the tracking URL
4. **Monitor** — Tracking Log shows every click and submission live

---

## File Structure
```
akid-phishing-tool/
├── app.py               # Flask backend
├── requirements.txt
├── templates/
│   └── index.html       # Dashboard UI
├── cloned_pages/        # Saved clone files
├── uploads/templates/   # Uploaded template files
└── data/
    └── data.json        # Campaign/template/event data
```

---

*AKID Global · Ethical Cybersecurity Portfolio · 2024*
