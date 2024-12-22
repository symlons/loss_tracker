import { io } from "socket.io-client";
// TODO: define TS types
export function handle_socket_connection(live_connection_callback) {
  let name: string;
  let data: { name: [] } | {} = {};
  let name_s: string[] = [];

  console.log(import.meta.env.VITE_SOCKET_HOST)
  const socket = io(import.meta.env.VITE_SOCKET_HOST, {
    transports: ["websocket"],
    path: "/api/socket/",
  });
  console.log("new socket testing")
  console.log(socket);

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
      console.log(data[name]);
      for (let i = 0; i < socket.xCoordinates.length; i++) {
	console.log(socket.xCoordinates[i])
        data[name].push({
          name: Date.now(),
          value: [socket.xCoordinates[i], socket.yCoordinates[i]],
        });
      }
    }
    live_connection_callback({ data, name: name, name_s });
  });
}
