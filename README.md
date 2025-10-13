# LeekDuck Calendar Sync

Automatically sync Pokemon GO events from [LeekDuck.com](https://leekduck.com/events/) to your iCloud calendar.

## Features

- Scrapes Pokemon GO events from LeekDuck
- Generates iCalendar (.ics) format
- Automatically updates daily via GitHub Actions
- Brussels/BE timezone (Europe/Brussels)
- Subscribe once, auto-updates forever

## Setup Instructions

### 1. Test Locally (Optional)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the scraper
python scraper.py

# Check the generated events.ics file
ls -l events.ics
```

### 2. Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository named `leekduck-calendar`
3. Make it **public** (required for GitHub Pages)
4. Don't initialize with README (we already have one)

### 3. Push to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Initial commit: LeekDuck calendar scraper"

# Add your GitHub repository as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/leekduck-calendar.git

# Push to GitHub
git push -u origin main
```

### 4. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Pages** in the left sidebar
4. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main** / **/ (root)**
5. Click **Save**

### 5. Enable GitHub Actions

1. Go to the **Actions** tab in your repository
2. If prompted, click "I understand my workflows, go ahead and enable them"
3. The workflow should run automatically on the next push

### 6. Trigger First Run

```bash
# Make a small change to trigger the workflow
git commit --allow-empty -m "Trigger first workflow run"
git push
```

Or manually trigger:
1. Go to **Actions** tab
2. Click "Update LeekDuck Calendar"
3. Click "Run workflow" button
4. Click green "Run workflow"

### 7. Subscribe to Calendar in iCloud

Once GitHub Pages is enabled and the workflow has run:

1. Get your calendar URL: `https://YOUR_USERNAME.github.io/leekduck-calendar/events.ics`
2. On **iPhone/iPad**:
   - Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar
   - Enter the URL above
3. On **Mac**:
   - Calendar app → File → New Calendar Subscription
   - Enter the URL above
4. On **Web**:
   - Go to [iCloud.com](https://icloud.com) → Calendar
   - Click the calendar icon with "+" → New Calendar Subscription
   - Enter the URL above

## How It Works

1. **GitHub Actions** runs the Python scraper daily at 6:00 AM UTC (8:00 AM Brussels)
2. Scraper fetches events from LeekDuck
3. Generates `events.ics` file with all events in Brussels timezone
4. Commits the updated file to the repository
5. **GitHub Pages** serves the `.ics` file at a public URL
6. iCloud Calendar refreshes subscriptions periodically (usually daily)

## Customization

### Change Update Schedule

Edit `.github/workflows/update-calendar.yml`:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # Change this cron expression
```

Cron format: `minute hour day month weekday`
- `0 6 * * *` = 6:00 AM UTC daily
- `0 */6 * * *` = Every 6 hours
- `0 0 * * *` = Midnight UTC daily

### Change Timezone

Edit `scraper.py` (line 22):

```python
self.timezone = pytz.timezone('Europe/Brussels')  # Change timezone here
```

[List of timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

### Customize Event Icons

Event titles are automatically prefixed with emoji icons based on event type. To add or modify icons:

1. Edit `scraper.py` - find the `get_event_icon()` method (around line 192)
2. Add your pattern matching rules following the existing format:

```python
def get_event_icon(self, title: str) -> str:
    title_lower = title.lower()

    # Add your custom patterns here
    if 'your event type' in title_lower:
        return '🎮'  # Your chosen emoji

    # Existing patterns (order matters - most specific first!)
    if 'raid hour' in title_lower:
        return '⏰'
    # ... more patterns ...
```

**Current icon mapping:**
- ⏰ Raid Hour
- 🎯 Raid Day / Raid Weekend
- 💫 Mega Raids
- ⚔️ Raid Battles (1-6 star raids)
- ⭐ Max Battles / Dynamax / Gigantamax
- 🔦 Spotlight Hour
- 👥 Community Day
- 🥊 GO Battle League / PvP
- 🎉 Festivals / Celebrations
- 🎃 Halloween events
- 🎫 GO Pass
- 🗺️ Wild Area / Safari
- 🌍 Seasons
- 🤝 Trade events
- 📸 PokéStop Showcase
- 🔍 Research events
- 📅 Default (any other event)

**Important:** Pattern order matters! More specific patterns should come before general ones. For example, "raid hour" must be checked before "raid battles" to avoid mismatches.

After editing, commit and push to GitHub:
```bash
git add scraper.py
git commit -m "Update event icon mappings"
git push
```

The GitHub Action will automatically run and update your calendar with the new icons.

## Troubleshooting

### Calendar not updating
- Check GitHub Actions tab for errors
- Verify GitHub Pages is enabled and serving the file
- Try resubscribing to the calendar in iCloud

### No events showing up
- Check `events.ics` file in repository to see if events were scraped
- Run scraper locally to debug: `python scraper.py`
- iCloud may take time to refresh (up to 24 hours)

### Workflow failing
- Check Actions tab for error logs
- Common issues: LeekDuck changed their HTML structure
- Open an issue if you need help

## License

MIT License - Feel free to modify and use as needed.

## Credits

Event data from [LeekDuck.com](https://leekduck.com/)
