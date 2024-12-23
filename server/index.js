import { MongoClient } from 'mongodb';
import { Server } from "socket.io";
import http from "http";
import express from 'express';
import chalk from 'chalk';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import Joi from 'joi';

// Constants
const HTTP_PORT = process.env.PORT || 5005;
const SOCKET_PORT = 3005;
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://localhost:27017";

// Initialize Express
const app = express();
const httpServer = http.createServer(app);

// Initialize Socket.IO on the same server
const io = new Server(httpServer, {
  cors: { origin: "*" }, // Permissive CORS for development
  path: "/socket/"
});

// MongoDB client
let mongoClient;
async function getMongoClient() {
  if (!mongoClient) {
    mongoClient = new MongoClient(MONGODB_URI);
    await mongoClient.connect();
  }
  return mongoClient;
}

// Middleware
app.use(helmet());
app.use(express.json({ limit: "10mb" }));

// Rate limiter applied only to /batch
const batchLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
});

// Logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  console.log(chalk.cyan(`→ ${req.method} ${req.path}`));

  res.on('finish', () => {
    const duration = Date.now() - start;
    const status = res.statusCode;
    const statusColor = status >= 400 ? chalk.red : chalk.green;

    console.log(
      statusColor(`← ${status}`),
      chalk.gray(`${duration}ms`),
      chalk.yellow(req.path)
    );
  });

  next();
});

// Input validation schemas
const batchSchema = Joi.object({
  name: Joi.string().required(),
  xCoordinates: Joi.array().items(Joi.number()).required(),
  yCoordinates: Joi.array().items(Joi.number()).required()
});

const querySchema = Joi.object({
  query_name: Joi.string().required()
});

// Routes
app.post("/batch", batchLimiter, async (req, res, next) => {
  try {
    const { error } = batchSchema.validate(req.body);
    if (error) throw new Error(error.details[0].message);

    const { name, xCoordinates, yCoordinates } = req.body;
	  console.log(req.body)
    const point = {
      x: xCoordinates.map(x => Number(x)),
      y: yCoordinates.map(y => Number(y)),
      timestamp: new Date()
    };

    const client = await getMongoClient();
    const db = client.db('training');

    await db.collection('points').updateOne(
      { name },
      {
        $push: { points: point },
        $set: { lastUpdate: new Date() }
      },
      { upsert: true }
    );

    io.emit("dataUpdate", { name, point });

    console.log(chalk.green('✓ Batch processed successfully:'),
      chalk.gray(`${name} - ${point.x.length} points`));

    res.status(200).json({ success: true });
  } catch (error) {
    next(error);
  }
});

app.post("/query", async (req, res, next) => {
  try {
    const { error } = querySchema.validate(req.body);
    if (error) throw new Error(error.details[0].message);

    const { query_name } = req.body;

    const client = await getMongoClient();
    const db = client.db('training');
    const result = await db.collection('points').findOne({ name: query_name });

    console.log(chalk.green('✓ Query successful:'),
      chalk.gray(`${query_name} - ${result ? 'found' : 'not found'}`));

    res.status(200).json(result);
  } catch (error) {
    next(error);
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(chalk.red('✗ Error:'), err.message);
  res.status(400).json({ error: err.message });
});

// Socket.IO handlers
io.on("connection", (socket) => {
  console.log(chalk.green('✓ Socket connected:'), chalk.gray(socket.id));

  socket.on("disconnect", () => {
    console.log(chalk.yellow('○ Socket disconnected:'), chalk.gray(socket.id));
  });
});

// Start server
httpServer.listen(HTTP_PORT, () => {
  console.log(chalk.green('✓ HTTP & Socket.IO server running on port:'),
    chalk.bold(HTTP_PORT));
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log(chalk.yellow('○ Graceful shutdown initiated'));
  try {
    if (mongoClient) await mongoClient.close();
    httpServer.close(() => {
      console.log(chalk.green('✓ Servers shut down successfully'));
      process.exit(0);
    });
  } catch (err) {
    console.error(chalk.red('✗ Error during shutdown:'), err.message);
    process.exit(1);
  }
});

