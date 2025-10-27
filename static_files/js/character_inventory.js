function getCsrfToken() {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; csrftoken=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".inventory-layout");
    if (!container) {
        return;
    }

    initInventoryTabs(container);
    initInventoryActions(container);
    initSellButtons();
});

function initInventoryTabs(container) {
    const tabs = document.createElement("div");
    tabs.className = "inventory-tabs";

    const btnEquip = document.createElement("button");
    btnEquip.type = "button";
    btnEquip.className = "tab-button";
    btnEquip.textContent = "Экипировка";

    const btnInv = document.createElement("button");
    btnInv.type = "button";
    btnInv.className = "tab-button";
    btnInv.textContent = "Инвентарь";

    tabs.append(btnEquip, btnInv);
    container.parentNode.insertBefore(tabs, container);

    const sections = container.querySelectorAll(".inventory-section");
    const equipSection = sections[0];
    const invSection = sections[1];

    if (!equipSection || !invSection) {
        return;
    }

    const activate = (tab) => {
        if (tab === "equip") {
            btnEquip.classList.add("active");
            btnInv.classList.remove("active");
            equipSection.classList.add("active");
            invSection.classList.remove("active");
        } else {
            btnInv.classList.add("active");
            btnEquip.classList.remove("active");
            invSection.classList.add("active");
            equipSection.classList.remove("active");
        }
    };

    btnEquip.addEventListener("click", () => activate("equip"));
    btnInv.addEventListener("click", () => activate("inv"));

    const showBoth = () => {
        btnEquip.classList.remove("active");
        btnInv.classList.remove("active");
        equipSection.classList.add("active");
        invSection.classList.add("active");
    };

    if (window.innerWidth <= 800) {
        activate("equip");
    } else {
        showBoth();
    }

    window.addEventListener("resize", () => {
        if (window.innerWidth <= 800) {
            activate("equip");
        } else {
            showBoth();
        }
    });
}

