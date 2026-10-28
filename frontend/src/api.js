import axios from 'axios';

// Use relative URL so it works with the same origin (FastAPI serving static files)
// If running separately (dev mode), use the env var or default to localhost:8004
const API_URL = import.meta.env.PROD ? '' : 'http://localhost:8007';

export const api = axios.create({
  baseURL: API_URL,
});

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  // Do NOT manually set Content-Type for FormData; axios/browser will handle it with the boundary
  const response = await api.post('/upload', formData);
  return response.data;
};

export const getDatasets = async () => {
  const response = await api.get('/datasets');
  return response.data;
};

export const getDataset = async (id) => {
  const response = await api.get(`/dataset/${id}`);
  return response.data;
};

export const deleteDataset = async (id) => {
  const response = await api.delete(`/dataset/${id}`);
  return response.data;
};

export const viewData = async (id, page = 0, limit = 10) => {
  const response = await api.get(`/dataset/${id}/view`, {
    params: { start: page * limit, rows: limit },
  });
  return response.data;
};

export const getSummary = async (id) => {
  const response = await api.get(`/dataset/${id}/summary`);
  return response.data;
};

export const getSuggestions = async (id) => {
  const response = await api.get(`/dataset/${id}/suggestions`);
  return response.data;
};

export const meltDataset = async (id, config) => {
  const response = await api.post(`/dataset/${id}/melt`, config);
  return response.data;
};

export const pivotMeasures = async (id, config) => {
  const response = await api.post(`/dataset/${id}/pivot_measures`, config);
  return response.data;
};

export const flexiblePivot = async (id, config) => {
  const response = await api.post(`/dataset/${id}/pivot`, config);
  return response.data;
};

export const cleanDataset = async (id, operations) => {
  const response = await api.post(`/dataset/${id}/clean`, { operations });
  return response.data;
};

export const undoOperation = async (id, steps = 1) => {
  const response = await api.post(`/dataset/${id}/undo`, null, {
    params: { steps },
  });
  return response.data;
};

export const resetDataset = async (id) => {
  const response = await api.post(`/dataset/${id}/reset`);
  return response.data;
};

export const getVizTypes = async (id) => {
  const response = await api.get(`/dataset/${id}/visualization/types`);
  return response.data;
};

export const createVisualization = async (id, type, parameters, title) => {
  const response = await api.post(`/dataset/${id}/visualize`, {
    chart_type: type,
    parameters,
    title,
  });
  return response.data;
};

export const getDashboard = async (id) => {
  const response = await api.get(`/dataset/${id}/dashboard`);
  return response.data;
};

export const exportDataset = async (id, format) => {
  const response = await api.get(`/dataset/${id}/export`, {
    params: { format },
    responseType: 'blob',
  });
  return response;
};

export const chatWithData = async (id, query) => {
  const response = await api.post(`/dataset/${id}/chat`, { query });
  return response.data;
};

export const transformDataset = async (id, operation, params) => {
  // Overload to support (id, { operation, params }) signature
  let op = operation;
  let p = params;
  if (typeof operation === 'object' && !params) {
    op = operation.operation;
    p = operation.params;
  }
  const response = await api.post(`/dataset/${id}/transform`, { operation: op, params: p });
  return response.data;
};

export const downloadReport = async (id) => {
  const response = await api.get(`/dataset/${id}/report`, {
    responseType: 'blob'
  });
  return response;
};

export const getDashboardConfig = async (id) => {
  const response = await api.get(`/dataset/${id}/dashboard/config`);
  return response.data;
};

export const saveDashboardConfig = async (id, config) => {
  const response = await api.post(`/dataset/${id}/dashboard/config`, { config });
  return response.data;
};
