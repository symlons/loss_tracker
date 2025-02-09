export const option = {
  title: {
    left: "center",
    text: "Loss",
  },
  dataZoom: [
    {
      type: "slider",
      filterMode: "none",
    },
  ],
  xAxis: [
    {
      type: "value",
      animation: false,
    },
  ],
  yAxis: {
    type: "value",
    interval: "auto",
  },
  series: [
    {
      showSymbol: false,
      type: "line",
      animation: true,
    },
  ],
};

export function set_option(
  new_max: number | undefined,
  new_name: string,
  new_data: { name: number; value: number[] }[],
): echarts.EChartOption.SeriesLine | null {
  if (!new_data || new_data.length === 0) {
    console.error(`No data available for series: ${new_name}`);
    return null;
  }

  console.log('----------------------------------------------------');
  const values = new_data.map((item) => item.value[0]);
  const nums = values.filter((v) => typeof v === 'number' && !isNaN(v));
  const minVal = nums.length ? Math.min(...nums) : undefined;
  const maxVal = nums.length ? Math.max(...nums) : undefined;

  console.log("Min:", minVal, "Max:", maxVal);
function generateRandomData(length: number, xStart = 1, xStep = 1, yMin = 1, yMax = 10): number[][] {
  let data: number[][] = [];
  let x = xStart;

  for (let i = 0; i < length; i++) {
    let y = Math.floor(Math.random() * (yMax - yMin + 1)) + yMin; // Random y value in range
    data.push([x, y]);
    x += xStep; // Ensure x-axis increases
  }

  return data;
}

const data = new_data.map((item) => item.value.slice(0, 2));
const xCount: Record<number, number> = {};

data.forEach(([x, _]) => {
  xCount[x] = (xCount[x] || 0) + 1;
});

  const seriesOption: echarts.EChartOption.SeriesLine = {
    name: new_name,
    type: "line",
    showSymbol: false,
    data: data.map((item) => ({ value: item })),
    animation: false,
    emphasis: {
      focus: "series",
    },
  };

  return seriesOption;
}
export const default_loading = {
  text: "loading",
  color: "#000",
  spinnerRadius: 20,
  maskColor: "rgba(255, 255, 255, 0.4)",
};
