document.addEventListener("DOMContentLoaded", () => {
    const toggleBtns = document.querySelectorAll(".toggle-trade-btn");

    toggleBtns.forEach((toggleBtn) => {
        const initialState = toggleBtn.dataset.current === "1";
        updateTradeButton(toggleBtn, initialState);

        toggleBtn.addEventListener("click", async (event) => {
            event.preventDefault();
            if (toggleBtn.dataset.loading === "1") {
                return;
            }

            const url = toggleBtn.dataset.url;
            if (!url) {
                showToast("Неизвестный адрес для запроса", "error");
                return;
            }

            toggleBtn.dataset.loading = "1";
            toggleBtn.setAttribute("aria-busy", "true");

            try {
                const response = await fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    credentials: "same-origin",
                });

                let payload = null;
                try {
                    payload = await response.json();
                } catch (error) {
                    // Ответ может быть не JSON (например, при ошибке CSRF)
                }

                if (!response.ok) {
                    const message = payload?.message || "Не удалось изменить состояние торговли";
                    throw new Error(message);
                }

                if (!payload || payload.status !== "ok") {
                    const message = payload?.message || "Не удалось изменить состояние торговли";
                    throw new Error(message);
                }

                const newState = Boolean(payload.new_value);
                updateTradeButton(toggleBtn, newState);
                showToast(`Торговля ${newState ? "разрешена" : "запрещена"}`, "success");
            } catch (error) {
                showToast(error.message || "Произошла ошибка при запросе", "error");
            } finally {
                toggleBtn.dataset.loading = "0";
                toggleBtn.removeAttribute("aria-busy");
            }
        });
    });
});

function updateTradeButton(button, canTrade) {
    button.dataset.current = canTrade ? "1" : "0";
    button.setAttribute("aria-pressed", canTrade ? "true" : "false");

    const labelEl = button.querySelector(".toggle-trade-label");
    if (labelEl) {
        labelEl.textContent = canTrade ? "Запретить торговлю" : "Разрешить торговлю";
    } else {
        const textNode = Array.from(button.childNodes).find(
            (node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim().length
        );
        if (textNode) {
            textNode.textContent = canTrade ? " Запретить торговлю" : " Разрешить торговлю";
        } else {
            button.textContent = canTrade ? "Запретить торговлю" : "Разрешить торговлю";
        }
    }

    const statusEl = button.querySelector(".toggle-trade-status");
    if (statusEl) {
        statusEl.textContent = canTrade ? "Торговля разрешена" : "Торговля запрещена";
    }
}

function getCsrfToken() {
    const name = "csrftoken";
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? match[2] : "";
}

function showToast(msg, type = "info") {
    removeExistingToasts();

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.role = "status";
    toast.ariaLive = "polite";
    toast.textContent = msg;

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
    document.querySelectorAll(".toast").forEach((toast) => toast.remove());
}
