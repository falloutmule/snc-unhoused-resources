"""Build SNC's resource overview, recovery directory, and three-page packet.

Run --published only after both actual GitHub Pages URLs are checked.
The source review date is deliberately separate from this packaging date.
"""
from pathlib import Path
import argparse
import html
import json
import re
from datetime import date
from urllib.parse import urlsplit

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--config', type=Path, default=ROOT / 'site-config.json')
parser.add_argument('--base-url', help='Override the base_url in site-config.json.')
parser.add_argument('--repo-url', help='Override the repository in site-config.json.')
parser.add_argument('--published', action='store_true', help='Remove the publication-proof notice after the live URLs are verified.')
parser.add_argument('--output-dir', type=Path, default=ROOT / 'print')
args = parser.parse_args()
CONFIG = json.loads(args.config.read_text(encoding='utf-8')) if args.config.exists() else {}
OUT = args.output_dir
OUT.mkdir(parents=True, exist_ok=True)
BASE = (args.base_url or CONFIG.get('base_url', 'https://falloutmule.github.io/snc-unhoused-resources/')).rstrip('/') + '/'
PHONEBOOK = BASE + 'phonebook/'
RECOVERY = BASE + 'recovery/'
REPO = args.repo_url or 'https://github.com/' + CONFIG.get('repository', 'falloutmule/snc-unhoused-resources')
ISSUES = REPO.rstrip('/') + '/issues'
LIVE = args.published
REVIEW_DATE = CONFIG.get('review_date', '2026-11-19')
PACKAGE_DATE = CONFIG.get('package_date', '2026-11-20')
REVIEW_SHORT = date.fromisoformat(REVIEW_DATE).strftime('%b %d, %Y').replace(' 0', ' ')
PACKAGE_SHORT = date.fromisoformat(PACKAGE_DATE).strftime('%b %d, %Y').replace(' 0', ' ')
ROWS = json.loads((ROOT / 'data/recovery-programs.json').read_text(encoding='utf-8'))

