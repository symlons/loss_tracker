import { useEffect, useRef, useState } from "react";
import * as echarts from "echarts";
import { useSocket } from "./live_connections";
import { option } from "./utils/options";
import { Store } from "./store_data";
import { Query } from "./query";
import { update_data } from "./utils/update_data";
import { State as AppState } from "./types";

function App() {
  const { data: socketData, name_s } = useSocket();

  const [state, setState] = useState<AppState>({
    query_name: "",
    data: {},
    name_s: [],
  });

  useEffect(() => {
    setState((prev) => ({
      ...prev,
      data: socketData,
      name_s: name_s,
    }));
  }, [socketData, name_s]);

  const [query, setQuery] = useState<{ status: boolean; value: string | null }>(
    {
      status: false,
      value: null,
    },
  );

  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    const chartDom = document.getElementById("main_1");
    if (chartDom && !chartRef.current) {
      chartRef.current = echarts.init(chartDom, null, { renderer: "svg" });
      chartRef.current.setOption(option);
    }
    return () => {
      if (chartRef.current) {
        chartRef.current.dispose();
        chartRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (chartRef.current) {
      const updatedOption = update_data(state);
      console.log("Updated Option:", updatedOption);
      chartRef.current.setOption(updatedOption, {
        notMerge: false,
        lazyUpdate: true,
      });
      chartRef.current.hideLoading();
    }
  }, [state]);

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
        <Store state={{ data: state.data, name_s: state.name_s }} />
        <Query state={state} setState={setState} setQuery={setQuery} />
      </div>
    </div>
  );
}

export default App;
