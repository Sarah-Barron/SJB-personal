#!/usr/bin/env python3
"""Convert Jira ticket description HTML to plain text.

Usage examples:
1) Convert inline HTML:
   python jira_html_to_text_agent.py --html "<p>Hello <b>world</b></p>"

2) Convert HTML from file:
   python jira_html_to_text_agent.py --html-file description.html

3) Fetch rendered Jira description HTML and convert:
   set JIRA_BASE_URL=https://your-domain.atlassian.net
   set JIRA_EMAIL=you@example.com
   set JIRA_API_TOKEN=your_api_token
   python jira_html_to_text_agent.py --issue OCTA-12345
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from html import unescape
from typing import Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class JiraConfig:
    base_url: str
    email: str
    api_token: str


class JiraHtmlToTextAgent:
    def __init__(self, jira_config: Optional[JiraConfig] = None) -> None:
        self.jira_config = jira_config

    def convert_html_to_text(self, html: str) -> str:
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")

        # Keep list item boundaries visible in text output.
        for li in soup.find_all("li"):
            if li.string:
                li.string = f"- {li.string}"
            else:
                li.insert(0, "- ")

        text = soup.get_text("\n")
        text = unescape(text)

        # Normalize excessive whitespace while preserving intentional line breaks.
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = "\n".join(line.strip() for line in text.split("\n"))
        text = re.sub(r"[ \t]{2,}", " ", text)

        return text.strip()

    def fetch_rendered_description_html(self, issue_key: str) -> str:
        if self.jira_config is None:
            raise ValueError(
                "Jira configuration is required for --issue mode. "
                "Set JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN."
            )

        url = (
            f"{self.jira_config.base_url.rstrip('/')}/rest/api/3/issue/{issue_key}"
            "?fields=description&expand=renderedFields"
        )
        response = requests.get(
            url,
            auth=(self.jira_config.email, self.jira_config.api_token),
            headers={"Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        rendered_fields = data.get("renderedFields", {})
        html_description = rendered_fields.get("description")

        if not html_description:
            raise ValueError(
                "No rendered HTML description was found for this issue. "
                "The field may be empty or unavailable."
            )

        return html_description


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Jira description HTML to plain text."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--html", help="Raw HTML string to convert")
    group.add_argument("--html-file", help="Path to a file containing HTML")
    group.add_argument("--issue", help="Jira issue key (for example: OCTA-12345)")

    parser.add_argument(
        "--output",
        help="Optional output file path. If omitted, prints to stdout.",
    )
    return parser


def load_jira_config_from_env() -> Optional[JiraConfig]:
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")

    if base_url and email and api_token:
        return JiraConfig(base_url=base_url, email=email, api_token=api_token)

    return None


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    agent = JiraHtmlToTextAgent(jira_config=load_jira_config_from_env())

    try:
        if args.html is not None:
            html_input = args.html
        elif args.html_file is not None:
            with open(args.html_file, "r", encoding="utf-8") as f:
                html_input = f.read()
        else:
            html_input = agent.fetch_rendered_description_html(args.issue)

        plain_text = agent.convert_html_to_text(html_input)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(plain_text)
                f.write("\n")
        else:
            print(plain_text)

        return 0
    except requests.HTTPError as exc:
        print(f"Jira API request failed: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"File not found: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # Defensive catch to keep CLI UX clear.
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
