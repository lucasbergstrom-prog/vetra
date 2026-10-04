// VETRA site. No dependencies, no network requests, nothing stored.
(function () {
  "use strict";

  // --- mobile navigation
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  // --- the product tour's tabs
  document.querySelectorAll("[data-tabs]").forEach(function (root) {
    var tabs = Array.prototype.slice.call(root.querySelectorAll('[role="tab"]'));
    var panels = Array.prototype.slice.call(root.querySelectorAll('[role="tabpanel"]'));
    function show(index, focus) {
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.setAttribute("aria-selected", on ? "true" : "false");
        tab.tabIndex = on ? 0 : -1;
        panels[i].hidden = !on;
      });
      if (focus) { tabs[index].focus(); }
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () { show(i, false); });
      tab.addEventListener("keydown", function (event) {
        var next = null;
        if (event.key === "ArrowRight") { next = (i + 1) % tabs.length; }
        if (event.key === "ArrowLeft") { next = (i - 1 + tabs.length) % tabs.length; }
        if (event.key === "Home") { next = 0; }
        if (event.key === "End") { next = tabs.length - 1; }
        if (next !== null) { event.preventDefault(); show(next, true); }
      });
    });
    show(0, false);
  });

  // --- before / after
  document.querySelectorAll("[data-compare]").forEach(function (root) {
    var range = root.querySelector("input[type=range]");
    var after = root.querySelector(".compare__after");
    var tag = root.querySelector(".compare__tag--after");
    function place() { root.style.setProperty("--pos", range.value + "%"); }
    range.addEventListener("input", place);
    place();
    var scope = root.closest("[data-compare-scope]") || document;
    var buttons = scope.querySelectorAll("[data-look]");
    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        buttons.forEach(function (other) { other.setAttribute("aria-pressed", other === button ? "true" : "false"); });
        after.src = button.getAttribute("data-look");
        after.alt = "The same photo with the " + button.textContent.trim() + " preset";
        if (tag) { tag.textContent = button.textContent.trim(); }
      });
    });
  });

  // --- copy the checksum
  document.querySelectorAll("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      var source = document.getElementById(button.getAttribute("data-copy"));
      if (!source || !navigator.clipboard) { return; }
      navigator.clipboard.writeText(source.textContent.trim()).then(function () {
        var label = button.querySelector("span");
        var before = label.textContent;
        label.textContent = "Copied";
        setTimeout(function () { label.textContent = before; }, 1600);
      });
    });
  });

  // --- sections ease in as they are reached
  var items = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    items.forEach(function (item) { item.classList.add("is-in"); });
  } else {
    var watcher = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-in");
          watcher.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach(function (item) { watcher.observe(item); });
  }
})();
