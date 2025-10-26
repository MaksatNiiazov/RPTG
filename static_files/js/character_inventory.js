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
    const csrfInput = container.querySelector('input[name="csrfmiddlewaretoken"]');
    const csrfToken = csrfInput ? csrfInput.value : getCsrfToken();
    const equipBase = container.dataset.equipBase;
    const dropBase = container.dataset.dropBase;
    const unequipBase = container.dataset.unequipBase || (equipBase ? equipBase.replace(/\/equip\/0\/$/, "/unequip/") : "");
    const invTableBody = container.querySelector("#inv-table tbody");

    if (!csrfToken || !equipBase || !dropBase || !invTableBody) {
        console.warn("Inventory script: missing required data attributes or CSRF token.");
        return;
    }

    container.addEventListener("submit", async (e) => {
        const form = e.target;
        if (!form.matches(".equip-form, .unequip-form, .drop-form")) return;
        e.preventDefault();

        // 1) Подтверждённое удаление
        if (form.matches(".drop-form")) {
            const name = form.closest("tr.inv-row").querySelector(".name-cell").textContent;
            if (!confirm(`Вы уверены, что хотите выбросить ${name} ?`)) return;
        }

        // 2) Построение URL
        let url;
        if (form.matches(".equip-form")) {
            const tr = form.closest("tr.inv-row");
            if (!tr) {
                showToast("Не удалось определить предмет.", "error");
                return;
            }
            url = equipBase.replace(/0\/$/, `${tr.dataset.itemId}/`);
        } else if (form.matches(".unequip-form")) {
            const row = form.closest("tr.equip-row");
            if (!row) {
                showToast("Не удалось определить слот.", "error");
                return;
            }
            const slot = row.dataset.slot;
            url = row.dataset.unequipUrl || (unequipBase ? `${unequipBase}${slot}/` : "");
        } else {  // .drop-form
            const tr = form.closest("tr.inv-row");
            if (!tr) {
                showToast("Не удалось определить предмет.", "error");
                return;
            }
            url = dropBase.replace(/0\/$/, `${tr.dataset.itemId}/`);
        }

        if (!url) {
            showToast("Не удалось сформировать запрос.", "error");
            return;
        }

        try {
            // 3) AJAX-запрос
            const res = await fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json",
                },
                body: new FormData(form),
            });
            if (!res.ok) throw new Error("HTTP " + res.status);
            const { status, data } = await res.json();
            if (status !== "ok") {
                return alert("Ошибка: " + (data.message || JSON.stringify(data)));
            }

            // 4) Обработка ответов
            if (form.matches(".equip-form")) {
                const { slot, item } = data;
                const eqRow = container.querySelector(`tr.equip-row[data-slot="${slot}"]`);
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
                // убавляем из инвентаря
                const invRow = container.querySelector(`tr.inv-row[data-item-id="${item.id}"]`);
                if (invRow) {
                    const cell = invRow.querySelector(".quantity-cell");
                    const q = parseInt(cell.textContent, 10) - 1;
                    if (q > 0) cell.textContent = q; else invRow.remove();
                }
            } else if (form.matches(".unequip-form")) {
                const { slot, item } = data;
                const eqRow = container.querySelector(`tr.equip-row[data-slot="${slot}"]`);
                eqRow.innerHTML = `
          <td>${eqRow.dataset.label}</td>
          <td colspan="4" class="empty-slot">Пусто</td>`;
                // добавляем в инвентарь
                let invRow = invTableBody.querySelector(`tr.inv-row[data-item-id="${item.id}"]`);
                if (invRow) {
                    invRow.querySelector(".quantity-cell").textContent =
                        parseInt(invRow.querySelector(".quantity-cell").textContent, 10) + 1;
                } else {
                    const tpl = document.getElementById("inv-row-template");
                    const clone = tpl.content.cloneNode(true);
                    const newRow = clone.querySelector("tr");
                    newRow.dataset.itemId = item.id;
                    newRow.querySelector(".name-cell").textContent = item.name;
                    newRow.querySelector(".quantity-cell").textContent = 1;
                    newRow.querySelector(".bonus-cell").textContent = "+" + item.bonus;
                    newRow.querySelector(".weight-cell").textContent = item.weight + " кг";
                    newRow.querySelector(".legendary-cell").textContent = item.legendary_buff || "—";
                    invTableBody.append(newRow);
                }
            } else {  // drop-form
                const { item_id, remaining } = data;
                const invRow = container.querySelector(`tr.inv-row[data-item-id="${item_id}"]`);
                if (!invRow) return;
                if (remaining > 0) invRow.querySelector(".quantity-cell").textContent = remaining;
                else invRow.remove();
            }

        } catch (err) {
            console.error(err);
            alert("Не удалось выполнить операцию: " + err.message);
        }
    });

}

function initSellButtons() {
    document.querySelectorAll(".btn-sell").forEach((button) => {
        button.addEventListener("click", async (event) => {
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
                    headers: {
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json",
                    },
                });

                if (!response.ok) {
                    throw new Error("HTTP " + response.status);
                }

                const data = await response.json();

                if (data.status === "ok") {
                    updateInventoryRow(row, data.remaining);
                    updateGoldDisplay(data.new_gold);
                    showToast(data.message, "success");
                } else {
                    showToast(data.message || "Не удалось продать предмет.", "error");
                }
            } catch (error) {
                console.error(error);
                showToast("Ошибка при отправке запроса.", "error");
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

function getCsrfToken() {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; csrftoken=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
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
