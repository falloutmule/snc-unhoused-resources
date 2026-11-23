# Corrections and additions

Thank you for helping maintain SNC Unhoused Resources. Corrections, new resources and clearer wording are welcome through [GitHub Issues](https://github.com/falloutmule/snc-unhoused-resources/issues/new/choose) or a pull request.

## A useful report

Please include the resource name, location, requested change, a source link, and the date checked. Official provider pages and direct confirmation are preferred. Describe what was actually confirmed: a working website does not establish current admission, available beds or eligibility.

For a new resource, include its services, public contact number, address or service area, hours, costs, eligibility and any referral requirements. For recovery programs, describe whether the count is staffed beds, design capacity, a campus total or a network total. Distinguish free admission from later charges, work requirements, benefit contributions and medical expenses.

Keep public reports free of personal client information, medical records and unpublished personal contact details. If an official source conflicts with another source, include both instead of guessing which is right.

## Editing

- Phonebook entries live in `phonebook/resources-01.js` through `resources-12.js`. Preserve entry IDs and record the date and scope of the new check in `last_verified`.
- Recovery profiles live in `recovery/index.html`. Keep the Colorado section first, numeric published sizes ascending within each section, and unknown totals and networks after known figures. Keep source conflicts visible.
- If printable program summaries change, update the printable data and regenerate all affected PDFs using the included tools.
- Run `python3 tools/configure_site.py` to rebuild the standalone HTML files and share QR after edits, then `python3 tools/verify_site.py`. The configuration tool does not change source-review dates or publish anything.
- After deployment, run `python3 tools/verify_site.py --live` and test the result in a phone browser, including offline use and a scanned paper QR code.

Do not merge unverified claims of vacancies or universal eligibility. A short, clearly qualified entry is more useful than a confident statement that its sources do not support.
