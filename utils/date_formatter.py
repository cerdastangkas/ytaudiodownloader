import pandas as pd

def format_published_date(date_str):
    """Convert ISO date to human readable format"""
    try:
        date = pd.to_datetime(date_str)
        now = pd.Timestamp.now(tz=date.tz)
        diff = now - date
        
        if diff.days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"
            return f"{hours} hours ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} weeks ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} months ago"
        else:
            years = diff.days // 365
            return f"{years} years ago"
    except:
        return date_str[:10]  # Fallback to YYYY-MM-DD format
