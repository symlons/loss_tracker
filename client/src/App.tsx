import React, { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { useSocket } from "./live_connections"; // Import the custom hook
import { option } from "./utils/options";
import { Store } from "./store_data";
import { Query } from "./query";
import { update_data } from "./utils/update_data";

function App() {
  const { data, name_s } = useSocket(); // Use the custom hook
  const [query, setQuery] = useState({ status: false, value: null });
  const [state, setState] = useState({ query_name: "", data, name_s }); // Initialize state
  const chartRef = useRef<echarts.ECharts | null>(null);
  const isMounted = useRef(false);

  useEffect(() => {
    const chartDom = document.getElementById("main_1");
    if (chartDom && !chartRef.current) {
      chartRef.current = echarts.init(chartDom, null, { renderer: "svg" });
      if (option) {
        chartRef.current.setOption(option);
      }
    }
    return () => {
      // Clean up the chart when the component unmounts
      if (chartRef.current) {
        chartRef.current.dispose();
        chartRef.current = null; // Set chartRef.current to null
      }
    };
  }, []);

  useEffect(() => {
    console.log("Data changed:", data);
    if (chartRef.current) {
      console.log("Updating chart with new data");
      const updatedOption = update_data({ data }, query); // Pass the correct state structure
      console.log("Updated ECharts options:", updatedOption); // Log the updated options

      // Log the chart options before setting them
      console.log("Chart options before setting:", updatedOption);

      if (updatedOption) {
        // Reset the chart before setting new options
        chartRef.current.setOption({
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
          series: [], // Clear existing series
        });
        chartRef.current.setOption(updatedOption);
        chartRef.current.hideLoading();
      }
    }
  }, [data, query]); // Ensure that this effect only runs when data or query changes

  return (
    <div
      style={{
        width: "60%",
        height: "100%",
        borderRadius: "0.5rem",
        border: "2px solid black",
      }}
    >
      <div id="main_1" style={{ width: "800px", height: "400px" }}></div>
      <div className="relative left-96 inline-block">
        <Store state={{ data, name_s }} />
        <Query
          state={state} // Pass the state object
          setState={setState} // Pass the setState function
          setQuery={setQuery}
        />
      </div>
    </div>
  );
}

export default App;