for name, filename in [('Body', 'DejaVuSans.ttf'), ('Bold', 'DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(ROOT / 'assets/fonts' / filename)))

ink = HexColor('#18323b')
teal = HexColor('#00625e')
muted = HexColor('#3f565f')
line = HexColor('#b9c7cc')
styles = {
    'name': ParagraphStyle('name', fontName='Bold', fontSize=12.2, leading=14.6, textColor=ink),
    'meta': ParagraphStyle('meta', fontName='Body', fontSize=8.4, leading=10.3, textColor=muted),
    'body': ParagraphStyle('body', fontName='Body', fontSize=9.2, leading=11.5, textColor=ink),
    'phone': ParagraphStyle('phone', fontName='Bold', fontSize=10.0, leading=12, textColor=teal),
    'url': ParagraphStyle('url', fontName='Body', fontSize=7.7, leading=9.4, textColor=muted),
    'footname': ParagraphStyle('footname', fontName='Bold', fontSize=9.1, leading=11.1, textColor=ink),
    'foot': ParagraphStyle('foot', fontName='Body', fontSize=7.5, leading=9.4, textColor=muted),
    'intro': ParagraphStyle('intro', fontName='Body', fontSize=11.4, leading=15.7, textColor=ink),
    'ovname': ParagraphStyle('ovname', fontName='Bold', fontSize=17.3, leading=21.2, textColor=ink),
    'ovbody': ParagraphStyle('ovbody', fontName='Body', fontSize=11.0, leading=15.3, textColor=ink),
    'ovurl': ParagraphStyle('ovurl', fontName='Bold', fontSize=9.5, leading=12.5, textColor=teal),
    'ovfoot': ParagraphStyle('ovfoot', fontName='Body', fontSize=9.5, leading=13, textColor=muted),
}
manifest = []
measurements = []


def para(c, text, x, top, width, style, maxheight=None):
    p = Paragraph(text, styles[style])
    _, height = p.wrap(width, 700)
    if maxheight is not None and height > maxheight + 0.01:
        raise ValueError((style, text, height, maxheight))
    p.drawOn(c, x, top - height)
    return height


def qr(c, url, x, y, size, filename, page, label):
    widget = QrCodeWidget(url, barLevel='M', barBorder=4)
    a, b, d, e = widget.getBounds()
    scale = size / (d - a)
    drawing = Drawing(size, size, transform=[scale, 0, 0, scale, 0, 0])
    drawing.add(widget)
    c.setFillColor(white)
    c.rect(x, y, size, size, fill=1, stroke=0)
    renderPDF.draw(drawing, c, x, y)
    c.linkURL(url, (x, y, x + size, y + size), relative=0, thickness=0)
    manifest.append({'file': filename, 'page': page, 'label': label, 'url': url,
                     'rect': [x, y, x + size, y + size]})


def printed_url(url):
    parts = urlsplit(url)
    return html.escape(parts.netloc) + '/<br/>' + html.escape(parts.path.lstrip('/'))


def make_overview():
    filename = 'SNC_Unhoused_Resources_Flyer.pdf'
    c = canvas.Canvas(str(OUT / filename), pagesize=(612, 792), pageCompression=1)
    c.setTitle('SNC Unhoused Resources - Two Community Directories')
    c.setAuthor('SNC Unhoused Resources')
    c.setSubject('Printable guide to the local offline phonebook and Colorado and national recovery directory.')
    c.setFillColor(teal)
    c.rect(30, 754, 43, 5, fill=1, stroke=0)
    c.setFont('Bold', 24)
    c.setFillColor(ink)
    c.drawString(30, 722, 'SNC Unhoused Resources')
    para(c, 'Local help and recovery options, with information you can save.',
         30, 705, 552, 'intro', 18)
    para(c, 'Scan a code or type the address. Both directories are free to use.<br/>'
         'Individual services may have costs or eligibility requirements.',
         30, 676, 552, 'ovfoot', 27)

    cards = [
        {'top': 640, 'kicker': '01 / LOCAL SERVICES',
         'name': 'Grand Junction &amp; Mesa County<br/>Offline Phonebook',
         'body': '<b>58 local resource entries</b> for food, shelter, healthcare, transportation, '
                 'legal help, benefits, pet care and other needs.',
         'action': 'Search or browse categories, then use the contact links. Choose '
                   '<b>Download offline HTML</b> to keep a copy on your device.',
         'url': PHONEBOOK, 'label': 'Local offline phonebook'},
        {'top': 397, 'kicker': '02 / RECOVERY OPTIONS',
         'name': 'Colorado &amp; National<br/>Recovery Programs',
         'body': '<b>10 programs and networks:</b> five Colorado programs, three national '
                 'programs and two networks. Includes costs, residency rules, contact details and published size.',
         'action': 'Compare options, check the sources and call intake. Known sizes appear '
                   'smallest first; unknown totals follow. A printable program list is included.',
         'url': RECOVERY, 'label': 'Recovery program directory'},
    ]
    for card in cards:
        top, height = card['top'], 229
        c.setFillColor(HexColor('#fafcfc'))
        c.setStrokeColor(line)
        c.setLineWidth(.7)
        c.roundRect(30, top - height, 552, height, 7, fill=1, stroke=1)
        c.setFillColor(teal)
        c.setFont('Bold', 8.5)
        c.drawString(44, top - 20, card['kicker'])
        t = top - 32
        t -= para(c, card['name'], 44, t, 370, 'ovname', 43)
        t -= 9
        t -= para(c, card['body'], 44, t, 367, 'ovbody', 47)
        t -= 7
        t -= para(c, card['action'], 44, t, 367, 'ovbody', 47)
        t -= 10
        t -= para(c, '<link href="' + card['url'] + '">' + printed_url(card['url']) + '</link>',
                  44, t, 367, 'ovurl', 26)
        measurements.append({'section': card['label'], 'clearance_pt': round(t - (top - height), 2)})
        assert t >= top - height + 9, (card['label'], t, top - height)
        qr(c, card['url'], 432, top - 157, 129, filename, 1, card['label'])
        c.setFillColor(ink)
        c.setFont('Bold', 8.2)
        c.drawCentredString(496.5, top - 170, 'SCAN TO OPEN')

    c.setFillColor(teal)
    c.setFont('Bold', 11)
    c.drawString(30, 146, 'Help keep these resources useful')
    para(c, 'Corrections and additions are welcome. Open an issue on GitHub with the '
         'resource name, the change or new listing, a source link, and the date you checked it.',
         30, 134, 552, 'ovfoot', 27)
    issue_display = ISSUES.replace('https://', '')
    para(c, '<link href="' + ISSUES + '"><b>' + html.escape(issue_display) + '</b></link>',
         30, 102, 552, 'ovfoot', 14)
    c.setStrokeColor(line)
    c.line(30, 78, 582, 78)
    para(c, '<b>Before you go:</b> confirm hours, costs, eligibility and availability. '
         'Saved pages can be read offline; website links need internet, and calls or texts need phone service.',
         30, 69, 552, 'ovfoot', 27)
    c.setFillColor(muted)
    c.setFont('Body', 7.5)
    c.drawString(30, 31, 'Information reviewed ' + REVIEW_SHORT + '  |  Print edition prepared ' + PACKAGE_SHORT)
    if not LIVE:
        c.setFillColor(HexColor('#875400'))
        c.setFont('Bold', 7.5)
        c.drawString(30, 18, 'Publication proof - publish and verify the new QR links before distribution.')
    c.save()
    return OUT / filename


def make_recovery():
    filename = 'SNC_Recovery_Programs.pdf'
    c = canvas.Canvas(str(OUT / filename), pagesize=(612, 792), pageCompression=1)
    c.setTitle('SNC Unhoused Resources - Recovery Programs - Reviewed November 19, 2026')
    c.setAuthor('SNC Unhoused Resources')
    c.setSubject('Ten recovery program summaries with official website QR codes, costs, residency and published capacity caveats.')

    def card(p, top, page):
        x, w, h, tx, tw, qx, qs = 30, 552, 111, 40, 435, 493, 77
        c.setFillColor(HexColor('#fafcfc'))
        c.setStrokeColor(line)
        c.setLineWidth(.55)
        c.roundRect(x, top - h, w, h, 6, fill=1, stroke=1)
        c.setFillColor(teal)
        c.roundRect(x, top - h, 3, h, 1.4, fill=1, stroke=0)
        t = top - 8
        t -= para(c, html.escape(p['flyer_name']), tx, t, tw, 'name', 15)
        t -= 2
        t -= para(c, html.escape(p['flyer_meta']), tx, t, tw, 'meta', 11)
        t -= 4
        t -= para(c, html.escape(p['flyer_summary']), tx, t, tw, 'body', 23.1)
        t -= 2
        t -= para(c, html.escape(p['flyer_rules']), tx, t, tw, 'body', 23.1)
        t -= 4
        if p['id'] == 'caritas':
            phone = 'Men: 804-230-1184  |  Women: 804-418-3049'
        elif p['id'] == 'mission-teens':
            phone = 'Office: 856-782-7771  |  Intake: contact a center'
        elif p['phones']:
            phone = p['phones'][0][1]
        else:
            phone = 'Scan or visit the website to find a center'
        t -= para(c, html.escape(phone), tx, t, tw, 'phone', 12.1)
        display = re.sub(r'^https?://(www\.)?', '', p['website']).rstrip('/')
        t -= 2
        t -= para(c, '<link href="' + html.escape(p['website'], quote=True) + '">' + html.escape(display) + '</link>',
                  tx, t, tw, 'url', 9.5)
        assert t >= top - h + 5, (p['id'], t, top - h)
        qr(c, p['website'], qx, top - qs - 9, qs, filename, page, p['id'])
        c.setFillColor(ink)
        c.setFont('Bold', 6.9)
        c.drawCentredString(qx + qs / 2, top - qs - 18, 'SCAN WEBSITE')
        measurements.append({'id': p['id'], 'bottom_clearance_pt': round(t - (top - h), 2),
                             'text_right': tx + tw, 'qr_left': qx})

    def footer(page):
        c.setStrokeColor(line)
        c.line(30, 97, 582, 97)
        for x, label, url, body in [
            (30, 'Full recovery guide', RECOVERY, 'Sources, detailed rules and updates'),
            (314, 'GJ offline phonebook', PHONEBOOK, '58 local resource entries; save offline'),
        ]:
            qr(c, url, x, 31, 59, filename, page, label)
            para(c, label, x + 65, 87, 199, 'footname', 12)
            para(c, body, x + 65, 73, 199, 'foot', 11)
            short = printed_url(url)
            para(c, '<link href="' + url + '">' + short + '</link>', x + 65, 59, 199, 'foot', 29)
        c.setFillColor(muted)
        c.setFont('Body', 7.1)
        c.drawCentredString(306, 17, 'Confirm medicines, costs and admission before travel. Do not stop prescribed care to qualify.')

    pages = [
        ('COLORADO PROGRAMS', '5 programs | Published size, small to large; unknown totals last.', [p for p in ROWS if p['section'] == 'colorado']),
        ('NATIONAL OPTIONS', '3 nationwide-admission programs, then 2 national networks.', [p for p in ROWS if p['section'] != 'colorado']),
    ]
    for page, (title, subtitle, items) in enumerate(pages, 1):
        c.setFillColor(teal)
        c.setFont('Bold', 9.3)
        c.drawString(30, 764, 'SNC UNHOUSED RESOURCES')
        c.setFillColor(muted)
        c.setFont('Body', 8)
        c.drawRightString(582, 764, 'WEB REVIEW: ' + REVIEW_SHORT.upper() + '  |  ' + str(page) + '/2')
        c.setFillColor(ink)
        c.setFont('Bold', 21)
        c.drawString(30, 734, title)
        if not LIVE:
            c.setFillColor(HexColor('#875400'))
            c.setFont('Bold', 7.3)
            c.drawString(30, 752, 'Publication proof - publish and verify the new QR links before distribution.')
        c.setFillColor(muted)
        c.setFont('Body', 9)
        c.drawString(30, 715, subtitle)
        c.setFillColor(HexColor('#f8f0dd'))
        c.roundRect(30, 688, 552, 19, 4, fill=1, stroke=0)
        c.setFillColor(HexColor('#61400f'))
        c.setFont('Bold', 8.7)
        c.drawString(39, 694, 'Call before traveling. Published capacity is not a count of open beds.')
        for i, p in enumerate(items):
            card(p, 679 - i * 116, page)
        footer(page)
        c.showPage()
    c.save()
    return OUT / filename


overview = make_overview()
recovery = make_recovery()
packet = OUT / 'SNC_Unhoused_Resources_Print_Packet.pdf'
writer = PdfWriter()
for source in [overview, recovery]:
    writer.append(PdfReader(source))
writer.add_metadata({'/Title': 'SNC Unhoused Resources - Printable Resource Packet', '/Author': 'SNC Unhoused Resources'})
with packet.open('wb') as stream:
    writer.write(stream)

(OUT / 'qr-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
(OUT / 'layout-check.json').write_text(json.dumps(measurements, indent=2), encoding='utf-8')
(OUT / 'build-info.json').write_text(json.dumps({
    'base_url': BASE, 'repository_url': REPO, 'publication_status': 'published' if LIVE else 'pending',
    'source_review_date': REVIEW_DATE, 'print_edition_date': PACKAGE_DATE,
    'files': [overview.name, recovery.name, packet.name], 'qr_instances': len(manifest),
}, indent=2), encoding='utf-8')
print(json.dumps({'files': [str(overview), str(recovery), str(packet)], 'qr_instances': len(manifest), 'publication_status': 'published' if LIVE else 'pending'}))
