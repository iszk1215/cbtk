import _data from "./data.json" assert {type: "json"};

function makeTooltip(context) {
  if (context.raw.duration) {
    return [`${context.formattedValue}`, `${context.raw.duration}`,
      `${context.raw.run_at}`];
  } else {
    return context.formattedValue;
  }
}

function init() {
  let elements = document.querySelectorAll(".by-runner-chart")
  for (let elem of elements) {
    let config = _data[elem.dataset.index];
    if (config) {
      config.options.plugins.tooltip = {
        callbacks: {
          label: makeTooltip,
        },
      }
      new Chart(elem, config);
    }
  }
}

function main() {
  init();
}

main()
