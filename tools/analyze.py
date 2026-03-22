"""
Analysis Toolkit — DuckDB + Visualization helpers for CLI workflows.

Usage from CLI:
    python tools/analyze.py query "SELECT * FROM 'data/sales.csv' LIMIT 10"
    python tools/analyze.py chart bar results.csv --x experiment --y accuracy --title "Accuracy"
    python tools/analyze.py diff file1.json file2.json
    python tools/analyze.py report results.csv --output report.html

Usage as module:
    from tools.analyze import DuckDB, Chart, Diff, Report

Requires: pip install duckdb matplotlib pandas
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import duckdb


class DuckDB:
    """Lightweight DuckDB wrapper for analytical queries on local files."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = duckdb.connect(db_path)
        self.conn.execute("SET autoinstall_known_extensions = true")
        self.conn.execute("SET autoload_known_extensions = true")

    def query(self, sql: str) -> list[dict]:
        result = self.conn.execute(sql)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    def query_df(self, sql: str):
        return self.conn.execute(sql).fetchdf()

    def query_table(self, sql: str) -> str:
        df = self.query_df(sql)
        if df.empty:
            return "(no results)"
        return df.to_string(index=False)

    def load_json(self, path: str, table_name: str = "data") -> str:
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_json_auto('{path}')")
        count = self.conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        return f"Loaded {count} rows into '{table_name}'"

    def load_csv(self, path: str, table_name: str = "data") -> str:
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_csv_auto('{path}')")
        count = self.conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
        return f"Loaded {count} rows into '{table_name}'"

    def describe(self, table_name: str = "data") -> str:
        return self.query_table(f"DESCRIBE {table_name}")

    def tables(self) -> list[str]:
        rows = self.query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'")
        return [r["table_name"] for r in rows]

    def close(self):
        self.conn.close()


