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

  const values_top = top_json.map((e) =>
    parseFloat(e["value"])
  );
  const times_top = top_json.map((e) => new Date(e["timestamp"]));
  const values_mid = mid_json.map((e) =>
    parseFloat(e["value"])
  );
  const times_mid = mid_json.map((e) => new Date(e["timestamp"]));
  const values_bot = bot_json.map((e) =>
    parseFloat(e["value"])
  );
  const times_bot = bot_json.map((e) => new Date(e["timestamp"]));

  const values_sensor = sensor_json.map((e) =>
    parseFloat(e["value"])
  );
  const times_sensor = sensor_json.map((e) => new Date(e["timestamp"]));


  const mid_scatter = dictionary_scatter(times_mid, values_mid);
  const top_scatter = dictionary_scatter(times_top, values_top);
  const bot_scatter = dictionary_scatter(times_bot, values_bot);

  const sensor_scatter = dictionary_scatter(times_sensor, values_sensor);

  const data = {
    label: "Prediction",
    datasets: [
      {
        label: "Upper bound",
        data: top_scatter,
        borderColor: "#ee978c",
        fill: false,
        borderDash: [1],
        pointRadius: 1,
        showLine: true,
      },
      {
        label: "Mean",
        data: mid_scatter,
        borderColor: "#ff0000",
        fill: "-1",
        borderDash: [2],
        pointRadius: 1.5,
        showLine: true,
      },
      {
        label: "Lower bound",
        data: bot_scatter,
        borderColor: "#ee978c",
        fill: "-1",
        borderDash: [1],
        pointRadius: 1,
        showLine: true,
      },
      {
        label: "Sensor reading",
        data: sensor_scatter,
        borderColor: "#a0a0a0",
        fill: false,
        pointRadius: 1.5,
        showLine: true,
      },
    ],
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