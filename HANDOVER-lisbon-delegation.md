# Handover: Yorkseed Lisbon Delegation (Web Summit 2026)

Written October 13, 2026, for the next agent picking up this work for Jessica Sophia Wong, founder of Yorkseed. Read the whole thing before changing anything.

## 1. What this is

A paid founder delegation Yorkseed runs at Web Summit Lisbon. Founders who are already attending Web Summit pay per company to travel with Yorkseed: investor introductions, delegate gatherings, a digital Deal Book profile, a December virtual showcase and 6 months of Yorkseed Connect. Investors, LPs and family offices join free. Jessica runs it solo, so every decision favors low manual work.

- **Dates:** November 8 to 12, 2026. Delegation kicks off Nov 8, the day before Web Summit opens (Web Summit itself is Nov 9 to 12).
- **Web Summit ticket:** NOT included and NOT required. The page is open to founders going to Lisbon who are still deciding on a ticket; the master side event spreadsheet covers side events. Copy voice is "we/us" (Yorkseed), never first-person singular.
- **Series hub:** https://yorkseed.co/web-summit-lisbon lists Opening Night, Executive/Capital/Allocator Lunches and the delegation. Keep it, sitemap.xml, llms.txt and llms-full.txt in sync when dates or links change.
- **Introductions are not guaranteed.** Do not reintroduce "first in line" or "we will introduce you" language.
- **Live page:** https://yorkseed.co/lisbon-delegation
- **Target size:** about 20 companies total. Founding rate capped at 10.

## 2. Pricing (final)

| Package | Price | Notes |
|---|---|---|
| Founding Delegation | €495 / company | First 10 companies only, 1 delegate |
| Delegation (Standard) | €595 / company | After founding sells out, 1 delegate |
| Premium Delegation | €695 / company | Limit 5. Featured Deal Book spread, first in line for intros and showcase |
| Additional delegate | €175 each | Same company, up to 3 |
| Investor / LP / Family office | Free | Application only, no checkout |
| Partner Delegate (added Oct 17) | €995 / company | Executives, corporates, advisors, law firms, banks, recruiters, EOR/payroll, consultants. Labeled Partner profile in the Deal Book, delegate group and selected gatherings, 3 months of Yorkseed Connect (founders get 6), relevant connections. Must offer delegates a perk. Stripe link: https://buy.stripe.com/9B628k5or6Sy43K0kdbo40q (send to approved partners). |

Priced per company, not per person. Refund policy on the page: every delegate is reviewed; if not a fit, full refund within 48 hours.

## 3. What's included (as promised on the site)

1. Introductions to investors and partners in Lisbon matched to stage and sector
2. Gatherings: Nov 8 kickoff, Yorkseed meetups, private delegate WhatsApp group, 25% off Yorkseed lunches
3. Profile in the Yorkseed Lisbon Delegation digital Deal Book (profiles due **October 30**)
4. Consideration for the virtual Global Founder Showcase in December (not guaranteed; Premium first)
5. Six months of Yorkseed Connect (app.yorkseed.co), complimentary
6. KoiCard access: 300 scans, November 5 to November 18, 2026, via the access code (send after payment, never post publicly)

## 4. The buying flow (changed Oct 17: approval first)

