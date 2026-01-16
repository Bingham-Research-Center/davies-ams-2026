"""Utility for writing analysis reports to markdown files."""
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).parent.parent / 'reports'


def create_report(filename: str) -> 'MarkdownReport':
    """Create a new markdown report file."""
    REPORTS_DIR.mkdir(exist_ok=True)
    return MarkdownReport(REPORTS_DIR / filename)


class MarkdownReport:
    def __init__(self, path: Path):
        self.path = path
        self.lines = []
        self.add_header()

    def add_header(self):
        self.lines.append(f"<!-- Generated: {datetime.now().isoformat()} -->")
        self.lines.append("")

    def add_title(self, title: str):
        self.lines.append(f"# {title}")
        self.lines.append("")

    def add_section(self, heading: str, level: int = 2):
        self.lines.append(f"{'#' * level} {heading}")
        self.lines.append("")

    def add_text(self, text: str):
        self.lines.append(text)
        self.lines.append("")

    def add_table(self, headers: list[str], rows: list[list[str]]):
        # Header row
        self.lines.append("| " + " | ".join(headers) + " |")
        # Separator
        self.lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        # Data rows
        for row in rows:
            self.lines.append("| " + " | ".join(str(c) for c in row) + " |")
        self.lines.append("")

    def add_key_value(self, key: str, value: str):
        self.lines.append(f"- **{key}:** {value}")

    def add_code_block(self, code: str, lang: str = ""):
        self.lines.append(f"```{lang}")
        self.lines.append(code)
        self.lines.append("```")
        self.lines.append("")

    def save(self):
        self.path.write_text("\n".join(self.lines))
        print(f"Saved report to {self.path}")
