import opts from "http-server/lib/core/opts";

export const option = {
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



export function set_option(new_max, new_name, new_data) {
	let options ={
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
      }
   return options;
}

