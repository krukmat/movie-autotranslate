import request from "supertest";
import axios from "axios";
import app from "./server";

jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockData = (data: unknown) => ({ data });

describe("gateway routes", () => {
  beforeEach(() => {
    mockedAxios.create.mockReturnThis();
  });

  it("forwards upload init", async () => {
    mockedAxios.request.mockResolvedValueOnce(mockData({ assetId: "a" }));
    await request(app).post("/api/upload/init").send({ filename: "test" }).expect(200, { assetId: "a" });
    expect(mockedAxios.request).toHaveBeenCalledWith(expect.objectContaining({ url: "/upload/init", method: "POST" }));
  });

  it("forwards job list", async () => {
    mockedAxios.request.mockResolvedValueOnce(mockData({ items: [] }));
    await request(app).get("/api/jobs").expect(200, { items: [] });
    expect(mockedAxios.request).toHaveBeenCalledWith(expect.objectContaining({ url: "/jobs", method: "GET" }));
  });
});
