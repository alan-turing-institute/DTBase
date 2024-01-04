import { dictionary_scatter } from "./utility";

function plot(
  top_json,
  mid_json,
  bot_json,
  sensor_json,
  sensor_measure,
  canvas_name,
  y_label,
  show_legend
) {
  const datasets = [];
  if (top_json !== null) {
    const values_top = top_json.map((e) => parseFloat(e["value"]));
    const times_top = top_json.map((e) => new Date(e["timestamp"]));
    const top_scatter = dictionary_scatter(times_top, values_top);
    datasets.push({
      label: "Upper bound",
      data: top_scatter,
      borderColor: "#ee978c",
      fill: false,
      borderDash: [1],
      pointRadius: 1,
      showLine: true,
    });
  }
  if (mid_json !== null) {
    const values_mid = mid_json.map((e) => parseFloat(e["value"]));
    const times_mid = mid_json.map((e) => new Date(e["timestamp"]));
    const mid_scatter = dictionary_scatter(times_mid, values_mid);
    datasets.push({
      label: "Mean",
      data: mid_scatter,
      borderColor: "#ff0000",
      fill: "-1",
      borderDash: [2],
      pointRadius: 1.5,
      showLine: true,
    });
  }
  if (bot_json !== null) {
    const values_bot = bot_json.map((e) => parseFloat(e["value"]));
    const times_bot = bot_json.map((e) => new Date(e["timestamp"]));
    const bot_scatter = dictionary_scatter(times_bot, values_bot);
    datasets.push({
      label: "Lower bound",
      data: bot_scatter,
      borderColor: "#ee978c",
      fill: "-1",
      borderDash: [1],
      pointRadius: 1,
      showLine: true,
    });
  }

  if (sensor_json !== null) {
    const values_sensor = sensor_json.map((e) => parseFloat(e["value"]));
    const times_sensor = sensor_json.map((e) => new Date(e["timestamp"]));
    const sensor_scatter = dictionary_scatter(times_sensor, values_sensor);
    datasets.push({
      label: "Sensor reading",
      data: sensor_scatter,
      borderColor: "#a0a0a0",
      fill: false,
      pointRadius: 1.5,
      showLine: true,
    });
  }

  const data = {
    label: "Prediction",
    datasets: datasets,
  };

  const config = {
    type: "scatter",
    data: data,
    options: {
      animation: {
        duration: 0,
      },
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: show_legend,
          position: "top",
        },
      },
      scales: {
        y: {
          display: true,
          title: {
            display: true,
            text: y_label,
            font: { size: 18 },
          },
        },
        x: {
          type: "time",
          time: {
            displayFormats: {
              hour: "DD MMM hA",
            },
          },
          ticks: {
            maxTicksLimit: 13,
            includeBounds: false,
          },
        },
      },
    },
  };
  const ctx = document.getElementById(canvas_name);
  return new Chart(ctx, config);
}

function updateScenarioSelector(scenarios, selectedScenarioDescription) {
  const modelName = document.getElementById("model_name").value;
  const scenarioSelector = document.getElementById("model_scenario");

  // Clear existing options
  scenarioSelector.innerHTML = "";

  // Add "Any scenario" option
  const defaultOption = document.createElement("option");
  defaultOption.text = "Any scenario";
  defaultOption.value = "ANY SCENARIO/NULL";
  scenarioSelector.add(defaultOption);

  // Filter scenarios for the selected model
  const filteredScenarios = scenarios.filter(function (scenario) {
    return scenario.model_name === modelName;
  });

  // Add filtered scenarios to the selector
  filteredScenarios.forEach(function (scenario) {
    const option = document.createElement("option");
    option.text = scenario.description;
    option.value = scenario.description;
    if (scenario.description == selectedScenarioDescription)
      option.selected = true;
    scenarioSelector.add(option);
  });
}

window.plot = plot;
window.updateScenarioSelector = updateScenarioSelector;
