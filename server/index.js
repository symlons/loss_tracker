import { MongoClient } from "mongodb";
import { Server } from "socket.io";
import http from "http";
import express from "express";
import rateLimit from "express-rate-limit";
import helmet from "helmet";
import Joi from "joi";
import winston from "winston";
import chalk from "chalk";
import dotenv from "dotenv";
import crypto from "crypto";

if (!process.env.MONGODB_URI) {
  dotenv.config();
}

const HTTP_PORT = process.env.PORT || 5005;
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017";
console.log(MONGODB_URI);

const app = express();
app.set("trust proxy", 1);
const httpServer = http.createServer(app);

const io = new Server(httpServer, {
  cors: { origin: "*" },
  path: "/api/socket",
});

let mongoClient;
async function getMongoClient() {
  if (!mongoClient) {
    mongoClient = new MongoClient(MONGODB_URI);
    await mongoClient.connect();
  }
  return mongoClient;
}

const logger = winston.createLogger({
  level: "info",
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      ),
    }),
    new winston.transports.File({
      filename: "app.log",
      format: winston.format.combine(winston.format.json()),
    }),
  ],
});

app.use(helmet());
app.use(express.json({ limit: "10mb" }));

const batchLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 10000, 
  message: "Too many requests, please try again later.",
  handler: (req, res, next) => {
    logger.warn(`Rate limit exceeded for ${req.ip} on /batch`);
    res
      .status(429)
      .json({ error: "Rate limit exceeded, please try again later." });
  },
});

export { batchLimiter };
const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 1000000,
  message: "Too many requests, please try again later.",
  handler: (req, res, next) => {
    logger.warn(`Rate limit exceeded for ${req.ip} globally`);
    res
      .status(429)
      .json({ error: "Rate limit exceeded, please try again later." });
  },
});

app.use(generalLimiter);

app.use((req, res, next) => {
  const start = Date.now();
  logger.info(`→ ${req.method} ${req.path}`);
  res.on("finish", () => {
    const duration = Date.now() - start;
    const status = res.statusCode;
    logger.log({
      level: status >= 400 ? "warn" : "info",
      message: `${status} ${duration}ms ${req.path}`,
    });
  });
  next();
});

const batchSchema = Joi.object({
  name: Joi.string().required(),
  xCoordinates: Joi.array().items(Joi.number()).required(),
  yCoordinates: Joi.array().items(Joi.number()).required(),
  runId: Joi.string().optional(),
});

const querySchema = Joi.object({
  query_name: Joi.string().required(),
});

let batchCounter = {};

app.get("/", (_, res) => {
  res.status(200).send("OK");
});

app.post("/batch", batchLimiter, async (req, res, next) => {
  try {
    const { error } = batchSchema.validate(req.body);
    if (error) {
      return next(new CustomError(400, error.details[0].message));
    }

    const { name, xCoordinates, yCoordinates, runId: incomingRunId } = req.body;
    const runId = incomingRunId || crypto.randomUUID();

    const validatedXCoordinates = Array.isArray(xCoordinates)
      ? xCoordinates
      : [];
    const validatedYCoordinates = Array.isArray(yCoordinates)
      ? yCoordinates
      : [];

    const point = {
      x: validatedXCoordinates.map((x) => Number(x)),
      y: validatedYCoordinates.map((y) => Number(y)),
      timestamp: new Date(),
      runId: runId,
    };

    console.log("Point to be pushed:", point.x.length);

    const client = await getMongoClient();
    const db = client.db("training");

    await db.collection("points").updateOne(
      { name, runId },
      {
        $push: { points: point },
        $set: { lastUpdate: new Date() },
      },
      { upsert: true }
    );

    const counterKey = `${name}-${runId}`;
    batchCounter[counterKey] = (batchCounter[counterKey] || 0) + 1;
    console.log("Batch Counter:", batchCounter[counterKey]);

    logger.info(
      `${chalk.green("✓")} Batch processed for ${chalk.blue(name)} (Run ID: ${chalk.yellow(
        runId
      )}): ${chalk.yellow(batchCounter[counterKey])} batch(es) received`
    );

    const emitPayload = {
      name,
      xCoordinates: validatedXCoordinates,
      yCoordinates: validatedYCoordinates,
    };

    io.emit("logging", emitPayload);
    res.status(201).json({ success: true, runId: runId });
  } catch (error) {
    logger.error("✗ Error in /batch endpoint", {
      error: error.message,
      stack: error.stack,
      requestData: {
        name: req.body.name,
        xCoordinatesExists: req.body.xCoordinates
          ? true
          : typeof req.body.xCoordinates,
        yCoordinatesExists: req.body.yCoordinates
          ? true
          : typeof req.body.yCoordinates,
      },
    });
    next(error);
  }
});

app.post("/query", async (req, res, next) => {
  try {
    const { error } = querySchema.validate(req.body);
    if (error) throw new CustomError(400, error.details[0].message);

    if (!req.body.query_name) {
      return res.status(400).json({ error: '"query_name" is required' });
    }
    const { query_name } = req.body;
    logger.info("Searching for:", query_name, " - Most Recent Run");
    const client = await getMongoClient();
    const db = client.db("training");

    const result = await db
      .collection("points")
      .findOne({ name: query_name }, { sort: { lastUpdate: -1 } });

    if (!result) {
      logger.info(`✓ Query successful: ${query_name} - not found`);
      return res.status(404).json({ error: "Batch not found" });
    }

    const allPoints = result.points;
    const xCoordinates = allPoints.map((point) => point.x).flat();
    const yCoordinates = allPoints.map((point) => point.y).flat();
    const runId = result.runId;

    logger.info(`✓ Retrieved runId: ${runId} for ${query_name}`);

    const counterKey = `${query_name}-${runId}`;
    const batchCount = batchCounter[counterKey] || 0;

    let totalPoints = 0;
    for (const point of allPoints) {
      totalPoints += point.x.length;
    }

    const emitPayload = {
      name: result.name,
      xCoordinates: xCoordinates,
      yCoordinates: yCoordinates,
      batchCount: batchCount,
      totalPoints: totalPoints,
      runId: runId,
    };

    io.emit("logging", emitPayload);

    const response = {
      name: result.name,
      xCoordinates: xCoordinates,
      yCoordinates: yCoordinates,
      runId: runId,
      points: allPoints,
      batchCount: batchCount,
      totalPoints: totalPoints,
    };

    res.status(200).json([response]);
  } catch (error) {
    console.log(error);
    next(error);
  }
});

class CustomError extends Error {
  constructor(statusCode, message) {
    super(message);
    this.statusCode = statusCode;
  }
}

app.use((err, req, res, next) => {
  if (err instanceof CustomError) {
    return res.status(err.statusCode).json({ error: err.message });
  }
  logger.error("✗ Error:", err.message);
  res.status(500).json({ error: "Internal Server Error" });
});

io.on("connection", (socket) => {
  logger.info(`✓ Socket connected: ${socket.id}`);
  socket.on("disconnect", () => {
    logger.info(`○ Socket disconnected: ${socket.id}`);
  });
});

httpServer.listen(HTTP_PORT, () => {
  logger.info(`✓ HTTP & Socket.IO server running on port: ${HTTP_PORT}`);
});

process.on("SIGINT", async () => {
  console.log("Gracefully shutting down...");
  try {
    if (mongoClient) await mongoClient.close();
    io.close();
    httpServer.close(() => {
      console.log("Server shut down");
      process.exit(0);
    });
  } catch (err) {
    logger.error("Error during shutdown", err);
    process.exit(1);
  }
});

export default app;
