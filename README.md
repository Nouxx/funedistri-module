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

> **Scope note.** What follows describes the workflow **as built today (Step 1 —
> the "tracer spine")**. It is deliberately thin: one hard-coded coffin, no
> roles yet, no price hiding yet, no configurable options yet. Those land in
> later steps (see [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)).
> The end-to-end *pipe* below is real and final; the *features* hanging off it
> are not all there yet.

### B2B user point of view (frontend)

The buyer. Logs into the **website only**.

1. **Log in** at `/web/login` as a portal user (e.g. the test user `b2b_test` /
   `b2b_test`, created for local clicking).
2. **Browse the shop** at `/shop` — sees the published coffin(s).
3. **Build + add to cart.** (Today: one tracer coffin with a fixed price. Later:
   pick wood / handles / engraving / dates — the actual configurator.)
4. **Checkout.** Goes through the address step (the test user already has a
   complete French address, required or checkout blocks).
5. **Submit.** The final button is **"Valider la commande"** — *not* "Pay now".
   There is **no online payment**: clicking it submits the order and stops.
6. **Confirmation.** Lands on **"Commande reçue — en attente de validation"**.
7. **Track it.** At `/my/orders` the order appears with a **"En attente de
   validation"** badge. (Later, for a Salesman, every price here is hidden.)

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
> submit (activity + email), the price being *hidden* from Salesmen across every
> surface, the two B2B roles, the real attribute-driven configurator, and the
> conditional reveal fields. Step 1 only proves: shop → submit → a draft order
> the Owner can see and confirm.

### The same order, two views

| | B2B user (`/my/orders`) | Owner (`/odoo` Sales) |
| --- | --- | --- |
| State `draft` + submitted | "En attente de validation" badge | listed under **Quotations** (label "Quotation") |
| After Owner clicks Confirm | (state `sale`) "Validée" | a **Sales Order** |
| Wording rule | never "quotation", never "paid" | native Odoo labels are fine |

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
`-i funedistri_coffin_configurator --dev=all`:

- `-i …` installs the module (and pulls `website_sale` + `sale` via the manifest
  `depends`); on a fresh database it also **creates** the database.
- `--dev=all` is developer mode: **hot-reload** of XML views and Python — edit a
  file, refresh the browser, no restart needed.

Leave this terminal running; it streams the Odoo log. `Ctrl-C` stops Odoo (the
Postgres container keeps running).

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
