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
      const { name, xCoordinates, yCoordinates } = socketData;

      if (!nameSet.current.has(name)) {
        nameSet.current.add(name);
        setData((prevData) => ({
          ...prevData,
          [name]: [],
        }));
      }

      const coordinates = Array.isArray(xCoordinates) ? xCoordinates : [xCoordinates];
      const yCoords = Array.isArray(yCoordinates) ? yCoordinates : [yCoordinates];

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

    // Cleanup on unmount
    return () => {
      socketRef.current.disconnect();
    };
  }, []);

  return { data, name_s: Array.from(nameSet.current) };
}

