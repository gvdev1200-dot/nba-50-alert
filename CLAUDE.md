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
| **EmailOctopus** | Email subscriptions + alerts | Embedded form + campaign sending |
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
4. Sends email campaign to all EmailOctopus subscribers
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
EMAILOCTOPUS_API_KEY   - EmailOctopus API key
EMAILOCTOPUS_LIST_ID   - EmailOctopus list ID for subscribers
SENDER_EMAIL           - Verified sender email in EmailOctopus
```

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

## Recent Changes (2025-11-27)

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
