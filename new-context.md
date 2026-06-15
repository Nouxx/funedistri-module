# Addition / Modifications

## Context precision

The owner use Odoo as a full business platform: Stock, Manufacturing etc. This is not only a website management tool.

Owner sells coffin with it but also some pieces of it (ex: handles)

## Products variants

All configuration data (per Configured coffin / order line) will be handled with native Odoo feature: Product Attributes. It's not perfect but it will do the job for v1.

## Open question

Owner defines options with product attributes (ex: handles). a order placed with a product that have this option (handle = value) should be decreasing the stock of a certain product in the owner Odoo backend stock. Is this possible, ideally with only native Odoo feature (no custom module)

## Order visibility per company

It should be already "a b2b user (salesman or owner) can only see order from his company and he can see all orders from it"

What happens if a user is not registered to any company in Odoo? What orders can he see? (ideally: none)

## Addresses management

New rule: Owner defines a set of addresses for a company.
When b2b users place an order, they can use ONLY theses addresses assign to their company.
They can't create new ones.

Context: Owner negotiate shipping fees with companies, for a few addresses. Allowing b2b users to set a new, not validated, address could mean higher cost and less margin. Not acceptable.

## Products variants

> **RESOLVED 2026-06-15 — conditional rendering is OUT for v1.** See ADR 0004
> (reaffirmed). Coffin configuration is done **exclusively with native Product
> Attributes**; native Odoo has **no** conditional reveal (only mutually-exclusive
> exclusion rules), and we are **not** building a custom layer for it. The
> always-visible "plaque name" contradiction (pick "no plaque" + type a name) is
> **accepted** — the Owner is the single validation backstop and fixes it at
> Validate. Post-v1 revival notes (native `is_custom` same-value reveal; the
> required + cross-attribute gaps a custom layer would fill) are in ADR 0004.
>
> _Original question, kept for history:_

It's nice to have, but some options in the product attributes in the shop should be rendered conditionally.

Example: 

Coffin plaque options:
- without
- silver (+15$)
- gold (+50$)

If a coffin is configured with a plaque, a name must be provided

Right now, a "plaque name" field is visible all the time, but it does not make sense: a user could select "no plaque" and set a "plaque name" -> impossible

I was thinking conditional rendering on the product page but this seems like not possible with native odoo features, so please:
- confirm what is possible with native Odoo features (maybe cart field?)
- suggest an approach with custom module but check solution maintainability (how to identify the field? -- name is flaky because it can change. will this survive Odoo migration, etc.)
