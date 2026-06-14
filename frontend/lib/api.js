import axios from "axios";

const API = "http://localhost:8000";

export const getTree = (date) =>
  axios.get(`${API}/tree`, { params: { date } });

export const calculate = (data) =>
  axios.post(`${API}/calculate`, data);

export const saveCalc = (id) =>
  axios.post(`${API}/save/${id}`);

export const getCalculations = () =>
  axios.get(`${API}/calculations`);

export const getCalc = (id) =>
  axios.get(`${API}/calculations/${id}`);

export const exportCalc = (id) =>
  `${API}/export/${id}`;