# DoorDash 50 Points Tracker

Automatically detects when NBA players score 50+ points to notify you about the DoorDash 50% OFF promotion.

## What Does This Do?

When any NBA player scores 50+ points in a game, DoorDash gives DashPass members 50% off (up to $10) the next day using code **NBA50**. This script automatically checks for those games so you never miss the promotion!

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main checker
python src/nba_50_checker.py

# Run tests
python tests/test_specific_date.py
```

## Project Structure

```
doordash50points/
├── src/                      # Main Python script
│   └── nba_50_checker.py    # Core checker with email notifications
├── tests/                    # Test scripts
├── docs/                     # Documentation and guides
├── google-apps-script/       # Automated Google Apps Script versions
├── website/                  # Web interface (optional)
├── archive/                  # Old versions and debug scripts
├── requirements.txt          # Python dependencies
└── config.json.example       # Configuration template
```

## How to Use

### Quick Test (Recommended First Step)

Test with specific dates from the 2024-25 season:

```bash
python tests/test_specific_date.py
```

### Check Yesterday's Games

Run the main script to check if anyone scored 50+ yesterday:

```bash
python src/nba_50_checker.py
```

### Automated Daily Checks

For automated notifications, see:
- `google-apps-script/` - Runs automatically via Google Apps Script
- `docs/QUICK_START.md` - Setup instructions

## Example Output

When a 50+ point game is found:

```
============================================================
RESULTS
============================================================

*** DoorDash 50% OFF promotion is ACTIVE today! ***

  * De'Aaron Fox (SAC) - 60 POINTS!

------------------------------------------------------------
Email notification would be sent:
------------------------------------------------------------

  Subject: DoorDash 50% OFF Today! - NBA50

  Body:
  De'Aaron Fox scored 60 points last night!

  Use code: NBA50
  Valid today until 11:59 PM PT
  Save 50% off (up to $10) on DoorDash delivery
```

When NO 50+ point games found:

```
No 50+ point performances yesterday.
No email would be sent (avoiding spam).
```

## Requirements

- Python 3.7 or higher (You have Python 3.13 ✓)
- `requests` library (installed via `pip install -r requirements.txt`)

## How It Works

1. **Efficient**: Only checks completed games (no wasted API calls)
2. **Accurate**: Uses official NBA Stats API (same data as NBA.com)
3. **Smart**: Checks actual box scores, not news articles
4. **Fast**: Typically completes in 10-30 seconds depending on number of games

## API Details

- **Source**: stats.nba.com (official NBA stats)
- **Endpoints Used**:
  - `scoreboardV2` - Gets game schedule and status
  - `boxscoretraditionalv2` - Gets player statistics
- **Rate Limits**: No authentication needed, reasonable rate limits
- **Reliability**: Very stable, same API used by NBA.com

## Next Steps

Once you verify the core functionality is working (which it is!), we can add:

1. **Automated Scheduling**
   - Google Apps Script (runs automatically every day)
   - Or GitHub Actions (runs in the cloud)

2. **Email Notifications**
   - Send you an email at 8 AM when the promo is active
   - Include player names and promo code

3. **Multiple Recipients** (Optional for future)
   - Google Form for signup
   - Send to distribution list

## Notes

- 50-point games are rare (only ~15-20 per NBA season)
- The script handles dates during the off-season gracefully
- No email spam - only notifies when 50+ points actually happened
- The promotion is valid the day AFTER a 50-point game
