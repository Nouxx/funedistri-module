this repo is a custom odoo module

# Context

- an existing odoo ecommerce website that sells coffin B2B: https://funedistri.odoo.com
- only B2B users approved by the owner can login and shop products
- right now, coffins are pre-configured (wood, details...) and users can pick the one they want
- hosted in Odoo.sh

# Need

- a custom module for the owner to configure (in Odoo backend) all options for the coffin, such as:
    - wood (oak, plywood...) -> dropdown
    - Engraving (yes, no + text)
    - ... 
    as well as their corresponding price

- Such "base" products to be integrated in Odoo catalog

## Details worth mentionning

- They will be 2 types of B2B users: "SALESMAN" and "STORE_OWNER"
- Only a user with either role can access the catalog and place order
- "SALESMAN" does not see any price, "STORE_OWNER" does
- By "place an order" what I mean is a user (registered in a company) can place an order without paying anything, the owner has to manually validate the order and organize to ship it

# What is this repo

answer these questions/tasks:
- Do I need the owner Odoo codebase (more like configuration) here?
- Depending on the answer of the question below, prepare a local setup for me in this repo, so that I can run everything in a single command (ex: `make dev`)

## Guidelines

- ALWAYS explain in comment what the code does and WHY. I am new to python and Odoo so I need this information
