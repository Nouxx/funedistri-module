# Funedistri — Coffin Configurator

Ubiquitous language for the Funedistri coffin-configurator Odoo module: a B2B
coffin shop where approved B2B users build a coffin from owner-defined options
and submit it as a Pending Order. Glossary only — no implementation details.

UI locale = **French** (site sells in euros; user-facing labels/tooltips in FR).

## Language

### Surfaces

**Public website** (landing):
The anonymous-visible marketing site presenting Funedistri. Owner may publish a
public catalog here at his discretion — **marketing only**, decoupled from Coffin
models. Has no configurator, no roles, no order flow.
_Avoid_: shop, site (bare)

**Protected configurator**:
The login-gated section where approved B2B users build and submit coffins. Holds
the whole shopping flow, roles, price-hiding and Orders. A logged-out visitor
sees none of it. Coffin models live **only** here — never published to the
Public website (publishing one would leak its price from the public door).
_Avoid_: shop (bare), B2B site, member area

### Actors

**Funedistri**:
The business selling coffins; owns the Odoo site.

**Owner**:
The single person running Funedistri. The only user of the Odoo **backend**.
Defines coffin options, validates and ships orders.
_Avoid_: admin, Funedistri (for the person — Funedistri is the business)

**B2B user**:
A customer user. Uses the e-commerce **frontend** only, never the backend.
Belongs to a customer company. Always a Salesman or a Store owner.
_Avoid_: client, shopper

**Approve** (an account):
The Owner granting a B2B user permission to log in and shop. Used **only** for
account access — never for orders (orders are Validated).
_Avoid_: validate (that is the order verb), authorize

**Salesman**:
A B2B user who places orders on behalf of their company and **sees no prices**
anywhere.

**Store owner**:
A B2B user who places orders and **sees prices**.

**Customer company**:
The B2B organization that buys from Funedistri. Its B2B users (one Store owner +
any number of Salesmen) all sit under it and share its order history.
_Avoid_: client, account, customer (bare)

**Company address**:
A delivery address the Owner has pre-defined for a Customer company (the Owner has
negotiated shipping for it). At checkout a B2B user may **only select** among their
company's Company addresses — never create or edit one. Only the Owner manages them
(backend). Applies to the delivery address; the invoice address stays native.
_Avoid_: shipping address (bare), new address, approved address (approval is an
account concept)

### Product

**Coffin model**:
The configurable catalog product the Owner defines — a coffin with its set of
options — that appears in the shop for B2B users to build from.
_Avoid_: base coffin, base product, configurable coffin

**Configured coffin**:
One Coffin model with a B2B user's chosen options, sitting on an order line.
The filled-in result of building from a Coffin model.
_Avoid_: built coffin, custom coffin

**Option**:
One configurable choice on a Coffin model (wood, handles, engraving…).
_Avoid_: attribute (Odoo's word), feature

**Option value**:
One selectable choice within an Option (oak, plywood…).
_Avoid_: attribute value, variant

**Priced option**:
An Option whose chosen value changes the coffin's price.

**Informational option**:
An Option captured for the Owner but with no price effect (e.g. a note, the
death date, a yes/no flag).

**Part**:
A physical component (e.g. a handle) the Funedistri Owner both **sells loose** and
**consumes inside a coffin** — one shared stock. Choosing the matching Option value
on a coffin must draw down the same Part stock, so loose sales and coffin sales
can't oversell it. (The Owner runs Odoo Stock + Manufacturing; how the draw-down is
wired is an implementation question — see docs/explore-bom-mo.md.)
_Avoid_: component (bare), piece

### Order

**Order**:
The thing a B2B user submits at checkout. An Order from the moment of submit —
it is never called a "quotation" in our language.
_Avoid_: quotation (Odoo's internal word), purchase, transaction

**Place an order** / **Submit order**:
The frontend checkout (final button "Submit order", replacing "Pay now") that
creates a Pending Order with no payment.

**Pending**:
An Order's state right after submit, awaiting the Owner. B2B-facing wording =
"pending validation" (FR: "en attente de validation"). Never "pending approval"
— approval is an account concept, not an order concept.

**Validate**:
The Owner's action of accepting a Pending Order, turning it into a real
(validated) Order. The single canonical verb for this — never used for accounts.
_Avoid_: confirm, approve

**Shipped**:
An Order the Owner has dispatched. (Tracking of this state is out of scope for
now — informal.)

### Configuration data (per Configured coffin / order line)

**Coffin plate**:
The engraved nameplate on a coffin; carries the engraving text and the death
date.
_Avoid_: plaque, nameplate

**Death date**:
The deceased's date of death, **engraved on the coffin plate**. Supplied by the
B2B user as a **free-text Option value** (no date type, no validation in v1); the
Owner reads and corrects it at Validate.

**Delivery date**:
The deadline by which the Salesman needs the order delivered. Logistics only;
**not engraved**. Captured as a **free-text Option value** in v1, like Death date.

**Engraving text**:
Free text engraved on the plate. A free-text Option value; the plate is short, so
the Owner trims overlong text at Validate (no system length limit in v1).

_(Retired for v1 — **Reveal rule**: the one-level conditional show/require of a
field. v1 has no conditional reveal; every field is always visible and the Owner
catches incoherent combinations at Validate. See ADR 0004.)_