function initInventoryActions(container) {
    if (container.dataset.actionsInitialized === "true") {
        return;
    }
    container.dataset.actionsInitialized = "true";

    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfInput) return;

    const csrfToken = csrfInput.value;
    const equipBase = container.dataset.equipBase;
    const dropBase = container.dataset.dropBase;
    const unequipBase = container.dataset.unequipBase || equipBase?.replace(/\/equip\/0\/$/, "/unequip/");
    const storeBase = container.dataset.storageStoreBase || "";
    const retrieveBase = container.dataset.storageRetrieveBase || "";
    const deleteBase = container.dataset.storageDeleteBase || "";
    const sellBase = container.dataset.sellBase || "";
    const canUseStorage = container.dataset.canUseStorage === "true";
    const canTrade = container.dataset.canTrade === "true";
    const invTableBody = document.querySelector("#inv-table tbody");
    const storageTableBody = document.querySelector(".home-storage-table tbody");
    const storageRowTemplate = document.getElementById("storage-row-template");

    if (!csrfToken || !equipBase || !dropBase || !invTableBody) {
        console.warn("Inventory script: missing required data attributes or CSRF token.");
        return;
    }

    function buildUnequipUrl(slot) {
        if (!slot || !unequipBase) return "";

        if (unequipBase.includes("{slot}")) {
            return ensureTrailingSlash(unequipBase.replace("{slot}", slot));
        }

        if (unequipBase.includes("SLOT")) {
            return ensureTrailingSlash(unequipBase.replace(/SLOT\/?$/, slot));
        }

        if (unequipBase.includes("SLO")) {
            return ensureTrailingSlash(unequipBase.replace(/SLO\/?$/, slot));
        }

        return ensureTrailingSlash(`${unequipBase.replace(/\/$/, "")}/${slot}`);
    }

    function ensureTrailingSlash(url) {
        return url.endsWith("/") ? url : `${url}/`;
    }

    document.addEventListener("submit", async (e) => {
        const form = e.target;

        if (!form.closest('.inventory-layout, .home-storage-table')) {
            return;
        }

        if (form.matches(".storage-form")) {
            e.preventDefault();
            if (form.dataset.pending === "true") {
                return;
            }
            if (canUseStorage) {
                await handleStorageForm(form);
            }
            return;
        }

        if (!form.matches(".equip-form, .unequip-form, .drop-form")) return;
        e.preventDefault();
        if (form.dataset.pending === "true") {
            return;
        }
        await handleEquipmentForm(form);
    });

    async function handleEquipmentForm(form) {
        if (form.matches(".drop-form")) {
            const name = form.closest("tr.inv-row")?.querySelector(".name-cell")?.textContent?.trim();
            if (name && !confirm(`Вы уверены, что хотите выбросить ${name}?`)) {
                return;
            }
        }

        if (!markFormBusy(form)) {
            return;
        }

        let url;
        if (form.matches(".equip-form")) {
            const tr = form.closest("tr.inv-row");
            if (!tr) {
                releaseFormBusy(form);
                return;
            }
            url = equipBase.replace(/0\/$/, tr.dataset.itemId + "/");
        } else if (form.matches(".unequip-form")) {
            const equipRow = form.closest("tr.equip-row");
            if (!equipRow) {
                releaseFormBusy(form);
                return;
            }
            const directUrl = equipRow.dataset.unequipUrl;
            const slot = equipRow.dataset.slot;
            if (directUrl) {
                url = directUrl;
            } else if (slot) {
                url = buildUnequipUrl(slot);
            } else {
                releaseFormBusy(form);
                return;
            }
        } else {
            const tr = form.closest("tr.inv-row");
            if (!tr) {
                releaseFormBusy(form);
                return;
            }
            url = dropBase.replace(/0\/$/, tr.dataset.itemId + "/");
        }

        if (!url) {
            releaseFormBusy(form);
            showToast("Не удалось определить действие.", "error");
            return;
        }

        try {
            const res = await fetch(url, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json",
                },
                body: new FormData(form),
            });
            const payload = await parseJsonResponse(res);
            if (!res.ok || payload.status !== "ok") {
                const message = payload.message || payload.data?.message || `HTTP ${res.status}`;
                throw Object.assign(new Error(message), { status: res.status, payload });
            }

            const data = payload.data;
            if (form.matches(".equip-form")) {
                const { slot, item } = data;
                const eqRow = container.querySelector(`tr.equip-row[data-slot="${slot}"]`);
                if (eqRow) {
                    eqRow.innerHTML = `
          <td>${eqRow.dataset.label}</td>
          <td>${item.name}</td>
          <td>+${item.bonus}</td>
          <td>${item.weight} кг</td>
          <td>
            <form class="unequip-form">
              <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
              <button class="btn-inventory btn-unequip">Снять</button>
            </form>
          </td>`;
                    eqRow.dataset.slot = slot;
                    eqRow.dataset.unequipUrl = buildUnequipUrl(slot);
                }
                const invRow = container.querySelector(`tr.inv-row[data-item-id="${item.id}"]`);
                if (invRow) {
                    const cell = invRow.querySelector(".quantity-cell");
                    const nextQuantity = Math.max(0, parseInt(cell.textContent, 10) - 1);
                    if (nextQuantity > 0) {
                        cell.textContent = nextQuantity;
                        updateInventoryStoreForm(invRow, item.id, nextQuantity);
                    } else {
                        invRow.remove();
                    }
                }
            } else if (form.matches(".unequip-form")) {
                const { slot, item } = data;
                const eqRow = container.querySelector(`tr.equip-row[data-slot="${slot}"]`);
                if (eqRow) {
                    eqRow.innerHTML = `
          <td>${eqRow.dataset.label}</td>
          <td colspan="4" class="empty-slot">Пусто</td>`;
                    delete eqRow.dataset.unequipUrl;
                }
                let invRow = invTableBody?.querySelector(`tr.inv-row[data-item-id="${item.id}"]`);
                if (invRow) {
                    const qtyCell = invRow.querySelector(".quantity-cell");
                    const newQty = parseInt(qtyCell.textContent, 10) + 1;
                    qtyCell.textContent = newQty;
                    updateInventoryStoreForm(invRow, item.id, newQty);
                } else {
                    const newRow = buildInventoryRow({
                        id: item.id,
                        name: item.name,
                        bonus: item.bonus,
                        weight: item.weight,
                        legendary_buff: item.legendary_buff || "",
                        rarity_color: item.rarity_color || "#a57c52",
                        sell_price: item.sell_price ?? null,
                    }, 1);
                    invTableBody?.append(newRow);
                    initSellButtons(newRow);
                }
            } else {
                const {item_id, remaining} = data;
                const invRow = container.querySelector(`tr.inv-row[data-item-id="${item_id}"]`);
                if (!invRow) return;
                if (remaining > 0) {
                    invRow.querySelector(".quantity-cell").textContent = remaining;
                    updateInventoryStoreForm(invRow, item_id, remaining);
                } else {
                    invRow.remove();
                }
            }

            if (payload.message) {
                showToast(payload.message, "success");
            }
        } catch (err) {
            console.error(err);
            const message = err.userMessage || err.message || "Не удалось выполнить операцию";
            showToast(message, "error");
            if (message === "Неожиданный ответ от сервера. Попробуйте перезагрузить страницу.") {
                location.reload();
            }
        } finally {
            releaseFormBusy(form);
        }
    }

    async function handleStorageForm(form) {
        const actionType = form.dataset.storageAction;
        const itemId = form.dataset.itemId;
        if (!actionType || !itemId) return;

        if (actionType === "delete") {
            const name = form.closest("tr")?.querySelector(".name-cell")?.textContent?.trim();
            if (name && !confirm(`Удалить ${name} из хранилища?`)) {
                return;
            }
        }

        if (!markFormBusy(form)) {
            return;
        }

        try {
            const res = await fetch(form.getAttribute("action"), {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },
                body: new FormData(form)
            });
            const payload = await parseJsonResponse(res);
            if (!res.ok || payload.status !== "ok") {
                const message = payload.message || `HTTP ${res.status}`;
                throw Object.assign(new Error(message), { status: res.status, payload });
            }

            if (payload.action === "store") {
                updateInventoryAfterStore(payload);
                updateStorageRow(payload.item, payload.storage_quantity);
            } else if (payload.action === "retrieve") {
                updateStorageRow(payload.item, payload.storage_quantity);
                updateInventoryAfterRetrieve(payload);
            } else if (payload.action === "delete") {
                updateStorageRow({id: payload.item_id}, payload.storage_quantity);
            }

            if (payload.message) {
                showToast(payload.message, "success");
            }
        } catch (err) {
            console.error(err);
            const message = err.userMessage || err.message || "Не удалось выполнить операцию";
            showToast(message, "error");
            if (message === "Неожиданный ответ от сервера. Попробуйте перезагрузить страницу.") {
                location.reload();
            }
        } finally {
            releaseFormBusy(form);
        }
    }

    function markFormBusy(form) {
        if (!form || form.dataset.pending === "true") {
            return false;
        }
        form.dataset.pending = "true";
        form.querySelectorAll("button").forEach((button) => {
            button.disabled = true;
            button.setAttribute("aria-busy", "true");
        });
        return true;
    }

    function releaseFormBusy(form) {
        if (!form) return;
        delete form.dataset.pending;
        form.querySelectorAll("button").forEach((button) => {
            button.disabled = false;
            button.removeAttribute("aria-busy");
        });
    }

    function buildInventoryRow(item, quantity) {
        const row = document.createElement("tr");
        row.className = "inv-row";
        row.dataset.itemId = item.id;

        const nameCell = document.createElement("td");
        nameCell.className = "name-cell";
        const nameSpan = document.createElement("span");
        nameSpan.style.borderLeft = `6px solid ${item.rarity_color || "#a57c52"}`;
        nameSpan.style.paddingLeft = "6px";
        nameSpan.textContent = item.name;
        nameCell.append(nameSpan);

        const quantityCell = document.createElement("td");
        quantityCell.className = "quantity-cell";
        quantityCell.textContent = quantity;

        const bonusCell = document.createElement("td");
        bonusCell.className = "bonus-cell";
        bonusCell.textContent = `+${item.bonus}`;

        const weightCell = document.createElement("td");
        weightCell.className = "weight-cell";
        weightCell.textContent = `${item.weight} кг`;

        const legendaryCell = document.createElement("td");
        legendaryCell.className = "legendary-cell";
        legendaryCell.textContent = item.legendary_buff ? item.legendary_buff : "—";

        const actionsCell = document.createElement("td");
        actionsCell.className = "td-buttons";

        if (canTrade && sellBase && item.sell_price != null) {
            const sellBtn = document.createElement("button");
            sellBtn.className = "btn-inventory btn-sell";
            sellBtn.dataset.sellUrl = sellBase.replace(/0\/$/, `${item.id}/`);
            sellBtn.textContent = `Продать (${item.sell_price}Ꞩ)`;
            actionsCell.append(sellBtn);
        }

        const equipForm = document.createElement("form");
        equipForm.className = "equip-form";
        equipForm.method = "post";
        equipForm.append(createCsrfInput());
        const equipBtn = document.createElement("button");
        equipBtn.className = "btn-inventory btn-equip";
        equipBtn.textContent = "Экипировать";
        equipForm.append(equipBtn);
        actionsCell.append(equipForm);

        const dropForm = document.createElement("form");
        dropForm.className = "drop-form";
        dropForm.method = "post";
        dropForm.append(createCsrfInput());
        const dropBtn = document.createElement("button");
        dropBtn.className = "btn-inventory btn-drop";
        dropBtn.textContent = "Выбросить";
        dropForm.append(dropBtn);
        actionsCell.append(dropForm);

        if (canUseStorage && storeBase) {
            const storeForm = document.createElement("form");
            storeForm.className = "storage-form";
            storeForm.method = "post";
            storeForm.dataset.storageAction = "store";
            storeForm.dataset.itemId = String(item.id);
            storeForm.action = storeBase.replace(/0\/$/, `${item.id}/`);
            storeForm.append(createCsrfInput());
            const quantityInput = document.createElement("input");
            quantityInput.type = "number";
            quantityInput.name = "quantity";
            quantityInput.min = "1";
            quantityInput.max = String(quantity);
            quantityInput.value = Math.min(quantity, 1);
            quantityInput.className = "storage-quantity-input";
            quantityInput.setAttribute("aria-label", "Количество");
            const storeBtn = document.createElement("button");
            storeBtn.className = "btn-inventory btn-store";
            storeBtn.textContent = "В хранилище";
            storeForm.append(quantityInput, storeBtn);
            actionsCell.append(storeForm);
        }

        row.append(nameCell, quantityCell, bonusCell, weightCell, legendaryCell, actionsCell);
        return row;
    }

    function createCsrfInput() {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = "csrfmiddlewaretoken";
        input.value = csrfToken;
        return input;
    }

    function updateInventoryAfterStore(payload) {
        const {item, inventory_quantity} = payload;
        const row = invTableBody?.querySelector(`tr.inv-row[data-item-id="${item.id}"]`);
        if (!row) return;
        if (inventory_quantity > 0) {
            row.querySelector(".quantity-cell").textContent = inventory_quantity;
            updateInventoryStoreForm(row, item.id, inventory_quantity);
        } else {
            row.remove();
        }
    }

    function updateInventoryAfterRetrieve(payload) {
        const {item, inventory_quantity} = payload;
        let row = invTableBody?.querySelector(`tr.inv-row[data-item-id="${item.id}"]`);
        if (row) {
            row.querySelector(".quantity-cell").textContent = inventory_quantity;
            updateInventoryStoreForm(row, item.id, inventory_quantity);
        } else {
            row = buildInventoryRow(item, inventory_quantity);
            invTableBody?.append(row);
            initSellButtons(row);
        }
    }

    function updateInventoryStoreForm(row, itemId, quantity) {
        if (!canUseStorage) return;
        const storeForm = row.querySelector('.storage-form[data-storage-action="store"]');
        if (!storeForm) return;
        storeForm.dataset.itemId = String(itemId);
        if (storeBase) {
            storeForm.action = storeBase.replace(/0\/$/, `${itemId}/`);
        }
        const input = storeForm.querySelector('input[name="quantity"]');
        if (!input) return;
        input.max = String(quantity);
        if (!input.value || parseInt(input.value, 10) < 1) {
            input.value = quantity > 0 ? 1 : 0;
        }
        if (parseInt(input.value, 10) > quantity) {
            input.value = quantity;
        }
    }

    function updateStorageRow(item, quantity) {
        if (!storageTableBody || !item?.id) return;
        let row = storageTableBody.querySelector(`tr.storage-row[data-item-id="${item.id}"]`);

        if (quantity <= 0) {
            if (row) row.remove();
            ensureStorageEmptyRow();
            return;
        }

        removeStorageEmptyRow();

        if (!row) {
            if (!storageRowTemplate) return;
            const clone = storageRowTemplate.content.cloneNode(true);
            row = clone.querySelector("tr.storage-row");
            if (!row) return;
            row.dataset.itemId = String(item.id);
            storageTableBody.append(row);
        }

        if (item.name !== undefined) {
            const nameCell = row.querySelector(".name-cell");
            if (nameCell) {
                let span = nameCell.querySelector("span");
                if (!span) {
                    span = document.createElement("span");
                    nameCell.innerHTML = "";
                    nameCell.append(span);
                }
                span.style.borderLeft = `6px solid ${item.rarity_color || "#a57c52"}`;
                span.style.paddingLeft = "6px";
                span.textContent = item.name;
            }
        }

        if (item.bonus !== undefined) {
            const bonusCell = row.querySelector(".bonus-cell");
            if (bonusCell) bonusCell.textContent = `+${item.bonus}`;
        }
        if (item.weight !== undefined) {
            const weightCell = row.querySelector(".weight-cell");
            if (weightCell) weightCell.textContent = `${item.weight} кг`;
        }
        if (item.legendary_buff !== undefined) {
            const legendaryCell = row.querySelector(".legendary-cell");
            if (legendaryCell) legendaryCell.textContent = item.legendary_buff ? item.legendary_buff : "—";
        }

        const qtyCell = row.querySelector(".quantity-cell");
        if (qtyCell) qtyCell.textContent = quantity;

        row.querySelectorAll(".storage-form").forEach(storageForm => {
            storageForm.dataset.itemId = String(item.id);
            const actionType = storageForm.dataset.storageAction;
            let base = "";
            if (actionType === "retrieve") base = retrieveBase;
            if (actionType === "delete") base = deleteBase;
            if (base) storageForm.action = base.replace(/0\/$/, `${item.id}/`);
            const input = storageForm.querySelector('input[name="quantity"]');
            if (input) {
                input.max = String(quantity);
                if (actionType === "delete") {
                    input.value = quantity;
                } else if (parseInt(input.value, 10) > quantity) {
                    input.value = quantity;
                } else if (parseInt(input.value || "1", 10) < 1) {
                    input.value = 1;
                }
            }
        });
    }

    function removeStorageEmptyRow() {
        if (!storageTableBody) return;
        const emptyRow = storageTableBody.querySelector("tr.empty-row[data-empty='storage']");
        if (emptyRow) emptyRow.remove();
    }

    function ensureStorageEmptyRow() {
        if (!storageTableBody) return;
        const hasItems = storageTableBody.querySelector("tr.storage-row");
        let emptyRow = storageTableBody.querySelector("tr.empty-row[data-empty='storage']");
        if (hasItems) {
            if (emptyRow) emptyRow.remove();
            return;
        }
        if (!emptyRow) {
            emptyRow = document.createElement("tr");
            emptyRow.className = "empty-row";
            emptyRow.dataset.empty = "storage";
            const td = document.createElement("td");
            td.colSpan = 6;
            td.className = "empty-slot";
            td.textContent = "Хранилище пусто.";
            emptyRow.append(td);
            storageTableBody.append(emptyRow);
        }
    }
}

