"""Export a finished gvmd report as PDF, CSV and XML.

Usage: python export_report.py REPORT_ID OUT_DIR

Runs gmp.sh for each format. gvmd returns PDF and CSV base64 encoded
inside the XML response, so those get decoded before saving.
"""
import base64
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

FORMATS = {
    "pdf": "c402cc3e-b531-11e1-9163-406186ea4fc5",
    "csv": "c1645568-627a-11e3-a660-406186ea4fc5",
    "xml": "a994b278-1f62-11e1-96ac-406186ea4fc5",
}
# Same default filter the web UI uses: hide results below 70% quality of detection.
FILTER = "apply_overrides=0 min_qod=70 rows=-1 sort-reverse=severity"

here = pathlib.Path(__file__).parent


def fetch(report_id, fmt_id):
    cmd = (f"<get_reports report_id='{report_id}' format_id='{fmt_id}' "
           f"details='1' ignore_pagination='1' filter='{FILTER}'/>")
    out = subprocess.run(["sh", "gmp.sh", cmd], cwd=here,
                         capture_output=True, check=True).stdout
    return ET.fromstring(out)


def main(report_id, out_dir):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext, fmt_id in FORMATS.items():
        root = fetch(report_id, fmt_id)
        report = root.find("report")
        path = out_dir / f"metasploitable2-openvas.{ext}"
        if ext == "xml":
            path.write_bytes(ET.tostring(report))
        else:
            # The encoded file is the text after the <report_format> child.
            path.write_bytes(base64.b64decode(report.find("report_format").tail))
        print(f"{path} {path.stat().st_size} bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
