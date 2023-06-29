import _data from "./data.json" assert {type: "json"};

function makeTooltip(context) {
  const tooltip = [`${context.formattedValue}`, `(version: ${context.raw.version})`]
  if (context.raw.tags)
    tooltip.push(`(tags: ${context.raw.tags})`)

  return tooltip
}


function init() {
  const params = new URLSearchParams(location.search)

  let dataIndex = null
  for (const [key, value] of params) {
    if (key === "index")
      dataIndex = value
  }

  const elem = document.getElementById("title")
  elem.innerHTML = `<h1 class="text-lg font-bold">${dataIndex}</h1>`

  const elements = document.querySelectorAll(".timeline-chart")
  for (let elem of elements) {
    // console.log(elem.dataset.sid, elem.dataset.cid)
    let config = _data[dataIndex]
    if (config) {
      config.options.plugins.tooltip = {
        callbacks: {
          label: makeTooltip,
        },
      }

      config.options.aspectRatio = 2.0
      config.options.plugins.legend.display = true

      const chart = new Chart(elem, config);
      elem.chart = chart;
    }
  }
}

init()
