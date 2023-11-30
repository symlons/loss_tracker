var MongoClient = require("mongodb").MongoClient;
var url = "mongodb://localhost:27017";

const createDOMPurify = require("dompurify");
const { JSDOM } = require("jsdom");
const window = new JSDOM("").window;
const DOMPurify = createDOMPurify(window);

const mongoose = require("mongoose");
const express = require("express");
const app = express();

app.use(express.json({ limit: "50mb" }));
app.use(function (req, res, next) {
  next();
});

app.use(express.json());
var http = require("http").createServer(app);

mongoose
  .connect("mongodb://localhost:27017", {
    //useCreateIndex: true,
    useNewUrlParser: true,
    useUnifiedTopology: true,
  })
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

app.post("/api/python", (req, res) => {
  io.emit("test", req.body);
  res.end();
});

app.post("/api/loss_charting", (req, res) => {
  console.log(req.body);
  io.emit("logging", req.body);
  res.end();
});

app.get("/", (req, res) => {
  res.send("test");
  console.log("test");
});

app.post("/api/query", async (req, res) => {
  res.status(200)
  let result = await query_name_model.findOne({ name: req.body.query_name });
  console.log("query searching for:", req.body.query_name);
  res.send(result);
});

app.post("/api/store", (req, res) => {
  req.body.name_s.map((item, index) => {
    req.body.data[item].map((item, index) => {
      item.name = parseFloat(item.name);
      item.value[0] = parseFloat(item.value[0]);
      item.value[1] = parseFloat(item.value[1]);
    });
  });

  try {
    MongoClient.connect(url, async function (err, db) {
      if (err) throw err;
      var dbo = db.db("test");
      req.body.name_s.map((item, index) => {
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
            .updateOne(filter, update, { upsert: true }, function (err, res) {
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

const io = require("socket.io")(http, {
  cors: {
    // origin: ["http://localhost:3000"], // if it doesn't matter at all type:" " "*" "
    origin: "*",
    methods: ["GET", "POST"],
    credentials: true

  },
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
