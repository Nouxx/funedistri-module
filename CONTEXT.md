# Funedistri — Coffin Configurator

Ubiquitous language for the Funedistri coffin-configurator Odoo module: a B2B
coffin shop where approved B2B users build a coffin from owner-defined options
and submit it as a Pending Order. Glossary only — no implementation details.

UI locale = **French** (site sells in euros; user-facing labels/tooltips in FR).

## Language

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
The deceased's date of death. **Engraved on the coffin plate.** Supplied by the
B2B user.

**Delivery date**:
The deadline by which the Salesman needs the order delivered. Logistics only;
**not engraved**.

**Engraving text**:
Free text engraved on the plate (≤20 chars).

**Reveal rule**:
A one-level link on a Coffin model: choosing a given Option value (or setting a
given flag) reveals — and may require — another configuration field. E.g.
engraving = yes reveals the Death date. The single statement of when a field
shows; the same rule the frontend obeys and the order validates against.
_Avoid_: condition, dependency, exclusion (Odoo's native, different thing)
