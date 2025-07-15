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
    charLimit("comment", "comment-limit")
    charLimit("name", "namelimit")

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
        cancel.addEventListener("click", () => {
            document.getElementById("comment-form").style.display = "none";
            const add = document.getElementById("add-comment");
            add.style.display = "block";
        });
    }

    let editComment = document.querySelectorAll('.edit-comment');
    if (editComment) {
        editComment.forEach(edit => {
            edit.addEventListener('click', () => {
                const id = edit.id.split('-')[2];
                const form = document.getElementById(`comment-form-edit-${id}`);
                const text = document.getElementById(`user-comment-${id}`);

                charLimit(`comment-edit-${id}`, `comment-edit-limit-${id}`)

                if (form.style.display === "none" || form.style.display === '') {
                    form.style.display = "flex";
                    text.style.display = "none";
                } else {
                    form.style.display = "none";
                    text.style.display = "block";
                }
            });
        });
    }

    let editCommentCancel = document.querySelectorAll('.comment-cancel-edit');
    if (editCommentCancel) {
        editCommentCancel.forEach(cancel => {
            cancel.addEventListener("click", () => {
                const id = cancel.id.split('-')[3];
                const form = document.getElementById(`comment-form-edit-${id}`);
                const text = document.getElementById(`user-comment-${id}`);

                if (form) {
                    form.style.display = "none";
                    text.style.display = "block";
                } else {
                    text.style.display = "none";
                }
            });
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
