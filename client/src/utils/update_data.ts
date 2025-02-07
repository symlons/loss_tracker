import { set_option } from "./options";

interface State {
  data: Record<string, { name: number; value: number[]; runId: string }[]>; // Adjusted to match the data structure
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

    // Log the data for each series
    console.log(`Data for series "${name}":`, new_data);

    // Filter out incomplete data points
    const filteredData = new_data.filter(item => item.value.length === 2); // Ensure each item has both x and y values

    // Log filtered data
    console.log(`Filtered data for series "${name}":`, filteredData);

    // Calculate max for the x-axis
    const max = filteredData.length > 0 ? Math.max(...filteredData.map(item => item.value[0])) : 0; // Example of calculating max

    // Call set_option with the filtered data and the corresponding color
    const option = set_option(max, name, filteredData); // Pass the filtered data

    // Log the option before returning
    console.log(`Option for series "${name}":`, option);

    // Return the option only if it's not null
    return option !== null ? option : null;
  }).filter(option => option !== null); // Filter out any null options

  // Log the final series options
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
