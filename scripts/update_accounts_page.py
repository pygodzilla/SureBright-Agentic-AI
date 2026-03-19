#!/usr/bin/env python3
"""
Daily update script for Dev-Accounts-Projects.md
Run this daily to keep the accounts page updated.

Usage:
    python scripts/update_accounts_page.py
    python scripts/update_accounts_page.py --dry-run
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json

OBSIDIAN_VAULT = Path("/Users/test/Documents/Backup/Obsidian/Work/OpenCodeData")
ACCOUNTS_PAGE = OBSIDIAN_VAULT / "Dev-Accounts-Projects.md"


def load_activity_log() -> list[dict]:
    """Load existing activity log or return empty list."""
    if not ACCOUNTS_PAGE.exists():
        return []

    content = ACCOUNTS_PAGE.read_text()
    # Parse activity log section
    # This is a simplified parser - in production you'd use proper parsing
    return []


def add_activity_entry(
    date: str, time: str, activity: str, account: str, status: str
) -> str:
    """Add a new entry to the activity log."""
    entry = f"| {time} | {activity} | {account} | {status} |\n"
    return entry


def check_account_status(account_name: str) -> dict:
    """Check current status of an account."""
    # This would integrate with actual APIs in production
    status_map = {
        "github": {"status": "Active", "action_required": False},
        "northflank": {
            "status": "Active",
            "action_required": True,
            "note": "Link GitHub repo",
        },
        "groq": {"status": "Not signed up", "action_required": True},
        "huggingface": {"status": "Not signed up", "action_required": False},
        "cohere": {"status": "Not signed up", "action_required": False},
        "mistral": {"status": "Not signed up", "action_required": False},
        "langfuse": {"status": "Not signed up", "action_required": False},
    }
    return status_map.get(
        account_name.lower(), {"status": "Unknown", "action_required": True}
    )


def generate_daily_summary() -> str:
    """Generate daily summary section."""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    summary = f"""
### Daily Summary - {today}

**Today's Focus:**
- Complete Groq signup for free LLM access
- Finish Northflank GitHub repository linking
- Deploy SureBright-Agentic-AI project

**Completed Yesterday:**
- GitHub SSH key setup
- GitHub repo pushed (commit: 6bab69c)
- Northflank account created
- Free LLM client implemented
- README updated with free tier instructions

**Pending Actions:**
| Priority | Account | Action |
|----------|---------|--------|
| 🔴 High | Groq | Sign up at console.groq.com |
| 🟡 Medium | Northflank | Complete repo linking |
| 🟡 Medium | Hugging Face | Optional for MVP |
| 🟢 Low | LangFuse | Set up evaluation (optional) |

"""
    return summary


def update_accounts_page(dry_run: bool = False):
    """Main function to update the accounts page."""

    if not ACCOUNTS_PAGE.exists():
        print(f"Error: Accounts page not found at {ACCOUNTS_PAGE}")
        return

    content = ACCOUNTS_PAGE.read_text()

    # Find the Daily Activity Log section and add new entry
    today = datetime.now().strftime("%Y-%m-%d")

    # Check if we already logged today
    if f"### {today}" in content:
        print(f"Already logged activity for {today}")
        return

    # Generate new daily section
    new_daily_section = f"""
### {today}

| Time | Activity | Account | Status |
|------|----------|---------|--------|
"""

    # Insert after the last ### YYYY-MM-DD section
    lines = content.split("\n")
    new_lines = []
    inserted = False

    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.startswith("### 20") and not inserted:
            # Check if this is the most recent date section
            next_lines = "\n".join(lines[i + 1 : i + 5])
            if "### 20" in next_lines or "## 🔜 Next Steps" in next_lines:
                new_lines.append(new_daily_section)
                inserted = True

    if not inserted:
        # Insert before "## 🔜 Next Steps"
        for i, line in enumerate(new_lines):
            if line == "## 🔜 Next Steps":
                new_lines.insert(i, new_daily_section)
                inserted = True
                break

    if dry_run:
        print("Dry run - would update with:")
        print(new_daily_section)
        return

    # Write updated content
    updated_content = "\n".join(new_lines)
    ACCOUNTS_PAGE.write_text(updated_content)
    print(f"Updated accounts page: {ACCOUNTS_PAGE}")


def create_account_checklist() -> str:
    """Create a quick checklist for accounts to set up."""
    return """
## 📋 Quick Setup Checklist

### Must Have (Today)
- [ ] **Groq Account** - https://console.groq.com
  - Free: 30 req/min, 14,400/day
  - Model: llama-3.3-70b-versatile
  - Add to `.env`: `GROQ_API_KEY=your_key`

### Should Have (This Week)
- [ ] **Northflank GitHub Link** - Complete repo linking
- [ ] **Deploy Project** - Test deployment

### Nice to Have (Later)
- [ ] Hugging Face Token (for embeddings)
- [ ] LangFuse Account (for evaluation)
"""


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update Dev Accounts Page")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be updated"
    )
    args = parser.parse_args()

    update_accounts_page(dry_run=args.dry_run)
