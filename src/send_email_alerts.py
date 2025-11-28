"""
Send email alerts when NBA players score 50+ points
Uses EmailOctopus API to notify subscribers about DoorDash promo
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path


class EmailAlertSender:
    def __init__(self, club_data_json_path, emails_json_path):
        self.club_data_json_path = club_data_json_path
        self.emails_json_path = emails_json_path
        self.api_key = os.environ.get('EMAILOCTOPUS_API_KEY')
        self.list_id = os.environ.get('EMAILOCTOPUS_LIST_ID')

        if not self.api_key:
            print("[ERROR] EMAILOCTOPUS_API_KEY environment variable not set")
            sys.exit(1)

        if not self.list_id:
            print("[ERROR] EMAILOCTOPUS_LIST_ID environment variable not set")
            sys.exit(1)

        self.base_url = "https://emailoctopus.com/api/1.6"

    def load_club_data(self):
        """Load 50+ Club data"""
        if not os.path.exists(self.club_data_json_path):
            print("[ERROR] 50+ Club data file not found")
            return None

        try:
            with open(self.club_data_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not load club data: {e}")
            return None

    def load_emails_data(self):
        """Load sent alerts history"""
        if not os.path.exists(self.emails_json_path):
            return {"sent_alerts": []}

        try:
            with open(self.emails_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not load emails data: {e}")
            return {"sent_alerts": []}

    def save_emails_data(self, data):
        """Save sent alerts history"""
        try:
            with open(self.emails_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Could not save emails data: {e}")
            return False

    def get_subscriber_count(self):
        """Get subscriber count from EmailOctopus"""
        try:
            response = requests.get(
                f"{self.base_url}/lists/{self.list_id}",
                params={"api_key": self.api_key},
                timeout=10
            )
            if response.ok:
                data = response.json()
                return data.get('counts', {}).get('subscribed', 0)
        except Exception as e:
            print(f"[WARNING] Could not get subscriber count: {e}")
        return 0

    def get_new_scorers(self, club_data, emails_data):
        """Get scorers that haven't been alerted yet"""
        sent_alerts = set(emails_data.get('sent_alerts', []))
        scorers = club_data.get('scorers', [])

        new_scorers = []
        for scorer in scorers:
            alert_key = f"{scorer['date']}_{scorer['player']}_{scorer['points']}"
            if alert_key not in sent_alerts:
                new_scorers.append({
                    'alert_key': alert_key,
                    'scorer': scorer
                })

        return new_scorers

    def format_date(self, date_str):
        """Format date string for display"""
        try:
            date = datetime.fromisoformat(date_str)
            return date.strftime('%B %d, %Y')
        except:
            return date_str

    def create_campaign(self, scorers):
        """Create and send an email campaign via EmailOctopus"""
        latest = scorers[0]['scorer']

        subject = f"🏀 DoorDash 50% OFF Today! {latest['player']} scored {latest['points']} points"

        # Build HTML content
        scorers_html = ""
        for item in scorers:
            scorer = item['scorer']
            scorers_html += f"""
            <div style="background: white; padding: 20px; margin: 15px 0; border-left: 4px solid #ff6600;">
                <div style="font-size: 20px; font-weight: bold; color: #ff6600;">{scorer['player']}</div>
                <div style="color: #666; margin-top: 5px;">
                    {scorer['points']} points • {scorer['team']} vs {scorer['opponent']} • {self.format_date(scorer['date'])}
                </div>
            </div>
            """

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #ff6600 0%, #ff3300 100%);
                         color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .header h1 {{ margin: 0; font-size: 28px; }}
                .content {{ background: #f9f9f9; padding: 30px; margin: 20px 0; border-radius: 10px; }}
                .promo-code {{ background: #ff6600; color: white; padding: 20px; text-align: center;
                             font-size: 32px; font-weight: bold; border-radius: 10px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏀 DoorDash 50% OFF Alert!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px;">The promo is active TODAY</p>
                </div>

                <div class="content">
                    <p><strong>Great news!</strong> An NBA player scored 50+ points, which means you get 50% off on DoorDash today!</p>

                    {scorers_html}

                    <div class="promo-code">
                        NBA50
                    </div>

                    <p><strong>How to use:</strong></p>
                    <ol>
                        <li>Open the DoorDash app</li>
                        <li>Make sure you have DashPass (required for this promo)</li>
                        <li>Add items to your cart</li>
                        <li>Enter promo code <strong>NBA50</strong> at checkout</li>
                        <li>Get 50% off (up to $10 savings)!</li>
                    </ol>

                    <p style="color: #ff6600; font-weight: bold;">⏰ This promo is only valid TODAY, so use it before midnight!</p>
                </div>

                <div class="footer">
                    <p>You're receiving this because you signed up for NBA 50-Point Alerts</p>
                    <p><a href="{{{{UnsubscribeURL}}}}" style="color: #666;">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        # Create campaign
        try:
            # First create the campaign
            campaign_response = requests.post(
                f"{self.base_url}/campaigns",
                json={
                    "api_key": self.api_key,
                    "name": f"NBA50 Alert - {latest['player']} {latest['points']}pts - {datetime.now().strftime('%Y-%m-%d')}",
                    "subject": subject,
                    "from": {
                        "name": "NBA 50-Point Alert",
                        "email_address": "alerts@nba50alert.com"
                    },
                    "content": {
                        "html": html_content,
                        "plain_text": f"DoorDash 50% OFF Today! {latest['player']} scored {latest['points']} points. Use code NBA50 at checkout. Valid today only!"
                    }
                },
                timeout=30
            )

            if not campaign_response.ok:
                print(f"[ERROR] Failed to create campaign: {campaign_response.text}")
                return False

            campaign_data = campaign_response.json()
            campaign_id = campaign_data.get('id')

            # Now send the campaign to the list
            send_response = requests.post(
                f"{self.base_url}/campaigns/{campaign_id}/send",
                json={
                    "api_key": self.api_key,
                    "list_id": self.list_id
                },
                timeout=30
            )

            if send_response.ok:
                print(f"[OK] Campaign sent successfully!")
                return True
            else:
                print(f"[ERROR] Failed to send campaign: {send_response.text}")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to create/send campaign: {e}")
            return False

    def send_alerts(self):
        """Main function to send alerts"""
        print("\n" + "="*70)
        print("NBA 50+ POINT EMAIL ALERT SENDER (EmailOctopus)")
        print("="*70 + "\n")

        # Load data
        emails_data = self.load_emails_data()
        club_data = self.load_club_data()

        if not club_data:
            print("[ERROR] No club data available")
            return False

        # Get subscriber count
        subscriber_count = self.get_subscriber_count()
        print(f"[INFO] Current subscribers: {subscriber_count}")

        if subscriber_count == 0:
            print("[INFO] No subscribers yet - skipping alert")
            return True

        # Get new scorers (not yet alerted)
        new_scorers = self.get_new_scorers(club_data, emails_data)

        if not new_scorers:
            print("[INFO] No new 50+ point games to alert about")
            return True

        print(f"[INFO] Found {len(new_scorers)} new 50+ point performance(s) to alert about:")
        for item in new_scorers:
            scorer = item['scorer']
            print(f"  - {scorer['player']}: {scorer['points']} pts on {scorer['date']}")

        # Send campaign
        print(f"\n[INFO] Sending campaign to {subscriber_count} subscriber(s)...")
        success = self.create_campaign(new_scorers)

        if success:
            # Mark scorers as alerted
            for item in new_scorers:
                emails_data['sent_alerts'].append(item['alert_key'])
            self.save_emails_data(emails_data)

        print("\n" + "="*70 + "\n")
        return success


def main():
    """Send email alerts for new 50+ point games"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    club_data_json = project_root / 'data' / '50_club.json'
    emails_json = project_root / 'data' / 'emails.json'

    sender = EmailAlertSender(club_data_json, emails_json)
    success = sender.send_alerts()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
