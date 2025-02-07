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
    interval: "auto", // should be adjusted according to the data type
  },
  series: [
    {
      showSymbol: false,
      type: "line",
      animation: true,
    },
  ],
};

export function set_option(new_max: number | undefined, new_name: string, new_data: { name: number; value: number[] }[]) {
  if (!new_data || new_data.length === 0) {
    console.error(`No data available for series: ${new_name}`);
    return null;
  }

  return {
    name: new_name,
    type: "line",
    showSymbol: false,
    data: new_data.map(item => item.value),
  };
}

export const default_loading = {
  text: "loading",
  color: "#000",
  spinnerRadius: 20,
  maskColor: "rgba(255, 255, 255, 0.4)",
};
