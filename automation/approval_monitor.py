#!/usr/bin/env python3
"""
Monday.com Approval Monitor - Direct API Automation
Checks Monday.com for approved blog posts and publishes to Ayrshare (Facebook)
NO ZAPIER NEEDED - Uses direct API calls for scalability
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime

# Load environment variables
def load_env():
    env_vars = {}
    env_path = '/home/claudeuser/workspace/.env'
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    return env_vars

ENV = load_env()
MONDAY_API_KEY = ENV['MONDAY_API_KEY']
AYRSHARE_API_KEY = ENV['AYRSHARE_API_KEY']
BOARD_ID = "18371710717"  # Blog Content Pipeline

def query_monday_approved_items():
    """Query Monday.com for items with Status = 'Approved'"""
    query = """
    {
      boards(ids: %s) {
        items_page {
          items {
            id
            name
            column_values {
              id
              text
              value
            }
          }
        }
      }
    }
    """ % BOARD_ID

    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(
        "https://api.monday.com/v2",
        data=json.dumps({"query": query}).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        items = result['data']['boards'][0]['items_page']['items']

        # Filter for "Approved" status (column: color_mkxjmjnc)
        approved_items = []
        for item in items:
            status_col = next((col for col in item['column_values'] if col['id'] == 'color_mkxjmjnc'), None)
            if status_col and status_col.get('text') == 'Approved':
                # Get URL column (link_mkxjvp0z)
                url_col = next((col for col in item['column_values'] if col['id'] == 'link_mkxjvp0z'), None)
                if url_col and url_col.get('value'):
                    url_data = json.loads(url_col['value'])
                    approved_items.append({
                        'id': item['id'],
                        'name': item['name'],
                        'url': url_data.get('url', '')
                    })

        return approved_items

def post_to_ayrshare(title, url):
    """Post to Ayrshare (Facebook only)"""
    post_text = f"📚 New blog post: {title}\n\nRead more: {url}\n\n#ModelItK12 #STEMEducation #MiddleSchoolScience"

    payload = {
        "post": post_text,
        "platforms": ["facebook"],
        "mediaUrls": []  # Could add hero image URL here
    }

    headers = {
        "Authorization": f"Bearer {AYRSHARE_API_KEY}",
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(
        "https://app.ayrshare.com/api/post",
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result

def update_monday_status(item_id, new_status="Published"):
    """Update Monday.com item status to 'Published'"""
    mutation = """
    mutation {
      change_simple_column_value (
        board_id: %s,
        item_id: %s,
        column_id: "color_mkxjmjnc",
        value: "%s"
      ) {
        id
      }
    }
    """ % (BOARD_ID, item_id, new_status)

    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(
        "https://api.monday.com/v2",
        data=json.dumps({"query": mutation}).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result

def main():
    """Main approval monitoring workflow"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for approved items...")

    # Step 1: Query Monday.com for approved items
    approved_items = query_monday_approved_items()

    if not approved_items:
        print("✅ No approved items found. Nothing to publish.")
        return

    print(f"📋 Found {len(approved_items)} approved item(s):")

    # Step 2: Process each approved item
    for item in approved_items:
        print(f"\n📝 Processing: {item['name']}")
        print(f"   URL: {item['url']}")

        try:
            # Step 3: Post to Ayrshare (Facebook)
            print("   📱 Posting to Facebook via Ayrshare...")
            ayrshare_result = post_to_ayrshare(item['name'], item['url'])
            print(f"   ✅ Posted to Facebook: {ayrshare_result.get('id', 'Success')}")

            # Step 4: Update Monday.com status to "Published"
            print("   📊 Updating Monday.com status...")
            update_monday_status(item['id'], "Published")
            print("   ✅ Status updated to 'Published'")

        except urllib.error.HTTPError as e:
            print(f"   ❌ Error: {e}")
            print(f"   Response: {e.read().decode()}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")

    print(f"\n🎉 Approval monitoring complete!")

if __name__ == "__main__":
    main()
