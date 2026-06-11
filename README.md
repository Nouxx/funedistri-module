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
