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
| **EmailOctopus** | Email subscriptions + alerts | Handles both subscribe form AND sending alerts |
| **Web3Forms** | Contact form only | Key: `e991c9d7-f928-4722-a9ea-ba20f35a4326` |
| **ESPN API** | NBA scores data | Free, no key needed |

### Services We DO NOT Use:
- ❌ Google Apps Script - never use
- ❌ Google Sheets - never use
- ❌ SendGrid - replaced by EmailOctopus
- ❌ Any manual processes

---

## Website Features (All Working ✅)

| Feature | Status | Notes |
|---------|--------|-------|
| Live promo status banner | ✅ | Shows if promo is active today |
| Click-to-copy promo code | ✅ | Click NBA50 to copy |
| 50+ Club sidebar | ✅ | All scorers this season |
| Last updated timestamp | ✅ | Shows when data was refreshed |
| Subscriber count | ✅ | Dynamic from EmailOctopus |
| Subscribe form | ✅ | EmailOctopus - direct subscription |
| Contact form | ✅ | Web3Forms - emails you messages |
| Smooth scroll | ✅ | "Got ideas?" link scrolls to contact |
| Mobile responsive | ✅ | Works on all screen sizes |

---

## How It Works

### Daily Flow (Automated):
1. **2 AM UTC**: GitHub Actions runs `update-50-club-data.yml`
2. Fetches yesterday's NBA scores from ESPN API
3. If any player scored 50+, updates `data/50_club.json`
4. Sends email campaign to all EmailOctopus subscribers
5. Commits changes back to repo
6. GitHub Pages auto-deploys updated site

### User Subscription Flow:
1. User enters email on website
2. EmailOctopus API adds them directly to the list
3. User automatically receives alerts when promo is active
4. **No manual work needed!**

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
  "subscriberCount": 0,
  "scorers": [...]
}
```

### `data/emails.json`
```json
{
  "sent_alerts": ["2025-11-22_James Harden_55"]
}
```
Note: `emails.json` only tracks sent alerts now. Subscribers are stored in EmailOctopus.

---

## GitHub Secrets Required
```
EMAILOCTOPUS_API_KEY   - EmailOctopus API key
EMAILOCTOPUS_LIST_ID   - EmailOctopus list ID for subscribers
```

---

## EmailOctopus Setup

### API Credentials (stored in GitHub Secrets):
- **API Key**: Set as `EMAILOCTOPUS_API_KEY` secret
- **List ID**: Set as `EMAILOCTOPUS_LIST_ID` secret

### Website Integration:
The subscribe form in `website/index.html` uses EmailOctopus embedded form API:
```javascript
const EMAILOCTOPUS_LIST_ID = '571d8d58-cc23-11f0-aeb6-6fbbc4d23873';
// Posts to: https://emailoctopus.com/lists/{LIST_ID}/members/embedded/1.3/add
```

### Email Alerts:
The `src/send_email_alerts.py` script:
1. Gets subscriber count from EmailOctopus API
2. Creates a campaign with promo details
3. Sends to all subscribers in the list

---

## File Structure
```
Doordash-50points/
├── .github/workflows/
│   └── update-50-club-data.yml    # Daily automation
├── data/
│   ├── 50_club.json               # Scorers + stats
│   └── emails.json                # Sent alerts history
├── src/
│   ├── nba_50_checker.py          # CLI checker (manual use)
│   ├── generate_50_club_data.py   # Updates 50_club.json
│   └── send_email_alerts.py       # EmailOctopus email sender
├── website/
│   ├── index.html                 # Main website
│   ├── unsubscribe.html           # Unsubscribe page
│   └── data/                      # Symlink to ../data
├── CLAUDE.md                      # THIS FILE - project context
└── README.md                      # Public readme
```

---

## Quick Commands

```bash
# Run NBA checker manually
py Doordash-50points/src/nba_50_checker.py

# Open the website locally
start Doordash-50points/website/index.html

# Check git status
git -C Doordash-50points status
```

---

## Development Rules

1. **Never use Google Apps Script** - everything via GitHub Actions
2. **Never require manual intervention** - automate everything
3. **Use existing services** - EmailOctopus, Web3Forms, GitHub
4. **Keep it simple** - static site, JSON data, scheduled workflows
5. **Update this CLAUDE.md** - when making significant changes

---

## Recent Changes (2025-11-27)

- ✅ Redesigned website for compact layout
- ✅ Added live promo status banner
- ✅ Added click-to-copy promo code
- ✅ Added subscriber count display
- ✅ Added last updated timestamp
- ✅ Added contact form with Web3Forms
- ✅ Improved mobile responsiveness
- ✅ Removed old backup files
- ✅ **Migrated from SendGrid to EmailOctopus** for email alerts
- ✅ **Subscribe form now uses EmailOctopus directly** (no manual work needed)
- ✅ Updated GitHub Actions workflow for EmailOctopus
- ✅ Updated CLAUDE.md with full project context
