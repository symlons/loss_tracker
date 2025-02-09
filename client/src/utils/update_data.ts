import { set_option } from "./options";

interface State {
  data: Record<string, { name: number; value: number[]; runId: string }[]>;
}

interface Query {
  status: boolean;
  value: string;
}

export function update_data(state: State, query: Query) {
  console.log("Query:", query);
  console.log("State:", state);

  const seriesOptions = Object.keys(state.data).map((name) => {
    const new_data = state.data[name];

    console.log(`Data for series "${name}":`, new_data);
    const filteredData = new_data.filter(item => item.value.length === 2); // Ensure each item has both x and y values
    console.log(`Filtered data for series "${name}":`, filteredData);
    console.log('+++++++++++++++++++++++++++++++++')
    console.log(filteredData.length)

    const max = filteredData.length > 0 ? Math.max(...filteredData.map(item => item.value[0])) : 0;
    const option = set_option(max, name, filteredData); // Pass the filtered data
    console.log(`Option for series "${name}":`, option);

    return option !== null ? option : null;
  }).filter(option => option !== null);

  console.log("Final seriesOptions:", seriesOptions);

  return {
    title: {
      text: 'Live Data Chart',
    },
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "shadow"
      }
    },
    xAxis: {
      type: "value",
    },
    yAxis: {
      type: "value",
    },
    series: seriesOptions,
  };
}
