const toggle = document.querySelector(".nav-toggle");
const navigation = document.getElementById("main-navigation");

if (toggle && navigation) {
  const closeNavigation = () => {
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Buka menu navigasi");
    navigation.classList.remove("is-open");
  };

  toggle.addEventListener("click", () => {
    const isOpen = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", String(!isOpen));
    toggle.setAttribute("aria-label", isOpen ? "Buka menu navigasi" : "Tutup menu navigasi");
    navigation.classList.toggle("is-open", !isOpen);
  });

  navigation.addEventListener("click", event => {
    if (event.target.closest("a")) closeNavigation();
  });

  document.addEventListener("pointerdown", event => {
    if (!navigation.contains(event.target) && !toggle.contains(event.target)) closeNavigation();
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
      closeNavigation();
      toggle.focus();
    }
  });

  window.matchMedia("(min-width: 641px)").addEventListener("change", closeNavigation);
}