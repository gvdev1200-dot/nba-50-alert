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
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Only send alerts for games from yesterday (promo active today)
# DoorDash promo is only active the DAY AFTER a 50+ point game
# Setting to 1 day prevents:
#   - Alerts for old games (promo already expired)
#   - Mass alerts if sent_alerts history is accidentally reset
MAX_ALERT_AGE_DAYS = 1

# Minimum success rate required to mark alerts as sent
# If less than this percentage succeed, we retry next run
# Set high to prevent false alarms - better to miss an alert than send duplicates
MIN_SUCCESS_RATE = 0.95  # 95%

# Maximum retries for transient API failures
MAX_RETRIES = 3


class EmailAlertSender:
    def __init__(self, club_data_json_path, emails_json_path):
        self.club_data_json_path = club_data_json_path
        self.emails_json_path = emails_json_path
        self.api_key = os.environ.get('EMAILOCTOPUS_API_KEY')
        self.list_id = os.environ.get('EMAILOCTOPUS_LIST_ID')
        self.automation_id = os.environ.get('EMAILOCTOPUS_AUTOMATION_ID')
        self.api_fetch_failed = False  # Track if API calls failed

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
        """Load sent alerts history - FAILS SAFE on corruption"""
        if not os.path.exists(self.emails_json_path):
            print("[INFO] emails.json not found, starting fresh")
            return {"sent_alerts": []}

        try:
            with open(self.emails_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("emails.json root is not a dict")
            if not isinstance(data.get('sent_alerts'), list):
                raise ValueError("sent_alerts is not a list")

            return data

        except Exception as e:
            # CRITICAL: File is corrupted - DO NOT return empty!
            # This would cause duplicate alerts
            print(f"[CRITICAL] emails.json is corrupted: {e}")

            # Backup the corrupted file for investigation
            backup_path = str(self.emails_json_path) + f".corrupted.{int(time.time())}"
            try:
                shutil.copy2(self.emails_json_path, backup_path)
                print(f"[INFO] Backed up corrupted file to: {backup_path}")
            except Exception:
                pass

            # EXIT - do not continue with empty data (would cause mass duplicates)
            print("[CRITICAL] Exiting to prevent duplicate alerts. Please fix emails.json manually.")
            sys.exit(1)

    def save_emails_data(self, data):
        """Save sent alerts history with validation and atomic write"""
        temp_path = str(self.emails_json_path) + ".tmp"
        try:
            # Write to temp file first
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # Validate the temp file is readable and correct
            with open(temp_path, 'r', encoding='utf-8') as f:
                validated = json.load(f)
                if not isinstance(validated.get('sent_alerts'), list):
                    raise ValueError("Validation failed: sent_alerts is not a list")

            # Use os.replace for atomic rename (works on both Windows and POSIX)
            # This is more reliable than shutil.move which may copy+delete on Windows
            os.replace(temp_path, self.emails_json_path)
            return True

        except Exception as e:
            print(f"[CRITICAL] Could not save emails data: {e}")
            # Clean up temp file if it exists
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            return False

    def get_all_subscribers(self):
        """Get all subscribed contacts from the list

        Returns:
            list: List of subscribers, or None if API failed
        """
        subscribers = []
        page = 1
        api_called = False

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
                api_called = True

                if not response.ok:
                    print(f"[ERROR] Failed to get subscribers (HTTP {response.status_code}): {response.text}")
                    self.api_fetch_failed = True
                    return None  # Return None to indicate API failure

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

            except requests.exceptions.Timeout:
                print("[ERROR] Timeout while fetching subscribers")
                self.api_fetch_failed = True
                return None
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Network error fetching subscribers: {e}")
                self.api_fetch_failed = True
                return None
            except Exception as e:
                print(f"[ERROR] Failed to fetch subscribers: {e}")
                self.api_fetch_failed = True
                return None

        return subscribers

    def validate_scorer(self, scorer):
        """Validate scorer data to prevent false alarms from corrupted data"""
        errors = []

        # Check required fields exist
        if not scorer.get('player'):
            errors.append("missing player name")
        if not scorer.get('date'):
            errors.append("missing date")
        if not scorer.get('team'):
            errors.append("missing team")

        # Validate points
        points = scorer.get('points')
        if points is None:
            errors.append("missing points")
        elif not isinstance(points, int):
            errors.append(f"points is not integer: {type(points)}")
        elif points < 50:
            errors.append(f"points below 50: {points}")
        elif points > 100:
            # NBA record is 100 (Wilt Chamberlain). Anything higher is likely data corruption.
            errors.append(f"points impossibly high: {points} (likely data corruption)")

        # Validate date format
        date_str = scorer.get('date', '')
        try:
            game_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Check date is not in the future
            today = datetime.now(timezone.utc).date()
            if game_date > today:
                errors.append(f"game date in future: {date_str}")
            # Check date is within current season (not years ago)
            season_start = today.replace(month=10, day=1)
            if today.month < 10:
                season_start = season_start.replace(year=today.year - 1)
            if game_date < season_start:
                errors.append(f"game date before season start: {date_str}")
        except ValueError:
            errors.append(f"invalid date format: {date_str}")

        # Validate team abbreviation (should be 2-4 uppercase letters)
        team = scorer.get('team', '')
        if team and (len(team) < 2 or len(team) > 4 or not team.isupper()):
            errors.append(f"invalid team abbreviation: {team}")

        return errors

    def get_new_scorers(self, club_data, emails_data):
        """Get scorers that haven't been alerted yet and are recent enough"""
        sent_alerts = set(emails_data.get('sent_alerts', []))
        scorers = club_data.get('scorers', [])

        # Use UTC for consistency across all environments
        today = datetime.now(timezone.utc).date()
        cutoff_date = today - timedelta(days=MAX_ALERT_AGE_DAYS)

        new_scorers = []
        skipped_old = []
        skipped_invalid = []

        for scorer in scorers:
            # Validate scorer data to prevent false alarms
            validation_errors = self.validate_scorer(scorer)
            if validation_errors:
                skipped_invalid.append((scorer, validation_errors))
                continue

            alert_key = f"{scorer['date']}_{scorer['player']}_{scorer['points']}"

            # Skip if already alerted
            if alert_key in sent_alerts:
                continue

            # Check if game is recent enough (promo only active day after game)
            try:
                game_date = datetime.strptime(scorer['date'], '%Y-%m-%d').date()
                if game_date < cutoff_date:
                    skipped_old.append(scorer)
                    continue
            except ValueError as e:
                # Log date parsing failures (don't skip silently)
                print(f"[WARN] Invalid date format for {scorer.get('player', 'unknown')}: {scorer.get('date')} - {e}")
                continue

            new_scorers.append({
                'alert_key': alert_key,
                'scorer': scorer
            })

        # Log skipped invalid scorers (potential data corruption)
        if skipped_invalid:
            print(f"[WARN] Skipping {len(skipped_invalid)} invalid scorer(s) (possible data corruption):")
            for scorer, errors in skipped_invalid:
                print(f"  - {scorer.get('player', '?')}: {', '.join(errors)}")

        # Log skipped old games for visibility
        if skipped_old:
            print(f"[INFO] Skipping {len(skipped_old)} old game(s) (older than {MAX_ALERT_AGE_DAYS} day(s) - promo expired):")
            for scorer in skipped_old:
                print(f"  - {scorer['player']}: {scorer['points']} pts on {scorer['date']}")

        return new_scorers

    def trigger_automation_for_contact(self, contact_id):
        """Trigger the automation for a single contact with retry logic"""
        last_error = None

        for attempt in range(MAX_RETRIES):
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

                    # Rate limit - wait and retry
                    if response.status_code == 429:
                        wait_time = 2 ** attempt  # Exponential backoff
                        time.sleep(wait_time)
                        last_error = 'RATE_LIMITED'
                        continue

                    last_error = error_code
                    return False, error_code

            except requests.exceptions.Timeout:
                last_error = 'TIMEOUT'
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
            except Exception as e:
                last_error = str(e)
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue

        return False, last_error

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

        # CRITICAL: Distinguish "no subscribers" from "API failure"
        if subscribers is None:
            print("[ERROR] Could not fetch subscribers - API may be down")
            print("[INFO] NOT marking alerts as sent - will retry next run")
            return False  # Don't mark as sent!

        if len(subscribers) == 0:
            print("[INFO] No subscribers yet - marking alerts as sent")
            for item in new_scorers:
                if item['alert_key'] not in emails_data['sent_alerts']:
                    emails_data['sent_alerts'].append(item['alert_key'])
            if not self.save_emails_data(emails_data):
                print("[CRITICAL] Failed to save - alerts may be re-sent next run")
                return False
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

        # CRITICAL: Detect if ALL subscribers returned ALREADY_STARTED
        # This indicates the automation may be misconfigured (set to "once per contact")
        # In this case, NO emails are actually being sent - this is a silent failure!
        total_attempts = success_count + skip_count + fail_count
        if total_attempts > 0 and success_count == 0 and skip_count == total_attempts:
            print("[CRITICAL] ALL subscribers returned ALREADY_STARTED!")
            print("[CRITICAL] This means NO emails were sent - automation may be misconfigured")
            print("[CRITICAL] Check EmailOctopus: automation should allow multiple triggers per contact")
            print("[INFO] NOT marking alerts as sent - please fix automation settings")
            return False

        # Calculate success rate
        actual_sends = success_count + skip_count  # already_started counts as "received"
        success_rate = actual_sends / total_attempts if total_attempts > 0 else 0

        print(f"[INFO] Success rate: {success_rate:.1%}")

        # Only mark as sent if we actually sent some NEW emails (not all skipped)
        # This prevents marking as sent when no emails actually went out
        if success_count == 0 and skip_count > 0:
            print("[WARN] No new emails sent (all were already_started)")
            print("[INFO] Marking as sent since subscribers already received automation")

        # Only mark as sent if success rate is high enough
        if success_rate >= MIN_SUCCESS_RATE:
            for item in new_scorers:
                if item['alert_key'] not in emails_data['sent_alerts']:
                    emails_data['sent_alerts'].append(item['alert_key'])

            if self.save_emails_data(emails_data):
                print("[OK] Alert tracking updated")
            else:
                print("[CRITICAL] Failed to save alert tracking!")
                print("[WARN] Alerts were sent but NOT recorded - may cause duplicates next run")
                return False
        else:
            print(f"[WARN] Success rate ({success_rate:.1%}) below threshold ({MIN_SUCCESS_RATE:.0%})")
            print("[INFO] NOT marking alerts as sent - will retry next run")
            return False

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
