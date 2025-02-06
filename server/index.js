import { MongoClient } from "mongodb";
import { Server } from "socket.io";
import http from "http";
import express from "express";
import rateLimit from "express-rate-limit";
import helmet from "helmet";
import Joi from "joi";
import winston from "winston";
import chalk from "chalk";
import pkg from "lodash";
import dotenv from "dotenv";
const { debounce } = pkg;

if (!process.env.MONGODB_URI) {
  dotenv.config();
}

const HTTP_PORT = process.env.PORT || 5005;
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017";

const app = express();
app.set("trust proxy", 1);
const httpServer = http.createServer(app);

const io = new Server(httpServer, {
  cors: { origin: "*" },
  path: "/api/socket",
});

let mongoClient;
async function getMongoClient() {
  // Check if the client exists and if it's connected using MongoDB v4+ driver
  if (!mongoClient || !mongoClient.topology.isConnected()) {
    mongoClient = new MongoClient(MONGODB_URI, { useUnifiedTopology: true });
    await mongoClient.connect();
  }

  // Check the connection state
  const connected = mongoClient.topology.isConnected();
  if (!connected) {
    logger.warn("MongoDB connection is not active");
  }

  return mongoClient;
}

const logger = winston.createLogger({
  level: "info",
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple(),
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

// Rate Limiting Configurations
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

const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000000, // Max number of requests
  message: "Too many requests, please try again later.",
  handler: (req, res, next) => {
    logger.warn(`Rate limit exceeded for ${req.ip} globally`);
    res
      .status(429)
      .json({ error: "Rate limit exceeded, please try again later." });
  },
});

app.use(generalLimiter);

// Logger Middleware
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

// Joi Schemas for validation
const batchSchema = Joi.object({
  name: Joi.string().required(),
  xCoordinates: Joi.array().items(Joi.number()).required(),
  yCoordinates: Joi.array().items(Joi.number()).required(),
});

const querySchema = Joi.object({
  query_name: Joi.string().required(),
});

// In-memory batch counter per name
let batchCounter = {};

// Batch Route to Handle Batches
app.post("/batch", batchLimiter, async (req, res, next) => {
  try {
    const { error } = batchSchema.validate(req.body);
    if (error) {
      logger.error("✗ Batch request validation failed", {
        error: error.details,
        body: {
          name: req.body.name,
          xCoordinatesExists: req.body.xCoordinates
            ? true
            : typeof req.body.xCoordinates,
          yCoordinatesExists: req.body.yCoordinates
            ? true
            : typeof req.body.yCoordinates,
        },
      });
      throw new Error(`Validation Error`);
    }

    const { name, xCoordinates, yCoordinates } = req.body;
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
    };

    // MongoDB client and database operations
    const client = await getMongoClient();
    const db = client.db("training");

    // Perform the MongoDB update operation
    await db
      .collection("points")
      .updateOne(
        { name },
        { $push: { points: point }, $set: { lastUpdate: new Date() } },
        { upsert: true },
      );

    // Increment the batch count for this name
    batchCounter[name] = (batchCounter[name] || 0) + 1;

    // Log the batch count for debugging
    logger.info(
      `${chalk.green("✓")} Batch processed for ${chalk.blue(name)}: ${chalk.yellow(batchCounter[name])} batch(es) received`,
    );

    // Emit the data to the socket (without debounce to handle each batch)
    const emitPayload = {
      name,
      xCoordinates: validatedXCoordinates,
      yCoordinates: validatedYCoordinates,
    };
    io.emit("logging", emitPayload);

    res.status(200).json({ success: true });
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
    next(error); // Pass the error to the global error handler
  }
});

// Query Route to Handle Queries
app.post("/query", async (req, res, next) => {
  try {
    const { error } = querySchema.validate(req.body);
    if (error) throw new Error(error.details[0].message);

    const { query_name } = req.body;
    console.log("Searching for:", query_name);
    const client = await getMongoClient();
    console.log('Issue already here')
    const db = client.db("training");
    const result = await db.collection("points").findOne({ name: query_name });

    logger.info(
      `✓ Query successful: ${query_name} - ${result ? "found" : "not found"}`,
    );

    res.status(200).json(result);
  } catch (error) {
    console.log(error);
    next(error);
  }
});

// Global Error Handler
class CustomError extends Error {
  constructor(statusCode, message) {
    super(message);
    this.statusCode = statusCode;
  }
}

app.use((err, req, res, next) => {
  if (err instanceof CustomError) {
    res.status(err.statusCode).json({ error: err.message });
  } else {
    logger.error("✗ Error:", err.message);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

// Socket.IO Setup
io.on("connection", (socket) => {
  logger.info(`✓ Socket connected: ${socket.id}`);

  socket.on("disconnect", () => {
    logger.info(`○ Socket disconnected: ${socket.id}`);
  });
});

// Start the HTTP & WebSocket server
httpServer.listen(HTTP_PORT, () => {
  logger.info(`✓ HTTP & Socket.IO server running on port: ${HTTP_PORT}`);
});

// Graceful Shutdown
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
