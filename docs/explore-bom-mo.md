# Discovering BoM & MO in Odoo — hands-on playground

Goal: learn Odoo's **Bill of Materials (BoM)** and **Manufacturing Order (MO)**
features so we can decide how an option choice (e.g. `handle = oak`) auto-consumes
the chosen part's **shared** stock when a coffin is ordered.

Context for the decision this feeds: see ADR 0004 (config data) and the open
"stock decrement" question. Two candidate native paths — **Kit BoM** (no MO) vs
**normal BoM + MO** — explored below. Pick after playing.

Prereqs: **Inventory** + **Manufacturing** apps installed (the Owner already runs
both). Use throwaway `TEST ...` products so you can poke freely without touching
the module's demo data.

---

## Setup — one part with real stock (5 min)

You need a stocked part to watch get consumed.

1. **Inventory → Products → Products → New.**
2. Name: `TEST Oak Handle`. Product type: **Goods**, and turn **Track Inventory**
   ON (this makes stock count — a service/consumable won't show stock moves).
3. Save.
4. On the product, click **Update Quantity** (or the **On Hand** smart button) →
   set **On Hand = 10**. Save.
5. Repeat for a second part: `TEST Plywood Handle`, On Hand = 10. (So you can see
   the *right* one drop.)

Now a coffin to build:

6. **Inventory → Products → Products → New.** Name: `TEST Coffin`. Type: **Goods**.
   Save. (Stock tracking on the coffin itself doesn't matter for Kit; leave default.)

---

## Track A — Kit BoM (no manufacturing order)

Goal: selling + delivering the coffin auto-consumes a handle, no MO.

1. **Manufacturing → Products → Bills of Materials → New.**
2. **Product** = `TEST Coffin`.
3. **BoM Type** = **Kit**. ← the whole trick. "Kit" = phantom, explodes into
   components at delivery.
4. **Components** tab → add line: `TEST Oak Handle`, Quantity 1. Save.
5. Watch it consume on a real sale:
   - **Sales → Orders → New.** Customer = any. Add line `TEST Coffin`, qty 1.
     **Confirm**.
   - A **Delivery** smart button appears. Open it. Delivery lines show **the
     handle**, not the coffin — that's the kit exploding.
   - **Validate** the delivery.
6. Back on `TEST Oak Handle` → On Hand is now **9**. Stock dropped, no MO. ✅

Lightest path. Stock only moves at **delivery validation**, after you confirm the
order — matches the Validate-then-ship flow.

### See the option→part mapping ("Apply on Variants")

How `handle = oak` picks the oak line vs `handle = plywood` picks plywood, from
one BoM.

1. Give `TEST Coffin` a variant axis: open the coffin product → **Attributes &
   Variants** tab → add attribute **Handle** with values **Oak**, **Plywood**.
   Save. (Now two coffin variants exist.)
2. Open the Kit BoM again. On each component line there's an **Apply on Variants**
   column (if hidden: turn on **Developer Mode** — Settings → General → Developer
   Tools — then it shows).
3. Oak-handle line → Apply on Variants = **Oak**. Add a Plywood-handle line →
   Apply on Variants = **Plywood**.
4. Sell the coffin choosing **Plywood** → only `TEST Plywood Handle` drops. One
   BoM, value-driven. ✅

---

## Track B — Normal BoM + Manufacturing Order

Goal: a build step you close by hand; the MO consumes parts.

1. Open (or new) BoM for `TEST Coffin`, **BoM Type = Manufacture this product**
   (not Kit).
2. Components: `TEST Oak Handle` qty 1. Save.
3. **Manufacturing → Operations → Manufacturing Orders → New.**
4. Product = `TEST Coffin`, Quantity 1 → it auto-pulls the BoM components.
5. **Confirm**, then **Produce / Mark as Done**.
6. Check `TEST Oak Handle` On Hand → dropped by 1. The coffin itself becomes +1
   finished-good stock.

Difference you feel: Track B made you open and close a **separate build order**
(the MO), and the coffin is now its own stocked finished good. Track A had no such
step — the coffin "is" its parts.

---

## What to notice while deciding

- **Paperwork:** Kit = 0 extra docs. BoM+MO = one MO per coffin to open/close.
- **Finished-good stock:** Kit doesn't track coffins as stock; MO does (+1 coffin
  each build).
- **Reservation timing:** both only touch stock after the order is confirmed (the
  Validate step). Draft/Pending orders reserve nothing.
- **Oversell protection:** both decrement the **shared** handle SKU, so loose-handle
  sales and coffin sales draw the same pool — the core requirement.

Cleanup when done: delete the `TEST` products + BoMs, or just leave them (test
data, harmless locally).

---

## Decision to bring back

Kit or BoM+MO? Either way, the stock-consuming options (handles, maybe wood) become
**real variant axes** while everything else stays no-variant — that part is settled
and gets an ADR. Kit vs MO is the remaining fork.
