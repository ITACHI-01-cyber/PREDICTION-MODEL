import api from './api';

export const predictionService = {
  async createPrediction(data) {
    const response = await api.post('/predictions', data);
    return response.data;
  },

  async getPredictions(page = 0, size = 10) {
    const response = await api.get('/predictions', { params: { page, size } });
    return response.data;
  },

  async getPredictionById(id) {
    const response = await api.get(`/predictions/${id}`);
    return response.data;
  },

  async getPredictionsByProject(projectId) {
    const response = await api.get(`/predictions/project/${projectId}`);
    return response.data;
  },
};
