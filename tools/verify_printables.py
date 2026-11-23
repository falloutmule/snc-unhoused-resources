"""Check vector-PDF text, page sizes, annotations and rendered QR targets.

Optional QA dependencies: PyMuPDF, Pillow, zxing-cpp. This does not test whether
the QR destinations are published. Verify that separately before --published.
"""
from pathlib import Path
import argparse
import json
import fitz
from PIL import Image
import zxingcpp

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir', type=Path, default=ROOT / 'print')
args = parser.parse_args()
OUT = args.output_dir
manifest = json.loads((OUT / 'qr-manifest.json').read_text(encoding='utf-8'))
info = json.loads((OUT / 'build-info.json').read_text(encoding='utf-8'))
results = []
opened = {}

for item in manifest:
    filename = item['file']
    if filename not in opened:
        opened[filename] = fitz.open(OUT / filename)
    page = opened[filename][item['page'] - 1]
    assert tuple(page.rect) == (0.0, 0.0, 612.0, 792.0), (filename, page.rect)
    x0, y0, x1, y1 = item['rect']
    clip = fitz.Rect(x0 - 2, 792 - y1 - 2, x1 + 2, 792 - y0 + 2)
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=clip, alpha=False)
    image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    codes = zxingcpp.read_barcodes(image)
    values = [code.text for code in codes]
    assert values == [item['url']], (filename, item['page'], item['label'], values, item['url'])
    results.append({'file': filename, 'page': item['page'], 'label': item['label'],
                    'expected': item['url'], 'decoded': values[0], 'dpi': 180, 'pass': True})

packet = fitz.open(OUT / 'SNC_Unhoused_Resources_Print_Packet.pdf')
assert len(packet) == 3
assert len(opened['SNC_Unhoused_Resources_Flyer.pdf']) == 1
assert len(opened['SNC_Recovery_Programs.pdf']) == 2
for page in packet:
    text = page.get_text()
    assert 'SNC UNHOUSED RESOURCES' in text.upper()
    assert 'solidarity-not-charity-can-run' not in text
    assert ('Publication proof' in text) == (info['publication_status'] == 'pending')
    for block in page.get_text('dict')['blocks']:
        if block['type'] != 0:
            continue
        for line in block['lines']:
            for span in line['spans']:
                x0, y0, x1, y1 = span['bbox']
                assert x0 >= 28 and x1 <= 584 and y0 >= 12 and y1 <= 780, span

summary = {'pass': True, 'rendered_qr_instances_checked': len(results), 'pages': {'overview': 1, 'recovery': 2, 'packet': 3},
           'publication_status': info['publication_status'], 'validation': results,
           'limits': ['No live-URL availability test in this script.', 'No physical print or phone-camera test.']}
(OUT / 'print-validation.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k != 'validation'}))
