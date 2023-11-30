const { io } = require("socket.io-client");



let socket_1 = io("http://167.235.139.154/socket")
socket_1.on("connect", () => {
	console.log('2:')
	console.log(socket_1.connected); // true
	socket.disconnect()
});

let socket_2 = io("http://167.235.139.154:3005/socket")
socket_2.on("connect", () => {
	console.log('3:')
	console.log(socket_2.connected); // true
	socket.disconnect()
});

let socket_3 = io("http://167.235.139.154/socket:3005")
socket_3.on("connect", () => {
	console.log('3:')
	console.log(socket_3.connected); // true
	socket.disconnect()
});

let socket = io("http://10.98.96.178:3005")
socket.on("connect", () => {
	console.log("1:")
	console.log(socket.connected); // true
	socket.disconnect()
})

let socket_4 = io("http://10.10.204.3:3005")
socket_4.on("connect", () => {
	console.log("4:")
	console.log(socket_4.connected); // true
	socket.disconnect()
})

let socket_5 = io("http://tracker.com/socket")
socket_5.on("connect", () => {
	console.log("5:")
	console.log(socket_5.connected); // true
	socket.disconnect()
})
