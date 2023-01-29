var MongoClient = require("mongodb").MongoClient;
var url = "mongodb://sfkost:mypassword@mongo:27017/?authSource=admin";

const createDOMPurify = require("dompurify");
const { JSDOM } = require("jsdom");
const window = new JSDOM("").window;
const DOMPurify = createDOMPurify(window);
const mongoose = require("mongoose");

const express = require("express");
const bodyParser = require("body-parser");

const app = express();

app.use(express.json({ limit: "50mb" }));
app.use(function (req, res, next) {
  //do stuff
  var datetime = new Date();
    console.log(datetime);

  console.log("just for logging it");
  next();
});

app.use(express.urlencoded({ limit: "50mb" }));

var http = require("http").createServer(app);

mongoose
  .connect("mongodb://localhost:27017", {
    //useCreateIndex: true,
    useNewUrlParser: true,
    useUnifiedTopology: true,
  })
  .then(() => console.log("connected"))
  .catch((e) => console.log("error"));

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

const io = require("socket.io")(http, {
  cors: {
    // origin: ["http://localhost:3000"], // if it doesn't matter at all type:" " "*" "
    methods: ["GET", "POST"],
    credentials: true, //true
  },
});

const socket_PORT = 3005;
//const port = process.env.PORT || 5005;
const port = 5005;
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.post("/api/python", (req, res) => {
  console.log(req.body);
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

app.post("/query", (req, res) => {
  console.log(req.body.query_name);
  let match = query_name_model.findOne(
    { name: req.body.query_name },
    (err, result) => {
      console.log(err);
      if (err) {
        return next(err);
      } else {
        console.log("query find result", result);
        res.send(result);
      }
    }
  );
});
app.post("/store", (req, res) => {
  console.log(req.body);
  req.body.name_s.map((item, index) => {
    req.body.data[item].map((item, index) => {
      item.name = parseFloat(item.name);
      item.value[0] = parseFloat(item.value[0]);
      item.value[1] = parseFloat(item.value[1]);
    });
  });
  console.log(req.body.data);

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
        console.log("did it try?");
      });
    });
  } catch {
    console.log("database related error");
  }
  res.end();
});

io.on("connection", (socket) => {
  console.log("New socket.io connection");
  socket.send("hello from node server");
  // socket.emit('message','Welcome to socket.io');
});

io.on("error", (error) => {
  console.log(error);
});

http.listen(socket_PORT, () => {
  console.log("listening on *:" + socket_PORT);
});
/*io.on(`client:event`, data => {
  console.log("hi")
  console.log(data)
})*/

app.listen(port, () => console.log(`Listening on port ${port}`));
