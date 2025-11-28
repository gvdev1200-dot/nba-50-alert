"""
Send email alerts when NBA players score 50+ points
Uses SendGrid API to notify subscribers about DoorDash promo
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
except ImportError:
    print("[ERROR] SendGrid library not installed. Run: pip install sendgrid")
    sys.exit(1)


class EmailAlertSender:
    def __init__(self, emails_json_path, club_data_json_path):
        self.emails_json_path = emails_json_path
        self.club_data_json_path = club_data_json_path
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL')

        if not self.sendgrid_api_key:
            print("[ERROR] SENDGRID_API_KEY environment variable not set")
            sys.exit(1)

        if not self.sender_email:
            print("[ERROR] SENDER_EMAIL environment variable not set")
            sys.exit(1)

    def load_emails_data(self):
        """Load subscriber emails and sent alerts history"""
        if not os.path.exists(self.emails_json_path):
            return {"subscribers": [], "sent_alerts": []}

        try:
            with open(self.emails_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not load emails data: {e}")
            return {"subscribers": [], "sent_alerts": []}

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

    def save_emails_data(self, data):
        """Save emails data back to file"""
        try:
            with open(self.emails_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Could not save emails data: {e}")
            return False

    def get_new_scorers(self, club_data, emails_data):
        """Get scorers that haven't been alerted yet"""
        sent_alerts = set(emails_data.get('sent_alerts', []))
        scorers = club_data.get('scorers', [])

        new_scorers = []
        for scorer in scorers:
            # Create unique key for this performance
            alert_key = f"{scorer['date']}_{scorer['player']}_{scorer['points']}"

            if alert_key not in sent_alerts:
                new_scorers.append({
                    'alert_key': alert_key,
                    'scorer': scorer
                })

        return new_scorers

    def create_email_content(self, scorers):
        """Create HTML email content for alert"""
        # Get the most recent scorer for the subject line
        latest = scorers[0]['scorer']

        subject = f"🏀 DoorDash 50% OFF Today! {latest['player']} scored {latest['points']} points"

        # Build HTML content
        html_parts = []
        html_parts.append("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #ff6600 0%, #ff3300 100%);
                         color: white; padding: 30px; text-align: center; border-radius: 10px; }
                .header h1 { margin: 0; font-size: 28px; }
                .content { background: #f9f9f9; padding: 30px; margin: 20px 0; border-radius: 10px; }
                .scorer { background: white; padding: 20px; margin: 15px 0; border-left: 4px solid #ff6600; }
                .scorer-name { font-size: 20px; font-weight: bold; color: #ff6600; }
                .scorer-stats { color: #666; margin-top: 5px; }
                .promo-code { background: #ff6600; color: white; padding: 20px; text-align: center;
                             font-size: 32px; font-weight: bold; border-radius: 10px; margin: 20px 0; }
                .footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; }
                .unsubscribe { color: #666; text-decoration: none; }
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
        """)

        # Add each scorer
        for item in scorers:
            scorer = item['scorer']
            html_parts.append(f"""
                    <div class="scorer">
                        <div class="scorer-name">{scorer['player']}</div>
                        <div class="scorer-stats">
                            {scorer['points']} points • {scorer['team']} vs {scorer['opponent']} • {self.format_date(scorer['date'])}
                        </div>
                    </div>
            """)

        html_parts.append("""
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
                    <p><a href="{{unsubscribe_url}}" class="unsubscribe">Unsubscribe</a></p>
                </div>
            </div>
        </body>
        </html>
        """)

        html_content = ''.join(html_parts)

        return subject, html_content

    def format_date(self, date_str):
        """Format date string for display"""
        try:
            date = datetime.fromisoformat(date_str)
            return date.strftime('%B %d, %Y')
        except:
            return date_str

    def send_email(self, to_email, subject, html_content, unsubscribe_token):
        """Send email via SendGrid"""
        try:
            # Replace unsubscribe placeholder
            unsubscribe_url = f"https://gvdev1200-dot.github.io/nba-50-alert/unsubscribe.html?token={unsubscribe_token}"
            html_content = html_content.replace('{{unsubscribe_url}}', unsubscribe_url)

            message = Mail(
                from_email=self.sender_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )

            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)

            return response.status_code == 202
        except Exception as e:
            print(f"[ERROR] Failed to send email to {to_email}: {e}")
            return False

    def send_alerts(self):
        """Main function to send alerts"""
        print("\n" + "="*70)
        print("NBA 50+ POINT EMAIL ALERT SENDER")
        print("="*70 + "\n")

        # Load data
        emails_data = self.load_emails_data()
        club_data = self.load_club_data()

        if not club_data:
            print("[ERROR] No club data available")
            return False

        subscribers = emails_data.get('subscribers', [])

        if not subscribers:
            print("[INFO] No subscribers yet")
            return True

        print(f"[INFO] Found {len(subscribers)} subscriber(s)")

        # Get new scorers (not yet alerted)
        new_scorers = self.get_new_scorers(club_data, emails_data)

        if not new_scorers:
            print("[INFO] No new 50+ point games to alert about")
            return True

        print(f"[INFO] Found {len(new_scorers)} new 50+ point performance(s) to alert about:")
        for item in new_scorers:
            scorer = item['scorer']
            print(f"  - {scorer['player']}: {scorer['points']} pts on {scorer['date']}")

        # Create email content
        subject, html_content = self.create_email_content(new_scorers)

        # Send emails to all subscribers
        print(f"\n[INFO] Sending alerts to {len(subscribers)} subscriber(s)...")

        sent_count = 0
        failed_count = 0

        for subscriber in subscribers:
            email = subscriber.get('email')
            token = subscriber.get('unsubscribe_token', '')

            if not email:
                continue

            success = self.send_email(email, subject, html_content, token)

            if success:
                sent_count += 1
                print(f"  ✓ Sent to {email}")
            else:
                failed_count += 1
                print(f"  ✗ Failed to send to {email}")

        # Mark scorers as alerted
        for item in new_scorers:
            emails_data['sent_alerts'].append(item['alert_key'])

        # Save updated data
        self.save_emails_data(emails_data)

        print(f"\n[OK] Alert sending complete!")
        print(f"  - Sent: {sent_count}")
        print(f"  - Failed: {failed_count}")
        print(f"  - Total performances alerted: {len(new_scorers)}")

        print("\n" + "="*70 + "\n")

        return failed_count == 0


def main():
    """Send email alerts for new 50+ point games"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    emails_json = project_root / 'data' / 'emails.json'
    club_data_json = project_root / 'data' / '50_club.json'

    sender = EmailAlertSender(emails_json, club_data_json)
    success = sender.send_alerts()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
