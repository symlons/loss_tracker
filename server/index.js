import { MongoClient } from 'mongodb'
import { Server } from "socket.io";
import http_client from "http";
import DOMPurify from 'dompurify';

var url = "mongodb://localhost:27017";
import { JSDOM } from "jsdom";
const window = new JSDOM("").window;

import mongoose from 'mongoose';
import express from 'express';
const app = express();

app.use(express.json({ limit: "50mb" }));
app.use(function (req, res, next) {
  next();
});

app.use(express.json());
var http = http_client.createServer(app);

mongoose
  .connect("mongodb://localhost:27017")
  .then(() => console.log("connected"))
  .catch((e) => console.log("error", e));

const query_name_model = mongoose.model(
  "query_name_model",
  new mongoose.Schema({
    name: {
      type: String,
      required: true,
    },
  }),
  "training_eval"
);

app.post("/python", (req, res) => {
  io.emit("test", req.body);
  res.end();
});

app.post("/loss_charting", (req, res) => {
  console.log(req.body);
  io.emit("logging", req.body);
  res.end();
});

app.get("/", (_, res) => {
  res.send("testin the root path /");
  console.log("test");
});

app.get("/test", (_, res) => {
  res.send("/test");
  console.log("/test");
});

app.post("/query", async (req, res) => {
  res.status(200);
  let result = await query_name_model.findOne({ name: req.body.query_name });
  console.log("query searching for:", req.body.query_name);
  res.send(result);
});

app.post("/store", (req, res) => {
  console.log("log");
  console.log(req);
  console.log(req.body);
  req.body.name_s.map((item, _) => {
    console.log(item);
    req.body.data[item].map((item, _) => {
      item.name = parseFloat(item.name);
      item.value[0] = parseFloat(item.value[0]);
      item.value[1] = parseFloat(item.value[1]);
    });
  });

  try {
    MongoClient.connect(url, async function (err, db) {
      if (err) throw err;
      var dbo = db.db("test");
      req.body.name_s.map((item, _) => {
        console.log(item);
        let filter = { [item]: { $exists: 1 } };
        let update = {
          $set: {
            [item]: req.body.data[item],
            name: item,
          },
        };
        try {
          dbo
            .collection("training_eval")
            .updateOne(filter, update, { upsert: true }, function (err, _) {
              if (err) throw err;
              console.log("1 document inserted");
              db.close();
            });
        } catch {
          console.log(err);
          console.log("database related error");
        }
        console.log("tried fetching");
      });
    });
  } catch {
    console.log("database related error");
  }
  res.end();
});

const io = new Server(http, {
  cors: {
    // origin: ["http://localhost:3000"], // if it doesn't matter at all type:" " "*" "
    origin: "*",
    methods: ["GET", "POST"],
    credentials: true,
  },
  path: "/socket/",
  transports: ["websocket", "polling"],
  allowEIO3: true,
});

io.on("connection", (socket) => {
  console.log("New socket.io connection");
  socket.send("hello from node server");
});

io.on("error", (error) => {
  console.log(error);
});

const socket_PORT = 3005;
const port = 5005;

http.listen(socket_PORT, () => {
  console.log("listening on *:" + socket_PORT);
});

app.listen(port, () => console.log(`Listening on port ${port}`));
