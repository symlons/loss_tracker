import ReactECharts from "echarts-for-react";
import * as echarts from "echarts";
import React from "react";
import { useState, useEffect } from "react";
import { useRef } from "react";
import { createRef } from "react";
import { option, set_option } from "./options";
import { handle_socket_connection } from "./live_connections.ts";
import { io } from "socket.io-client";

const socket = io("http://localhost:3005");

function App() {
  const [state, setState] = useState({
    data: {}, //comment out?
    name: "",
    name_s: [],
    query_name: "",
    query: false,
  });

  function trigger_events(myChart) {}
  function live_connection_callback(socket_data) {
    setState(socket_data);
  }

  // change to useEffect []
  useEffect(() => {
      const chartDom = document.getElementById("main_1");
      const myChart = echarts.init(chartDom, null, { renderer: "svg" });
      let option = getOption();
      option && myChart.setOption(option);
    handle_socket_connection(live_connection_callback);
  }, []);

  useEffect(() => {
    let query_name = state.query_name;
    const chartDom = document.getElementById("main_1");
    const myChart = echarts.getInstanceByDom(chartDom)


      let new_max, new_data, new_name;
      if (state.name === undefined || state.query_name !== "") {
        // TODO: check if query_name data is finished
        // otherwise this will run also if you stram new data via the python api
        // and you won't be able to search after another search
	console.log(state.query_name)
        console.log(state.data[state.query_name])
        if (state.data[state.query_name] !== undefined) {
          new_max =
            state.data[state.query_name][
              state.data[state.query_name].length - 1
            ].value[0];

          new_name = state.query_name;
          new_data = state.data[state.query_name];
          myChart.hideLoading();
        }
      }

      // if the user isn't searching
      if (state.query !== true) {
        //let query = this.state.query_name;
        new_name = state.name;
        new_data = state.data[new_name];
        /*new_max =
        state.data[state.name_s[0]][
          state.data[state.name_s[0]].length - 1
        ].value[0];*/ //now
      }

      if (new_data !== undefined) {
	      console.log('set new option')
        let settings = set_option(new_max, new_name, new_data);
        myChart.setOption(settings);
      }
  });

  async function handleChange(event) {
    const target = event.target;
    const user = state.user;
    let query_name = target.value;
    query_name = query_name.toString();

    await setState({
      ...state,
      query_name,
      query: true,
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    let response, body;
	  /*
    response = await fetch("/csrf", {
      method: "GET",
      // creadentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });
	  */

    //body = await response.json()
    let query_name = state.query_name;
    const chartDom = document.getElementById("main_1");
    const myChart = echarts.getInstanceByDom(chartDom)

    myChart.showLoading({
      text: "loading",
      color: "#000",
      spinnerRadius: 20,
      maskColor: "rgba(255, 255, 255, 0.4)",
    });
    response = await fetch("/api/query", {
      method: "POST", // or 'PUT',
      credentials: "omit", //same site
      headers: {
        "Content-Type": "application/json",
        //    "csrf-token": body.csrfToken,
      },
      body: JSON.stringify({ query_name }),
    });

    if (response.status === 200) {
      body = await response.json();
      let data_name = body[body.name];
      console.log(data_name);
      setState({ ...state, data: body });
      //let new_data = this.state.data.push({ data_name });
      console.log("new data");
      //  this.setState((previousState) => ({ data: [...previousState.name_s, 'halo'] }));
    } else {
    }
  }

  function getOption() {
    return option;
  }

  async function store() {
    let data = state.data;
    let name = state.name;
    let name_s = state.name_s;
    //data.s[95].value[0] = "<script>hallo</script>hallo";
    //for testing against xss
    let response = await fetch("/api/store", {
      method: "POST", // or 'PUT',
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ data, name, name_s }),
    });
    let body = await response.text();
  }


  return (
    <div
      style={{
        width: "60%",
        height: "100%",
      }}
    >
      <div id="main_1" style={{ width: "800px", height: "400px" }}></div>
      <div className="inline-block relative left-96">
        <button
          className="bg-white hover:bg-black hover:text-white font-bold py-2 px-2 rounded border-2 border-black mb-4"
          onClick={store}
        >
          Store results
        </button>
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
      </div>
    </div>
  );
}

export default App;
