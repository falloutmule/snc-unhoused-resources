"""Assemble the reviewed phonebook into one self-contained HTML file.

Run only after resource edits are complete. Website hyperlinks intentionally
remain online links; all code, saved entries, styles, and the share QR are inline.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse
import re

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--source', type=Path, default=ROOT / 'phonebook')
parser.add_argument('--output', type=Path, default=ROOT / 'downloads' / 'SNC_Grand_Junction_Offline_Phonebook.html')
args = parser.parse_args()
source_dir = args.source.resolve()
html = (source_dir / 'index.html').read_text(encoding='utf-8')
script_paths = re.findall(r'<script src="([^"]+)"\s*></script>', html)
if len(script_paths) != 13:
    raise ValueError(f'Expected 12 resource files and app.js; found {script_paths}')
script_text = '\n'.join((source_dir / name).read_text(encoding='utf-8') for name in script_paths)
script_text = re.sub(r'</script', lambda _: '<\\/script', script_text, flags=re.I)
html = re.sub(r'<script src="[^"]+"\s*></script>', '', html)
html = re.sub(r'<link rel="(?:manifest|icon)"[^>]*>', '', html)
qr = re.search(r'<svg\b[\s\S]*</svg>', (source_dir / 'share-qr.svg').read_text(encoding='utf-8')).group(0)
qr = qr.replace('<svg', '<svg class="embedded-qr" role="img" aria-label="QR code for the online Grand Junction phonebook"', 1)
html, count = re.subn(r'<img[^>]*data-share-qr[^>]*>', lambda _: qr, html)
if count != 1:
    raise ValueError('Expected exactly one share QR image')
html = html.replace('<html lang="en">', '<html lang="en" data-offline-copy="true">')
html = html.replace('id="installApp">Install on this phone', 'id="installApp">Offline copy help')
html = html.replace('Checking offline availability…', 'Saved offline copy. Website links require internet; calls and texts require phone service.')
html = html.replace('</body>', '<script>' + script_text + '</script>\n</body>')

class Inspect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.external = []
        self.scripts = 0
        self.svg = 0
        self.download = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'script':
            self.scripts += 1
            if 'src' in attrs:
                self.external.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') in ['manifest', 'icon', 'stylesheet']:
            self.external.append(attrs.get('href'))
        if tag == 'img' and 'src' in attrs:
            self.external.append(attrs['src'])
        if tag == 'svg':
            self.svg += 1
        if attrs.get('id') == 'downloadHtml':
            self.download = attrs

check = Inspect()
check.feed(html)
assert not check.external, check.external
assert check.scripts == 1 and check.svg == 1
assert check.download is not None and 'disabled' not in check.download
assert len(check.ids) == len(set(check.ids)), 'Duplicate HTML IDs'
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_bytes(html.encode('utf-8'))
print(f'Created {args.output.resolve()} ({args.output.stat().st_size} bytes); structural checks passed.')
