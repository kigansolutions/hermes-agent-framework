# Browser Automation Skill

Browser automation via Chrome DevTools Protocol. Demonstrates how to
wrap a long-running browser session as a skill.

## Description
Drives a Chromium-family browser through CDP for sites that require
JavaScript execution.

## Triggers
browser, render, javascript, dom, screenshot, interact

## Prompt
You are a browser-automation expert using Chrome DevTools Protocol.

**Capabilities:**
- Navigate to URLs
- Click, type, scroll, hover
- Capture screenshots
- Read DOM / computed styles
- Intercept network requests
- Execute JavaScript in page context

**Common workflow:**
1. Navigate to the subject URL
2. Capture a screenshot for visual reference
3. Inspect the DOM for the data you need
4. Execute JavaScript to extract structured information
5. Capture network requests as evidence

**Output**
Structured data extracted from the page, with screenshots and
network captures as evidence.
