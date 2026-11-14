"""Self-contained HTML report renderer."""

from pathlib import Path

from jinja2 import Template

from config import BASE_DIR, OUTPUT_DIR


HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>QA Report {{ run_id }}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #172033; background: #f7f8fb; }
    header, section { background: white; border: 1px solid #dde2ea; border-radius: 8px; padding: 20px; margin-bottom: 18px; }
    h1, h2 { margin: 0 0 12px; }
    .meta { color: #536075; line-height: 1.6; }
    .summary { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
    .pill { border-radius: 999px; padding: 8px 12px; background: #eef2f7; font-weight: 700; }
    .pass { color: #087443; }
    .info { color: #1d4ed8; }
    .fail, .error { color: #b42318; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; border-top: 1px solid #e6eaf0; padding: 10px; vertical-align: top; }
    th { color: #536075; font-size: 13px; }
    img { max-width: 180px; border: 1px solid #dde2ea; border-radius: 6px; }
    .detail { max-width: 560px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <header>
    <h1>QA Report</h1>
    <div class="meta">
      <div><strong>Run:</strong> {{ run_id }}</div>
      <div><strong>Target:</strong> {{ target_url }}</div>
      <div><strong>Date:</strong> {{ timestamp }}</div>
    </div>
    <div class="summary">
      <div class="pill">Items: {{ total_tests }}</div>
      <div class="pill pass">Pass: {{ total_pass }}</div>
      <div class="pill fail">Fail/Error: {{ total_fail }}</div>
      <div class="pill info">Info: {{ total_info }}</div>
      <div class="pill">Duration: {{ "%.1f"|format(total_duration_ms / 1000) }}s</div>
    </div>
  </header>

  {% for agent, items in grouped_results.items() %}
  <section>
    <h2>{{ agent }}</h2>
    <table>
      <thead>
        <tr>
          <th>Test</th>
          <th>Status</th>
          <th>Duration</th>
          <th>Detail</th>
          <th>Screenshot</th>
        </tr>
      </thead>
      <tbody>
      {% for item in items %}
        <tr>
          <td>{{ item.test_name }}</td>
          <td class="{{ item.status|lower }}">{{ item.status }}</td>
          <td>{{ item.duration_ms }}ms</td>
          <td class="detail">{{ item.detail }}</td>
          <td>{% if item.screenshot_path %}<img src="{{ screenshot_url(item.screenshot_path) }}" alt="{{ item.test_name }} screenshot">{% endif %}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </section>
  {% endfor %}
</body>
</html>
"""


def screenshot_url(value: str) -> str:
    """Convert a saved screenshot path into a URL served by the FastAPI app."""
    if not value:
        return ""

    path = Path(value)
    screenshots_dir = BASE_DIR / "screenshots"
    try:
        relative = path.resolve().relative_to(screenshots_dir.resolve())
    except (OSError, ValueError):
        return path.as_posix()
    return f"/screenshots/{relative.as_posix()}"


def render_html_report(report_data) -> str:
    """Render the final HTML report and return the output path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_timestamp = report_data["timestamp"].replace(":", "-").replace(" ", "_")
    path = OUTPUT_DIR / f"report_{safe_timestamp}.html"
    html = Template(HTML_TEMPLATE).render(**report_data, screenshot_url=screenshot_url)
    path.write_text(html, encoding="utf-8")
    return str(path)
