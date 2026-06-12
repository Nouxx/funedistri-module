# 3. B2B users are portal users behind a two-layer login gate

Date: 2026-06-12

## Status

Accepted

## Context

The owner must be the **only** user who reaches the Odoo backend. Every B2B user
(Salesman, Store owner) acts solely through the website. Two surfaces share that
website:

- **Public website** (landing): anonymous marketing pages presenting Funedistri.
  The owner may publish a public catalog here at his discretion — marketing only.
- **Protected configurator**: the login-gated shop where approved B2B users build
  and submit coffins. Holds the whole `website_sale` flow, roles, price-hiding and
  Orders.

The initial instinct was to build a custom login-protected route layer for B2B
actions, on the belief that "B2B users not having backend access is safer." The
intuition is right; the mechanism needed pinning down, because several Odoo
defaults fight it:

- Native `website_sale` is built for **public** e-commerce — anonymous visitors
  browse products and prices, logging in only at checkout.
- Odoo's website-wide "require login / B2B mode" would wall the **public landing**
  too — unacceptable, the landing must stay anonymous.
- Native websites often ship **public self-registration** on, so "approved by the
  owner" would be meaningless if a stranger can self-provision.
- Our own `b2b_role` → group sync (see CLAUDE.md) is a footgun: assigning a group
  whose `implied_ids` reach an internal group silently **promotes a portal user to
  internal**, handing them the backend through our own code.

So "lock B2B out of the backend" is not one switch; it is a user-type decision
plus a per-surface gate plus a provisioning rule plus a sync guardrail.

## Decision

**B2B users are native portal users, and the protected configurator is gated by
two independent layers, while the public landing stays anonymous.**

1. **User type = portal.** Every B2B user is a `base.group_portal` user. Backend
   lockout is then **native and structural**: Odoo redirects the backend
   (`/odoo`, `/web`) to the portal for portal users — they cannot load the backend
   client at all. We do **not** build a custom auth wall; we rely on the user type.
   The `coffin_salesman_group` / `coffin_store_owner_group` ride on top of portal
   to flag the role for price rendering; they do **not** grant backend access.

2. **Two-layer gate on the protected configurator** (belt and braces):
   - **Data layer:** Coffin models are **never published** to the public website.
     A public hit on the shop renders no coffins. (A published coffin would leak
     its price from the public door, defeating the price-hiding ADR.)
   - **Auth layer:** the shop / cart / checkout / portal routes are forced to
     logged-in (anonymous → login redirect). Data-hiding alone is insufficient
     because native cart/checkout routes still answer anonymous sessions; auth
     alone is one accidental publish away from a public leak.

3. **No public self-signup.** "Free sign up" is off. Accounts exist only because
   the **Owner** created the contact (under the customer company, for native
   `commercial_partner_id` order visibility) and granted portal access. "Approve
   an account" = this owner-driven portal grant.

4. **Role-sync guardrail.** The `b2b_role` `write()` sync toggles **only** the two
   coffin groups, never `base.group_user`, and never a group whose `implied_ids`
   chain reaches an internal group. A B2B user stays portal regardless of role. A
   test asserts: after any `b2b_role` change, the user is still portal, not
   internal.

## Consequences

- Backend lockout costs **no custom code** — it is the portal user type. Less to
  build, nothing to keep in sync with Odoo upgrades, stronger than a hand-rolled
  auth wall.
- The public landing keeps standard anonymous Odoo website behavior; only the
  configurator surface diverges. We could not have used website-wide B2B mode.
- Two layers mean a single mistake (an accidental publish, or a missed route
  override) does not by itself expose the configurator or a price — the other
  layer still holds.
- Provisioning is owner-only and manual; there is no self-service onboarding. This
  matches the B2B-approval model and is acceptable given the small, curated user
  base.
- The role sync is the one place our own code could undo the backend lockout; the
  guardrail + test make that failure mode explicit and caught.
- Residual: this defends the *normal* surfaces (backend lockout, gated shop). It
  is not a claim of ORM-level field secrecy — price hiding's adversarial scope
  stays as decided in ADR 0001.
