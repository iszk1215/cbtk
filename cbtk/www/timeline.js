import _data from "./data.json" assert {type: "json"};

function makeTooltip(context) {
  const tooltip = [`${context.formattedValue}`, `(version: ${context.raw.version})`]
  if (context.raw.tags)
    tooltip.push(`(tags: ${context.raw.tags})`)

  return tooltip
}

function initNav() {
  const sections = document.querySelectorAll("[id^='section']");

  const nav = document.getElementById("page_nav")
  const links = nav.querySelectorAll("a")

  links.forEach((link) => {
    link.addEventListener("click", (ev) => {
      ev.preventDefault();

      const target = `section-${link.dataset.index}`;

      sections.forEach((section) => {
        if (section.id === target) {
          section.classList.remove("hidden");
        } else {
          section.classList.add("hidden");
        }
      })
    })
  })
}


function initTab(root) {
  const cls = ["border-l", "border-r", "border-t", "-mb-px", "font-bold"]

  const tabs = root.querySelectorAll(".tabs a");
  const bodies = root.querySelectorAll(".tab-body")

  tabs.forEach((tab) => {
    tab.addEventListener("click", (ev) => {
      ev.preventDefault();

      tab.parentElement.classList.add(...cls);

      tabs.forEach((t, i) => {
        if (t == tab) { // selected
          if (i < bodies.length) {
            bodies[i].classList.remove("hidden");
          }
        } else {
          t.parentElement.classList.remove(...cls);
          if (i < bodies.length) {
            bodies[i].classList.add("hidden");
          }
        }
      });
    });
  });
}

function initTabs() {
  const tabs = document.querySelectorAll(".cbtk-tab");
  tabs.forEach(initTab);
}

function initCharts() {
  const elements = document.querySelectorAll(".timeline-chart")
  for (let elem of elements) {
    let config = _data[elem.dataset.index]
    if (config) {
      config.options.plugins.tooltip = {
        callbacks: {
          label: makeTooltip,
        },
      }
      const chart = new Chart(elem, config);
    }
  }
}

function initSingleMultiChart(elem) {
  const multiDiv = elem.querySelector(".timeline-multi");
  const singleDiv = elem.querySelector(".timeline-single");
  const title = elem.querySelector(".timeline-single-title");
  const canvas = elem.querySelector(".timeline-single-canvas");
  const links = elem.querySelectorAll(".timeline-link-single");

  const multiLink = elem.querySelector(".timeline-single-back");
  multiLink.addEventListener("click", (ev) => {
    multiDiv.classList.remove("hidden");
    singleDiv.classList.add("hidden");
  });

  links.forEach((link) => {
    link.addEventListener("click", (ev) => {
      ev.preventDefault();

      multiDiv.classList.add("hidden");
      singleDiv.classList.remove("hidden");

      title.innerText = link.dataset.bench;

      let config = _data[link.dataset.index];
      if (config) {
        // deep copy to edit
        config = JSON.parse(JSON.stringify(config));
        config.options.aspectRatio = 2.0
        config.options.plugins.legend.display = true

        if ("chart" in singleDiv) {
          singleDiv.chart.destroy();
        }

        const chart = new Chart(canvas, config);
        singleDiv.chart = chart;
      }
    })
  })
}

function initSingleMultiCharts() {
  const elements = document.querySelectorAll(".single-multi-charts");

  elements.forEach((elem) => {
    initSingleMultiChart(elem);
  })
}

function init() {
  initNav();
  initTabs();
  initCharts();
  initSingleMultiCharts()
}

init()
