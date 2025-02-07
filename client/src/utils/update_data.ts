import { set_option } from "./options";

interface State {
  data: Record<string, { name: number; value: number[] }[]>; // Adjusted to match the data structure
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
    console.log(`Processing series for name: ${name}`, new_data); // Log the data for each series

    // Ensure new_data is not empty
    if (!new_data || new_data.length === 0) {
      console.warn(`No data available for series: ${name}`);
      return null; // Skip this series if there's no data
    }

    const max = Math.max(...new_data.map(item => item.value[0])); // Example of calculating max

    return set_option(max, name, new_data);
  }).filter(option => option !== null); // Filter out any null options

  console.log("Series options:", seriesOptions); // Log the series options being returned

  return {
    title: {
      text: 'Live Data Chart',
    },
    tooltip: {},
    xAxis: {
      type: "value",
    },
    yAxis: {
      type: "value",
    },
    series: seriesOptions,
  };
}

