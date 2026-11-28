"""Check the static package and optionally exact live GitHub Pages bytes.

The --live check is read-only. It detects 404s, wrong HTML, missing deployment
assets and mismatched versions. It does not replace a phone-browser/offline test.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import Request, urlopen
import argparse
import hashlib
import json
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--live', action='store_true')
args = parser.parse_args()
config = json.loads((ROOT / 'site-config.json').read_text(encoding='utf-8'))
base = config['base_url']
errors = []

class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.ids = []; self.deps = []; self.programs = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'): self.ids.append(attrs['id'])
        if tag == 'article' and 'program' in attrs.get('class', '').split(): self.programs += 1
        for field in ['href', 'src']:
            if field in attrs: self.links.append(attrs[field])
        if tag == 'script' and 'src' in attrs: self.deps.append(attrs['src'])
        if tag == 'img' and 'src' in attrs: self.deps.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') in ['stylesheet', 'icon', 'manifest']: self.deps.append(attrs.get('href'))

for path in [ROOT/'index.html', ROOT/'phonebook/index.html', ROOT/'recovery/index.html', *sorted((ROOT/'downloads').glob('*.html'))]:
    parsed = HTMLLinks(); parsed.feed(path.read_text(encoding='utf-8'))
    if len(parsed.ids) != len(set(parsed.ids)): errors.append(str(path.relative_to(ROOT)) + ': duplicate element IDs')
    if path.parent.name == 'recovery' and parsed.programs != 10: errors.append('Recovery profile count is not 10')
    if path.parent.name == 'downloads' and parsed.deps: errors.append(str(path.relative_to(ROOT)) + ': external rendering dependencies ' + str(parsed.deps))
    for link in parsed.links:
        if not link or link.startswith(('#', 'tel:', 'sms:', 'mailto:', 'data:', 'javascript:')): continue
        if link.startswith(base):
            candidate = ROOT / unquote(urlsplit(link[len(base):]).path)
        elif urlsplit(link).scheme or link.startswith('//'):
            continue
        else:
            candidate = path.parent / unquote(urlsplit(link).path)
        candidate = candidate.resolve()
        if candidate.is_dir(): candidate = candidate / 'index.html'
        # The recovery standalone file deliberately retains a hidden download
        # anchor to its own source page; its script never exposes it as a file.
        if path.parent.name == 'downloads' and link == './index.html': continue
        if not candidate.is_file(): errors.append(str(path.relative_to(ROOT)) + ': missing local target ' + link)

resources = sorted((ROOT/'phonebook').glob('resources-*.js'))
if len(resources) != 12: errors.append('Expected 12 resource-data files')
ids = []
for path in resources:
    ids.extend(re.findall(r'"id"\s*:\s*"([^"]+)"', path.read_text(encoding='utf-8')))
if len(ids) != 58 or len(set(ids)) != 58: errors.append('Expected 58 unique phonebook entries, found ' + str(len(ids)))
for path in ROOT.rglob('*'):
    if path.is_file() and path.suffix in {'.html','.js','.webmanifest'} and '.verification' not in path.parts:
        if 'solidarity-not-charity-can-run/phonebook' in path.read_text(encoding='utf-8'): errors.append(str(path.relative_to(ROOT)) + ': old resource URL remains')
cache = re.search(r"const CACHE_PREFIX = '([^']+)'", (ROOT/'sw.js').read_text(encoding='utf-8')).group(1) + re.search(r"const CACHE = CACHE_PREFIX \+ '([^']+)'", (ROOT/'sw.js').read_text(encoding='utf-8')).group(1)
if cache not in (ROOT/'phonebook/app.js').read_text(encoding='utf-8') or cache not in (ROOT/'recovery/index.html').read_text(encoding='utf-8'): errors.append('Offline cache guard does not match service worker')
shell = json.loads(re.search(r'const APP_SHELL = (\[[\s\S]*?\]);', (ROOT/'sw.js').read_text(encoding='utf-8')).group(1))
for relative in shell:
    target = (ROOT / relative).resolve()
    if target.is_dir(): target = target / 'index.html'
    if not target.is_file(): errors.append('Missing offline shell file: ' + relative)

if errors:
    print('\n'.join('FAIL: ' + error for error in sorted(set(errors))))
    sys.exit(1)
print('PASS: 58 unique local entries, 10 recovery profiles, standalone files, local links and offline cache paths.')

if args.live:
    downloads = sorted((ROOT / 'downloads').glob('*.html'))
    printables = sorted((ROOT / 'print').glob('*.pdf'))
    paths = sorted(set(shell + ['./sw.js'] + ['./' + p.relative_to(ROOT).as_posix() for p in downloads + printables]))
    failures = []
    for relative in paths:
        local = ROOT / relative
        if local.is_dir(): local = local / 'index.html'
        url = urljoin(base, relative)
        try:
            request = Request(url + '?verify=' + str(int(time.time())), headers={'User-Agent':'Mesa-County-resource-publication-check/1.0','Cache-Control':'no-cache'})
            with urlopen(request, timeout=30) as response:
                content = response.read()
                if response.status != 200: raise ValueError('HTTP ' + str(response.status))
            if hashlib.sha256(content).digest() != hashlib.sha256(local.read_bytes()).digest(): raise ValueError('live bytes differ from package')
            print('PASS:', url)
        except Exception as exc:
            failures.append(url + ': ' + str(exc))
    if failures:
        print('\n'.join('FAIL: ' + x for x in failures)); sys.exit(1)
    print('PASS: all checked public routes return the exact package bytes. Browser installation and physical print scanning are separate checks.')
