const { io } = require("socket.io-client");

let socket_7 = io("http://tracker.com/tracker")
console.log(socket_7)
socket_7.on("connect", () => {
	console.log("7:")
	console.log(socket_7.connected); // true
	socket_7.disconnect()
})

let socket_8 = io("http://167.235.139.154/socket")
console.log(socket_8)
socket_8.on("connect", () => {
	console.log("8:")
	console.log(socket_8.connected); // true
	socket_8.disconnect()
})
