// types.ts
export interface SocketData {
  name: string;
  totalPoints: number;
  xCoordinates: number[];
  yCoordinates: number[];
}

export interface Point {
  name: number;              // Timestamp
  value: [number, number];   // [x, y] tuple
  runId?: string;            // Optional runId (set as needed)
}

export interface State {
  query_name: string;
  data: { [key: string]: Point[] };
  name_s: string[];
}

