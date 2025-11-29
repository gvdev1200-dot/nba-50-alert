"""
Send email alerts when NBA players score 50+ points
Uses EmailOctopus Automations API to notify subscribers about DoorDash promo

Setup required in EmailOctopus dashboard:
1. Create an automation with "Started via API" trigger
2. Add an email step with your alert template
3. Copy the automation ID to EMAILOCTOPUS_AUTOMATION_ID secret
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from pathlib import Path


class EmailAlertSender:
    def __init__(self, club_data_json_path, emails_json_path):
        self.club_data_json_path = club_data_json_path
        self.emails_json_path = emails_json_path
        self.api_key = os.environ.get('EMAILOCTOPUS_API_KEY')
        self.list_id = os.environ.get('EMAILOCTOPUS_LIST_ID')
        self.automation_id = os.environ.get('EMAILOCTOPUS_AUTOMATION_ID')

        if not self.api_key:
            print("[ERROR] EMAILOCTOPUS_API_KEY environment variable not set")
            sys.exit(1)

        if not self.list_id:
            print("[ERROR] EMAILOCTOPUS_LIST_ID environment variable not set")
            sys.exit(1)

        if not self.automation_id:
            print("[ERROR] EMAILOCTOPUS_AUTOMATION_ID environment variable not set")
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

    def get_all_subscribers(self):
        """Get all subscribed contacts from the list"""
        subscribers = []
        page = 1

        while True:
            try:
                response = requests.get(
                    f"{self.base_url}/lists/{self.list_id}/contacts",
                    params={
                        "api_key": self.api_key,
                        "limit": 100,
                        "page": page
                    },
                    timeout=30
                )

                if not response.ok:
                    print(f"[ERROR] Failed to get subscribers: {response.text}")
                    break

                data = response.json()
                contacts = data.get('data', [])

                # Filter for subscribed contacts only
                for contact in contacts:
                    if contact.get('status') == 'SUBSCRIBED':
                        subscribers.append({
                            'id': contact.get('id'),
                            'email': contact.get('email_address')
                        })

                # Check if there are more pages
                paging = data.get('paging', {})
                if not paging.get('next'):
                    break

                page += 1

            except Exception as e:
                print(f"[ERROR] Failed to fetch subscribers: {e}")
                break

        return subscribers

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

    def trigger_automation_for_contact(self, contact_id):
        """Trigger the automation for a single contact"""
        try:
            response = requests.post(
                f"{self.base_url}/automations/{self.automation_id}/queue",
                json={
                    "api_key": self.api_key,
                    "list_member_id": contact_id
                },
                timeout=10
            )

            if response.ok:
                return True, None
            else:
                error_data = response.json() if response.text else {}
                error_code = error_data.get('error', {}).get('code', 'UNKNOWN')

                # ALREADY_STARTED is not a failure - contact already received this automation
                if error_code == 'ALREADY_STARTED':
                    return True, 'already_started'

                return False, error_code

        except Exception as e:
            return False, str(e)

    def send_alerts(self):
        """Main function to send alerts via automation"""
        print("\n" + "="*70)
        print("NBA 50+ POINT EMAIL ALERT SENDER (EmailOctopus Automations)")
        print("="*70 + "\n")

        # Load data
        emails_data = self.load_emails_data()
        club_data = self.load_club_data()

        if not club_data:
            print("[ERROR] No club data available")
            return False

        # Get new scorers (not yet alerted)
        new_scorers = self.get_new_scorers(club_data, emails_data)

        if not new_scorers:
            print("[INFO] No new 50+ point games to alert about")
            return True

        print(f"[INFO] Found {len(new_scorers)} new 50+ point performance(s):")
        for item in new_scorers:
            scorer = item['scorer']
            print(f"  - {scorer['player']}: {scorer['points']} pts on {scorer['date']}")

        # Get all subscribers
        print("\n[INFO] Fetching subscribers...")
        subscribers = self.get_all_subscribers()

        if not subscribers:
            print("[INFO] No subscribers yet - skipping alert")
            # Still mark as sent so we don't retry
            for item in new_scorers:
                emails_data['sent_alerts'].append(item['alert_key'])
            self.save_emails_data(emails_data)
            return True

        print(f"[INFO] Found {len(subscribers)} subscriber(s)")
        print(f"\n[INFO] Triggering automation for each subscriber...")

        # Trigger automation for each subscriber
        success_count = 0
        skip_count = 0
        fail_count = 0

        for i, subscriber in enumerate(subscribers):
            success, error = self.trigger_automation_for_contact(subscriber['id'])

            if success:
                if error == 'already_started':
                    skip_count += 1
                else:
                    success_count += 1
            else:
                fail_count += 1
                print(f"  [WARN] Failed for {subscriber['email']}: {error}")

            # Rate limiting: max 10 requests per second
            if (i + 1) % 10 == 0:
                time.sleep(1)
                print(f"  Progress: {i + 1}/{len(subscribers)}...")

        print(f"\n[RESULT] Triggered: {success_count}, Skipped: {skip_count}, Failed: {fail_count}")

        # Mark scorers as alerted if we had any success
        if success_count > 0 or skip_count > 0:
            for item in new_scorers:
                emails_data['sent_alerts'].append(item['alert_key'])
            self.save_emails_data(emails_data)
            print("[OK] Alert tracking updated")

        print("\n" + "="*70 + "\n")
        return fail_count == 0


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
