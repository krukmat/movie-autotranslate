import axios from "axios";

const client = axios.create({
  baseURL: "/v1",
  timeout: 15000
});

export default client;
