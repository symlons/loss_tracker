import ReactECharts from "echarts-for-react";
import React from "react";
import { io } from "socket.io-client";

const socket = io("http://localhost:3005");

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      data: {}, //comment out?
      name: "",
      name_s: [],
      query_name: "",
      query: false,
    };
  }

  trigger_events(myChart) {}

  componentDidMount() {
    const myChart = this.echartRef.getEchartsInstance();

    let data = {}; //comment out?
    let name;
    let name_s = [];

    socket.on("logging", (socket) => {
      name = socket.name;
      if (name_s.length == 0) {
        name_s.push(name);
        data[name] = [];
      }
      if (name_s.includes(socket.name) == false) {
        name_s.push(name);
        data[name] = [];
      }
      if (socket.xCoordinates.length == undefined) {
        data[name].push({
          name: Date.now(),
          value: [socket.xCoordinates, socket.yCoordinates],
        });
      } else {
        for (let i = 0; i < socket.xCoordinates.length; i++) {
          data[name].push({
            name: Date.now(),
            value: [socket.xCoordinates[i], socket.yCoordinates[i]],
          });
        }
      }
      this.setState({ data, name: name, name_s });
    });
  }

  componentDidUpdate = async () => {
    const myChart = this.echartRef.getEchartsInstance();
    let new_max, new_data, new_name;
    //console.log(this.state.name);
    //console.log(this.state.query_name == "");
    if (this.state.name == undefined || this.state.query_name !== "") {
      // TODO: check if query_name data is finished
      // otherwise this will run also if you stram new data via the python api
      // and you won't be able to search after another search
      if (this.state.data[this.state.query_name] != undefined) {
        new_max =
          this.state.data[this.state.query_name][
            this.state.data[this.state.query_name].length - 1
          ].value[0];
        new_name = this.state.query_name;
        new_data = this.state.data[this.state.query_name];
      }
    }
    if (this.state.query != true) {
      //let query = this.state.query_name;
      new_name = this.state.name;
      new_data = this.state.data[new_name];
      new_max =
        this.state.data[this.state.name_s[0]][
          this.state.data[this.state.name_s[0]].length - 1
        ].value[0];
    }

    if (new_data !== undefined) {
      myChart.setOption({
        color: ["#0f2", "#000", "#d24", "#24d", "#00ddff", "#ffdd22"],
        grid: {
          bottom: "30%",
        },
        legend: {
          bottom: "15%",
          itemStyle: {
            decal: {
              symbol: "rect",
            },
          },
        },
        xAxis: {
          type: "value",
          max: new_max,
        },
        toolbox: {
          feature: {
            dataZoom: {},
            //restore: {},
            saveAsImage: {},
          },
        },
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "cross",
          },
          position: function (pt) {
            return [pt[0], "10%"];
          },
        },

        series: [
          {
            name: new_name,
            id: new_name,
            type: "line",
            showSymbol: false,
            data: new_data,
            animation: false,
            emphasis: {
              focus: "series",
            },
            triggerLineEvent: true,
            //animationThreshold: 800,
          },
        ],
      });
    }
    console.log("sdfasdfds");
    console.log(this.state);
    myChart.on("click", (params) => {
      //only works, when: "triggerLineEvent: true" is set
      if (params.componentType === "series") {
        if (params.seriesType === "line") {
          console.log("line");
          console.log(params.seriesName);
          console.log(this.state.data);
          console.log(this.state.data[params.seriesName]);
          console.log(
            this.state.data[params.seriesName][
              this.state.data[params.seriesName].length - 1
            ]
          );

          let new_max =
            this.state.data[params.seriesName][
              this.state.data[params.seriesName].length - 1
            ].value[0];

          myChart.setOption({
            xAxis: { max: new_max },
          });
        }
        if (params.seriesType === "edge") {
          console.log("edge");
        }
      }
    });
  };

  handleChange = async (event) => {
    const target = event.target;
    const user = this.state.user;
    let query_name = target.value;
    query_name = query_name.toString();
    await this.setState({
      query_name,
      query: true,
    });
  };

  handleSubmit = async (event) => {
    event.preventDefault();
    let response, body;
    /*response = await fetch("/csrf", {
      method: "GET",
      // creadentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });

    body = await response.json();*/
    let query_name = this.state.query_name;
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
      console.log(this.state);
      this.setState({ data: body });
      //let new_data = this.state.data.push({ data_name });
      console.log("new data");
      //  this.setState((previousState) => ({ data: [...previousState.name_s, 'halo'] }));
    } else {
    }
  };

  getOption() {
    let option = {
      title: {
        left: "center",
        text: "Loss",
      },
      dataZoom: [
        {
          type: "slider",
          filterMode: "none",
        },
      ],
      xAxis: [
        {
          type: "value",
          animation: false,
        },
      ],
      yAxis: {
        type: "value",
        interval: "auto", // should be adjusted according to the data type
      },
      series: [
        {
          showSymbol: false,
          hoverAnimation: false,
          type: "line",
          animation: true,
        },
      ],
    };

    return option;
  }

  store = async () => {
    let data = this.state.data;
    let name = this.state.name;
    let name_s = this.state.name_s;
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
  };

  render() {
    return (
      <div
        style={{
          width: "60%",
          height: "100%",
        }}
      >
        <ReactECharts
          ref={(e) => {
            this.echartRef = e;
          }}
          option={this.getOption()}
          opts={{ renderer: "svg", useCoarsePointer: true, pointerSize: 100 }}
        />
        <div className="inline-block relative left-96">
          <button
            className="bg-white hover:bg-black hover:text-white font-bold py-2 px-2 rounded border-2 border-black mb-4"
            onClick={this.store}
          >
            Store results
          </button>
          <form onSubmit={this.handleSubmit}>
            <input
              name="query_name"
              onChange={this.handleChange}
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
}

export default App;
