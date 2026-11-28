# Publish Mesa County Unhoused Resources

## Publishing scope

**Mesa County Unhoused Resources** is a standalone public repository for the local phonebook, recovery guide, offline downloads and printable summaries with QR codes. The README links to both directories and invites corrections and additions.

Publish this complete static package as its own repository. Do not merge draft PR #39 or change `falloutmule/solidarity-not-charity-can-run`; that older repository contains a separate game and the earlier resource copies.

## Editions and source review

The original package was prepared November 20, 2026. The Mesa County edition was prepared November 28, 2026. The README lists the public addresses and `print/build-info.json` records the print edition. Resource QR codes open the directories. Program QR codes open the operators' websites.

The source review is dated November 19, 2026. Individual phonebook entries record the date and scope of their checks. Preserve those dates and the qualifications about beds, openings, admission, hours and eligibility.

## Configuration and intended addresses

`site-config.json` is the source of truth for the public addresses used below.

| Item | Intended value |
| --- | --- |
| Public repository | `falloutmule/mesa-county-unhoused-resources` |
| Default branch | `main` |
| Pages source | `main`, root `/` |
| Home | https://falloutmule.github.io/mesa-county-unhoused-resources/ |
| Phonebook | https://falloutmule.github.io/mesa-county-unhoused-resources/phonebook/ |
| Recovery guide | https://falloutmule.github.io/mesa-county-unhoused-resources/recovery/ |

Keep the lower-case path spelling and trailing slashes. No custom domain or purchased URL is required. Do not silently choose another owner or repository name if these are unavailable; resolve the conflict with the user.

## 1. Inspect and validate the package

Extract the ZIP and work in the folder containing this README and `index.html`. Do not publish the ZIP itself as the website. Do not include scratch folders, credentials, local caches or unrelated files.

For direct local review, open the standalone HTML files in `downloads/`. To preview the complete website with its clean folder URLs, serve the package with `python3 -m http.server 8123 --bind 127.0.0.1` and open `http://127.0.0.1:8123/`. Double-clicking the root `index.html` may show folder listings for the resource links instead of loading their index pages.

Use Python 3. On Windows, replace `python3` below with `py -3` or the available Python 3 executable.

```bash
python3 -m pip install -r requirements-print.txt
python3 tools/configure_site.py
python3 tools/build_printables.py
python3 tools/verify_site.py
node tools/verify_behavior.cjs
```

The configuration tool updates project URLs, generates the phonebook sharing QR, rebuilds both standalone HTML files, and derives a fresh offline cache version from the app content. It does not publish, recheck provider facts or change source-review dates. PDFs are regenerated separately by the print tool.

If any public path must change, update it with the configuration tool and rebuild all QR-bearing files:

```bash
python3 tools/configure_site.py --base-url https://falloutmule.github.io/mesa-county-unhoused-resources/ --repository falloutmule/mesa-county-unhoused-resources
python3 tools/build_printables.py
python3 tools/verify_site.py
```

For printable QA, see `PRINTING.md`. The included QR verifier uses the optional `requirements-print-qa.txt` dependencies. Confirm the PDFs remain one overview page plus two recovery pages with no clipped text. The Node behavioral checks use the built-in Node modules only and exercise key phonebook/offline flows with mocks; they are not a physical-device test.

## 2. Create or inspect the public repository

Check the authenticated account and access first. Use the configured repository value.

```bash
gh auth status
gh api user --jq .login
gh repo view falloutmule/mesa-county-unhoused-resources --json nameWithOwner,isPrivate,defaultBranchRef,url
```

If it already exists, inspect its contents and history before adding anything. Do not overwrite unrelated work, force-push, or change an existing private repository to public without checking what it contains. The authorization is to publish this resource package.

If it does not exist and the authenticated owner is correct, initialize this package and create the public repository:

```bash
git init -b main
git add .
git commit -m "Add Mesa County Unhoused Resources directories and printables"
gh repo create falloutmule/mesa-county-unhoused-resources --public --description "Grand Junction and Mesa County offline phonebook, recovery programs, and printable QR resource guides" --source=. --remote=origin --push
```

