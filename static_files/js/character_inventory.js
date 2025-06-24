document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".inventory-layout");
    if (!container) return;

    // создаём таб-бар
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

    // находим секции
    const equipSection = container.querySelector(".inventory-section:nth-child(1)");
    const invSection = container.querySelector(".inventory-section:nth-child(2)");
    if (!equipSection || !invSection) return;

    // функция переключения
    function activate(tab) {
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
    }

    // обработчики
    btnEquip.addEventListener("click", () => activate("equip"));
    btnInv.addEventListener("click", () => activate("inv"));

    // при загрузке: на мобиле показываем экипировку по умолчанию
    if (window.innerWidth <= 800) {
        activate("equip");
    } else {
        // на десктопе показываем обе секции
        equipSection.classList.add("active");
        invSection.classList.add("active");
    }

    // при ресайзе: пересчитать
    window.addEventListener("resize", () => {
        if (window.innerWidth <= 800) {
            activate("equip");
        } else {
            btnEquip.classList.remove("active");
            btnInv.classList.remove("active");
            equipSection.classList.add("active");
            invSection.classList.add("active");
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".inventory-layout");
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    const equipBase = container.dataset.equipBase;   // e.g. "/characters/characters/3/equip/0/"
    const dropBase = container.dataset.dropBase;    // e.g. "/characters/characters/3/drop/0/"
    const unequipBase = equipBase.replace(/\/equip\/0\/$/, "/unequip/");
    const invTableBody = document.querySelector("#inv-table tbody");

    container.addEventListener("submit", async e => {
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
            url = equipBase.replace(/0\/$/, tr.dataset.itemId + "/");
        } else if (form.matches(".unequip-form")) {
            const slot = form.closest("tr.equip-row").dataset.slot;
            url = unequipBase + slot + "/";
        } else {  // .drop-form
            const tr = form.closest("tr.inv-row");
            url = dropBase.replace(/0\/$/, tr.dataset.itemId + "/");
        }

        try {
            // 3) AJAX-запрос
            const res = await fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },
                body: new FormData(form)
            });
            if (!res.ok) throw new Error("HTTP " + res.status);
            const {status, data} = await res.json();
            if (status !== "ok") {
                return alert("Ошибка: " + (data.message || JSON.stringify(data)));
            }

            // 4) Обработка ответов
            if (form.matches(".equip-form")) {
                const {slot, item} = data;
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
                const {slot, item} = data;
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
                const {item_id, remaining} = data;
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
});
document.addEventListener("DOMContentLoaded", () => {
    initSellButtons();
});

function initSellButtons() {
    document.querySelectorAll(".btn-sell").forEach(button => {
        button.addEventListener("click", event => {
            event.preventDefault();

            const url = button.dataset.sellUrl;
            const row = button.closest("tr");

            const itemName = row.querySelector(".name-cell").textContent.trim();
            const quantity = row.querySelector(".quantity-cell").textContent.trim();

            const priceText = button.textContent.match(/\d+/g)?.[0] || "?";
            const confirmText = `Продать ${itemName} за ${priceText} Ꞩ ?\nУ вас ${quantity} шт.`;
            if (!confirm(confirmText)) return;

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === "ok") {
                        updateInventoryRow(row, data.remaining);
                        updateGoldDisplay(data.new_gold);
                        showToast(data.message, "success");
                    } else {
                        showToast(data.message, "error");
                    }
                })
                .catch(() => {
                    showToast("Ошибка при отправке запроса.", "error");
                });
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
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    Object.assign(toast.style, {
        position: "fixed",
        bottom: "20px",
        right: "20px",
        background: type === "success" ? "#2ecc71" : "#e74c3c",
        color: "#fff",
        padding: "10px 15px",
        borderRadius: "6px",
        boxShadow: "0 2px 6px rgba(0,0,0,0.3)",
        zIndex: 9999,
        fontSize: "14px",
        opacity: 0.95,
    });

    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
