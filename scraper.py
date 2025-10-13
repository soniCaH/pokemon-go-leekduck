#!/usr/bin/env python3
"""
LeekDuck Events to iCalendar Scraper
Scrapes Pokemon GO events from LeekDuck and generates an iCalendar file
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz
from typing import List, Dict, Optional
import re
import time


class LeekDuckScraper:
    """Scrapes events from LeekDuck and generates iCalendar files"""

    def __init__(self):
        self.url = "https://leekduck.com/events/"
        self.timezone = pytz.timezone('Europe/Brussels')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def fetch_page(self) -> str:
        """Fetch the LeekDuck events page"""
        response = requests.get(self.url, headers=self.headers)
        response.raise_for_status()
        return response.text

    def parse_datetime(self, date_str: str, prefer_future: bool = True) -> Optional[datetime]:
        """
        Parse date string from LeekDuck format
        Examples: "Mon, Oct 13, at 7:00 PM Local Time"
                  "Tue, Oct 14, at 10:00 AM Local Time"
                  "Monday, October 13, 2025, at 6:00 PM Local Time"
                  "Tuesday, October 7, 2025, at 10:00 AM Local Time"
        """
        if not date_str:
            return None

        # Remove "Local Time" and clean up
        date_str = date_str.replace('Local Time', '').strip()

        # Try full format with year first: "Monday, October 13, 2025, at 6:00 PM"
        pattern_with_year = r'(\w+),\s+(\w+)\s+(\d+),\s+(\d{4}),\s+at\s+(\d+):(\d+)\s+(AM|PM)'
        match = re.search(pattern_with_year, date_str)

        if match:
            day_name, month_name, day, year, hour, minute, ampm = match.groups()
            date_string = f"{month_name} {day} {year} {hour}:{minute} {ampm}"
            parsed_date = datetime.strptime(date_string, "%B %d %Y %I:%M %p")
            return self.timezone.localize(parsed_date)

        # Try short format without year: "Mon, Oct 13, at 7:00 PM"
        pattern = r'(\w+),\s+(\w+)\s+(\d+),\s+at\s+(\d+):(\d+)\s+(AM|PM)'
        match = re.search(pattern, date_str)

        if not match:
            return None

        day_name, month_name, day, hour, minute, ampm = match.groups()

        # Get current year (or next year if date has passed)
        current_year = datetime.now().year

        # Parse the date
        date_string = f"{month_name} {day} {current_year} {hour}:{minute} {ampm}"
        parsed_date = datetime.strptime(date_string, "%b %d %Y %I:%M %p")

        # Localize to Brussels timezone
        localized_date = self.timezone.localize(parsed_date)

        # If the date is in the past and we prefer future dates, assume it's next year
        if prefer_future and localized_date < datetime.now(self.timezone):
            parsed_date = datetime.strptime(
                f"{month_name} {day} {current_year + 1} {hour}:{minute} {ampm}",
                "%b %d %Y %I:%M %p"
            )
            localized_date = self.timezone.localize(parsed_date)

        return localized_date

    def fetch_event_details(self, event_url: str) -> Dict[str, any]:
        """
        Fetch detailed information from an event's detail page
        Returns dict with 'title', 'start', 'end', and 'description'
        """
        try:
            # Add delay to be respectful to the server
            time.sleep(0.5)

            response = requests.get(event_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            details = {
                'title': '',
                'start': None,
                'end': None,
                'description': ''
            }

            # Extract title from page
            title_elem = soup.find('h1')
            if not title_elem:
                title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Clean up title - remove " - Leek Duck" suffix and other common suffixes
                title_text = re.sub(r'\s*-\s*Leek Duck.*$', '', title_text)
                title_text = re.sub(r'\s*\|\s*Pokémon GO.*$', '', title_text)
                details['title'] = title_text

            # Find date/time information
            # Look for text patterns like "Tuesday, October 7, 2025, at 10:00 AM Local Time"
            text_content = soup.get_text()

            # Extract start date
            # Look for "Starts:" or "Start:" pattern (use \s+ to handle variable whitespace)
            start_pattern = r'Starts?:\s+([A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d{4},\s+at\s+\d+:\d+\s+[AP]M\s+Local\s+Time)'
            start_match = re.search(start_pattern, text_content, re.IGNORECASE)
            if start_match:
                details['start'] = self.parse_datetime(start_match.group(1), prefer_future=False)
            else:
                # Try to find any date that looks like a start date
                date_pattern = r'([A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d{4},\s+at\s+\d+:\d+\s+[AP]M)\s+Local\s+Time'
                dates = re.findall(date_pattern, text_content)
                if dates and len(dates) >= 1:
                    details['start'] = self.parse_datetime(dates[0], prefer_future=False)

            # Extract end date
            # Look for "Ends:" or "End:" pattern (use \s+ to handle variable whitespace)
            end_pattern = r'Ends?:\s+([A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d{4},\s+at\s+\d+:\d+\s+[AP]M\s+Local\s+Time)'
            end_match = re.search(end_pattern, text_content, re.IGNORECASE)
            if end_match:
                details['end'] = self.parse_datetime(end_match.group(1), prefer_future=False)
            else:
                # Look for pattern "from DATE to DATE at TIME" with full dates
                date_range_pattern1 = r'from\s+[A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d{4}\s+to\s+([A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d{4}),?\s+at\s+(\d+:\d+\s+[AP]M)'
                range_match = re.search(date_range_pattern1, text_content, re.IGNORECASE)
                if range_match:
                    end_date_str = f"{range_match.group(1)}, at {range_match.group(2)} Local Time"
                    details['end'] = self.parse_datetime(end_date_str, prefer_future=False)
                else:
                    # Look for pattern "from Month Day, Year to Month Day, Year" (no time)
                    date_range_pattern2 = r'from\s+([A-Za-z]+\s+\d+,\s+\d{4})\s+to\s+([A-Za-z]+\s+\d+,\s+\d{4})'
                    range_match2 = re.search(date_range_pattern2, text_content, re.IGNORECASE)
                    if range_match2 and details['start']:
                        # Use same time as start date
                        end_date = range_match2.group(2)
                        start_time = details['start'].strftime('%I:%M %p')
                        end_date_str = f"Monday, {end_date}, at {start_time} Local Time"
                        details['end'] = self.parse_datetime(end_date_str, prefer_future=False)
                    elif dates and len(dates) >= 2:
                        # If we found multiple dates, assume last one is end date
                        details['end'] = self.parse_datetime(dates[-1], prefer_future=False)

            # Extract description from main content area
            # Try different selectors for description
            desc_selectors = [
                'div.entry-content',
                'div.event-description',
                'div.content',
                'article',
                'main'
            ]

            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    # Get text but clean it up
                    paragraphs = desc_elem.find_all('p')
                    if paragraphs:
                        desc_parts = []
                        for p in paragraphs:
                            text = p.get_text(strip=True)
                            # Skip empty paragraphs and navigation elements
                            if text and len(text) > 20 and 'cookie' not in text.lower():
                                desc_parts.append(text)
                        details['description'] = '\n\n'.join(desc_parts[:5])  # Limit to first 5 paragraphs
                        break

            return details

        except Exception as e:
            print(f"Error fetching event details from {event_url}: {e}")
            return {'title': '', 'start': None, 'end': None, 'description': ''}

    def get_event_icon(self, title: str) -> str:
        """
        Determine event type and return appropriate emoji icon
        """
        title_lower = title.lower()

        # Raid-related events (order matters - most specific first)
        if 'raid hour' in title_lower:
            return '⏰'  # Clock for raid hour
        if 'raid day' in title_lower or 'raid weekend' in title_lower:
            return '🎯'  # Target for special raid days
        if 'mega raid' in title_lower or 'in mega raids' in title_lower:
            return '💫'  # Sparkles for mega raids
        if any(tier in title_lower for tier in ['in 1-star', 'in 2-star', 'in 3-star', 'in 4-star', 'in 5-star', 'in 6-star', 'raid battles']):
            return '⚔️'  # Swords for raid battles (all tiers)

        # Max/Dynamax battles
        if 'max battle' in title_lower or 'max monday' in title_lower or 'dynamax' in title_lower or 'gigantamax' in title_lower:
            return '⭐'  # Star for max battles

        # Spotlight hours
        if 'spotlight hour' in title_lower:
            return '🔦'  # Flashlight for spotlight hour

        # Community events
        if 'community day' in title_lower:
            return '👥'  # People for community day

        # GO Battle League / PvP
        if 'go battle' in title_lower or 'battle league' in title_lower or 'pvp' in title_lower:
            return '🥊'  # Boxing glove for battles

        # Special events / festivals
        if 'festival' in title_lower or 'celebration' in title_lower:
            return '🎉'  # Party popper for festivals
        if 'halloween' in title_lower:
            return '🎃'  # Pumpkin for Halloween

        # GO Pass
        if 'go pass' in title_lower:
            return '🎫'  # Ticket for GO Pass

        # Wild Area / Safari
        if 'wild area' in title_lower or 'safari' in title_lower:
            return '🗺️'  # Map for wild area events

        # Season
        if 'season' in title_lower or 'tales of transformation' in title_lower:
            return '🌍'  # Globe for seasons

        # Trade events
        if 'trade' in title_lower:
            return '🤝'  # Handshake for trade events

        # PokéStop Showcase
        if 'showcase' in title_lower:
            return '📸'  # Camera for showcases

        # Research / Timed Research
        if 'research' in title_lower:
            return '🔍'  # Magnifying glass for research

        # Default event icon
        return '📅'  # Calendar for general events

    def scrape_events(self) -> List[Dict]:
        """Scrape all events from LeekDuck"""
        html = self.fetch_page()
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        seen_urls = set()  # Track URLs to avoid duplicates

        # LeekDuck structure: Find all links that point to /events/[event-name]/
        # These are the event detail pages
        all_links = soup.find_all('a', href=True)
        event_links = [
            a for a in all_links
            if a.get('href', '').startswith('/events/')
            and a.get('href') != '/events/'
            and len(a.get('href')) > 10  # Filter out short/invalid links
        ]

        print(f"Found {len(event_links)} potential event links")

        for link in event_links:
            try:
                href = link.get('href')
                detail_url = f"https://leekduck.com{href}"

                # Skip if we've already processed this URL
                if detail_url in seen_urls:
                    continue
                seen_urls.add(detail_url)

                # Extract title from link text (fallback)
                title_text = link.get_text(strip=True)
                fallback_title = title_text.split('\n')[0] if '\n' in title_text else title_text

                # Fetch detailed information from detail page
                print(f"  Fetching: {fallback_title[:50]}...")
                details = self.fetch_event_details(detail_url)

                # Use title from detail page if available, otherwise use fallback
                title = details['title'] if details['title'] else fallback_title

                # Add icon to title
                icon = self.get_event_icon(title)
                title_with_icon = f"{icon} {title}"

                # Use detailed info
                event_start = details['start']
                event_end = details['end']
                description = details['description']

                # If we couldn't get dates from detail page, skip this event
                if not event_start:
                    print(f"    Skipping (no start date found)")
                    continue

                # If we still don't have an end time, default to 1 hour after start
                if not event_end:
                    event_end = event_start + timedelta(hours=1)

                events.append({
                    'title': title_with_icon,
                    'start': event_start,
                    'end': event_end,
                    'description': description or f"Event details from LeekDuck",
                    'image_url': '',  # Not extracting from listing page anymore
                    'url': detail_url
                })

            except Exception as e:
                print(f"Error parsing event {detail_url}: {e}")
                continue

        return events

    def create_ical(self, events: List[Dict]) -> Calendar:
        """Create iCalendar object from events"""
        cal = Calendar()
        cal.add('prodid', '-//LeekDuck Events Calendar//EN')
        cal.add('version', '2.0')
        cal.add('x-wr-calname', 'LeekDuck Pokemon GO Events')
        cal.add('x-wr-timezone', 'Europe/Brussels')
        cal.add('x-wr-caldesc', 'Pokemon GO events from LeekDuck.com')

        for event_data in events:
            event = Event()
            event.add('summary', event_data['title'])
            event.add('dtstart', event_data['start'])
            event.add('dtend', event_data['end'])
            event.add('dtstamp', datetime.now(self.timezone))

            # Create description with full details
            description = event_data['description']
            if event_data.get('url') and event_data['url'] != self.url:
                description += f"\n\nMore info: {event_data['url']}"
            if event_data.get('image_url'):
                description += f"\n\nImage: {event_data['image_url']}"
            description += f"\n\nData from LeekDuck.com"

            event.add('description', description)
            event.add('location', 'Pokemon GO')

            # Add URL if available
            if event_data.get('url'):
                event.add('url', event_data['url'])

            event.add('uid', f"{event_data['start'].isoformat()}-{hash(event_data['title'])}@leekduck-calendar")

            cal.add_component(event)

        return cal

    def save_ical(self, cal: Calendar, filename: str = 'events.ics'):
        """Save iCalendar to file"""
        with open(filename, 'wb') as f:
            f.write(cal.to_ical())
        print(f"Calendar saved to {filename}")


def main():
    """Main execution function"""
    print("Scraping LeekDuck events...")

    scraper = LeekDuckScraper()

    # Scrape events
    events = scraper.scrape_events()
    print(f"Found {len(events)} events")

    # Print events for debugging
    for event in events:
        start_str = event['start'].strftime('%Y-%m-%d %H:%M %Z')
        end_str = event['end'].strftime('%Y-%m-%d %H:%M %Z')
        duration = event['end'] - event['start']
        duration_str = f"{duration.days}d {duration.seconds//3600}h" if duration.days > 0 else f"{duration.seconds//3600}h {(duration.seconds//60)%60}m"
        print(f"  - {event['title']}")
        print(f"    {start_str} -> {end_str} ({duration_str})")

    # Create iCalendar
    cal = scraper.create_ical(events)

    # Save to file
    scraper.save_ical(cal)

    print("Done! Calendar file generated successfully.")


if __name__ == "__main__":
    main()
