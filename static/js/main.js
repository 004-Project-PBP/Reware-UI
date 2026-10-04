// Navbar: mobile menu, shadow once scrolled, link of the section in view
const header = document.querySelector('.site-header');
const nav = header.querySelector('.nav');
const toggle = nav.querySelector('.nav__toggle');

function setMenu(open) {
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', open);
    toggle.setAttribute('aria-label', open ? 'Tutup menu' : 'Buka menu');
}

toggle.addEventListener('click', () => setMenu(!nav.classList.contains('is-open')));
nav.querySelectorAll('.nav__menu a').forEach((link) => {
    link.addEventListener('click', () => setMenu(false));
});
document.addEventListener('click', (event) => {
    if (!nav.contains(event.target)) setMenu(false);
});
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setMenu(false);
});
// same breakpoint as the mobile nav in style.css
window.matchMedia('(min-width: 761px)').addEventListener('change', (event) => {
    if (event.matches) setMenu(false);
});

function updateHeader() {
    header.classList.toggle('is-scrolled', window.scrollY > 24);
}
updateHeader();
window.addEventListener('scroll', updateHeader, { passive: true });

const navLinks = [...nav.querySelectorAll('.nav__links a')].filter((link) => link.hash);
const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        const link = navLinks.find((a) => a.hash === `#${entry.target.id}`);
        link.classList.toggle('is-active', entry.isIntersecting);
    });
}, { rootMargin: '-45% 0px -50% 0px' });

navLinks.forEach((link) => {
    const section = document.getElementById(link.hash.slice(1));
    if (section) sectionObserver.observe(section);
});
