(function () {
  function initMobileMenu() {
    const toggle = document.getElementById("mobile-menu-toggle");
    const panel = document.getElementById("mobile-menu-panel");
    const overlay = document.getElementById("mobile-menu-overlay");

    if (!toggle || !panel || !overlay) return;

    const closeMenu = () => {
      panel.classList.remove("open");
      overlay.classList.remove("active");
      toggle.classList.remove("active");
      toggle.setAttribute("aria-expanded", "false");
      panel.setAttribute("aria-hidden", "true");
      overlay.setAttribute("aria-hidden", "true");
      document.body.classList.remove("menu-open");
    };

    const openMenu = () => {
      panel.classList.add("open");
      overlay.classList.add("active");
      toggle.classList.add("active");
      toggle.setAttribute("aria-expanded", "true");
      panel.setAttribute("aria-hidden", "false");
      overlay.setAttribute("aria-hidden", "false");
      document.body.classList.add("menu-open");
    };

    toggle.addEventListener("click", () => {
      if (panel.classList.contains("open")) closeMenu();
      else openMenu();
    });

    overlay.addEventListener("click", closeMenu);

    panel.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closeMenu);
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeMenu();
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 768) closeMenu();
    });
  }

  function initRevealAnimations() {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const targets = document.querySelectorAll(
      ".page-hero .container, .section-header, .content-block, .info-card, .mode-card, .demo-box, .disclaimer-card, .result-card"
    );

    if (targets.length === 0) return;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      targets.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    targets.forEach((el, idx) => {
      el.classList.add("reveal");
      el.style.setProperty("--reveal-delay", `${Math.min(idx * 0.05, 0.25)}s`);
    });

    const observer = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        });
      },
      {
        threshold: 0.15,
        rootMargin: "0px 0px -10% 0px",
      }
    );

    targets.forEach((el) => observer.observe(el));
  }

  document.addEventListener("DOMContentLoaded", () => {
    initMobileMenu();
    initRevealAnimations();
  });
})();
