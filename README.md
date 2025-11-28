# NBA 50-Point Alert

**Never miss DoorDash's 50% OFF promo again!**

When any NBA player scores 50+ points, DoorDash gives DashPass members **50% off (up to $10)** the next day using code **NBA50**. This project automatically tracks those games and emails you when the promo is active.

**Live site:** https://gvdev1200-dot.github.io/nba-50-alert/

---

## How It Works

1. An NBA player scores 50+ points in a game
2. The next morning, you get an email alert
3. Use code **NBA50** on DoorDash for 50% off

**Promo timing:** Valid from 9:00 AM PT until 11:59 PM PT the day after the 50-point game.

---

## Features

- **Automatic email alerts** - Get notified the morning the promo is active
- **Live promo status** - Website shows if promo is active today
- **50+ Club tracker** - See all 50-point performances this season
- **Click-to-copy promo code** - One click to copy NBA50
- **100% free** - No cost, no spam, unsubscribe anytime

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Website | Static HTML/CSS/JS on GitHub Pages |
| Email alerts | EmailOctopus |
| Daily automation | GitHub Actions (runs at 2 AM UTC) |
| NBA data | ESPN API |
| Contact form | Web3Forms |

---

## Project Structure

```
nba-50-alert/
├── index.html                     # Main website
├── unsubscribe.html               # Unsubscribe page
├── doordash-promo.jpg             # Promo image
├── data/
│   ├── 50_club.json               # All 50+ scorers this season
│   └── emails.json                # Sent alerts history
├── src/
│   ├── generate_50_club_data.py   # Fetches NBA data from ESPN
│   └── send_email_alerts.py       # Sends email campaigns
├── .github/workflows/
│   └── update-50-club-data.yml    # Daily automation
├── LICENSE                        # MIT License
└── README.md                      # This file
```

---

## Contributing

This project is open source under the MIT License. Contributions welcome!

Ideas for contributions:
- Add SMS notifications
- Support other sports/promos
- Improve the design
- Add more stats/analytics

To contribute:
1. Fork this repo
2. Make your changes
3. Submit a pull request

---

## Local Development

```bash
# Clone the repo
git clone https://github.com/gvdev1200-dot/nba-50-alert.git
cd nba-50-alert

# Install Python dependencies
pip install -r requirements.txt

# Run the data generator manually
python src/generate_50_club_data.py

# Open the website locally
open index.html  # or just double-click it
```

---

## License

MIT License - see [LICENSE](LICENSE) file.

---

## Author

Built by [@gvdev1200-dot](https://github.com/gvdev1200-dot)

*Not affiliated with DoorDash or the NBA.*
