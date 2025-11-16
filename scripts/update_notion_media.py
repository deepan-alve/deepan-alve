#!/usr/bin/env python3
"""
Update README.md with recently consumed media from Notion database
"""

import os
import re
from notion_client import Client
from datetime import datetime

def get_recent_media(notion, database_id):
    """Fetch the 5 most recently consumed media from Notion"""
    try:
        # Use the specific data source ID
        # Your data source: f66074b5-15e5-4e50-8f87-7f2346a594e6
        data_source_id = "f66074b5-15e5-4e50-8f87-7f2346a594e6"
        
        # Query ALL items to get stats (with pagination)
        stats = {
            "Movie": 0,
            "Series": 0,
            "Anime": 0,
            "Book": 0
        }
        
        has_more = True
        next_cursor = None
        
        print("📊 Fetching all items for statistics...")
        while has_more:
            query_params = {
                "data_source_id": data_source_id,
                "page_size": 100
            }
            if next_cursor:
                query_params["start_cursor"] = next_cursor
            
            all_results = notion.data_sources.query(**query_params)
            
            for page in all_results.get("results", []):
                props = page.get("properties", {})
                if "Type" in props and props["Type"]["type"] == "select":
                    if props["Type"]["select"]:
                        media_type = props["Type"]["select"]["name"]
                        if media_type in stats:
                            stats[media_type] += 1
            
            has_more = all_results.get("has_more", False)
            next_cursor = all_results.get("next_cursor")
            
        print(f"✅ Found {sum(stats.values())} total items: {stats}")
        
        # Now query the 5 most recent items (without sorting to avoid timeout)
        results = notion.data_sources.query(
            data_source_id=data_source_id,
            page_size=5
        )
        
        media_items = []
        
        for page in results["results"]:
            props = page["properties"]
            
            # Extract title
            title = ""
            if "Title" in props and props["Title"]["type"] == "title":
                title_array = props["Title"]["title"]
                if title_array:
                    title = title_array[0]["plain_text"]
            
            # Extract type (Movie, Series, Anime, Book)
            media_type = ""
            if "Type" in props and props["Type"]["type"] == "select":
                if props["Type"]["select"]:
                    media_type = props["Type"]["select"]["name"]
            
            # Extract created time
            created_time = ""
            if "created_time" in page:
                # Format: 2025-11-16 or just the date part
                created_time = page["created_time"][:10]
            
            # Extract rating (0-10 scale)
            rating = ""
            if "Rating" in props and props["Rating"]["type"] == "number":
                if props["Rating"]["number"] is not None:
                    rating = f"⭐ {props['Rating']['number']}/10"
            
            if title:
                media_items.append({
                    "title": title,
                    "type": media_type,
                    "date": created_time,
                    "rating": rating
                })
        
        return media_items, stats
        
    except Exception as e:
        print(f"Error fetching Notion data: {e}")
        return [], {}

def format_media_list(media_items, stats):
    """Format media items as markdown list with stats"""
    if not media_items:
        return "<!-- No recent media found -->"
    
    # Create stats badges
    lines = ["#### 📊 Stats"]
    lines.append("")
    
    stat_badges = []
    if stats.get("Movie", 0) > 0:
        stat_badges.append(f"![Movies](https://img.shields.io/badge/Movies-{stats['Movie']}-blueviolet?style=flat-square&logo=themoviedatabase)")
    if stats.get("Series", 0) > 0:
        stat_badges.append(f"![Series](https://img.shields.io/badge/Series-{stats['Series']}-red?style=flat-square&logo=netflix)")
    if stats.get("Anime", 0) > 0:
        stat_badges.append(f"![Anime](https://img.shields.io/badge/Anime-{stats['Anime']}-green?style=flat-square&logo=crunchyroll)")
    if stats.get("Book", 0) > 0:
        stat_badges.append(f"![Books](https://img.shields.io/badge/Books-{stats['Book']}-brown?style=flat-square&logo=bookstack)")
    
    lines.append(" ".join(stat_badges))
    lines.append("")
    lines.append("#### 🕒 Recently Added")
    lines.append("")
    
    # Create minimal cards for recent items
    lines.append('<table>')
    
    for item in media_items:
        # Color scheme based on type
        colors = {
            "Movie": "#8b5cf6",
            "Series": "#ef4444",
            "Anime": "#10b981",
            "Book": "#f59e0b"
        }
        color = colors.get(item["type"], "#6366f1")
        
        # Create minimal card row
        lines.append(f'''<tr>
    <td align="left">
      <div style="border-left: 3px solid {color}; padding-left: 12px;">
        <div style="color: {color}; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">{item["type"]}</div>
        <div style="color: #c9d1d9; font-size: 16px; font-weight: 500;">{item["title"]}</div>
      </div>
    </td>
  </tr>''')
    
    lines.append('</table>')
    
    return "\n".join(lines)

def update_readme(content):
    """Update the README.md file with new content"""
    readme_path = "readme.md"
    
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()
        
        # Replace content between markers
        pattern = r"(<!-- NOTION:START -->).*?(<!-- NOTION:END -->)"
        replacement = f"\\1\n{content}\n\\2"
        
        new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme)
        
        print("✅ README updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating README: {e}")

def main():
    # Get credentials from environment variables
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not notion_token or not database_id:
        print("❌ Missing NOTION_TOKEN or NOTION_DATABASE_ID environment variables")
        return
    
    # Initialize Notion client
    notion = Client(auth=notion_token)
    
    # Fetch recent media and stats
    print("📡 Fetching recent media from Notion...")
    media_items, stats = get_recent_media(notion, database_id)
    
    # Format as markdown
    content = format_media_list(media_items, stats)
    
    # Update README
    update_readme(content)

if __name__ == "__main__":
    main()
