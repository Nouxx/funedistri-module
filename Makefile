# Local dev shortcuts. Dev-only file — Odoo.sh ignores it.
#
# Quick start:
#   1. Start Docker Desktop (the daemon must be running).
#   2. make dev      → boots Postgres + Odoo, installs the module, dev mode.
#   3. open http://localhost:8069   (login: admin / admin)
#
# Name of the dev database. Override with: make dev DB=foo
DB ?= funedistri
MODULE := funedistri_coffin_configurator

.PHONY: dev down reset logs

dev: ## Boot PG + Odoo, (re)install the module, hot-reload XML/Python.
	# Bring up Postgres in the background first so it is ready for Odoo.
	docker compose up -d db
	# Run Odoo in the foreground:
	#   -d $(DB)        → use/create this database
	#   -i $(MODULE)    → install the module (pulls website_sale + sale via
	#                     'depends'); on a fresh DB this also creates the DB.
	#   --with-demo     → load demo data (v19 made demo OPT-IN; without this the
	#                     demo coffin + B2B users are NOT seeded). Only affects a
	#                     FRESH DB — demo loads at creation, so `make reset` first
	#                     if an existing DB was created without it.
	#   --dev=all       → developer mode: hot-reload of XML views and Python.
	# --rm cleans up the one-off container; --service-ports exposes 8069.
	docker compose run --rm --service-ports odoo \
		odoo -d $(DB) -i $(MODULE) --with-demo --dev=all

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
