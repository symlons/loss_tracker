import ReactECharts from 'echarts-for-react';
import React from 'react';
import { io } from "socket.io-client";
const socket = io('http://localhost:3005');

class App extends React.Component {

  componentDidMount() {

    const myChart = this.echartRef.getEchartsInstance();
    let data = [];
    let dataX = [];
    let delay = 1000;

    socket.on('yCoordinates', (socket) => {
      console.log(socket.yCoordinates)
      dataX.push(socket.xCoordinates);
      data.push({ name: socket.xCoordinates, value: [socket.xCoordinates, socket.yCoordinates] });
      console.log(data)
    })
    setInterval(function () {

      myChart.setOption({
        xAxis: {
          type: 'value',
          max: dataX[dataX.length - 1] + 1,
        },
        series: [{
          data: data,
          animationThreshold: 5000
        }]
      });

    }, delay);
  }

  getOption() {

    let option = {
      dataZoom: [
        {
          type: 'slider',
          filterMode: 'none'
        },],
      xAxis: {
        type: 'value',
      },
      yAxis: {
        type: 'value',
      },
      series: [{
        showSymbol: false,
        hoverAnimation: false,
        type: 'line',
        animation: true,

      }]
    };

    return option;
  }

  render() {

    return (
      <div
        style={{
          width: "60%",
          height: "100%",
        }}>
        <ReactECharts ref={(e) => { this.echartRef = e; }} option={this.getOption()} opts={{ renderer: 'svg' }} />
      </div>
    )
  }
}

export default App;
