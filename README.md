# SJB-personal

Jira HTML-to-Text Agent

This repository includes a small CLI agent that converts a Jira ticket description from HTML to plain text.

Files
- jira_html_to_text_agent.py: Main agent script
- requirements.txt: Python dependencies

Setup
1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

	pip install -r requirements.txt

Usage

Convert an inline HTML string:

python jira_html_to_text_agent.py --html "<p>Hello <b>world</b></p>"

Convert HTML from a file:

python jira_html_to_text_agent.py --html-file description.html

Fetch rendered Jira description HTML and convert it:
1. Set environment variables:

	set JIRA_BASE_URL=https://your-domain.atlassian.net
	set JIRA_EMAIL=you@example.com
	set JIRA_API_TOKEN=your_api_token

2. Run:

	python jira_html_to_text_agent.py --issue OCTA-12345

Write output to a file:

python jira_html_to_text_agent.py --issue OCTA-12345 --output description.txt