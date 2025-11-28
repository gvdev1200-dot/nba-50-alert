"""
Manage email subscribers - Add, remove, list
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path


class SubscriberManager:
    def __init__(self, emails_json_path):
        self.emails_json_path = emails_json_path

    def load_data(self):
        """Load subscribers data"""
        if not self.emails_json_path.exists():
            return {"subscribers": [], "sent_alerts": []}

        with open(self.emails_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_data(self, data):
        """Save subscribers data"""
        with open(self.emails_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_subscriber(self, email):
        """Add a new subscriber"""
        data = self.load_data()

        # Check if already subscribed
        for sub in data['subscribers']:
            if sub['email'].lower() == email.lower():
                print(f"[INFO] {email} is already subscribed")
                return False

        # Add new subscriber
        subscriber = {
            "email": email,
            "subscribed_date": datetime.now().isoformat(),
            "unsubscribe_token": str(uuid.uuid4())
        }

        data['subscribers'].append(subscriber)
        self.save_data(data)

        print(f"[OK] Added subscriber: {email}")
        print(f"  Unsubscribe token: {subscriber['unsubscribe_token']}")
        return True

    def remove_subscriber(self, email):
        """Remove a subscriber by email"""
        data = self.load_data()

        original_count = len(data['subscribers'])
        data['subscribers'] = [s for s in data['subscribers'] if s['email'].lower() != email.lower()]

        if len(data['subscribers']) < original_count:
            self.save_data(data)
            print(f"[OK] Removed subscriber: {email}")
            return True
        else:
            print(f"[INFO] Email not found: {email}")
            return False

    def remove_by_token(self, token):
        """Remove a subscriber by unsubscribe token"""
        data = self.load_data()

        original_count = len(data['subscribers'])
        removed_email = None

        for sub in data['subscribers']:
            if sub.get('unsubscribe_token') == token:
                removed_email = sub['email']
                break

        data['subscribers'] = [s for s in data['subscribers'] if s.get('unsubscribe_token') != token]

        if len(data['subscribers']) < original_count:
            self.save_data(data)
            print(f"[OK] Removed subscriber: {removed_email}")
            return True
        else:
            print(f"[INFO] Token not found: {token}")
            return False

    def list_subscribers(self):
        """List all subscribers"""
        data = self.load_data()

        if not data['subscribers']:
            print("[INFO] No subscribers yet")
            return

        print(f"\n{'='*70}")
        print(f"SUBSCRIBERS ({len(data['subscribers'])} total)")
        print(f"{'='*70}\n")

        for i, sub in enumerate(data['subscribers'], 1):
            print(f"{i}. {sub['email']}")
            print(f"   Subscribed: {sub.get('subscribed_date', 'Unknown')}")
            print(f"   Token: {sub.get('unsubscribe_token', 'N/A')}")
            print()


def main():
    """CLI for managing subscribers"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    emails_json = project_root / 'data' / 'emails.json'

    manager = SubscriberManager(emails_json)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_subscribers.py add <email>")
        print("  python manage_subscribers.py remove <email>")
        print("  python manage_subscribers.py remove-token <token>")
        print("  python manage_subscribers.py list")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'add':
        if len(sys.argv) < 3:
            print("[ERROR] Email required")
            sys.exit(1)
        email = sys.argv[2]
        manager.add_subscriber(email)

    elif command == 'remove':
        if len(sys.argv) < 3:
            print("[ERROR] Email required")
            sys.exit(1)
        email = sys.argv[2]
        manager.remove_subscriber(email)

    elif command == 'remove-token':
        if len(sys.argv) < 3:
            print("[ERROR] Token required")
            sys.exit(1)
        token = sys.argv[2]
        manager.remove_by_token(token)

    elif command == 'list':
        manager.list_subscribers()

    else:
        print(f"[ERROR] Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
