# Mesa County Unhoused Resources

Practical, source-linked resources for people experiencing homelessness or housing instability, and for neighbors and volunteers helping them find support.

**Publication status: published; verify the live routes after every deployment.** The Mesa County edition was prepared November 28, 2026. The source review was completed November 19, 2026. Individual phonebook entries retain the date and scope of their checks.

## Resources

| Resource | What it includes | Public address |
| --- | --- | --- |
| Resource home | A simple starting page with links, offline files, printables and ways to suggest updates. | https://falloutmule.github.io/mesa-county-unhoused-resources/ |
| Grand Junction offline phonebook | 58 entries covering Grand Junction and immediately relevant Mesa County services: basic needs, shelter, food, health care, transportation, benefits, legal help and more. Search and categories, Call or Text actions where supported, source links and Print all. | https://falloutmule.github.io/mesa-county-unhoused-resources/phonebook/ |
| Recovery programs | 5 Colorado options, 3 national programs and 2 national networks. Summaries, cost exceptions, residency rules, contact numbers, sources and published capacity information. Colorado comes first; published figures run smallest to largest, with unknown totals afterward. | https://falloutmule.github.io/mesa-county-unhoused-resources/recovery/ |

The national section is a focused shortlist. It is not a complete national directory or a promise that every applicant qualifies. Capacity figures describe the source's stated scope and **do not show current openings**. Free-entry programs can have later costs or benefit contributions.

## Print and share

The `print/` folder contains US Letter PDFs:

- One-page introduction with a summary and QR code for each resource page. [Resource overview flyer](print/Mesa_County_Unhoused_Resources_Flyer.pdf)
- Two-page program list with summaries, phone contacts and individual program website QR codes. [Recovery program list](print/Mesa_County_Recovery_Programs.pdf)
- All three pages together for printing. [Complete print packet](print/Mesa_County_Unhoused_Resources_Print_Packet.pdf)

The resource-page QR codes use the addresses above. Program website QR codes point directly to the listed operators. Verify the live routes and scan the regenerated printables after every URL change.

## Keep a copy offline

- In either resource, choose **Download offline HTML**. The saved file includes its entries, styles and JavaScript. The `downloads/` folder also contains prebuilt standalone copies.
- On the hosted site, the phonebook can be added to the home screen when the browser supports it. Wait for **Ready offline** before relying on the browser's saved copy.
- The service worker saves the resource home, phonebook and recovery guide. **PDFs and downloadable HTML files must be downloaded separately.** Provider websites need internet; calls and texts need phone service.
- A saved HTML file is a snapshot. Download a new copy when the information changes. Some Android file viewers do not run HTML scripts; open the saved file in a browser that supports local HTML.

## Corrections and additions are welcome

To suggest a correction or addition, submit a pull request, give the information to the person who shared the resource, or [open an issue using the correction or addition form](https://github.com/falloutmule/mesa-county-unhoused-resources/issues/new/choose).

Include:

1. The resource or program name, city and the page or entry involved.
2. What should change or what should be added.
3. An official website, current flyer, or the date and method of direct confirmation.
4. Current public phone numbers, eligibility, hours, costs and location when relevant.

Please distinguish **bed capacity** from **currently available beds**, and tell us whether a service is local-only, Colorado-only or open to out-of-state applicants. Do not include personal client information, private medical details, or unpublished staff contact information in a public issue. See [CONTRIBUTING.md](CONTRIBUTING.md) for the editing checklist.

## Accuracy and limitations

Program hours, funding, costs, residency requirements and admission rules can change. Call before traveling or arranging admission. The November review included targeted source/contact checks for all 58 phonebook entries and a review of all 10 recovery profiles; it did not include telephone confirmation of every listing or current vacancies. Unresolved items are labeled in the resources.

Notable source conflicts are retained rather than silently resolved: Sage Ridge residency wording, Stout Street program duration and CARITAS capacity. TOSA and TROSA current total capacities remain unverified. Eleven local entries have fields still needing provider confirmation. Source links and entry-specific notes explain the limits.

Do not stop prescribed treatment to meet a program's listed restrictions. Discuss medication compatibility directly with the program and your clinician.

## Repository structure

```text
index.html                         Resource home
phonebook/                         Phonebook UI and 12 resource-data files
recovery/index.html                Self-contained recovery directory
downloads/                         Standalone HTML copies
print/                             Printable PDFs
sw.js                              Project-scoped offline cache
site-config.json                   Public URLs and publication status
tools/                             Regeneration and verification scripts
.github/ISSUE_TEMPLATE/             Correction and addition forms
CODEX_HANDOFF.md                    Public GitHub Pages deployment instructions
```

This is a static website. No account, backend, database, API key, tracking service or build framework is required to read it. GitHub is required only to host it or submit issues and changes.

For local review without a server, open either standalone HTML file in `downloads/`. For a full-site preview, follow the local HTTP preview instructions in `CODEX_HANDOFF.md`.

## Publishing and maintenance

GitHub Pages serves the root of `main` in `falloutmule/mesa-county-unhoused-resources`. Keep this project separate from the existing game repository and its draft PR #39. Follow the [deployment and verification instructions](CODEX_HANDOFF.md).

If the repository name or owner changes, run the configuration script and regenerate the printables before sharing any QR codes. Do not change the source-review date just because the files were repackaged.
