import * as React from "react";
import * as echarts from "echarts";
import { default_loading, option, set_option } from "./utils/options";

// TODO: define TS types
export function Query(props) {
  async function handleChange(event) {
    const target = event.target;
    let query_name = target.value;

    query_name = query_name.toString();
    let state = props.state;
    let setState = props.setState;

    let setQuery = props.setQuery;

    await setState({
      ...state,
      query_name,
      query: true,
    });

    await setQuery({ status: false, value: query_name }); // triggers rerender in useffect in app.js
  }

  async function handleSubmit(event) {
    event.preventDefault();

    let state = props.state;
    let query_name = state.query_name;

    const chartDom = document.getElementById("main_1")!;
    const myChart = echarts.getInstanceByDom(chartDom)!;
    myChart.showLoading(default_loading);

    let response = await fetch("/api/query", { // TODO: use React Query
      method: "POST",
      credentials: "omit", //same site
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query_name }),
    });

    if (response.status === 200) {
      let body = await response.json();
      let setState = props.setState;
      setState({ ...state, data: body });
      let setQuery = props.setQuery;
      setQuery({ status: true, value: query_name }); // only display query in echarts after query has been submitted
    } else {
      //TODO:
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="query_name"
        onChange={handleChange}
        className="shadow outline-none appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight"
        id="query_name"
        type="text"
        placeholder="query_name"
      />
    </form>
  );
}
