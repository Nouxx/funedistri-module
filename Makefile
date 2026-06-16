# Local dev shortcuts. Dev-only file — Odoo.sh ignores it.
#
# Quick start:
#   1. Start Docker Desktop (the daemon must be running).
#   2. make dev      → boots Postgres + Odoo, installs the module, dev mode.
#   3. open http://localhost:8069   (login: admin / admin)
#
# Name of the dev database. Override with: make dev DB=foo
DB ?= funedistri
MODULE := funedistri_customizations
# Local-only seed module (test B2B companies + users). Installed for dev ONLY,
# never on Odoo.sh. See funedistri_dev_seed/__manifest__.py for the why.
SEED := funedistri_dev_seed

.PHONY: dev down reset logs test

# Throwaway DB for the test suite (kept separate from the dev DB).
TESTDB ?= funedistri_test

test: ## Run the module test suite on a throwaway DB, then exit.
	docker compose up -d db
	# Drop + recreate so each run is clean. --db-filter='.*' is REQUIRED: odoo.conf
	# pins dbfilter to ^funedistri$, which would otherwise log HttpCase sessions
	# out of $(TESTDB) (sessions get "dbfilter rejects it"). --test-tags limits to
	# our module so Odoo's own (browser) tests don't run/hang.
	-docker compose exec -T db dropdb -U odoo --if-exists $(TESTDB)
	docker compose run --rm -T odoo \
		odoo -d $(TESTDB) --db-filter='.*' -i $(MODULE),$(SEED) \
		--without-demo --stop-after-init --test-enable \
		--test-tags /$(MODULE) --log-level=test

dev: ## Boot PG + Odoo, (re)install the module, hot-reload XML/Python.
	# Bring up Postgres in the background first so it is ready for Odoo.
	docker compose up -d db
	# Run Odoo in the foreground:
	#   -d $(DB)        → use/create this database
	#   -i $(MODULE),$(SEED) → install the main module (pulls website_sale + sale
	#                     via 'depends') AND the local-only seed module that
	#                     creates the test B2B companies + users. On a fresh DB
	#                     this also creates the DB.
	#   --without-demo  → NEVER load Odoo's GLOBAL demo data (sample furniture
	#                     products, sample customers, etc). Our test accounts come
	#                     from $(SEED)'s regular `data`, not from demo, so the DB
	#                     stays clean with ONLY our seed. (This flag is a plain
	#                     boolean in this Odoo build; default is already off, we
	#                     pass it to be explicit.)
	#   --dev=all       → developer mode: hot-reload of XML views and Python.
	# --rm cleans up the one-off container; --service-ports exposes 8069.
	docker compose run --rm --service-ports odoo \
		odoo -d $(DB) -i $(MODULE),$(SEED) --without-demo --dev=all

down: ## Stop containers (Postgres data is kept in the named volume).
	# `compose down` does NOT stop one-off `compose run` containers, so a
	# foreground/detached Odoo (which uses `compose run`) lingers and keeps the
	# network "in use". Remove any odoo:19 run containers first, then down.
	-docker ps -aq --filter "ancestor=odoo:19" | xargs -r docker rm -f
	docker compose down

reset: ## Drop the dev database for a clean slate (keeps the PG server).
	docker compose up -d db
	-docker compose exec db dropdb -U odoo $(DB)

logs: ## Tail Odoo logs.
	docker compose logs -f odoo
