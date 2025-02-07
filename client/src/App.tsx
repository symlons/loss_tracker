import React, { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { useSocket } from "./live_connections";
import { option } from "./utils/options";
import { Store } from "./store_data";
import { Query } from "./query";
import { update_data } from "./utils/update_data";

function App() {
  const { data, name_s } = useSocket();
  const [query, setQuery] = useState({ status: false, value: null });
  const chartRef = useRef<echarts.ECharts | null>(null);
  const isMounted = useRef(false);

  useEffect(() => {
    if (!isMounted.current) {
      console.log('Initial Mount');
      const chartDom = document.getElementById("main_1");
      if (chartDom && !chartRef.current) {
        chartRef.current = echarts.init(chartDom, null, { renderer: "svg" });
        if (option) {
          chartRef.current.setOption(option);
        }
        isMounted.current = true;
      }
    }
  }, []);

  useEffect(() => {
    console.log("Data changed:", data);
    if (chartRef.current) {
      console.log("Updating chart with new data");
      const updatedOption = update_data({ data }, query);
      console.log("Updated ECharts options:", updatedOption);
      if (updatedOption) {
        chartRef.current.setOption(updatedOption);
        chartRef.current.hideLoading();
      }
    }
  }, [data, query]);

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
          query={query}
          setQuery={setQuery}
        />
      </div>
    </div>
  );
}

export default App;
