"""
NBA 50-Point Scorer Checker with Email Notifications
Checks yesterday's NBA games for any player who scored 50+ points
Sends email notification when detected
"""

import requests
from datetime import datetime, timedelta
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class NBA50PointChecker:
    def __init__(self, config_path='config.json'):
        self.scoreboard_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        self.summary_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
        self.config = self.load_config(config_path)

    def load_config(self, config_path):
        """Load email configuration from config.json"""
        if not os.path.exists(config_path):
            print(f"Warning: {config_path} not found. Email notifications disabled.")
            print(f"Copy config.json.example to config.json and fill in your email settings.")
            return {'email': {'enabled': False}}

        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {'email': {'enabled': False}}

    def get_yesterday_date(self):
        """Get yesterday's date in YYYYMMDD format for ESPN API"""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime("%Y%m%d")

    def get_games_for_date(self, date_str):
        """
        Get all games for a specific date
        date_str should be in YYYYMMDD format (e.g., '20251120')
        """
        try:
            response = requests.get(
                self.scoreboard_url,
                params={'dates': date_str},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Extract completed games
            events = data.get('events', [])
            completed_games = []

            for event in events:
                # Check if game is completed
                status = event.get('status', {}).get('type', {}).get('name', '')

                if status == 'STATUS_FINAL':
                    completed_games.append({
                        'game_id': event['id'],
                        'name': event['name'],
                        'short_name': event['shortName']
                    })

            return completed_games

        except requests.exceptions.RequestException as e:
            print(f"Error fetching games: {e}")
            return []

    def get_box_score(self, game_id):
        """Get box score and player stats for a specific game"""
        try:
            response = requests.get(
                self.summary_url,
                params={
                    'event': game_id,
                    'region': 'us',
                    'lang': 'en'
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Extract player stats
            boxscore = data.get('boxscore', {})
            players_data = boxscore.get('players', [])

            all_players = []

            for team in players_data:
                team_name = team.get('team', {}).get('abbreviation', 'UNK')

                # Each team has statistics groups (starters, bench)
                for stat_group in team.get('statistics', []):
                    for player in stat_group.get('athletes', []):
                        athlete = player.get('athlete', {})
                        stats = player.get('stats', [])

                        # Stats array format: [MIN, PTS, FG, 3PT, FT, REB, AST, ...]
                        # Points is at index 1 (after minutes)
                        if stats and len(stats) > 1:
                            try:
                                points = int(stats[1]) if stats[1] != '' else 0

                                all_players.append({
                                    'name': athlete.get('displayName', 'Unknown'),
                                    'points': points,
                                    'team': team_name
                                })
                            except (ValueError, TypeError):
                                continue

            return all_players

        except requests.exceptions.RequestException as e:
            print(f"Error fetching box score for game {game_id}: {e}")
            return []

    def send_email(self, scorers, date_str):
        """Send email notification about 50+ point scorers"""
        email_config = self.config.get('email', {})

        if not email_config.get('enabled', False):
            print("\nEmail notifications are disabled in config.json")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = '🏀 DoorDash 50% OFF Today! - NBA50'
            msg['From'] = f"{email_config.get('sender_name', 'NBA Alert')} <{email_config['sender_email']}>"
            msg['To'] = email_config['recipient_email']

            # Convert date for display
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            game_date = date_obj.strftime("%B %d, %Y")

            # Create plain text version
            text_content = self.create_text_email(scorers, game_date)

            # Create HTML version
            html_content = self.create_html_email(scorers, game_date)

            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            print(f"\nSending email to {email_config['recipient_email']}...")

            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)

            print("✓ Email sent successfully!")
            return True

        except Exception as e:
            print(f"✗ Error sending email: {e}")
            return False

    def create_text_email(self, scorers, game_date):
        """Create plain text email content"""
        content = f"NBA 50-Point Alert - {game_date}\n\n"

        for scorer in scorers:
            content += f"{scorer['name']} scored {scorer['points']} points last night!\n"

        content += f"\nDoorDash 50% OFF Promotion is ACTIVE Today!\n\n"
        content += f"Use code: NBA50\n"
        content += f"Valid today until 11:59 PM PT\n"
        content += f"Save 50% off (up to $10) on DoorDash delivery orders\n\n"
        content += f"---\n"
        content += f"This is an automated alert from your NBA 50-Point Checker"

        return content

    def create_html_email(self, scorers, game_date):
        """Create HTML email content"""
        players_html = ""
        for scorer in scorers:
            players_html += f"""
            <div style="background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ff6600;">
                <h2 style="margin: 0; color: #1a1a1a; font-size: 20px;">
                    🏀 {scorer['name']} ({scorer['team']})
                </h2>
                <p style="margin: 5px 0; color: #666; font-size: 24px; font-weight: bold;">
                    {scorer['points']} POINTS
                </p>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #ff6600 0%, #ff8800 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🏀 DoorDash 50% OFF!</h1>
                <p style="color: white; margin: 10px 0 0 0; font-size: 16px;">NBA 50-Point Alert</p>
            </div>

            <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <p style="font-size: 16px; color: #666; margin-top: 0;">
                    Great news! A player scored 50+ points on {game_date}:
                </p>

                {players_html}

                <div style="background: #e8f5e9; padding: 20px; margin: 20px 0; border-radius: 8px; border: 2px dashed #4caf50;">
                    <h3 style="margin: 0 0 10px 0; color: #2e7d32; font-size: 18px;">
                        💰 Your DoorDash Promo Code
                    </h3>
                    <div style="background: white; padding: 15px; border-radius: 5px; text-align: center;">
                        <code style="font-size: 32px; font-weight: bold; color: #ff6600; letter-spacing: 3px;">
                            NBA50
                        </code>
                    </div>
                    <p style="margin: 15px 0 0 0; color: #666; font-size: 14px;">
                        ✓ Valid today until 11:59 PM PT<br>
                        ✓ Save 50% off (up to $10)<br>
                        ✓ DoorDash delivery orders only<br>
                        ✓ DashPass members only
                    </p>
                </div>

                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Automated alert from your NBA 50-Point Checker
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def find_50_point_scorers(self, date_str=None):
        """
        Find all players who scored 50+ points on a given date
        If no date provided, checks yesterday
        date_str should be in YYYYMMDD format
        """
        if date_str is None:
            date_str = self.get_yesterday_date()

        # Convert YYYYMMDD to readable format for display
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        readable_date = date_obj.strftime("%B %d, %Y")

        print(f"\n{'='*60}")
        print(f"Checking NBA games for {readable_date}")
        print(f"{'='*60}\n")

        # Get all completed games for the date
        games = self.get_games_for_date(date_str)

        if not games:
            print(f"No completed games found for {readable_date}")
            print("Note: This could mean:")
            print("  - No games were scheduled")
            print("  - Games haven't finished yet")
            print("  - It's the off-season\n")
            return []

        print(f"Found {len(games)} completed game(s)\n")

        # Check each game for 50+ point scorers
        fifty_point_scorers = []

        for game in games:
            game_id = game['game_id']
            game_name = game['short_name']

            print(f"Checking {game_name}...", end=" ")

            players = self.get_box_score(game_id)

            # Find 50+ scorers in this game
            game_scorers = [p for p in players if p['points'] >= 50]

            if game_scorers:
                print(f"[FOUND 50+ SCORER(S)!]")
                fifty_point_scorers.extend(game_scorers)
            else:
                # Find highest scorer for this game
                if players:
                    highest = max(players, key=lambda x: x['points'])
                    print(f"[High: {highest['name']} - {highest['points']} pts]")
                else:
                    print("[No data]")

        return fifty_point_scorers


def main():
    """Main function to run the checker"""
    checker = NBA50PointChecker()

    # Check yesterday's games
    scorers = checker.find_50_point_scorers()

    # Display results
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}\n")

    if scorers:
        print("*** DoorDash 50% OFF promotion is ACTIVE today! ***\n")

        for scorer in scorers:
            print(f"  * {scorer['name']} ({scorer['team']}) - {scorer['points']} POINTS!")

        # Send email notification
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y%m%d")

        print(f"\n{'-'*60}")
        if checker.send_email(scorers, date_str):
            print("Email notification sent successfully!")
        else:
            print("Email notification skipped or failed")
        print(f"{'-'*60}\n")

    else:
        print("No 50+ point performances yesterday.")
        print("No email sent (avoiding spam).\n")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