Verify visibility with `gh repo view` after creation. Enable Issues so the README's correction and addition forms work:

```bash
gh repo edit falloutmule/mesa-county-unhoused-resources --enable-issues
```

## 3. Enable GitHub Pages explicitly

A public repository alone does not publish a website. Configure Pages to deploy from **main / (root)**. The `.nojekyll` file is already included. Use Settings → Pages → Deploy from a branch, or the official Pages API.

Check current configuration first:

```bash
gh api repos/falloutmule/mesa-county-unhoused-resources/pages
```

If Pages is not configured, create it:

```bash
gh api --method POST repos/falloutmule/mesa-county-unhoused-resources/pages -f "source[branch]=main" -f "source[path]=/"
```

If Pages already exists with the wrong source, inspect it and use the matching update operation or Settings UI. Do not interpret an authorization failure as a request to create another repository.

Check the Pages build status and canonical HTML URL; wait for completion rather than claiming deployment immediately:

```bash
gh api repos/falloutmule/mesa-county-unhoused-resources/pages
gh api repos/falloutmule/mesa-county-unhoused-resources/pages/builds/latest
```

## 4. Prove the public routes work

Run:

```bash
python3 tools/verify_site.py --live
```

This checks the home, both resource routes, JavaScript, icons, manifest, service worker, standalone HTML files and PDFs against the package's exact bytes. All must return HTTP 200 with the intended content. A generic successful HTTP response is insufficient: GitHub may serve an error document or an older build.

Open both resource pages in a phone browser. Check search, filters, phone actions, cross-resource links and downloaded HTML. Wait for Ready offline, then disconnect and reopen both resource routes. PDFs and downloaded files are separate from the browser app cache; save them explicitly. Do not describe a code-only check as an Android installation test.

Scan the two resource QR codes and several program codes from a real printed copy. Confirm they resolve to the correct pages. Keep written URLs on the flyer.

If a physical phone or printer is unavailable, report those checks as unperformed. They do not block the authorized publication once the automated checks and live-route checks pass. The included rendered-PDF verifier checks QR destinations without a physical printer.

## 5. Produce and deploy the final printables

Only after the public routes pass, change the publication label and regenerate the final PDFs:

```bash
python3 tools/configure_site.py --publication-status published
python3 tools/build_printables.py --published
python3 tools/verify_site.py
git add .
git commit -m "Mark verified Pages publication and finalize printables"
git push
```

Wait for that deployment, then rerun `python3 tools/verify_site.py --live`. This second check catches a final PDF or status update that did not deploy. Provide the user with the verified home, phonebook, recovery guide, public repository, overview PDF, recovery PDF and complete print packet URLs.

## Content and maintenance boundaries

- Preserve all 58 local entries and all 10 recovery program/network profiles, their source links and visible qualifications.
- The Pet Pantry November 21, 2026 distribution is a dated holiday exception; refresh or mark it historical if publication occurs after that date. Do not infer a new recurring schedule from it.
- Keep the Colorado-first, ascending published-capacity order. Unknown totals follow; capacity is not current vacancy.
- Keep the separate scopes of free entry, later fees/contributions, medical costs, residency and admission restrictions.
- Leave the old game repository and its existing service worker/cache untouched. This package uses a unique cache prefix and storage key scoped to the new project.
- No new software/content license was selected. Preserve the included font license and any third-party notices. Ask before adopting a new license on the owner's behalf.

## Official publishing references

- [GitHub CLI: create a repository](https://cli.github.com/manual/gh_repo_create)
- [GitHub Pages publishing-source settings](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub Pages REST API](https://docs.github.com/en/rest/pages/pages)
- [Troubleshooting GitHub Pages 404 errors](https://docs.github.com/en/pages/getting-started-with-github-pages/troubleshooting-404-errors-for-github-pages-sites)
