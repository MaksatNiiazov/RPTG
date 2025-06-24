document.addEventListener("DOMContentLoaded", () => {
    const toggleBtns = document.querySelectorAll(".toggle-trade-btn");

    toggleBtns.forEach(toggleBtn => {
        toggleBtn.addEventListener("click", (event) => {
            event.preventDefault(); // предотвращает скролл и поведение <a href="#">

            const url = toggleBtn.dataset.url;

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "ok") {
                        const newState = data.new_value;
                        toggleBtn.dataset.current = newState ? "1" : "0";
                        toggleBtn.textContent = newState
                            ? "🔒 Запретить торговлю"
                            : "🛒 Разрешить торговлю";
                        showToast(`Торговля ${newState ? "разрешена" : "запрещена"}`, "success");
                    } else {
                        showToast(data.message, "error");
                    }
                })
                .catch(() => {
                    showToast("Произошла ошибка при запросе", "error");
                });
        });
    });
});

function getCsrfToken() {
    const name = "csrftoken";
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : '';
}

function showToast(msg, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    Object.assign(toast.style, {
        position: "fixed",
        bottom: "20px",
        right: "20px",
        background: type === "success" ? "#2ecc71" : "#e74c3c",
        color: "#fff",
        padding: "10px 15px",
        borderRadius: "6px",
        zIndex: 9999,
        fontSize: "14px",
        opacity: 0.95,
    });
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