class Chart:
    """Chart generator using matplotlib. Saves to PNG."""

    @staticmethod
    def bar(data: list[dict], x: str, y: str, title: str = "", output: str = "chart.png",
            color: str = "#4C78A8", figsize: tuple = (10, 6), sort: bool = True) -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        x_vals = [str(d[x]) for d in data]
        y_vals = [float(d[y]) for d in data]
        if sort:
            pairs = sorted(zip(x_vals, y_vals), key=lambda p: p[1], reverse=True)
            x_vals, y_vals = zip(*pairs) if pairs else ([], [])

        fig, ax = plt.subplots(figsize=figsize)
        bars = ax.bar(x_vals, y_vals, color=color, edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, y_vals):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(y_vals)*0.01,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=9)
        ax.set_title(title or f"{y} by {x}", fontsize=14, fontweight="bold")
        ax.set_xlabel(x, fontsize=11)
        ax.set_ylabel(y, fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(output, dpi=150, bbox_inches="tight")
        plt.close()
        return os.path.abspath(output)

    @staticmethod
    def line(data: list[dict], x: str, y: str, title: str = "", output: str = "chart.png",
             color: str = "#4C78A8", figsize: tuple = (10, 6)) -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        x_vals = [str(d[x]) for d in data]
        y_vals = [float(d[y]) for d in data]
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(x_vals, y_vals, color=color, marker="o", linewidth=2, markersize=6)
        for xi, yi in zip(x_vals, y_vals):
            ax.annotate(f'{yi:.1f}', (xi, yi), textcoords="offset points",
                       xytext=(0, 10), ha='center', fontsize=9)
        ax.set_title(title or f"{y} over {x}", fontsize=14, fontweight="bold")
        ax.set_xlabel(x, fontsize=11)
        ax.set_ylabel(y, fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(output, dpi=150, bbox_inches="tight")
        plt.close()
        return os.path.abspath(output)

    @staticmethod
    def grouped_bar(data: list[dict], x: str, groups: list[str], title: str = "",
                    output: str = "chart.png", figsize: tuple = (12, 6)) -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        x_vals = [str(d[x]) for d in data]
        n_groups = len(groups)
        bar_width = 0.8 / n_groups
        indices = np.arange(len(x_vals))
        colors = ["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B", "#EECA3B"]

        fig, ax = plt.subplots(figsize=figsize)
        for i, group in enumerate(groups):
            values = [float(d.get(group, 0)) for d in data]
            offset = (i - n_groups/2 + 0.5) * bar_width
            ax.bar(indices + offset, values, bar_width, label=group,
                   color=colors[i % len(colors)], edgecolor="white", linewidth=0.5)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.set_xticks(indices)
        ax.set_xticklabels(x_vals, rotation=45, ha="right")
        ax.legend()
        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        plt.savefig(output, dpi=150, bbox_inches="tight")
        plt.close()
        return os.path.abspath(output)

    @staticmethod
    def heatmap(data: list[dict], x: str, y: str, value: str, title: str = "",
                output: str = "chart.png", figsize: tuple = (10, 8)) -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd

        df = pd.DataFrame(data)
        pivot = df.pivot(index=y, columns=x, values=value)
        fig, ax = plt.subplots(figsize=figsize)
        im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                if not pd.isna(val):
                    ax.text(j, i, f'{val:.1f}', ha="center", va="center", fontsize=9)
        ax.set_title(title, fontsize=14, fontweight="bold")
        plt.colorbar(im, ax=ax)
        plt.tight_layout()
        plt.savefig(output, dpi=150, bbox_inches="tight")
        plt.close()
        return os.path.abspath(output)


class Diff:
    """Compare JSON/text files with meaningful diffs."""

    @staticmethod
    def json_diff(file1: str, file2: str) -> dict:
        with open(file1) as f:
            data1 = json.load(f)
        with open(file2) as f:
            data2 = json.load(f)
        return Diff._deep_diff(data1, data2, "")

    @staticmethod
    def _deep_diff(d1: Any, d2: Any, path: str) -> dict:
        changes = {"added": [], "removed": [], "changed": []}
        if isinstance(d1, dict) and isinstance(d2, dict):
            all_keys = set(d1.keys()) | set(d2.keys())
            for key in sorted(all_keys):
                kpath = f"{path}.{key}" if path else key
                if key not in d1:
                    changes["added"].append({"path": kpath, "value": d2[key]})
                elif key not in d2:
                    changes["removed"].append({"path": kpath, "value": d1[key]})
                elif d1[key] != d2[key]:
                    if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                        sub = Diff._deep_diff(d1[key], d2[key], kpath)
                        changes["added"].extend(sub["added"])
                        changes["removed"].extend(sub["removed"])
                        changes["changed"].extend(sub["changed"])
                    elif isinstance(d1[key], list) and isinstance(d2[key], list):
                        changes["changed"].append({"path": kpath, "old_len": len(d1[key]), "new_len": len(d2[key])})
                    else:
                        changes["changed"].append({"path": kpath, "old": d1[key], "new": d2[key]})
        elif d1 != d2:
            changes["changed"].append({"path": path or "(root)", "old": str(d1)[:100], "new": str(d2)[:100]})
        return changes

    @staticmethod
    def text_diff(file1: str, file2: str, context_lines: int = 3) -> str:
        import difflib
        with open(file1) as f:
            lines1 = f.readlines()
        with open(file2) as f:
            lines2 = f.readlines()
        diff = difflib.unified_diff(lines1, lines2,
                                     fromfile=os.path.basename(file1),
                                     tofile=os.path.basename(file2),
                                     n=context_lines)
        return "".join(diff) or "(no differences)"


class Report:
    """Generate HTML reports from data."""

    @staticmethod
    def from_data(title: str, sections: list[dict], output: str = "report.html") -> str:
        html_parts = [
            "<!DOCTYPE html>", "<html><head>",
            f"<title>{title}</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #333; }",
            "h1 { color: #0078D4; border-bottom: 2px solid #0078D4; padding-bottom: 10px; }",
            "h2 { color: #444; margin-top: 30px; }",
            "table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
            "th { background: #f0f0f0; text-align: left; padding: 10px 12px; border: 1px solid #ddd; }",
            "td { padding: 8px 12px; border: 1px solid #ddd; }",
            "tr:nth-child(even) { background: #fafafa; }",
            "pre { background: #f5f5f5; padding: 15px; border-radius: 6px; overflow-x: auto; }",
            "img { max-width: 100%; border: 1px solid #eee; border-radius: 4px; }",
            ".metric { display: inline-block; padding: 15px 25px; margin: 5px; background: #f0f7ff; border-left: 4px solid #0078D4; }",
            ".metric .value { font-size: 24px; font-weight: bold; color: #0078D4; }",
            ".metric .label { font-size: 12px; color: #666; }",
            "</style>", "</head><body>",
            f"<h1>{title}</h1>",
        ]
        for section in sections:
            html_parts.append(f"<h2>{section['title']}</h2>")
            stype = section.get("type", "text")
            if stype == "table" and isinstance(section["content"], list):
                if section["content"]:
                    keys = section["content"][0].keys()
                    html_parts.append("<table>")
                    html_parts.append("<tr>" + "".join(f"<th>{k}</th>" for k in keys) + "</tr>")
                    for row in section["content"]:
                        html_parts.append("<tr>" + "".join(f"<td>{row.get(k, '')}</td>" for k in keys) + "</tr>")
                    html_parts.append("</table>")
            elif stype == "image":
                html_parts.append(f'<img src="{section["content"]}" alt="{section["title"]}">')
            elif stype == "metrics" and isinstance(section["content"], dict):
                for label, value in section["content"].items():
                    html_parts.append(f'<div class="metric"><div class="value">{value}</div><div class="label">{label}</div></div>')
            else:
                html_parts.append(f"<pre>{section['content']}</pre>")
        html_parts.extend(["</body></html>"])
        with open(output, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))
        return os.path.abspath(output)


def main():
    parser = argparse.ArgumentParser(description="Analysis Toolkit — DuckDB + Charts + Diff")
    sub = parser.add_subparsers(dest="command")

    q = sub.add_parser("query", help="Run a DuckDB SQL query")
    q.add_argument("sql", help="SQL query string")

    c = sub.add_parser("chart", help="Generate a chart")
    c.add_argument("type", choices=["bar", "line", "grouped_bar", "heatmap"])
    c.add_argument("file", help="Input CSV/JSON file")
    c.add_argument("--x", required=True)
    c.add_argument("--y", required=True)
    c.add_argument("--title", default="")
    c.add_argument("--output", default="chart.png")

    d = sub.add_parser("diff", help="Diff two files")
    d.add_argument("file1")
    d.add_argument("file2")
    d.add_argument("--type", choices=["json", "text"], default="text")

    args = parser.parse_args()

    if args.command == "query":
        db = DuckDB()
        print(db.query_table(args.sql))
        db.close()
    elif args.command == "chart":
        db = DuckDB()
        data = db.query(f"SELECT * FROM read_csv_auto('{args.file}')")
        db.close()
        chart_fn = getattr(Chart, args.type)
        path = chart_fn(data, args.x, args.y, title=args.title, output=args.output)
        print(f"Chart saved to: {path}")
    elif args.command == "diff":
        if args.type == "json":
            result = Diff.json_diff(args.file1, args.file2)
            print(json.dumps(result, indent=2))
        else:
            print(Diff.text_diff(args.file1, args.file2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
