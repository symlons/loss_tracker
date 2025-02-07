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
import crypto from 'crypto'; // Import crypto

const { debounce } = pkg;

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
  if (!mongoClient || !mongoClient.topology.isConnected()) {
    mongoClient = new MongoClient(MONGODB_URI, { useUnifiedTopology: true });
    await mongoClient.connect();
  }

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

// Batch Limiter
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

// Rate Limiter
const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
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

// Joi Schemas for validation
const batchSchema = Joi.object({
  name: Joi.string().required(),
  xCoordinates: Joi.array().items(Joi.number()).required(),
  yCoordinates: Joi.array().items(Joi.number()).required(),
  runId: Joi.string().optional(), // runId is now optional
});

const querySchema = Joi.object({
  query_name: Joi.string().required(),
});

// In-memory batch counter per name
let batchCounter = {}; // TODO: how to reset this counter?

app.post("/batch", batchLimiter, async (req, res, next) => {
  try {
    // Validate request body
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

    const { name, xCoordinates, yCoordinates, runId: incomingRunId } = req.body; // Destructure runId

    const validatedXCoordinates = Array.isArray(xCoordinates)
      ? xCoordinates
      : [];
    const validatedYCoordinates = Array.isArray(yCoordinates)
      ? yCoordinates
      : [];

    // Generate a runId if one is not provided
    const runId = incomingRunId || crypto.randomUUID(); // Use incomingRunId if provided, otherwise generate a new one

    // Ensure the point structure is correct with x and y inside it
    const point = {
      x: validatedXCoordinates.map((x) => Number(x)), // x coordinates as an array
      y: validatedYCoordinates.map((y) => Number(y)), // y coordinates as an array
      timestamp: new Date(), // Timestamp for when the point is created
      runId: runId, // Include runId in the point object
    };

    // Log the point to verify structure before updating the database
    console.log("Point to be pushed:", point);

    const client = await getMongoClient();
    const db = client.db("training");

    // Update or insert document with upsert: true
    await db.collection("points").updateOne(
      { name, runId }, // Use name and runId as the unique identifier
      {
        $push: { points: point }, // Push new point object into the points array
        $set: { lastUpdate: new Date() }, // Update lastUpdate field
      },
      { upsert: true }, // Insert document if it doesn't exist
    );

    // Update the batch counter for the name
    batchCounter[name] = (batchCounter[name] || 0) + 1;
    console.log("Batch Counter:", batchCounter[name]);

    // Log success
    logger.info(
      `${chalk.green("✓")} Batch processed for ${chalk.blue(name)}: ${chalk.yellow(batchCounter[name])} batch(es) received`,
    );

    // Emit the logging payload
    const emitPayload = {
      name,
      xCoordinates: validatedXCoordinates,
      yCoordinates: validatedYCoordinates,
    };

    io.emit("logging", emitPayload);

    // Respond with success
    res.status(200).json({ success: true, runId: runId }); // Include runId in the response
  } catch (error) {
    // Log any errors that occur during the batch process
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
    next(error); // Pass error to next middleware
  }
});

app.post("/query", async (req, res, next) => {
  try {
    const { error } = querySchema.validate(req.body);
    if (error) throw new Error(error.details[0].message);

    const { query_name } = req.body;
    logger.info("Searching for:", query_name);
    const client = await getMongoClient();
    const db = client.db("training");

    // Find the most recent document with the matching name
    const mostRecentResult = await db
      .collection("points")
      .find({ name: query_name })
      .sort({ lastUpdate: -1 }) // Sort by lastUpdate descending
      .limit(1)
      .toArray();

    console.log("Most Recent Result from MongoDB:", mostRecentResult);

    if (mostRecentResult.length === 0) {
      logger.info(`✓ Query successful: ${query_name} - not found`);
      return res.status(200).json(null); // Or an empty object, depending on your needs
    }

    const runId = mostRecentResult[0].runId;

    if (!runId) {
      logger.warn(`✗ runId is undefined for ${query_name}, skipping`);
      return res.status(200).json(null); // Skip if runId is undefined
    }

    logger.info(`✓ Retrieved runId: ${runId} for ${query_name}`);

    // Find all batches with the specific runId
    const results = await db
      .collection("points")
      .find({ name: query_name, runId: runId })
      .sort({ "points.timestamp": 1 }) // Sort by timestamp ascending
      .toArray();

    console.log("Batches with runId from MongoDB:", results);

    logger.info(
      `✓ Query successful: ${query_name} - ${results.length > 0 ? "found" : "not found"
      } batches for runId ${runId}`,
    );

    if (results.length > 0) {
      const allPoints = results[0].points;
      const xCoordinates = allPoints.map((point) => point.x).flat();
      const yCoordinates = allPoints.map((point) => point.y).flat();

      const emitPayload = {
        name: results[0].name,
        xCoordinates: xCoordinates,
        yCoordinates: yCoordinates,
      };

      io.emit("logging", emitPayload);
      res.status(200).json({
        name: results[0].name,
        xCoordinates: xCoordinates,
        yCoordinates: yCoordinates,
        runId: runId, // Include the runId in the response
        points: allPoints,
      }); // Return all batches
    } else {
      res.status(200).json(null); // Or an empty object, depending on your needs
    }
  } catch (error) {
    console.log(error);
    next(error);
  }
});

