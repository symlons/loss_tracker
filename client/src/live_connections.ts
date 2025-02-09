import { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";
import { SocketData, Point } from "./types";

export function useSocket() {
  // Data is stored as an object with keys (names) and arrays of Points
  const [data, setData] = useState<{ [key: string]: Point[] }>({});
  const nameSet = useRef<Set<string>>(new Set());
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    const socketHost = import.meta.env.VITE_SOCKET_HOST;
    socketRef.current = io(socketHost, { transports: ["websocket"], path: "/api/socket/" });

    socketRef.current.on("logging", (socketData: SocketData) => {
      const { name, totalPoints, xCoordinates, yCoordinates } = socketData;

      // If this is a new series, initialize its array.
      if (!nameSet.current.has(name)) {
        nameSet.current.add(name);
        setData(prev => ({ ...prev, [name]: [] }));
      }

      // If we've received all points for this series, reset the array.
      if (xCoordinates.length === totalPoints) {
        setData(prev => ({ ...prev, [name]: [] }));
      }

      // Update the series with new data points.
      setData(prev => ({
        ...prev,
        [name]: [
          ...(prev[name] || []),
          ...xCoordinates.map((x, i) => ({
            name: Date.now(),
            value: [x, yCoordinates[i]] as [number, number],
            runId: name  // (Using the series name here as runId; adjust if needed.)
          }))
        ]
      }));
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  return { data, name_s: Array.from(nameSet.current) };
}
