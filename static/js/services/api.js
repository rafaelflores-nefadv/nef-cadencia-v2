import { storage } from '../utils/storage.js';

/**
 * Generic HTTP client for Django backend communication.
 */
class ApiClient {
  constructor() {
    this.baseURL = window.location.origin;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
  }

  getCsrfToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');

    for (const cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(name + '=')) {
        return trimmed.substring(name.length + 1);
      }
    }

    return '';
  }

  getAuthToken() {
    return storage.getAuthToken();
  }

  isAuthEndpoint(endpoint) {
    return (
      endpoint.startsWith('/api/auth/login') ||
      endpoint.startsWith('/api/auth/refresh') ||
      endpoint.startsWith('/api/auth/verify')
    );
  }

  extractErrorMessage(rawError) {
    if (!rawError) {
      return 'Erro ao comunicar com o servidor';
    }

    if (typeof rawError === 'string') {
      return rawError;
    }

    if (typeof rawError === 'object') {
      if (typeof rawError.error === 'string') {
        return rawError.error;
      }
      if (typeof rawError.detail === 'string') {
        return rawError.detail;
      }
      if (Array.isArray(rawError.non_field_errors) && rawError.non_field_errors.length > 0) {
        return String(rawError.non_field_errors[0]);
      }

      const firstValue = Object.values(rawError)[0];
      if (Array.isArray(firstValue) && firstValue.length > 0) {
        return String(firstValue[0]);
      }
      if (typeof firstValue === 'string') {
        return firstValue;
      }

      try {
        return JSON.stringify(rawError);
      } catch (jsonError) {
        return 'Erro ao comunicar com o servidor';
      }
    }

    return String(rawError);
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const useAuthHeader = !this.isAuthEndpoint(endpoint);
    const token = useAuthHeader ? this.getAuthToken() : null;

    const headers = {
      ...this.defaultHeaders,
      'X-CSRFToken': this.getCsrfToken(),
      ...options.headers,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      if (response.status === 401 && token && !this.isAuthEndpoint(endpoint)) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          headers.Authorization = `Bearer ${this.getAuthToken()}`;
          const retryResponse = await fetch(url, { ...options, headers });

          let retryData;
          const retryContentType = retryResponse.headers.get('content-type');
          if (retryContentType && retryContentType.includes('application/json')) {
            retryData = await retryResponse.json();
          } else {
            retryData = await retryResponse.text();
          }

          if (!retryResponse.ok) {
            throw {
              status: retryResponse.status,
              statusText: retryResponse.statusText,
              data: retryData,
            };
          }

          return {
            success: true,
            data: retryData,
            status: retryResponse.status,
          };
        }
      }

      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        throw {
          status: response.status,
          statusText: response.statusText,
          data,
        };
      }

      return {
        success: true,
        data,
        status: response.status,
      };
    } catch (error) {
      console.error('API Error:', error);

      const payload = error?.data || error?.message || error;
      return {
        success: false,
        error: this.extractErrorMessage(payload),
        status: error?.status || 500,
      };
    }
  }

  async get(endpoint, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'GET',
    });
  }

  async post(endpoint, data = null, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : null,
    });
  }

  async put(endpoint, data = null, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : null,
    });
  }

  async delete(endpoint, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'DELETE',
    });
  }

  async patch(endpoint, data = null, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : null,
    });
  }

  async refreshToken() {
    try {
      const refreshToken = storage.get('refresh_token');

      if (!refreshToken) {
        return false;
      }

      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.getCsrfToken(),
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        const nextAccess = data.access || data.token;
        if (nextAccess) {
          storage.setAuthToken(nextAccess);
          return true;
        }
      }

      storage.clearAuth();
      return false;
    } catch (error) {
      console.error('Refresh token error:', error);
      storage.clearAuth();
      return false;
    }
  }
}

export const api = new ApiClient();
