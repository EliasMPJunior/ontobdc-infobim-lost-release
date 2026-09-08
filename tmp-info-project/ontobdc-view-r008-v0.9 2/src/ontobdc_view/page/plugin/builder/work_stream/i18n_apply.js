(function (window) {
  "use strict";

  var runtime = window.OntoBDCWorkStreamViewRuntime =
    window.OntoBDCWorkStreamViewRuntime || { state: {} };
  var catalogElement = document.getElementById("ontobdc-i18n");
  var catalog = JSON.parse(catalogElement?.textContent || "{}");

  function translate(key, variables) {
    var locale =
      document.documentElement.lang ||
      document.documentElement.dataset.language ||
      "en";
    var translations = catalog[locale] || catalog.en || {};
    var text = translations[key] ?? key;
    for (var entry of Object.entries(variables || {})) {
      text = text.replaceAll("{" + entry[0] + "}", entry[1]);
    }
    return text;
  }

  function applyI18n() {
    for (var node of document.querySelectorAll("[data-i18n]")) {
      var key = node.getAttribute("data-i18n");
      if (key) node.textContent = translate(key);
    }
    for (var titleNode of document.querySelectorAll("[data-i18n-title]")) {
      var titleKey = titleNode.getAttribute("data-i18n-title");
      if (titleKey) titleNode.setAttribute("title", translate(titleKey));
    }
    for (var labelNode of document.querySelectorAll("[data-i18n-aria-label]")) {
      var labelKey = labelNode.getAttribute("data-i18n-aria-label");
      if (labelKey) labelNode.setAttribute("aria-label", translate(labelKey));
    }
  }

  runtime.t = translate;
  runtime.applyI18n = applyI18n;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyI18n);
  } else {
    applyI18n();
  }
})(window);
