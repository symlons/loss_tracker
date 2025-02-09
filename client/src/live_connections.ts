import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";

export function useSocket() {
  const [data, setData] = useState({});
  const nameSet = useRef(new Set());
  const socketRef = useRef(null);

  useEffect(() => {
    const socketHost = import.meta.env.VITE_SOCKET_HOST;
    socketRef.current = io(socketHost, {
      transports: ["websocket"],
      path: "/api/socket/",
    });

    socketRef.current.on("logging", (socketData) => {
      const { name, totalPoints, runId, xCoordinates, yCoordinates } = socketData;
      console.log(name)
      console.log(totalPoints)
      console.log(runId)

      if (!nameSet.current.has(name)) {
        nameSet.current.add(name);
        setData((prevData) => ({
          ...prevData,
          [name]: [],
        }));
      }

      const coordinates = Array.isArray(xCoordinates) ? xCoordinates : [xCoordinates];
      const yCoords = Array.isArray(yCoordinates) ? yCoordinates : [yCoordinates];

	if (xCoordinates.length == totalPoints) {
		console.log("9999999999999999999999999999999")
	      updatedData[name] = [];
	      setData((state) => updatedData[name] = [])
	 }

      // Update the data for the given name
      setData((prevData) => {
        const updatedData = { ...prevData };
        for (let i = 0; i < coordinates.length; i++) {
          if (!updatedData[name]) {
            updatedData[name] = [];
          }
          updatedData[name].push({
            name: Date.now(),
            value: [coordinates[i], yCoords[i]],
          });
        }
        return updatedData;
      });
    });

    return () => {
      socketRef.current.disconnect();
    };
  }, []);

  return { data, name_s: Array.from(nameSet.current) };
}
