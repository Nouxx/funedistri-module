# 3. B2B users are portal users behind a two-layer login gate

Date: 2026-06-12 · Status: Accepted

## Decision

The Owner is the **only** backend user; every B2B user acts solely through the
website. Two website surfaces: the **public landing** (anonymous marketing) and the
**protected configurator** (the login-gated shop).

1. **User type = portal.** Every B2B user is a `base.group_portal` user. Backend
   lockout is then **native and structural** — Odoo redirects `/odoo`, `/web` to the
   portal for portal users; no custom auth wall. The coffin role groups ride on top
   and do **not** grant backend access.
2. **Two-layer gate on the configurator** (belt and braces):
   - **Data:** Coffin models are **never published** to the public website (a
     published coffin would leak its price from the public door).
   - **Auth:** shop / cart / checkout / portal routes force login (anonymous →
     redirect). Auth alone is one accidental publish away from a leak; data-hiding
     alone leaves native cart routes answering anonymous sessions — need both.
3. **No public self-signup.** Accounts exist only because the Owner created the
   contact (under the customer company, for native `commercial_partner_id` order
   visibility) and granted portal access. "Approve an account" = that grant.
4. **Role-sync guardrail.** The `b2b_role` sync toggles **only** the two coffin
   groups — never `base.group_user`, never a group whose `implied_ids` reach an
   internal group. A test asserts a B2B user stays portal (not internal) after any
   role change.

## Why

Backend lockout via the portal user type costs no custom code, stays correct across
upgrades, and is stronger than a hand-rolled wall. The public landing keeps standard
anonymous behaviour, so website-wide "B2B mode" was unusable. Two layers mean one
mistake (an accidental publish, a missed route override) doesn't by itself expose a
price. The role sync is the one place our own code could undo the lockout — hence the
guardrail + test. Not a claim of ORM-level field secrecy (that scope stays in ADR 0001).
