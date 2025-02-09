import { set_option } from "./options";
import { State } from "../types";

export function update_data(state: State) {
  const seriesOptions = Object.keys(state.data)
    .map(name => {
      const filteredData = state.data[name].filter(item => item.value.length === 2);
      const max = filteredData.length > 0 ? Math.max(...filteredData.map(item => item.value[0])) : 0;
      const seriesOpt = set_option(max, name, filteredData);
      return seriesOpt !== null ? seriesOpt : undefined;
    })
    .filter((option): option is NonNullable<typeof option> => option !== undefined);

  return {
    title: { text: "Live Data Chart" },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    xAxis: { type: "value" },
    yAxis: { type: "value" },
    series: seriesOptions,
  };
}

