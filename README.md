# funedistri-module

Custom Odoo module **`funedistri_coffin_configurator`** for [Funedistri](https://funedistri.odoo.com) —
a B2B coffin shop on Odoo.sh. It lets the Owner define configurable coffins and
their option prices in the backend, and lets approved B2B users build and submit
a coffin as a draft order on the website.

See [`CLAUDE.md`](CLAUDE.md) for the design, [`CONTEXT.md`](CONTEXT.md) for the
glossary, [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for the
step-by-step build, and [`docs/adr/`](docs/adr) for the architecture decisions.

> This repo **is** the Odoo.sh addons repo: the module sits at the repo root, and
> `git push` deploys to prod. The files below (`Makefile`, `docker-compose.yml`,
> `odoo.conf`) are local-dev only — Odoo.sh ignores anything without a manifest.

## How the order workflow works

There are **two completely separate surfaces**, and a user only ever touches one:

| Surface | URL | Who | What they do |
| ------- | --- | --- | ------------ |
| **Backend** (Odoo admin) | `/odoo` | **Owner** only | defines coffins + prices, validates and ships orders |
| **Frontend** (website / portal) | `/shop`, `/my/orders` | **B2B users** only | build a coffin, submit it, track its status |

A B2B user never logs into the backend; the Owner never shops on the frontend.
Keeping these mentally separate is the single most important thing — the same
order shows up on both, but with different labels and different powers.

> **Scope note.** What follows describes the workflow **as built today (Steps 1–4)**.
> There's a configurable coffin, priced options, and conditional-reveal fields.
> The one big gap: **B2B roles exist but price-hiding does not yet** (the masking
> sweep is a later step). So today a Salesman still *sees* prices; the role is
> wired, the suppression is not. Remaining work (masking, owner notifications) is
> in [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md). The end-to-end
> *pipe* below is real and final; the *features* hanging off it are not all there yet.

### Setup: the Owner assigns B2B roles (backend)

Before a B2B user shops, the Owner gives them a role on their **contact**
(`/odoo` → Contacts → open the contact → **B2B role** dropdown):

| Role | Places orders | Sees prices |
| ---- | ------------- | ----------- |
| **Salesman** | yes, on behalf of their company | **no** (once masking ships) |
| **Store owner** | yes | **yes** |

Picking the role flips one dropdown; behind the scenes the module keeps a hidden
security group in sync on that contact's login user(s). Every later price-hiding
branch reads that group via `has_group(...)` — so the dropdown is the single
control, the groups are the plumbing. Leave the field empty for a company record
or a contact who never logs in.

### B2B user point of view (frontend)

The buyer. Logs into the **website only**.

1. **Log in** at `/web/login` as a portal user. The demo seed (Step 3) ships two,
   both under the same company **Pompes Funèbres Demo SARL** so they share order
   history: `demo_store_owner` / `demo_store_owner` (**Store owner**, sees prices)
   and `demo_salesman` / `demo_salesman` (**Salesman**).
2. **Browse the shop** at `/shop` — sees the published coffin(s).
3. **Build + add to cart.** The demo **Cercueil configurable** offers priced
   Options: **Bois** (Chêne +0 / Contreplaqué +120, image picker), **Poignées**
   (Standard +0 / Dorées +80), and **Gravure** (Oui/Non, unpriced). Base 600 €.
4. **Fill conditional fields on the cart.** On the cart page, choosing
   **Gravure = Oui** reveals — and requires — **Date de décès** and **Texte de
   gravure** (≤20 chars). **Date de livraison** is always shown, optional. These
   live on the order line; see "Conditional reveal" below.
5. **Checkout.** Goes through the address step (the test user already has a
   complete French address, required or checkout blocks).
6. **Submit.** The final button is **"Valider la commande"** — *not* "Pay now".
   There is **no online payment**: clicking it submits the order and stops. If a
   required revealed field is missing, the server refuses the submit.
7. **Confirmation.** Lands on **"Commande reçue — en attente de validation"**.
8. **Track it.** At `/my/orders` the order appears with a **"En attente de
   validation"** badge. (Once masking ships, a Salesman sees no price here; a
   Store owner always does.)

Behind the scenes, the cart *is* a draft `sale.order`; submitting just marks it
submitted and detaches it from the live cart — it stays in `draft`, which is our
**Pending** state. Nothing is paid, nothing is confirmed yet.

### Owner point of view (backend)

The single admin running Funedistri. Logs into the **backend only** (`/odoo`,
`admin` / `admin` locally).

1. **See the new order.** Open the **Sales** app → **Orders → Quotations**.
   The submitted order is here. (Odoo's native label is *Quotation* — we only
   relabel the *frontend* to "Pending"; the backend keeps Odoo's own words, by
   design. A submitted Pending order is a `draft` `sale.order`.)
   - If the list looks empty and shows an ad ("Beat competitors with stunning
     quotations!"), clear the **"My Quotations"** search filter — website orders
     have no salesperson, so that default filter hides them.
2. **Review / edit.** The Owner can fully edit the draft — options, quantities,
   and price — *before* validating. (This matters later: a Salesman builds the
   order blind to price, so the Owner is the one who sets/checks the money.)
3. **Validate.** Click **Confirm** on the order → it moves to `state = 'sale'`
   (a real Sales Order). This is the Owner's "accept" action.
4. **Ship.** Handled informally for now — out of scope as a tracked state.

> **What is NOT here yet (later steps):** the Owner being *notified* on each
> submit (activity + email), the price actually being *hidden* from Salesmen
> across every surface (roles are wired, suppression is not), the real
> attribute-driven configurator, and the conditional reveal fields. Steps 1–2
> prove: shop → submit → a draft order the Owner sees and confirms, with B2B
> roles assignable on contacts.

### The same order, two views

| | B2B user (`/my/orders`) | Owner (`/odoo` Sales) |
| --- | --- | --- |
| State `draft` + submitted | "En attente de validation" badge | listed under **Quotations** (label "Quotation") |
| After Owner clicks Confirm | (state `sale`) "Validée" | a **Sales Order** |
| Wording rule | never "quotation", never "paid" | native Odoo labels are fine |

## How coffin options and prices are stored

Options (wood, handles…) and their price add-ons use **native Odoo product
attributes** — no custom tables. Four model layers, and the price lives on a
specific one:

| Layer | Model | Example | Holds the price? |
| ----- | ----- | ------- | ---------------- |
| Option | `product.attribute` | "Bois" | no |
| Option value (global) | `product.attribute.value` | "Contreplaqué" | **no** |
| Option on a coffin | `product.template.attribute.line` | Bois offered on *Cercueil configurable* | no |
| Value on a coffin | `product.template.attribute.value` (**PTAV**) | Contreplaqué *on this coffin* | **yes → `price_extra`** |

So **the +120 € for Contreplaqué is stored on the PTAV**, the per-coffin
materialisation of the value — *not* on the global "Contreplaqué" value. Why:
the same wood can cost differently on different coffins, so the price belongs to
the (coffin × value) pair, not the value alone. The coffin's base `list_price`
(600 €) plus each chosen value's `price_extra` is the configured price.

Check it directly:

```sql
SELECT pa.name->>'en_US' AS option, pav.name->>'en_US' AS value, ptav.price_extra
FROM product_template_attribute_value ptav
JOIN product_attribute pa ON pa.id = ptav.attribute_id
JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
JOIN product_template pt ON pt.id = ptav.product_tmpl_id
WHERE pt.name->>'en_US' = 'Cercueil configurable';
```

Two more facts:

- **No-variant mode.** The attributes are set to *Never* create variants
  (`create_variant = 'no_variant'`), so Odoo does **not** explode the catalog
  into one SKU per wood×handles combination. The chosen values are captured on
  the **order line** instead (`product_no_variant_attribute_value_ids`), which is
  why the price is computed per line rather than per stored variant.
- **The Owner edits all of this in the UI — no code.** Both the option list and
  the prices are owner self-serve in the backend: open the product → **Attributes
  & Variants** tab → add/remove attributes and values there, and type each value's
  add-on in the **Extra Price** column (the `price_extra` field, editable inline).
- **Seeding the price in *demo* code is a one-off hack, unrelated to the Owner.**
  A PTAV is auto-created by Odoo when you attach a value to a coffin, so it has no
  XML id of its own. Demo XML loads at install with nobody to click, so to set
  `price_extra` we register an id onto the PTAV via `ir.model.data._update_xmlids`
  then write the price — see `demo/coffin_product.xml`. A human in the product
  form never touches any of that.

### Demo XML is a one-time seed, not a sync — UI edits live only in the DB

This trips people up, so be explicit. Options you add in the **UI** and options
that come from `demo/coffin_attributes.xml` end up in the **same DB tables**, but
they are decoupled:

| | From the demo XML | Added in the UI |
| --- | --- | --- |
| Stored in DB | yes | yes |
| Has an `ir_model_data` **xml_id** | yes (`funedistri_coffin_configurator.attr_…`) | **no** — exists nowhere in code |
| Survives `make reset` | yes (re-seeded on the fresh DB) | **no — gone** |
| Exists in production | no (demo never loads in prod) | yes, persists in the prod DB |

Consequences:

- The demo file loads **once, at database creation** (`--with-demo`) and is
  `noupdate="1"`, so a later module **upgrade does not touch** existing rows.
  Editing the XML ≠ changing the DB; editing the DB (UI) ≠ changing the XML.
- A value you add by hand (e.g. a new wood "Hêtre") is **real and persistent in
  that DB**, but invisible to git and **wiped by `make reset`** — only the demo
  seed comes back. Treat UI tinkering in the dev DB as throwaway.
- To make an option **survive resets or ship to prod**, it must go into code
  (a `data`/`demo` XML record). In real production, though, the Owner's
  UI-created catalog lives in the prod DB and is the source of truth — the XML
  here is dev scaffolding only.

## Conditional reveal (death date / engraving)

Some fields only make sense for some choices: pick **Gravure = Oui** and you must
give a **Date de décès** and a **Texte de gravure**; pick **Non** and neither
applies. This one-level "pick X → reveal/require Y" logic is **not native** Odoo,
so it's a thin custom layer (see [`docs/adr/0002`](docs/adr/0002-dedicated-model-for-conditional-reveal-rules.md)).

**One source of truth: the `coffin.config.rule` model.** Each row is
`(trigger value, target field, required when)` — e.g. *(Gravure: Oui, death_date,
required)*. The trigger is a native attribute value (so the Owner manages the
option in the Attributes & Variants tab); the target is one of the custom fields
on `sale.order.line` (`death_date`, `delivery_date`, `engraving_text`).

Three readers consume those same rows — nothing is duplicated:

1. The **cart page** renders the rules into DOM `data-*` attributes.
2. A small **generic JS** (`static/src/js/coffin_cart_fields.js`) reads the
   `data-*` and shows/hides each field. It contains no rules of its own.
3. The **server** reads the same rows to **validate** at submit
   (`sale.order.line._validate_reveal_rules`) — a Salesman builds blind to price
   and JS is only UX, so a missing *required* field is refused server-side. The
   ≤20-char engraving limit is an `@api.constrains`, enforced on every write.

Where you fill them: **on the cart page**, under each configured coffin. (ADR-0002
originally said the product page; v19's product page is an OWL/JS configurator, so
capture moved to the server-rendered cart — the rule mechanism is unchanged. See
the ADR's Step 4 update.)

Adding a new conditional field is a **dev** touch (new column on the line + an
entry in the field list + the rule Selection); wiring an existing field to a
trigger is **data only** (a new `coffin.config.rule` row the Owner could manage).

## Local dev setup

A throwaway Odoo 19 + Postgres 16 stack in Docker, so you can click the module
locally before pushing.

### Prerequisites

- **Docker Desktop** running (the daemon must be up before any `make` target).
- Ports **8069** (Odoo web) and **5432** (only inside the Docker network) free.

> Note: the local `odoo:19` image is the community **19.0** series, while prod
> (Odoo.sh) is **19.2**. Close enough to develop against; the manifest version is
> series-agnostic so the module installs on both. See `CLAUDE.md`.

### Quick start

```bash
make dev
```

Then open <http://localhost:8069> and log in:

| Field    | Value   |
| -------- | ------- |
| Database | `funedistri` |
| Login    | `admin` |
| Password | `admin` |

`make dev` boots Postgres, then runs Odoo in the **foreground** with
`-i funedistri_coffin_configurator --with-demo --dev=all`:

- `-i …` installs the module (and pulls `website_sale` + `sale` via the manifest
  `depends`); on a fresh database it also **creates** the database.
- `--with-demo` loads the demo seed (configurable coffin + B2B users). **Odoo 19
  made demo data opt-in** — without this flag, none of it is created. Demo loads
  only at **database creation**, so to add it to a DB made without it you must
  `make reset` first (see below).
- `--dev=all` is developer mode: **hot-reload** of XML views and Python — edit a
  file, refresh the browser, no restart needed.

Leave this terminal running; it streams the Odoo log. `Ctrl-C` stops Odoo (the
Postgres container keeps running).

> **Demo seed (dev only).** A fresh `make dev` gives you a clickable store:
> the **Cercueil configurable** Coffin model (priced Bois / Poignées options)
> and two B2B logins under one company — `demo_store_owner` and `demo_salesman`
> (password = login). None of this loads in production.

## Make targets

| Command         | What it does |
| --------------- | ------------ |
| `make dev`      | Boot Postgres + Odoo, (re)install the module, hot-reload. The main loop. |
| `make logs`     | Tail the Odoo container logs (when running detached). |
| `make down`     | Stop the containers. **Database data is kept** in the `pgdata` volume. |
| `make reset`    | Drop the `funedistri` database for a clean slate (keeps the PG server). |

Override the database name on any target: `make dev DB=scratch`.

## Common operations

**Apply a code change** — with `make dev` running, just save the file and refresh
the browser (hot-reload). For changes Odoo loads only at install/upgrade (new
manifest `data` files, new models), re-run with an explicit upgrade:

```bash
# stop the running make dev (Ctrl-C), then:
docker compose run --rm --service-ports odoo \
  odoo -d funedistri -u funedistri_coffin_configurator --dev=all
```

(`-u` upgrades an already-installed module; `-i` only installs if it isn't.)

**Start over from an empty database**

```bash
make reset   # drops the funedistri DB
make dev     # recreates it and reinstalls the module
```

**Open a psql shell**

```bash
docker compose exec db psql -U odoo -d funedistri
```

**Full teardown (including data)**

```bash
docker compose down -v   # also deletes the pgdata volume — irreversible
```

## Troubleshooting

- **`port is already allocated` (8069)** — a previous one-off Odoo container is
  still up. List and remove it:
  ```bash
  docker ps -a --filter "name=funedistri-module-odoo-run"
  docker rm -f $(docker ps -aq --filter "name=funedistri-module-odoo-run")
  ```
- **`has an incompatible version, setting installable=False`** — the manifest
  version was prefixed with a series that doesn't match the running server. Keep
  it as the short form (`"1.0.0"`); Odoo prepends the right series itself.
- **Image pull times out** — transient registry hiccup. Re-pull directly and
  retry: `docker pull odoo:19 && make dev`.
- **Changes not showing** — XML/Python should hot-reload under `--dev=all`; if a
  new model or `data` file isn't picked up, run the `-u` upgrade above.

## Project layout

```
.
├── funedistri_coffin_configurator/   # the Odoo module (deploys to Odoo.sh)
│   ├── __manifest__.py               # module metadata + dependencies
│   └── __init__.py
├── docker-compose.yml                # local dev: odoo:19 + postgres:16
├── odoo.conf                         # Odoo config (addons path, DB creds)
├── Makefile                          # make dev / down / reset / logs
├── CLAUDE.md                         # design decisions
├── CONTEXT.md                        # ubiquitous-language glossary
└── docs/                             # implementation plan + ADRs
```