function initSellButtons(context = document) {
    if (!context || typeof context.querySelectorAll !== "function") return;
    context.querySelectorAll(".btn-sell").forEach(button => {
        if (button.dataset.sellHandlerAttached === "true") return;
        button.dataset.sellHandlerAttached = "true";
        button.addEventListener("click", async event => {
            event.preventDefault();

            const url = button.dataset.sellUrl;
            const row = button.closest("tr");

            if (!url || !row) {
                showToast("Не удалось определить товар для продажи.", "error");
                return;
            }

            const itemName = row.querySelector(".name-cell")?.textContent.trim() || "";
            const quantity = row.querySelector(".quantity-cell")?.textContent.trim() || "0";

            const priceText = button.textContent.match(/\d+/g)?.[0] || "?";
            const confirmText = `Продать ${itemName} за ${priceText} Ꞩ ?\nУ вас ${quantity} шт.`;
            if (!confirm(confirmText)) return;

            button.disabled = true;
            button.setAttribute("aria-busy", "true");

            try {
                const response = await fetch(url, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json",
                    },
                });

                const data = await parseJsonResponse(response);

                if (!response.ok || data.status !== "ok") {
                    throw Object.assign(
                        new Error(data.message || `HTTP ${response.status}`),
                        { status: response.status, payload: data }
                    );
                }

                updateInventoryRow(row, data.remaining);
                updateGoldDisplay(data.new_gold);
                if (data.message) {
                    showToast(data.message, "success");
                }
            } catch (error) {
                console.error(error);
                const message = error.userMessage || error.message || "Ошибка при отправке запроса.";
                showToast(message, "error");
            } finally {
                button.disabled = false;
                button.removeAttribute("aria-busy");
            }
        });
    });
}

