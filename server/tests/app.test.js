import { describe, it, expect, afterEach } from "vitest";
import request from "supertest";
import app from "../index.js"; // Assuming your app is exported from index.js

// Reset the rate limiter store after each test to avoid cross-test interference.
afterEach(() => {
  if (app.batchLimiter && app.batchLimiter.store && typeof app.batchLimiter.store.resetAll === "function") {
    app.batchLimiter.store.resetAll();
  }
});

describe("API Endpoints", () => {
  it("GET / should return 200 OK", async () => {
    const response = await request(app).get("/");
    expect(response.status).toBe(200);
    expect(response.text).toBe("OK");
  });

  describe("POST /batch", () => {
    const validBatchData = {
      name: "testBatch",
      xCoordinates: [1, 2, 3],
      yCoordinates: [4, 5, 6],
    };

    const invalidBatchData = {
      name: "testBatch",
      xCoordinates: [1, 2, 3]  // Missing yCoordinates
    };

    it("should return 201 for valid batch data", async () => {
      const response = await request(app).post("/batch").send(validBatchData);
      expect(response.status).toBe(201);
      expect(response.body.success).toBe(true);
      expect(response.body.runId).toBeDefined();
    });

    it("should return 400 for invalid batch data", async () => {
      const response = await request(app).post("/batch").send(invalidBatchData);
      expect(response.status).toBe(400);
      expect(response.body.error).toBeDefined();
    });
  });

  describe("POST /query", () => {
    const validBatchData = {
      name: "testBatch",
      xCoordinates: [1, 2, 3],
      yCoordinates: [4, 5, 6],
    };

    it("should return 200 for a valid query", async () => {
      // First, create a batch.
      const batchResponse = await request(app)
        .post("/batch")
        .send(validBatchData);
      expect(batchResponse.status).toBe(201);

      const response = await request(app)
        .post("/query")
        .send({ query_name: "testBatch" });
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body[0].name).toBe("testBatch");
    });

    it("should return 400 for an invalid query", async () => {
      // Sending an empty object should trigger a validation error.
      const response = await request(app).post("/query").send({});
      expect(response.status).toBe(400);
      expect(response.body.error).toBeDefined();
    });

    it("should return 404 for a non-existing query", async () => {
      const response = await request(app)
        .post("/query")
        .send({ query_name: "nonExistingBatch" });
      expect(response.status).toBe(404);
      expect(response.body.error).toBe("Batch not found");
    });
  });
});

