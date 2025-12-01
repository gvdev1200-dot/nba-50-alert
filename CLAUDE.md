# NBA 50-Point Alert Project

## Project Summary
A website that notifies users when an NBA player scores 50+ points, which activates the DoorDash "NBA50" promo code giving DashPass members 50% off (up to $10 savings). The site displays live promo status, shows all 50+ scorers this season, and allows users to subscribe for email alerts.

**Live site**: https://gvdev1200-dot.github.io/nba-50-alert/

---

## Core Principle: Full Automation
**We ALWAYS use automations - no manual work at all.**

---

## Services We Use

| Service | Purpose | Details |
|---------|---------|---------|
| **GitHub Pages** | Website hosting | Auto-deploys on push to main |
| **GitHub Actions** | Daily data updates | Runs at 2 AM UTC daily |
| **EmailOctopus** | Email subscriptions + alerts | Embedded form + Automations API |
| **Web3Forms** | Contact form only | Key is public (designed for client-side) |
| **ESPN API** | NBA scores data | Free, no key needed |

### Services We DO NOT Use:
- Google Apps Script - never use
- Google Sheets - never use
- SendGrid - replaced by EmailOctopus
- Any manual processes

---

## Website Features (All Working)

| Feature | Status | Notes |
|---------|--------|-------|
| Live promo status banner | Done | Shows if promo is active today |
| Click-to-copy promo code | Done | Click NBA50 to copy |
| 50+ Club sidebar | Done | All scorers this season |
| Last updated timestamp | Done | Shows when data was refreshed |
| Subscribe form | Done | EmailOctopus embedded form |
| Contact form | Done | Web3Forms - emails you messages |
| Smooth scroll | Done | "Got ideas?" link scrolls to contact |
| Mobile responsive | Done | Works on all screen sizes |
| Open source footer | Done | Links to GitHub repo |

---

## How It Works

### Daily Flow (Automated):
1. **2 AM UTC**: GitHub Actions runs `update-50-club-data.yml`
2. Fetches yesterday's NBA scores from ESPN API
3. If any player scored 50+, updates `data/50_club.json`
4. Triggers EmailOctopus automation for all subscribers (sends alert email)
5. Commits changes back to repo
6. GitHub Pages auto-deploys updated site

### User Subscription Flow:
1. User enters email on website (EmailOctopus embedded form)
2. EmailOctopus adds them directly to the list
3. User automatically receives alerts when promo is active
4. Unsubscribe link in every email (handled by EmailOctopus)

### Contact Form Flow:
1. User fills out contact form
2. Web3Forms sends YOU an email with the message
3. Reply directly to the user's email

---

## Data Files

### `data/50_club.json`
```json
{
  "season": "2025-26",
  "lastUpdated": "2025-11-27T...",
  "lastCheckedDate": "2025-11-27",
  "totalGames": 289,
  "scorers": [...]
}
```

### `data/emails.json`
```json
{
  "sent_alerts": ["2025-11-22_James Harden_55"]
}
```
Note: Only tracks sent alerts. Subscribers are stored in EmailOctopus.

---

## GitHub Secrets Required
```
EMAILOCTOPUS_API_KEY       - EmailOctopus API key
EMAILOCTOPUS_LIST_ID       - EmailOctopus list ID for subscribers
EMAILOCTOPUS_AUTOMATION_ID - Automation ID (from dashboard URL)
```

## EmailOctopus Automation Setup

1. Go to EmailOctopus dashboard > Automations
2. Create new automation with trigger: **"Started via API"**
3. Add email step with this content:
   - Subject: "DoorDash 50% OFF is Active Today!"
   - Body: Generic alert that links to website for details
4. Copy automation ID from URL: `emailoctopus.com/automations/<AUTOMATION_ID>`
5. Add as GitHub secret: `EMAILOCTOPUS_AUTOMATION_ID`

---

