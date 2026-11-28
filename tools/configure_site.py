"""Configure public URLs and rebuild sharing QR / standalone HTML. Never publishes.

Usage: python3 tools/configure_site.py [--base-url https://OWNER.github.io/REPO/]
       [--repository OWNER/REPO] [--publication-status pending|published]

Requires reportlab (also used by the PDF generator). A publication-status change
is an editorial label, not proof of deployment; run verify_site.py --live first.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url')
parser.add_argument('--repository')
parser.add_argument('--publication-status', choices=['pending', 'published'])
args = parser.parse_args()
config_path = ROOT / 'site-config.json'
config = json.loads(config_path.read_text(encoding='utf-8'))
old_base, old_repo = config['base_url'], config['repository']
base = (args.base_url or old_base).rstrip('/') + '/'
repo = args.repository or old_repo
parsed = urlparse(base)
if parsed.scheme != 'https' or not parsed.netloc or parsed.query or parsed.fragment:
    parser.error('base-url must be an absolute HTTPS URL without a query or fragment')
if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
    parser.error('repository must be OWNER/REPOSITORY')
status = args.publication_status or config.get('publication_status', 'pending')

# Replace only the project's old URLs. Provider source URLs and source-review
# dates are not touched. Derived QR and downloads are regenerated below.
for path in ROOT.rglob('*'):
    if not path.is_file() or any(x in {'.git', '.verification', 'downloads', 'print', 'assets'} for x in path.relative_to(ROOT).parts):
        continue
    if path.suffix not in {'.html', '.js', '.md', '.json', '.webmanifest', '.yml', '.txt'}:
        continue
    if path == config_path:
        continue
    text = path.read_text(encoding='utf-8')
    updated = text.replace(old_base, base).replace(old_repo, repo)
    updated = updated.replace(old_base.removeprefix('https://'), base.removeprefix('https://'))
    if text != updated:
        path.write_bytes(updated.encode('utf-8'))

config.update(base_url=base, repository=repo, publication_status=status)
config_path.write_bytes((json.dumps(config, indent=2) + '\n').encode('utf-8'))

home_path = ROOT / 'index.html'
home = home_path.read_text(encoding='utf-8')
home = re.sub(r'<div class="pending" id="publication-notice"(?: hidden)?>',
              '<div class="pending" id="publication-notice"' + (' hidden' if status == 'published' else '') + '>', home)
if status == 'published':
    home = home.replace('Planned home address:', 'Home address:')
    home = home.replace('The GitHub reporting link becomes available after the public repository is created. You can also give the information to the person who shared this resource.',
                        'You can also give the information to the person who shared this resource.')
else:
    home = home.replace('Home address:', 'Planned home address:')
    home = home.replace('<p class="note">You can also give the information to the person who shared this resource.</p>',
                        '<p class="note">The GitHub reporting link becomes available after the public repository is created. You can also give the information to the person who shared this resource.</p>')
home_path.write_bytes(home.encode('utf-8'))
readme_path = ROOT / 'README.md'
readme = readme_path.read_text(encoding='utf-8')
pending = '**Publication status: prepared for deployment; the new public repository and GitHub Pages URLs have not been verified.**'
published = '**Publication status: published; verify the live routes after every deployment.**'
readme = readme.replace(pending if status == 'published' else published, published if status == 'published' else pending)
if status == 'published':
    readme = readme.replace('Planned public address', 'Public address')
    readme = readme.replace('The resource-page QR codes use the planned addresses above. **Do not distribute them as live links until GitHub Pages is deployed and checked.** Program website QR codes point directly to the listed operators. The draft printables carry a publication-pending notice; the handoff explains how to regenerate them after deployment.',
                            'The resource-page QR codes use the addresses above. Program website QR codes point directly to the listed operators. Verify the live routes and scan the regenerated printables after every URL change.')
else:
    readme = readme.replace('| Public address |', '| Planned public address |')
    readme = readme.replace('The resource-page QR codes use the addresses above. Program website QR codes point directly to the listed operators. Verify the live routes and scan the regenerated printables after every URL change.',
                            'The resource-page QR codes use the planned addresses above. **Do not distribute them as live links until GitHub Pages is deployed and checked.** Program website QR codes point directly to the listed operators. The draft printables carry a publication-pending notice; the handoff explains how to regenerate them after deployment.')
readme_path.write_bytes(readme.encode('utf-8'))

try:
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing, Rect
    from reportlab.graphics import renderSVG
    from reportlab.lib.colors import white
except ImportError:
    raise SystemExit('Install print dependencies first: python3 -m pip install -r requirements-print.txt')
qr = QrCodeWidget(base + 'phonebook/', barLevel='M', barBorder=4)
x, y, x2, y2 = qr.getBounds()
drawing = Drawing(x2-x, y2-y)
drawing.add(Rect(x, y, x2-x, y2-y, fillColor=white, strokeColor=None))
drawing.add(qr)
with (ROOT / 'phonebook' / 'share-qr.svg').open('w', encoding='utf-8', newline='\n') as svg:
    renderSVG.drawToFile(drawing, svg)

# Change the cache whenever the saved app changes. Normalize its own cache name
# before hashing so a repeated build is stable instead of hashing itself forever.
worker_path = ROOT / 'sw.js'
worker = worker_path.read_text(encoding='utf-8')
old_version = re.search(r"const CACHE = CACHE_PREFIX \+ '([^']+)'", worker).group(1)
prefix = re.search(r"const CACHE_PREFIX = '([^']+)'", worker).group(1)
current_cache = prefix + old_version
core_paths = [ROOT/'index.html', ROOT/'recovery/index.html', worker_path] + sorted((ROOT/'phonebook').iterdir())
digest = hashlib.sha256()
for path in core_paths:
    if not path.is_file(): continue
    text = path.read_text(encoding='utf-8').replace(current_cache, '__PROJECT_CACHE__')
    if path == worker_path:
        text = re.sub(r"const CACHE = CACHE_PREFIX \+ '[^']+'", "const CACHE = CACHE_PREFIX + '__VERSION__'", text)
    digest.update(path.relative_to(ROOT).as_posix().encode('utf-8') + b'\0' + text.encode('utf-8'))
new_version = 'v1-' + digest.hexdigest()[:12]
new_cache = prefix + new_version
worker = worker.replace("const CACHE = CACHE_PREFIX + '" + old_version + "'", "const CACHE = CACHE_PREFIX + '" + new_version + "'")
worker_path.write_bytes(worker.encode('utf-8'))
for path in [ROOT/'phonebook/app.js', ROOT/'recovery/index.html']:
    updated = path.read_text(encoding='utf-8').replace(current_cache, new_cache)
    path.write_bytes(updated.encode('utf-8'))

subprocess.run([sys.executable, str(ROOT / 'tools' / 'build_offline_phonebook.py')], check=True)
recovery = (ROOT / 'recovery' / 'index.html').read_text(encoding='utf-8')
recovery = recovery.replace('<html lang="en">', '<html lang="en" data-offline-copy="true">')
(ROOT / 'downloads').mkdir(exist_ok=True)
(ROOT / 'downloads' / 'Mesa_County_Recovery_Programs.html').write_bytes(recovery.encode('utf-8'))
print('Configured:', base, '| repository:', repo, '| publication label:', status)
print('Rebuilt phonebook sharing QR and both standalone HTML files. No remote writes were made.')
print('Regenerate PDFs next: python3 tools/build_printables.py' + (' --published' if status == 'published' else ''))
