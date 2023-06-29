import _data from "./data.json" assert {type: "json"};

function makeTooltip(context) {
  const tooltip = [`${context.formattedValue}`, `(version: ${context.raw.version})`]
  if (context.raw.tags)
    tooltip.push(`(tags: ${context.raw.tags})`)

  return tooltip
}


function initTab(section) {
  const tabs = section.querySelectorAll("#tabs a");

  const cls = ["border-l", "border-r", "border-t", "-mb-px", "font-bold"]

  tabs.forEach((tab) => {
    tab.addEventListener("click", (ev) => {
      ev.preventDefault();
      const target = ev.srcElement.dataset.title;

      tab.parentElement.classList.add(...cls);

      tabs.forEach((tab0) => {
        if (tab0.dataset.title != target) {
          tab0.parentElement.classList.remove(...cls);
        }
      });

      const contents = section.querySelectorAll("[id^='tab-body']")
      contents.forEach((body) => {
        if (body.dataset.title == target) {
          body.classList.remove("hidden");
        } else {
          body.classList.add("hidden");
        }
      });
    });
  });
}

function init() {
  const sections = document.querySelectorAll("[id^='section']");
  sections.forEach(initTab);

  const elements = document.querySelectorAll(".timeline-chart")
  for (let elem of elements) {
    // console.log(elem.dataset.sid, elem.dataset.cid)
    let config = _data[elem.dataset.index]
    if (config) {
      config.options.plugins.tooltip = {
        callbacks: {
          label: makeTooltip,
        },
      }
      config.options.onClick = (e) => {
        console.log(e)
      }
      const chart = new Chart(elem, config);
      elem.chart = chart;
    }
  }
}

init()
