Cognitive Orchestrator — Design Partner Pilot Campaign Pack
============================================================

Contents
--------
1. Design-Partner-One-Pager.pdf
   Attach to outbound email. Single page: problem, product, pilot terms.

2. Design-Partner-Pilot-SOW.pdf
   Send after a green discovery call. Replace [Company Legal Name] before sending.

3. Discovery-Call-Script.pdf
   30-minute qualification script and scorecard. Do not product-tour.

4. Outbound-Email.txt
   Subject line and body for first touch.

5. This-Week-Plan.txt
   Operating checklist for the first 7 days.


Outbound email
--------------
Subject: Vendor approval trail for audit

Hi {{FirstName}},

When a vendor is approved under a spend or data-class rule, can your team still produce a clean trail for risk or audit without reconstructing Slack and spreadsheets?

We run a 60-day design-partner pilot ($50k) that puts a policy gate and a hash-chained evidence pack in front of vendor onboarding. Risk/finance get an export they can stand behind; procurement gets a consistent path.

Open to a 30-minute call this week or next? One-pager attached.

— Mourad


This week
---------
Day 1  List 40 target accounts (fintech, healthtech, industrial, professional services). Prefer warm intros.
Day 2  Send 20 emails with Design-Partner-One-Pager.pdf.
Day 3–5  Discovery calls using Discovery-Call-Script.pdf. Score volume, audit owner, budget path, timeline.
Day 5–7  For green scorecards only: send Design-Partner-Pilot-SOW.pdf and book SOW review.

Success this week = 3 verbal yeses or scheduled SOW reviews. Decline free API experiments.


Product endpoints (for demos after qualification)
-------------------------------------------------
POST /decisions/vendor
GET  /audit/export
Repo: github.com/Mourad-Soltani/cognitive-orchestrator
