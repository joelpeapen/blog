document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        const msgs = document.getElementsByClassName("messages");
        for (let i = 0; i < msgs.length; i++) {
            msgs[i].style.display = "none";
        }
    }, 5000);


    const navbarBurgers = document.querySelectorAll('.navbar-burger');

    navbarBurgers.forEach(el => {
        el.addEventListener('click', () => {
            const target = el.dataset.target;
            const targetElement = document.getElementById(target);

            el.classList.toggle('is-active');
            targetElement.classList.toggle('is-active');
        });
    });

    const links = document.querySelectorAll(".confirm");
    links.forEach(link => {
        link.addEventListener("click", (event) => {
            const confirmed = confirm("Are you sure?");
            if (!confirmed) {
                event.preventDefault();
            }
        });
    });

    charLimit("title", "titlelimit")
    charLimit("subtitle", "sublimit")
    charLimit("splashdesc", "splashlimit")

    copyURL("share", "copied")

    const add = document.getElementById("add-comment");
    if (add) {
        add.addEventListener('click', function() {
            let c = document.getElementById("comment-form");
            if (c.style.display === "none" || c.style.display === '') {
                c.style.display = "block";
                add.style.display = "none";
            } else {
                c.style.display = "none";
            }
        });
    }

    const cancel = document.getElementById("comment-cancel");
    if (cancel) {
        cancel.addEventListener("click", function() {
            document.getElementById("comment-form").style.display = "none";
            const add = document.getElementById("add-comment");
            add.style.display = "block";
        });
    }

    const edit = document.getElementById("edit-comment");
    if (edit) {
        edit.addEventListener('click', function() {
            let c = document.getElementById("comment-form-edit");
            let t = document.getElementById("user-comment")
            if (c.style.display === "none" || c.style.display === '') {
                c.style.display = "flex";
                t.style.display = "none";
            } else {
                c.style.display = "none";
                t.style.display = "block";
            }
        });
    }

    const cancelEdit = document.getElementById("comment-cancel-edit");
    if (cancelEdit) {
        cancelEdit.addEventListener("click", function() {
            let c = document.getElementById("comment-form-edit");
            let t = document.getElementById("user-comment")
            if (c) {
                c.style.display = "none";
                t.style.display = "block";
            } else {
                t.style.display = "none";
            }
        });
    }
});

function charLimit(input, limit) {
    const box = document.getElementById(input);
    const left = document.getElementById(limit);

    if (box) {
        box.oninput = () => {
            const max = box.getAttribute("maxlength");
            const len = box.value.length;

            const width = (len / max) * 100;
            left.style.display = "none";

            if (width <= 60) {
                box.style.borderBottom = "4px solid rgb(19, 160, 19)";
            } else if (width > 60 && width < 80) {
                box.style.borderBottom = "4px solid rgb(236, 157, 8)";
            } else {
                box.style.borderBottom = "4px solid rgb(241, 9, 9)";
                left.innerHTML = `${max - len} characters left`;
                left.style.color = "rgb(236, 157, 8)";
                left.style.display = "block";
            }
        }
    }
}

function copyURL(button, popup) {
    const b = document.getElementById(button)
    const pop = document.getElementById(popup)
    if (b && pop) {
        b.addEventListener('click', () => {
            navigator.clipboard.writeText(window.location.href).then(() => {
                pop.style.display = "block";

                setTimeout(() => {
                    pop.style.display = "none";
                }, 2000);

            }).catch((error) => {
                console.error("Error copying text: ", error);
            });
        });
    }
}
