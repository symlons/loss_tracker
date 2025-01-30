import * as echarts from "echarts";
import React from "react";
import { useState, useEffect } from "react";

import { handle_socket_connection } from "./live_connections.ts";
import { option } from "./utils/options";
import { Store } from "./store_data.tsx";
import { Query } from "./query.tsx";
import { update_data } from "./utils/update_data.ts"; // utils

function App() {
  const [query, setQuery] = useState({ status: false, value: null });
  const [state, setState] = useState({
    data: {},
    name: "",
    name_s: [],
  });

  function live_connection_callback(socket_data) {
    setState(socket_data);
  }

  function getOption() {
    return option;
  }

  useEffect(() => {
    const id = "main_1";
    const chartDom = document.getElementById(id);
    const myChart = echarts.init(chartDom, null, { renderer: "svg" });

    let option = getOption();
    option && myChart.setOption(option);
    handle_socket_connection(live_connection_callback);
  }, []);

  useEffect(() => {
    const id = "main_1";
    const chartDom = document.getElementById(id);
    const myChart = echarts.getInstanceByDom(chartDom);
    const option = update_data(state, query);

    myChart.setOption(option);
    myChart.hideLoading();
  });

  return (
    <div
      style={{
        width: "60%",
        height: "100%",
      }}
      className="rounded-lg border-2 border-black"
    >
      <div id="main_1" style={{ width: "800px", height: "400px" }}></div>
      <div className="relative left-96 inline-block">
        <Store state={state}/>
        <Query
          state={state}
          setState={setState}
          query={query}
          setQuery={setQuery}
        />
      </div>
    </div>
  );
}

export default App;
