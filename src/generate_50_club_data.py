"""
Generate 50+ Club JSON data for the current NBA season
Uses incremental updates - only scans new games since last check
"""

import requests
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

class SeasonClubGenerator:
    def __init__(self, json_path):
        self.scoreboard_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        self.summary_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
        self.json_path = json_path

    def get_current_season(self):
        """Get current NBA season (e.g., '2024-25')"""
        now = datetime.now()
        year = now.year
        month = now.month

        # NBA season starts in October
        if month >= 10:
            return f"{year}-{str(year + 1)[2:]}"
        else:
            return f"{year - 1}-{str(year)[2:]}"

    def get_season_start_date(self):
        """Get approximate season start date (October 15 of current season year)"""
        now = datetime.now()
        year = now.year
        month = now.month

        # If we're before October, season started last year
        if month < 10:
            year -= 1

        # NBA season typically starts mid-October
        return datetime(year, 10, 15)

    def load_existing_data(self):
        """Load existing JSON data if it exists"""
        if not os.path.exists(self.json_path):
            return None

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing data: {e}")
            return None

    def get_games_for_date_range(self, start_date, end_date):
        """Get all completed games in a date range"""
        games_list = []

        print(f"Scanning games from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")

        # ESPN API allows batch requests with date range
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        try:
            response = requests.get(
                self.scoreboard_url,
                params={
                    'dates': f"{start_str}-{end_str}",
                    'limit': 1000  # Get up to 1000 games
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            events = data.get('events', [])

            for event in events:
                status = event.get('status', {}).get('type', {}).get('name', '')

                if status == 'STATUS_FINAL':
                    game_date = event.get('date', '')
                    # Parse ISO date and convert to US Eastern Time for correct game date
                    if game_date:
                        # Parse UTC time
                        date_obj_utc = datetime.fromisoformat(game_date.replace('Z', '+00:00'))

                        # Convert to US Eastern Time (UTC-5 or UTC-4 depending on DST)
                        # Subtract 5 hours to get ET (approximation - covers most NBA games)
                        date_obj_et = date_obj_utc - timedelta(hours=5)

                        games_list.append({
                            'game_id': event['id'],
                            'date': date_obj_et.strftime('%Y-%m-%d'),
                            'name': event.get('shortName', 'Unknown'),
                            'home_team': event.get('competitions', [{}])[0].get('competitors', [{}])[0].get('team', {}).get('abbreviation', ''),
                            'away_team': event.get('competitions', [{}])[0].get('competitors', [{}])[1].get('team', {}).get('abbreviation', '')
                        })

            print(f"Found {len(games_list)} completed games\n")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching games: {e}")

        return games_list

    def get_box_score(self, game_id):
        """Get box score for a game and return all players with stats"""
        try:
            response = requests.get(
                self.summary_url,
                params={'event': game_id},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            boxscore = data.get('boxscore', {})
            players_data = boxscore.get('players', [])

            all_players = []

            for team in players_data:
                team_abbr = team.get('team', {}).get('abbreviation', 'UNK')

                for stat_group in team.get('statistics', []):
                    for player in stat_group.get('athletes', []):
                        athlete = player.get('athlete', {})
                        stats = player.get('stats', [])

                        # Points is at index 1
                        if stats and len(stats) > 1:
                            try:
                                points = int(stats[1]) if stats[1] != '' else 0

                                if points >= 50:  # Only return 50+ scorers
                                    all_players.append({
                                        'name': athlete.get('displayName', 'Unknown'),
                                        'points': points,
                                        'team': team_abbr
                                    })
                            except (ValueError, TypeError):
                                continue

            return all_players

        except requests.exceptions.RequestException:
            # Silently skip errors - some games might not have box scores yet
            return []

    def update_50_club_data(self, force_full_scan=False):
        """
        Update 50+ Club data incrementally
        Only scans games since last check (or full season if first run)
        """
        season = self.get_current_season()

        print(f"\n{'='*70}")
        print(f"50+ CLUB DATA UPDATER - {season} Season")
        print(f"{'='*70}\n")

        # Load existing data
        existing_data = self.load_existing_data()

        # Determine date range to scan
        end_date = datetime.now()

        if existing_data and not force_full_scan:
            # Incremental update - only scan since last check
            last_checked = existing_data.get('lastCheckedDate')
            if last_checked:
                start_date = datetime.fromisoformat(last_checked) + timedelta(days=1)
                print(f"[INCREMENTAL UPDATE]")
                print(f"Last checked: {last_checked}")
                print(f"Checking new games since then...\n")
            else:
                # No lastCheckedDate in old format, do full scan
                start_date = self.get_season_start_date()
                print(f"[FULL SCAN] (no previous check date found)\n")
        else:
            # First run or forced full scan
            start_date = self.get_season_start_date()
            print(f"[FULL SCAN] (first run)\n")

        # Get games in date range
        games = self.get_games_for_date_range(start_date, end_date)

        if not games:
            print("No new games to check")

            if existing_data:
                # Just update lastCheckedDate
                existing_data['lastCheckedDate'] = end_date.strftime('%Y-%m-%d')
                existing_data['lastUpdated'] = datetime.now().isoformat()
                return existing_data
            else:
                # Return empty data
                return {
                    'season': season,
                    'lastUpdated': datetime.now().isoformat(),
                    'lastCheckedDate': end_date.strftime('%Y-%m-%d'),
                    'totalGames': 0,
                    'scorers': []
                }

        # Scan games for 50+ scorers
        new_scorers = []
        processed = 0

        print(f"Scanning {len(games)} game(s) for 50+ point performances...")
        if len(games) > 10:
            print("Progress: ", end="", flush=True)

        for game in games:
            game_id = game['game_id']
            game_date = game['date']

            processed += 1
            if len(games) > 10 and processed % 10 == 0:
                print(f"{processed}...", end="", flush=True)

            scorers_in_game = self.get_box_score(game_id)

            for scorer in scorers_in_game:
                new_scorers.append({
                    'date': game_date,
                    'player': scorer['name'],
                    'team': scorer['team'],
                    'points': scorer['points'],
                    'opponent': game['away_team'] if scorer['team'] == game['home_team'] else game['home_team']
                })

        if len(games) > 10:
            print()  # New line after progress

        print(f"\nFound {len(new_scorers)} new 50+ point performance(s)!")

        # Merge with existing data
        if existing_data and 'scorers' in existing_data:
            all_scorers = existing_data['scorers'] + new_scorers
            total_games = existing_data.get('totalGames', 0) + len(games)
        else:
            all_scorers = new_scorers
            total_games = len(games)

        # Remove duplicates (same player, date, points)
        unique_scorers = []
        seen = set()
        for scorer in all_scorers:
            key = (scorer['date'], scorer['player'], scorer['points'])
            if key not in seen:
                seen.add(key)
                unique_scorers.append(scorer)

        # Sort by date (most recent first)
        unique_scorers.sort(key=lambda x: x['date'], reverse=True)

        # Create updated JSON structure
        data = {
            'season': season,
            'lastUpdated': datetime.now().isoformat(),
            'lastCheckedDate': end_date.strftime('%Y-%m-%d'),
            'totalGames': total_games,
            'scorers': unique_scorers
        }

        return data

    def save_to_json(self, data):
        """Save data to JSON file"""
        try:
            # Create directory if it doesn't exist
            output_dir = Path(self.json_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Write JSON with nice formatting
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"\n[OK] Data saved to: {self.json_path}")
            print(f"  - Season: {data['season']}")
            print(f"  - Last Checked: {data['lastCheckedDate']}")
            print(f"  - Total 50+ Performances: {len(data['scorers'])}")

            return True

        except Exception as e:
            print(f"\n[ERROR] Error saving JSON: {e}")
            return False


def main():
    """Generate/update 50+ Club data"""
    # Determine output path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_path = project_root / 'data' / '50_club.json'

    # Create generator
    generator = SeasonClubGenerator(output_path)

    # Check for --full flag
    import sys
    force_full = '--full' in sys.argv

    # Update data (incremental by default, full if --full flag passed)
    data = generator.update_50_club_data(force_full_scan=force_full)

    # Save to file
    generator.save_to_json(data)

    print(f"\n{'='*70}")
    print("DONE! Run this script daily to keep data updated.")
    print("Tip: Use --full flag to force a complete re-scan.")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
