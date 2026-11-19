# Event match pages

One page per Yorkseed event at `intro/<event-slug>.html` (served as `yorkseed.co/intro/<event-slug>`).
Guests enter their first name and RSVP email and see 3 curated matches.

**Standard format (from Fall Venture Evening NYC, Nov 19 2026). Use it for every new event, starting with Dec 8.**
Start from `intro/_template/event-match-template.html`: copy it to `intro/<event-slug>.html`, then fill in `EVENT`, `ATTENDEES`, `FUND_BY_MATCH` and `NOT_FOUNDERS`, and replace `EVENT-SLUG` in the utm links.

## Page sections, in order (after login)

1. **"N curated Yorkseed matches"** label, then "Hi {first name}." and "Not you? Switch account".
2. **Event details**: date, time, venue name (linked to Google Maps), street address, on-site host.
3. **About tonight's host: Yorkseed**: these three paragraphs, word for word:
   - Yorkseed is a global capital network and venture infrastructure platform connecting founders, investors, fund managers, capital allocators and ecosystem leaders, from early stage to IPO. With 50+ city hubs across five continents, we bring together curated gatherings, global delegations and strategic relationships that turn connections into meaningful opportunities.
   - Beyond events, **Yorkseed Connect** is our intelligent dealmaking platform for investor discovery, warm introductions, fund diligence, strategic partnerships and sharing deal flow. **Valois by Yorkseed** is our dedicated capital circle connecting family offices, LPs, GPs and institutional investors to exchange investment opportunities, share deal flow and explore co-investments. Across our ecosystem, we focus on quality over quantity, bringing the right people together and creating opportunities that extend well beyond the room.
   - **Next Stop: Hong Kong | January 26–27, 2027.** Following our Lisbon delegation, Yorkseed is heading to the Asian Financial Forum (AFF) as an Official Community Partner. ... (update this paragraph when the next delegation changes)
   - Links row: yorkseed.co · Yorkseed Connect · Valois · Join AFF Delegation (`https://yorkseed.co/hong-kong-delegation`).
4. **Deal Room box** (one of two versions, chosen by `NOT_FOUNDERS`):
   - Founders: "Put your company in the Deal Room": list your company as a deal in the Yorkseed Connect Deal Room*; monthly curated deal flow goes to investors who opted in. Button "List my company" -> `/submit-deal`. Then Deal Memo (pressure-test your narrative) and Investor List (getting ready to raise).
   - Investors: "Share your deals and get ours": add portfolio companies and open deals*; opt in to monthly deal flow. Button "Add a deal" -> `/submit-deal`. Then Deal Memo (scoring, signals, diligence questions, IC memo, your fund's criteria) and Allocator List (raising a fund).
   - Italic footnote under the button: *Listing deals is available to Core members. Claim your free month of Yorkseed Connect below.
5. **Match cards** (3 per guest), each with:
   - Name, role, one-line hook (italic).
   - **4 bullets, personalized, from LinkedIn + RSVP**: (1) who they are, (2) what they're building or investing in / what they want tonight, (3) why they fit *this* guest, (4) what the two can do for each other.
   - Conversation starter.
   - Buttons: "Run Connection Intelligence on {first name}" (every card); "Run Fund Diligence on {fund}" (when the match is in `FUND_BY_MATCH`: VCs, venture scouts, deal partners, fund managers); Deal Memo ("Pressure-test your pitch before meeting {name}" for founder viewers, "Evaluate {company} with Deal Memo" for investor viewers looking at a founder).
6. **Complimentary Bonus: 1 Month of Yorkseed Connect** -> `https://app.yorkseed.co/eventoffer` (general Yorkseed event offer, code WS202630).

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
