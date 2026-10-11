"""Collection and publication rules based on original listing dates."""
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone


def nepal_today():
    return datetime.now(timezone(timedelta(hours=5, minutes=45))).date()


def six_month_cutoff(today=None):
    today = today or nepal_today()
    year, month = divmod(today.year * 12 + today.month - 1 - 6, 12)
    month += 1
    return date(year, month, min(today.day, monthrange(year, month)[1]))


def is_recent_listing(item, today=None):
    today = today or nepal_today()
    try:
        listed = date.fromisoformat(str(item.get('listing_date') or ''))
    except ValueError:
        return False
    return six_month_cutoff(today) <= listed <= today


def has_property_information(item):
    return bool(str(item.get('title') or '').strip() and str(item.get('address') or '').strip()
                and item.get('property_type') in ('house','land','apartment')
                and item.get('transaction_type') in ('sale','rent')
                and (item.get('price_npr') or str(item.get('size') or '').strip()
                     or len(str(item.get('description') or '').strip()) >= 30))


def qualified_where():
    today = nepal_today()
    # Require a property image, excluding site logos and generic preview assets.
    photo = """EXISTS (
        SELECT 1 FROM (
            SELECT COALESCE(image_url,'') AS url
            UNION ALL SELECT value AS url FROM json_each(CASE WHEN json_valid(image_urls) THEN image_urls ELSE '[]' END)
        ) WHERE url LIKE 'https://%' AND lower(url) NOT LIKE '%/static/%'
          AND lower(url) NOT LIKE '%og-image%' AND lower(url) NOT LIKE '%logo%'
          AND lower(url) NOT LIKE '%placeholder%'
    )"""
    return (f"listing_date >= '{six_month_cutoff(today).isoformat()}' "
            f"AND listing_date <= '{today.isoformat()}' "
            "AND length(trim(COALESCE(title,'')))>0 AND length(trim(COALESCE(address,'')))>0 "
            "AND property_type IN ('house','land','apartment') AND transaction_type IN ('sale','rent') "
            f"AND {photo} "
            "AND (price_npr>0 OR length(trim(COALESCE(size,'')))>0 OR length(trim(COALESCE(description,'')))>=30)")
