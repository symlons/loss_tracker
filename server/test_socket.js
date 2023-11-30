const { io } = require("socket.io-client");

let socket_1 = io("http://167.235.139.154/socket/")
socket_1.on("connect", () => {
	console.log('1:')
	console.log(socket_1.connected); // true
	socket_1.disconnect()
});

let socket_2 = io("http://167.235.139.154:3005/socket")
socket_2.on("connect", () => {
	console.log('2:')
	console.log(socket_2.connected); // true
	socket_2.disconnect()
});

let socket_3 = io("http://167.235.139.154/socket:3005")
socket_3.on("connect", () => {
	console.log('3:')
	console.log(socket_3.connected); // true
	socket_3.disconnect()
});

let socket_4 = io("http://10.98.96.178:3005", {
})

socket_4.on("connect", () => {
	console.log("4:")
	console.log(socket_4.connected); // true
	socket_4.disconnect()
})

let socket_5 = io("http://10.10.204.14:3005")
socket_5.on("connect", () => {
	console.log("5:")
	console.log(socket_5.connected); // true
	socket_5.disconnect()
})

let socket_6 = io("http://tracker.com/socket/", {
  path: "/socket"
})
console.log(socket_6)
socket_6.on("connect", () => {
	console.log("6:")
	console.log(socket_6.connected); // true
	socket_6.disconnect()
})

let socket_7 = io("http://tracker.com/")
console.log(socket_7)
socket_7.on("connect", () => {
	console.log("7:")
	console.log(socket_7.connected); // true
	socket_7.disconnect()
})

let socket_8 = io("http://tracker.com/", {path:"/socket/"})
console.log(socket_8)
socket_8.on("connect", () => {
	console.log("8:")
	console.log(socket_8.connected); // true
	socket_8.disconnect()
})
