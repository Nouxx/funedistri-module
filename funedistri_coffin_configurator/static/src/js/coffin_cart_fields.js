/** @odoo-module **/

// Step 4.6 — generic conditional-reveal + save for the cart-page config fields.
//
// This JS holds NO business rules. It reads the rules the server rendered into
// data-* attributes (which option value reveals which field, and whether it's
// required) and just obeys them: show/hide each field, and POST changes to the
// server. The server stays the source of truth (it re-validates at submit and
// enforces the ≤20-char limit on write).

import { rpc } from "@web/core/network/rpc";

function parseIds(value) {
    return (value || "")
        .split(",")
        .filter(Boolean)
        .map(Number);
}

function initCoffinCartFields() {
    document.querySelectorAll(".o_coffin_config_fields").forEach((container) => {
        const lineId = parseInt(container.dataset.lineId, 10);
        const selected = parseIds(container.dataset.selectedValueIds);

        container.querySelectorAll(".o_coffin_field").forEach((field) => {
            const triggers = parseIds(field.dataset.triggerValueIds);
            // Reveal when the field has no trigger (always shown) or one of its
            // trigger values is among the line's selected options.
            const revealed =
                triggers.length === 0 ||
                triggers.some((id) => selected.includes(id));
            field.style.display = revealed ? "" : "none";

            const input = field.querySelector(".o_coffin_input");
            const errEl = field.querySelector(".o_coffin_field_error");
            if (!input) {
                return;
            }

            input.addEventListener("change", async () => {
                try {
                    const res = await rpc("/coffin/cart/line/save", {
                        line_id: lineId,
                        field: field.dataset.field,
                        value: input.value,
                    });
                    if (res && res.error) {
                        errEl.textContent = res.error;
                        errEl.classList.remove("d-none");
                        input.classList.add("is-invalid");
                    } else {
                        errEl.textContent = "";
                        errEl.classList.add("d-none");
                        input.classList.remove("is-invalid");
                    }
                } catch (_e) {
                    errEl.textContent = "Erreur d'enregistrement.";
                    errEl.classList.remove("d-none");
                }
            });
        });
    });
}

// Assets may load before or after DOMContentLoaded — handle both.
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCoffinCartFields);
} else {
    initCoffinCartFields();
}
