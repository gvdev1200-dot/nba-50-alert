# Email Alert System Guide

## Overview

Fully automated email alert system that notifies subscribers when NBA players score 50+ points (activating the DoorDash promo).

## Architecture

**Components:**
1. **Email Storage** (`website/data/emails.json`) - Stores subscriber emails
2. **Email Sender** (`src/send_email_alerts.py`) - Sends alerts via SendGrid
3. **Subscriber Manager** (`src/manage_subscribers.py`) - Add/remove subscribers
4. **GitHub Actions** (`.github/workflows/update-50-club-data.yml`) - Automation
5. **Unsubscribe Page** (`website/unsubscribe.html`) - Self-service unsubscribe

## How It Works

### Daily Automated Flow

**Every day at 2 AM UTC**, GitHub Actions automatically:

1. ✅ Checks for new 50+ point games (via `generate_50_club_data.py`)
2. ✅ If new 50+ games found:
   - Sends email alerts to all subscribers (via `send_email_alerts.py`)
   - Includes player name, points, and promo code NBA50
   - Includes unsubscribe link
3. ✅ Commits updated data (50_club.json and emails.json)
4. ✅ GitHub Pages auto-deploys changes

**Zero manual work required!**

## Email Storage Format

```json
{
  "subscribers": [
    {
      "email": "user@example.com",
      "subscribed_date": "2025-11-27T10:30:00",
      "unsubscribe_token": "uuid-here"
    }
  ],
  "sent_alerts": [
    "2025-11-22_James Harden_55",
    "2025-11-21_Tyrese Maxey_54"
  ]
}
```

## Managing Subscribers

### Add a Subscriber

```bash
python src/manage_subscribers.py add email@example.com
```

### Remove a Subscriber

```bash
python src/manage_subscribers.py remove email@example.com
```

### Remove by Unsubscribe Token

```bash
python src/manage_subscribers.py remove-token abc-123-def
```

### List All Subscribers

```bash
python src/manage_subscribers.py list
```

## How Users Subscribe

### Current Method (Temporary)

1. User fills out form on website
2. Form uses Google Apps Script OR Formspree
3. You receive email notification
4. Manually add subscriber using: `python src/manage_subscribers.py add email@example.com`

### Future Automation (Optional)

Can integrate form directly with GitHub API to auto-add subscribers (requires additional development).

## How Users Unsubscribe

1. Click unsubscribe link in email
2. Opens `unsubscribe.html?token=xxx`
3. User clicks "Unsubscribe" button
4. **Temporary**: User emails you with token
5. You run: `python src/manage_subscribers.py remove-token xxx`

**Future**: Can automate unsubscribe via GitHub API.

## SendGrid Configuration

### Required Secrets (Already Set Up)

In GitHub repository settings → Secrets → Actions:
- `SENDGRID_API_KEY` - Your SendGrid API key
- `SENDER_EMAIL` - gvdev1200@gmail.com (verified sender)

### Email Features

- ✅ Professional HTML template
- ✅ Shows all new 50+ scorers since last alert
- ✅ Includes NBA50 promo code prominently
- ✅ Instructions on how to use the promo
- ✅ Unsubscribe link (required by law)
- ✅ Mobile-responsive design

### SendGrid Free Tier Limits

- 100 emails/day
- Perfect for <100 subscribers
- Includes analytics and bounce tracking

## Testing the Email System

### Test Locally (Without Sending Emails)

```bash
# 1. Add test subscriber
python src/manage_subscribers.py add your-test-email@gmail.com

# 2. Check subscriber was added
python src/manage_subscribers.py list

# 3. Run email sender (requires API keys as environment variables)
set SENDGRID_API_KEY=your-key-here
set SENDER_EMAIL=gvdev1200@gmail.com
python src/send_email_alerts.py
```

### Test in GitHub Actions

1. Go to repository Actions tab
2. Select "Update 50+ Club Data" workflow
3. Click "Run workflow"
4. Watch it run in real-time
5. Check your email for alert

## Troubleshooting

### Emails Not Sending

1. Check GitHub Actions logs for errors
2. Verify SENDGRID_API_KEY and SENDER_EMAIL secrets are set
3. Verify sender email is verified in SendGrid
4. Check SendGrid dashboard for delivery stats

### Emails Going to Spam

1. Ask subscribers to whitelist gvdev1200@gmail.com
2. Consider upgrading to custom domain for better deliverability
3. Check SendGrid's spam score in dashboard

### Duplicate Alerts

The system prevents duplicates by tracking sent_alerts in emails.json:
- Each 50+ performance gets unique key: `date_player_points`
- Only sends alert if key not in sent_alerts list
- Updates sent_alerts after sending

### Unsubscribe Not Working

Current system requires manual processing:
1. User emails you with token
2. You run: `python src/manage_subscribers.py remove-token <token>`

## Cost Breakdown

- **SendGrid**: $0 (free tier, 100 emails/day)
- **GitHub Actions**: $0 (included in free tier)
- **GitHub Pages**: $0 (free for public repos)
- **Total Cost**: $0/month

## Future Enhancements (Optional)

1. **Automated Form Submissions** - Integrate form with GitHub API to auto-add subscribers
2. **Automated Unsubscribe** - API endpoint to remove subscribers without manual work
3. **Custom Domain** - Better email deliverability (costs ~$10/year)
4. **Email Analytics** - Track open rates, click rates
5. **Welcome Email** - Send confirmation when users subscribe
6. **Preference Center** - Let users choose alert frequency

## Security Notes

- API keys stored in GitHub Secrets (encrypted)
- Never commit API keys to repository
- Unsubscribe tokens are UUIDs (hard to guess)
- Email addresses not publicly visible
- SendGrid handles email delivery securely

## Support

For issues or questions:
- Check GitHub Actions logs
- Review SendGrid dashboard
- Test locally with manage_subscribers.py
- Verify secrets are set correctly
