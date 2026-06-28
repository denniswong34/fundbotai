/**
 * Broker API service — wraps all broker connection endpoints.
 */

import client from '@/api/client'

export default {
  getTypes() {
    return client.get('/brokers/types')
  },

  list() {
    return client.get('/brokers')
  },

  get(id) {
    return client.get(`/brokers/${id}`)
  },

  create(data) {
    return client.post('/brokers', data)
  },

  update(id, data) {
    return client.put(`/brokers/${id}`, data)
  },

  delete(id) {
    return client.delete(`/brokers/${id}`)
  },

  test(id) {
    return client.post(`/brokers/${id}/test`)
  },
}
