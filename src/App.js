import ReactECharts from "echarts-for-react";
import React from "react";
import { io } from "socket.io-client";

const socket = io("http://localhost:3005");

class App extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      data: {},
      name: "",
    };
  }
  componentDidMount() {
    const myChart = this.echartRef.getEchartsInstance();
    let data = {};
    //let dataX = [];
    let delay = 1000;
    let name;
    let name_s = [];

    socket.on("logging", (socket) => {
      name = socket.name;
      console.log(name);
      if (name_s.length == 0) {
        name_s.push(name);
        data[name] = [];
      }
      if (name_s[name_s.length - 1] != socket.name) {
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
      this.setState({ data, name: name });
      console.log(this.state.data);
    });

    setInterval(function () {
      if (data[name] != undefined) {
        myChart.setOption({
          xAxis: {
            type: "value",
            max: data[name_s[0]][data[name_s[0]].length - 1].value[0],
          },
          series: [
            {
              name: name,
              id: name,
              type: "line",
              showSymbol: false,
              /*itemStyle: {
              color: name
            },*/
              data: data[name],

              animationThreshold: 10000,
            },
          ],
        });
      }
    }, delay);
  }

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
      xAxis: {
        type: "value",
      },
      yAxis: {
        type: "value",
        interval: 0.5, // should be adjusted according to the data type
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
    //data.s[95].value[0] = "<script>hallo</script>hallo";
    //for testing against xss
    let response = await fetch("/store", {
      method: "POST", // or 'PUT',
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ data, name }),
    });
    let body = await response.text();
    console.log(body);
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
          opts={{ renderer: "svg" }}
        />
        <button onClick={this.store}>Store results</button>
      </div>
    );
  }
}

export default App;
