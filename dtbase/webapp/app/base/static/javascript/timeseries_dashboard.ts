import { Sensor } from "./interfaces";
import {
  Chart,
  Colors,
  LinearScale,
  TimeScale,
  LineController,
  PointElement,
  LineElement,
  Legend,
  Title,
  SubTitle,
  Tooltip,
  Filler,
} from "chart.js";
import "chartjs-adapter-moment";

// See https://www.chartjs.org/docs/latest/getting-started/usage.html for how importing
// and registering Chart.js components works.
Chart.register(
  Colors,
  LinearScale,
  TimeScale,
  LineController,
  PointElement,
  LineElement,
  Legend,
  Title,
  SubTitle,
  Tooltip,
  Filler
);

function getCheckedSensorIds(): string[] {
  const sensorCheckboxesDiv = document.getElementById(
    "sensorCheckboxesDiv"
  ) as HTMLDivElement;
  const sensorIds: string[] = [];
  for (const childElement of sensorCheckboxesDiv.children) {
    const checkbox = childElement.children[0] as HTMLInputElement;
    const id = checkbox.value;
    const checked = checkbox.checked;
    if (checked) sensorIds.push(id);
  }
  return sensorIds;
}

function getSelectedSensorTypeStr(): string {
  const sensorTypeSelector = document.getElementById(
    "sensorTypeSelector"
  ) as HTMLSelectElement;
  const sensorType = sensorTypeSelector.value;
  const sensorTypeStr = encodeURIComponent(sensorType);
  return sensorTypeStr;
}

export function changeSensorType(): void {
  const sensorTypeStr = encodeURIComponent(getSelectedSensorTypeStr());
  const url = "/sensors/time-series-plots";
  const params = "sensorType=" + sensorTypeStr;
  location.replace(url + "?" + params);
}

export function requestTimeSeries(url: string, download: boolean): void {
  const sensorIds = getCheckedSensorIds();
  const startDatePicker = document.getElementById(
    "startDatePicker"
  ) as HTMLInputElement;
  const endDatePicker = document.getElementById(
    "endDatePicker"
  ) as HTMLInputElement;
  const startDate = startDatePicker.value;
  const endDate = endDatePicker.value;
  if (sensorIds === undefined || sensorIds.length === 0) {
    alert("Please select sensors to plot/download data for.");
    return;
  }
  if (startDate === undefined || endDate === undefined) {
    alert("Please set start and end date.");
    return;
  }

  const startStr = encodeURIComponent(startDate);
  const endStr = encodeURIComponent(endDate);
  const idsStr = encodeURIComponent(sensorIds.toString());
  const sensorTypeStr = getSelectedSensorTypeStr();

  const params =
    "startDate=" +
    startStr +
    "&endDate=" +
    endStr +
    "&sensorIds=" +
    idsStr +
    "&sensorType=" +
    sensorTypeStr;
  console.log("requesting timeseries with params ", params);
  if (download) {
    // A clunky way to trigger a download: Make a form that generates a POST request.
    const form = document.createElement("form");
    form.method = "POST";
    form.action = url + "?" + params;
    document.body.appendChild(form);
    form.submit();
  } else {
    location.replace(url + "?" + params);
  }
}

const plotConfigTemplate = {
  type: "line",
  options: {
    responsive: true,
    plugins: {
      legend: {
        position: "top",
      },
    },
    scales: {
      y: {
        display: true,
        title: {
          display: true,
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
          maxTicksLimit: 6,
          includeBounds: false,
        },
      },
    },
  },
};

// blue to red
const colouramp_redblue = [
  "rgba(63,103,126,1)",
  "rgba(27,196,121,1)",
  "rgba(137,214,11,1)",
  "rgba(207,19,10,1)",
];

interface DataPoint {
  [key: string]: number | string;
}

export function makePlot(
  data: { [key: string]: DataPoint[] },
  allSensors: Sensor[],
  yDataName: string,
  yLabel: string,
  canvasName: string
): void {
  const datasets = [];
  const sensorIds = Object.keys(data);
  const numSensors = sensorIds.length;
  for (let i = 0; i < numSensors; i++) {
    const sensorId = sensorIds[i];
    let label = sensorId;
    if (allSensors[sensorId] && allSensors[sensorId].aranet_code) {
      label = allSensors[sensorId].aranet_code;
    }
    let colour = colouramp_redblue[Math.min(i, numSensors - 1)];
    let pointRadius = 1;
    let borderWidth = 1;
    // Make the line for mean look a bit different
    if (sensorId === "mean") {
      pointRadius = 0;
      borderWidth *= 4;
      colour = "#111111";
    }
    datasets.push({
      label: label,
      data: data[sensorId].map((row) => {
        return { x: row["timestamp"], y: row[yDataName] };
      }),
      pointRadius: pointRadius,
      borderWidth: borderWidth,
      borderColor: colour,
      fill: true,
    });
  }
  const config = JSON.parse(JSON.stringify(plotConfigTemplate)); // Make a copy
  config.options.scales.y.title.text = yLabel;
  config.data = { datasets: datasets };
  const ctx = document.getElementById(canvasName) as HTMLCanvasElement;
  new Chart(ctx, config);
}

declare global {
  interface Window {
    makePlot: (
      data: { [key: string]: DataPoint[] },
      allSensors: Sensor[],
      yDataName: string,
      yLabel: string,
      canvasName: string
    ) => void;
    requestTimeSeries: (url: string, download: boolean) => void;
    changeSensorType: () => void;
  }
}

window.makePlot = makePlot;
window.requestTimeSeries = requestTimeSeries;
window.changeSensorType = changeSensorType;
