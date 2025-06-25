document.addEventListener("DOMContentLoaded", function() {
    setTimeout(() => {
        const msgs = document.getElementsByClassName("messages");
        for (let i = 0; i < msgs.length; i++) {
            msgs[i].style.display = "none";
        }
    }, 3000);


    const navbarBurgers = document.querySelectorAll('.navbar-burger');

    navbarBurgers.forEach(el => {
        el.addEventListener('click', () => {
            const target = el.dataset.target;
            const targetElement = document.getElementById(target);

            el.classList.toggle('is-active');
            targetElement.classList.toggle('is-active');
        });
    });


    charLimit("title", "titlelimit")
    charLimit("subtitle", "sublimit")
    charLimit("bio", "biolimit")

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