function updateInventoryRow(row, remainingQuantity) {
    if (remainingQuantity <= 0) {
        row.remove();
    } else {
        const qtyCell = row.querySelector(".quantity-cell");
        if (qtyCell) qtyCell.textContent = remainingQuantity;
    }
}

function updateGoldDisplay(newGold) {
    const goldDisplay = document.querySelector("#char-gold");
    if (goldDisplay) {
        goldDisplay.textContent = `${newGold} Ꞩ`;
    }
}

function showToast(message, type = "info") {
    removeExistingToasts();

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.role = "status";
    toast.ariaLive = "polite";
    toast.textContent = message;

    document.body.appendChild(toast);
    requestAnimationFrame(() => {
        toast.classList.add("toast-visible");
    });

    setTimeout(() => {
        toast.classList.remove("toast-visible");
        toast.addEventListener("transitionend", () => toast.remove(), { once: true });
    }, 3200);
}

function removeExistingToasts() {
    document.querySelectorAll(".toast").forEach((toast) => {
        toast.remove();
    });
}

async function parseJsonResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        try {
            return await response.json();
        } catch (err) {
            err.userMessage = "Не удалось обработать ответ сервера.";
            throw err;
        }
    }

    const text = await response.text();
    const status = response.status || 0;
    const error = new Error(`Сервер вернул неожиданный ответ (HTTP ${status || "?"}).`);
    error.status = status;
    error.responseText = text;
    error.userMessage = "Неожиданный ответ от сервера. Попробуйте перезагрузить страницу.";
    throw error;
}