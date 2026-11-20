# Event match pages

One page per Yorkseed event at `intro/<event-slug>.html` (served as `yorkseed.co/intro/<event-slug>`).
Guests enter their first name and RSVP email and see 3 curated matches.

**Standard format (from Fall Venture Evening NYC, Nov 19 2026). Use it for every new event, starting with Dec 8.**
Start from `intro/_template/event-match-template.html`: copy it to `intro/<event-slug>.html`, then fill in `EVENT`, `ATTENDEES`, `FUND_BY_MATCH` and `NOT_FOUNDERS`, and replace `EVENT-SLUG` in the utm links.

## Page sections

**Before sign-in:** "Find out who to meet." form, then one **Yorkseed Connect** box ("Know who to meet, all year"): Matches and warm intros; Investor List and Allocator List (24,000+ investors, 1,600+ allocators); Connection Intelligence; Deal Room and monthly deal flow. Button "Start free for 30 days" -> `/eventoffer` (code WS202630). No "tonight" wording here.

**After sign-in, in this order (host box, then matches; guests open this at the event):**
1. "N curated Yorkseed matches", "Hi {first name}.", "Not you? Switch account".
2. Event details: date, time, venue (Google Maps link), street address, on-site host.
2b. **About tonight's host: Yorkseed** box (see item 5 for the copy), placed here, above the matches. Then "Based on what you shared in your RSVP, here's who we think you should meet."
3. **Match cards** (3 per guest): name, role, italic hook, **4 personalized bullets** (who they are; what they build/invest in or want tonight; why they fit *this* guest; what they can do for each other), conversation starter, then buttons:
   - "Run Connection Intelligence on {first name}" on every card.
   - "Run Fund Diligence on {fund}" when the match is in `FUND_BY_MATCH` (VCs, venture scouts, deal partners, fund managers).
   - Deal Memo: founder viewer + investor match -> "Pressure-test your pitch before meeting {name}"; investor viewer + founder match -> "Evaluate {company} with Deal Memo". No Deal Memo button on founder-founder or investor-investor cards.
3b. **"Also worth meeting"**: 2 extra people per guest, each with a one-line description, a one-line reason and a Connection Intelligence link, then "Want more matches like these? Yorkseed Connect finds them for you all year. Claim 1 month free." Keep 3 full matches; pick extras by shared sector, skip anyone already on 6+ lists so the busiest investors aren't crowded, and skip people who already know each other.
4. **One Connect box, "1 month of Yorkseed Connect, free"** (replaces the old Complimentary Bonus box), version chosen by `NOT_FOUNDERS`:
   - Founders: list your company in the Deal Room*, monthly curated deal flow to opted-in investors. "Claim 1 month free" -> `/eventoffer`. Then Deal Memo (pressure-test your narrative) and Investor List.
   - Investors: share your deals and get ours, add portfolio companies and open deals*, opt in to monthly deal flow. "Claim 1 month free". Then Deal Memo (scoring, signals, diligence questions, IC memo, fund criteria) and Allocator List.
   - Italic footnote: *Listing deals is available to Core members. Code WS202630 gives you 30 days free on any plan, including Core. Already a member? List my company / Add a deal (-> `/submit-deal`).
5. **About tonight's host: Yorkseed** copy (box sits at 2b, above the matches), these three paragraphs word for word:
   - Yorkseed is a global capital network and venture infrastructure platform connecting founders, investors, fund managers, capital allocators and ecosystem leaders, from early stage to IPO. With 50+ city hubs across five continents, we bring together curated gatherings, global delegations and strategic relationships that turn connections into meaningful opportunities.
   - Beyond events, **Yorkseed Connect** is our intelligent dealmaking platform for investor discovery, warm introductions, fund diligence, strategic partnerships and sharing deal flow. **Valois by Yorkseed** is our dedicated capital circle connecting family offices, LPs, GPs and institutional investors to exchange investment opportunities, share deal flow and explore co-investments. Across our ecosystem, we focus on quality over quantity, bringing the right people together and creating opportunities that extend well beyond the room.
   - **Next Stop: Hong Kong | January 26–27, 2027.** (update when the next delegation changes)
   - Links: yorkseed.co · Yorkseed Connect · Valois · Join AFF Delegation (`https://yorkseed.co/hong-kong-delegation`).

## Writing rules

- No em dashes anywhere (use a full stop or comma). En dash only in date ranges like 26–27.
- Only facts from LinkedIn or the guest's RSVP. Never invent traction, funds or titles. Don't guess pronouns; use names.
- Use the guest's real name for display (e.g. "Jay Cruz", not a company name). Add `aliases` so they can log in with nicknames.
- Investors' current firm and title from LinkedIn win over an outdated RSVP title.
- Don't match people who already know each other; when a guest is raising, give them real investor matches and add them to those investors' lists too.

## Technical rules

- Inputs stay at 16px (iPhone zooms in on anything smaller). Login blurs the field and scrolls to top.
- Test every guest login at 390px width before deploying: 3 cards, no horizontal overflow.
- Deploys only happen when the commit message contains `[deploy]` (see `netlify.toml`). Push without it to stage changes.
