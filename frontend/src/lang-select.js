// =====================
// DOM
// =====================
const langBtn = document.getElementById("select-trigger-audio");

// =====================
// Display languages
// =====================
function setupCustomSelect(selectRootId, defaultValue) {
    const root = document.getElementById(selectRootId);
    const trigger = root.querySelector(".select-trigger");
    const menu = root.querySelector(".select-menu");

    fetch("/lang_list.json")
        .then(res => res.json())
        .then(languages => {
            menu.innerHTML = "";

            languages.forEach(lang => {
                const li = document.createElement("li");
                li.textContent = lang.label;
                li.dataset.value = lang.code;

                li.addEventListener("click", () => {
                    trigger.textContent = lang.label;
                    trigger.dataset.value = lang.code;
                    root.classList.remove("open");
                });

                menu.appendChild(li);

                if (lang.code === defaultValue) {
                    trigger.textContent = lang.label;
                    trigger.dataset.value = lang.code;
                }
            });
        });

    // ouvrir / fermer
    trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        root.classList.toggle("open");
    });

    // fermer si clic ailleurs
    document.addEventListener("click", () => {
        root.classList.remove("open");
    });
}

function getSelectedLanguages() {
    return {
        audio: document
            .querySelector("#select-audio .select-trigger")
            .dataset.value
    };
}

document.addEventListener("DOMContentLoaded", () => {
    setupCustomSelect("select-audio", "fr-FR");
});

