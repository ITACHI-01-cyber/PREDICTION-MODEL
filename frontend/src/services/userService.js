import api from './api';

export const userService = {
  async getUsers() {
    const response = await api.get('/users');
    return response.data;
  },

  async createUser(data) {
    const response = await api.post('/users', data);
    return response.data;
  },

  async updateUserStatus(id, active) {
    const response = await api.patch(`/users/${id}/status`, { active });
    return response.data;
  },
};