As of Oct 17 there is ONE application flow and NO payment on the page. "I am joining as": Founder, Partner or Investor, each with its own questions. Every application emails Jessica (subject `Lisbon Delegation: Founder | Acme | Premium`, `Partner | Acme | Legal`, `Investor | Fund`). The email includes "Rate to send if approved" and "Deal Book section" (Companies, Partners, Investors). Jessica approves manually, then emails founders the right Stripe link from section 5, partners the €995 link (https://buy.stripe.com/9B628k5or6Sy43K0kdbo40q), and investors a complimentary confirmation. The Deal Book has three sections: Companies, Partners, Investors.

### Old flow (before Oct 17, kept for reference)

1. Founder fills in the **Yorkseed application form** on yorkseed.co/lisbon-delegation.
2. Form submits to Jessica's inbox via **Web3Forms** (subject like `Lisbon Delegation: Founder | Acme | Premium`).
3. Founder is redirected **straight to Stripe checkout** with email prefilled (`?prefilled_email=`).
   - Delegation picks Founding link, or Standard link automatically if founding is marked sold out.
   - If they add teammates, they instead see a 2-step panel: pay delegation, then pay teammates (separate fixed-quantity links).
4. Investors submit the same form in "Investor" mode. No checkout.
5. Jessica reviews payments in Stripe daily, refunds non-fits within 48h, adds paid delegates and teammates to the **Luma guest list** and WhatsApp group, sends the welcome message with the lunch code.

Luma is used for **discovery and the guest list only**, not for payment (Luma free plan takes 5%; Stripe links are cheaper). Jessica chose this deliberately. Do not move payment back to Luma.

## 5. Links and codes

**Stripe Payment Links** (account public name currently shows "Jessica Wong"; post-payment invoice PDFs are OFF by her choice):
- Founding €495: https://buy.stripe.com/28EdR2cQT3GmcAgff7bo40k (limit 10 payments)
- Standard €595: https://buy.stripe.com/14A3co5or90GfMs3wpbo40l
- Premium €695: https://buy.stripe.com/3cI00c2cf5Ou7fWeb3bo40m
- Additional delegate x1 €175: https://buy.stripe.com/5kQ8wI4kn7WC43K2slbo40n
- Additional delegate x2 €350: https://buy.stripe.com/dRm9AM2cf7WC2ZG2slbo40o
- Additional delegate x3 €525: https://buy.stripe.com/dRm00cg353GmcAg8QJbo40p
- Partner Delegate €995 (created Oct 17): https://buy.stripe.com/9B628k5or6Sy43K0kdbo40q

Stripe cannot prefill quantity via URL, which is why teammates have one link per quantity.

**Luma:**
- Delegation listing: https://luma.com/vmqjiq9m (should say "Apply at yorkseed.co/lisbon-delegation"; paid tickets should be free/approval or removed)
- Global Founder Showcase (December, virtual): https://luma.com/relg9v16 (has a Partnership sponsor ticket, 3 spots)
- Yorkseed Executive Lunch, Mon Nov 9, 12:00 to 2:30 PM: https://luma.com/ryyphlgu
- Yorkseed Capital Lunch, Tue Nov 10, 12:00 to 2:30 PM: https://luma.com/lj25z4k3

**Lunch discount code for delegates:** `4N4M1V`, 25% off, works on both lunches. Never print it on a public page. It goes in the welcome message only.

## 6. Website files (repo: github.com/yorkseedventures-code/yorkseed-landing)

Static site on yorkseed.co. **Jessica deploys by uploading files through the GitHub web UI** (Add file, Upload files, Commit). Agent sessions have had read-only access; pushes were refused. Always hand her the files (a zip with the repo folder layout works well) and tell her exactly where each goes.

| File | What changed |
|---|---|
| `lisbon-delegation.html` | The delegation page. Design: mix of yorkseedhouse.com, yorkseed.co, Web Summit and RAISE (oxblood hero with azulejo tile pattern, gold italic accent word, blue ticker, bold date strip, black "/01 to /05" included section, cream editorial sections). Fonts Cormorant Garamond + DM Sans. Contains the application form, Stripe redirect logic, teammate cards (name, role, email, WhatsApp, all required except role) and the founding sold-out toggle. |
| `index.html` | Homepage: oxblood announcement strip above header and a "Now open" featured news card, both auto-switch to sold-out wording. Homepage has its own inline header/footer (not site-chrome), already updated. |
| `assets/site-chrome.js` | Shared header/footer for all other pages. "Yorkseed Delegations" added to Ecosystem dropdown and footer Properties. |
| `event-admin.html` | Team login (Event Manager). New "Lisbon Delegation" card with a **Mark founding sold out / Reopen** switch, plus a link to the invoice tool. |
| `invoice.html` | Private invoice generator (noindex, disallowed in robots). Fill fields, Print / Save as PDF. Numbers YS-LIS-2026-001 and up, issuer details saved in localStorage. |
| `robots.txt` | Added `Disallow: /invoice.html`. |
| `sitemap.xml` | Added `/lisbon-delegation`. |

**Form backend:** Web3Forms, access key `5c1c96c6-7a4f-4cc7-85d3-4dd79f67e20a` (same inbox as other site forms). Fixed field order so emails parse into consistent rows.

**Sold-out switch:** Pages fetch `https://yorkseed-backend-production.up.railway.app/api/site-events/public`, find the event whose `lumaUrl` contains `vmqjiq9m`, and enter sold-out mode if its `spots` field matches `/founding\s+sold\s+out/i`. The Team login button writes `From €595 · Founding sold out` (or back to `From €495 · Apply on Luma`). **Setup prerequisite:** the delegation Luma link must be added once in Team login, step 1, or the switch shows "Add the delegation first". The backend repo itself was not accessible; nothing there was changed. Elements use `data-fo` (founding open) and `data-so` (sold out) attributes toggled by `html.fso`.

The latest versions of all these files are in the same zip as this doc.

## 7. Messages ready to use

Approval/welcome email templates were written for Founding, Standard, Premium and Investor. Since the flow switched to instant checkout, use them as **welcome messages**: remove the "Confirm it here" payment line. Each includes the teammate link, WhatsApp group mention, Deal Book profile due Oct 30, lunch code and lunch links, and an invoice-on-request line. Add a Luma invite mention.

Suggested Stripe confirmation message (on all delegation links): "You're in. Watch your inbox in the next 24 hours for the delegate WhatsApp group, your Deal Book profile form, your Luma invite and your 25% lunch code. Bringing a teammate? https://buy.stripe.com/5kQ8wI4kn7WC43K2slbo40n"

## 8. Open items (not done yet)

1. **Deal Book profile form**: promised to delegates, due Oct 30. Not built. Suggested fields: logo, founder photo, one-liner, sector, stage, location, traction, raise or partnership goals, who they want to meet, links. Deal Book structure agreed: cover, short welcome from Jessica, Meet the Delegation (a page or half page per company), optional investor profiles, "Who to Meet in Lisbon" quick index (most important page), schedule, showcase, back page with Connect and links. No separate Connect page.
2. **Luma fixes**: delegation page says 30% lunch discount (should be 25%), add event dates, add €175 extra delegate, add refund terms, switch paid tickets off. Both lunch pages say "Web Summit Lisbon 2025" (should be 2026), "CVS" should be "CVCs", "UNSDGS -backed" should be "UN SDG-backed", "We bridges" should be "We bridge".
3. **Luma lunch pricing** advice given (not confirmed applied): founder tickets €79 to €99 are fine; investors should be free at the Capital Lunch and €89 at the Executive Lunch instead of €109 to €119; All-Access Week Pass €950 is too high next to the €495 delegation, suggested €395 to €450.
4. **Homepage "Coming up"** row says "Web Summit Lisbon week, Nov 8 to 11" linking to https://luma.com/44qkfxdu. Delegation runs to Nov 12. Unconfirmed whether that's intentional.
5. **Luma page mentions a pre-Lisbon briefing and an Insider Investor Circle** (tally.so/r/vGX1YA) that the site doesn't show. Offered to add the briefing to the week timeline; no answer yet.
6. **VAT**: not set up in Stripe. Jessica was told to ask her accountant. Invoice tool has a VAT % field defaulting to 0.
7. **Invoice tool**: her business address and tax ID are blank; she fills them once on her device.

## 9. How to work with Jessica

- Never use em dashes in anything you write for her.
- Marketing copy: punchy, terse, high impact. She rejected an early page as "too AI": avoid slogan pairs, "not X, Y" lines and filler taglines. She removed the hero tagline "Founders and investors. The right rooms."
- Give step-by-step, copy-pasteable instructions for anything technical; she does not code and deploys by GitHub upload.
- She often says "you decide": make the call, state it in one line, move on.
- She is solo and cash-conscious: prefer zero-cost, low-maintenance setups.
- Brand: yorkseed.co red #cc1e2b, oxblood #6e0d17, gold #B8936A, cream #F4EFE4; DM Sans body. Yorkseed House uses Cormorant Garamond.
- Contact email for public pages: partnership@yorkseed.co.


## 10. Oct 17 changes

- "Where did you hear about the delegation?" is now a required dropdown for every role, with an optional "Who or where exactly?" field. Emails carry "Heard via" and "Heard via details".
- Investor notice: funds, angel groups and allocators only; others are pointed to Partner Delegate.
- Partner Delegates get an Executive Lunch seat (Mon Nov 9), and so does every partner teammate paid at €175. Comp them on the Luma Executive Lunch guest list. The application email shows the seat count in "Rate to send if approved". Founder teammates do not get a lunch seat (25% code only).
- Teammates question now shows for founders and partners (not investors). Same €175 teammate links.
