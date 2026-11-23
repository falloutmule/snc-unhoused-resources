# Printable resources

The three PDFs in `print/` are US Letter documents with selectable text,
embedded fonts, clickable links, and vector QR codes:

- `SNC_Unhoused_Resources_Flyer.pdf`: one-page overview of the local phonebook
  and recovery guide, with a summary and QR code for each.
- `SNC_Recovery_Programs.pdf`: two-page list of ten recovery programs and
  networks. Each entry has a summary, contact information, eligibility/cost
  notes, published capacity information, and a QR code to its provider website.
  Both resource directories are linked by QR on each page.
- `SNC_Unhoused_Resources_Print_Packet.pdf`: the overview followed by both
  recovery pages, combined for convenient printing.

## Print edition

The published PDFs link to the live phonebook and recovery guide on GitHub
Pages. Each program QR code opens the provider's website. The build status
in `print/build-info.json` identifies the edition. A proof build is marked
`pending` and carries a visible notice on every page.

The provider-information review date is November 19, 2026. The packaging date
is November 20, 2026. Rebuilding or publishing a PDF does not perform a new
provider review; do not advance `review_date` without doing that work.

## Rebuild

From the repository root, with Python 3 available:

```bash
python -m pip install -r requirements-print.txt
python tools/build_printables.py
```

The generator reads `site-config.json` (`base_url`, `repository`, `review_date`
and `package_date`), the reviewed program data in
`data/recovery-programs.json`, and bundled fonts in `assets/fonts/`.
It writes PDFs and layout/QR manifests to `print/`.

After publication, verify that the intended landing page and both resource
URLs return HTTP 200, display the intended revised content, and have working
navigation. Then build the distribution version:

```bash
python tools/build_printables.py --published
```

The `--published` flag only removes the proof notice. It does **not** publish
the site or check any URLs. It must only be used after the above checks.

If the repository or Pages address changes, update `site-config.json` using
the repository's configuration tool and rebuild the PDFs. A one-off override
is supported:

```bash
python tools/build_printables.py --base-url https://OWNER.github.io/REPOSITORY/ --repo-url https://github.com/OWNER/REPOSITORY
```

Use `--output-dir PATH` for another destination. Keep manifests with the PDFs
for validation. The DejaVu font notices are preserved in
`assets/fonts/LICENSE.txt`.

## Check before distribution

Render and inspect every page after changing text or URLs. The optional QA
script decodes all QR codes from 180-dpi PDF renders, checks their destinations
against the generated manifest, checks page counts and text bounds, and ensures
the proof notice matches the build status:

```bash
python -m pip install -r requirements-print-qa.txt
python tools/verify_printables.py
```

This check needs no browser or image-generation service. Its decoding test
checks the URL encoded in the QR, not whether that URL is available online.
Print at actual size/100% on US Letter. Test a physical copy with a phone camera
before producing a large batch.
