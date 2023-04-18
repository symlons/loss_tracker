import { io } from "socket.io-client";

export function handle_socket_connection(live_connection_callback) {
  let data = {}; //comment out?
  let name: [];
  let name_s = [];

const socket = io("http://localhost:3005");

  socket.on("logging", (socket: any) => {
    name = socket.name;
    if (name_s.length === 0) {
      name_s.push(name);
      data[name] = [];
    }
    if (name_s.includes(socket.name) === false) {
      name_s.push(name);
      data[name] = [];
    }
    if (socket.xCoordinates.length === undefined) {
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
    //this.setState({ data, name: name, name_s });
    live_connection_callback({data, name: name, name_s})
  });
}

