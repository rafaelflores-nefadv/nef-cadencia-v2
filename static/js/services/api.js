/**
 * Cliente HTTP genérico para comunicação com backend Django
 * 
 * Responsabilidades:
 * - Gerenciar requisições HTTP
 * - Adicionar CSRF token automaticamente
 * - Tratar erros de forma centralizada
 * - Suportar interceptors futuros
 */

class ApiClient {
  constructor() {
    this.baseURL = window.location.origin;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
  }

  /**
   * Obtém o CSRF token dos cookies
   */
  getCsrfToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    
    for (let cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(name + '=')) {
        return trimmed.substring(name.length + 1);
      }
    }
    
    return '';
  }

  /**
   * Obtém o token JWT do localStorage
   */
  getAuthToken() {
    return localStorage.getItem('nef_auth_token');
  }

  /**
   * Requisição genérica com suporte a JWT
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    // Adicionar token JWT se disponível
    const token = this.getAuthToken();
    const headers = {
      ...this.defaultHeaders,
      'X-CSRFToken': this.getCsrfToken(),
      ...options.headers
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      
      // Se 401, tentar refresh token
      if (response.status === 401 && token) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Tentar novamente com novo token
          headers['Authorization'] = `Bearer ${this.getAuthToken()}`;
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
              data: retryData
            };
          }
          
          return {
            success: true,
            data: retryData,
            status: retryResponse.status
          };
        }
      }
      
      // Tentar parsear JSON
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
          data: data
        };
      }

      return {
        success: true,
        data: data,
        status: response.status
      };

    } catch (error) {
      console.error('API Error:', error);
      
      return {
        success: false,
        error: error.data || error.message || 'Erro ao comunicar com o servidor',
        status: error.status || 500
      };
    }
  }

  /**
   * GET request
   */
  async get(endpoint, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'GET'
    });
  }

  /**
   * POST request
   */
  async post(endpoint, data = null, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : null
    });
  }

  /**
   * PUT request
   */
  async put(endpoint, data = null, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : null
    });
  }

  /**
   * DELETE request
   */
  async delete(endpoint, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'DELETE'
    });
  }

  /**
   * PATCH request
   */
  async patch(endpoint, data = null, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : null
    });
  }

  /**
   * Refresh JWT token
   */
  async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('nef_refresh_token');
      
      if (!refreshToken) {
        return false;
      }

      const response = await fetch(`${this.baseURL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh: refreshToken })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('nef_auth_token', data.access);
        return true;
      }

      // Refresh falhou, limpar tokens
      localStorage.removeItem('nef_auth_token');
      localStorage.removeItem('nef_refresh_token');
      return false;

    } catch (error) {
      console.error('Refresh token error:', error);
      return false;
    }
  }
}

// Exportar instância singleton
export const api = new ApiClient();
