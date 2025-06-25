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
});
