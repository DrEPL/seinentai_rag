/**
 * SEINENTAI4US — Admin API
 */
import api from './axios';

export const adminApi = {
  getHealth: () => api.get('/admin/health'),
};