## File Structure
```
nba-50-alert/
├── .github/workflows/
│   └── update-50-club-data.yml    # Daily automation
├── data/
│   ├── 50_club.json               # Scorers + stats
│   └── emails.json                # Sent alerts history
├── src/
│   ├── generate_50_club_data.py   # Updates 50_club.json
│   └── send_email_alerts.py       # EmailOctopus email sender
├── index.html                     # Main website
├── unsubscribe.html               # Unsubscribe page (redirects to EmailOctopus)
├── doordash-promo.jpg             # Promo image
├── CLAUDE.md                      # THIS FILE - project context
├── LICENSE                        # MIT License
└── README.md                      # Public readme
```

---

## Quick Commands

```bash
# Run data generator manually
py src/generate_50_club_data.py

# Open the website locally
start index.html

# Check git status
git status
```

---

## Development Rules

1. **Never use Google Apps Script** - everything via GitHub Actions
2. **Never require manual intervention** - automate everything
3. **Use existing services** - EmailOctopus, Web3Forms, GitHub
4. **Keep it simple** - static site, JSON data, scheduled workflows
5. **Update this CLAUDE.md** - when making significant changes

---

## Email Alert Safety Features

The email sender has multiple protections to **prevent ALL types of false alarms**:

### Type 1: Duplicate Alerts (same game twice)
| Protection | How it prevents duplicates |
|------------|---------------------------|
| **Concurrency control** | Workflow prevents duplicate runs from overlapping |
| **Git push retry (3x)** | Ensures sent alerts are recorded even if push fails |
| **File corruption detection** | Exits if emails.json corrupted (won't re-send everything) |
| **Atomic file saves** | Uses os.replace() to prevent partial writes |
| **MIN_SUCCESS_RATE = 95%** | Won't mark as "sent" unless 95%+ succeed |

### Type 2: Old Alerts (promo already expired)
| Protection | How it prevents old alerts |
|------------|---------------------------|
| **MAX_ALERT_AGE_DAYS = 1** | Only alerts for games from yesterday (promo active today) |
| **Season date validation** | Rejects games from before current season started |

### Type 3: True False Alarms (no 50+ game happened)
| Protection | How it prevents fake alerts |
|------------|---------------------------|
| **Points validation** | Must be integer, 50-100 range (NBA record is 100) |
| **Date validation** | Must be valid format, not in future, within season |
| **Team validation** | Must be valid NBA team abbreviation |
| **Required fields check** | Player, date, team, points all required |
| **ESPN as only source** | Data comes directly from ESPN API (trusted) |

**Design principle:** Better to miss an alert than send a false alarm.

---

## Recent Changes

### 2025-11-30
- **Priority: Prevent ALL false alarms** - Added comprehensive safety features
- **Duplicates prevention:**
  - Added concurrency control to prevent duplicate workflow runs
  - Added git push retry (3 attempts) to prevent duplicates after push failure
  - Increased MIN_SUCCESS_RATE from 80% to 95%
  - Added ALREADY_STARTED detection (catches misconfigured automation)
  - Changed to atomic file writes using os.replace()
  - Added file corruption detection and backup
  - API failures no longer mark alerts as sent
- **Old alerts prevention:**
  - Changed MAX_ALERT_AGE_DAYS from 7 to 1 (promo only active day after game)
  - Added season date validation (rejects games from before season)
- **True false alarms prevention:**
  - Added scorer validation (points 50-100, valid date, valid team, required fields)
  - Points > 100 rejected as data corruption (NBA record is 100)
  - Future dates rejected
  - Pre-season dates rejected
- **Other improvements:**
  - Changed workflow time from 2 AM to 6 AM UTC (catches late West Coast games)
  - Added workflow timeout (30 minutes)
  - Added validation steps for both JSON files in workflow
  - Added retry logic with exponential backoff

### 2025-11-29
- Switched from EmailOctopus Campaigns API to Automations API
- Campaigns API was deprecated/removed (returned 405 error)
- Now requires EMAILOCTOPUS_AUTOMATION_ID secret
- Email content is now static (defined in EmailOctopus dashboard)

### 2025-11-27
- Redesigned website for compact layout
- Added live promo status banner
- Added click-to-copy promo code
- Added contact form with Web3Forms
- Improved mobile responsiveness
- Migrated from SendGrid to EmailOctopus for email alerts
- Subscribe form now uses EmailOctopus embedded form
- Added MIT license (open source)
- Added GitHub link in footer
- Cleaned up project structure (removed /website folder, deprecated files)
