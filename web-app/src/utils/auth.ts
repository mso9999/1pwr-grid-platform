/**
 * Authentication utilities for API communication
 */

import { jwtDecode } from 'jwt-decode';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'procurement' | 'requestor' | 'field_team' | 'viewer';
  is_active: boolean;
  permissions: string[];
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  expires_in: number;
}

export interface JWTPayload {
  sub: string;
  role: string;
  exp: number;
  type: string;
}

class AuthService {
  private static instance: AuthService;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;

  private constructor() {
    // Load tokens from localStorage on initialization
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
      
      // Only setup refresh if tokens are valid
      if (this.accessToken && this.refreshToken) {
        try {
          const decoded = jwtDecode<JWTPayload>(this.accessToken);
          if (decoded.exp * 1000 > Date.now()) {
            this.setupTokenRefresh();
          } else {
            // Token expired, clear and redirect
            this.clearTokens();
            window.location.href = '/login';
          }
        } catch (error) {
          // Invalid token, clear and redirect
          this.clearTokens();
          window.location.href = '/login';
        }
      }
    }
  }

  static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  /**
   * Login with username and password
   */
  async login(credentials: LoginCredentials): Promise<User> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const tokens: AuthTokens = await response.json();
    this.setTokens(tokens);
    
    // Get user info after successful login
    const user = await this.getCurrentUser();
    return user;
  }

  /**
   * Logout and clear tokens
   */
  async logout(): Promise<void> {
    try {
      if (this.accessToken) {
        await fetch(`${API_BASE_URL}/api/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.accessToken}`,
          },
        });
      }
    } catch (error) {
    } finally {
      this.clearTokens();
    }
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    if (!this.accessToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired, try to refresh
        await this.refreshAccessToken();
        return this.getCurrentUser();
      }
      throw new Error('Failed to get user info');
    }

    return response.json();
  }

  /**
   * Refresh the access token
   */
  async refreshAccessToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (!response.ok) {
      this.clearTokens();
      throw new Error('Failed to refresh token');
    }

    const tokens: AuthTokens = await response.json();
    this.setTokens(tokens);
  }

  /**
   * Set authentication tokens
   */
  private setTokens(tokens: AuthTokens): void {
    this.accessToken = tokens.access_token;
    if (tokens.refresh_token) {
      this.refreshToken = tokens.refresh_token;
    }

    // Store in localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', this.accessToken);
      if (this.refreshToken) {
        localStorage.setItem('refresh_token', this.refreshToken);
      }
    }

    this.setupTokenRefresh();
  }

  /**
   * Clear authentication tokens
   */
  private clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;

    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }

    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  /**
   * Setup automatic token refresh
   */
  private setupTokenRefresh(): void {
    if (!this.accessToken) return;

    try {
      const decoded = jwtDecode<JWTPayload>(this.accessToken);
      const expiresIn = decoded.exp * 1000 - Date.now();
      
      // Refresh 1 minute before expiry
      const refreshIn = Math.max(0, expiresIn - 60000);

      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer);
      }

      this.refreshTimer = setTimeout(() => {
        this.refreshAccessToken().catch((error) => {
          console.error('Token refresh failed:', error);
          // Clear tokens and redirect to login on refresh failure
          this.clearTokens();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        });
      }, refreshIn);
    } catch (error) {
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (!this.accessToken) return false;

    try {
      const decoded = jwtDecode<JWTPayload>(this.accessToken);
      return decoded.exp * 1000 > Date.now();
    } catch {
      return false;
    }
  }

  /**
   * Get the access token for API requests
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Check if user has a specific permission
   */
  async hasPermission(permission: string): Promise<boolean> {
    try {
      const user = await this.getCurrentUser();
      return user.permissions.includes(permission);
    } catch {
      return false;
    }
  }

  /**
   * Check if user has a specific role
   */
  async hasRole(role: string): Promise<boolean> {
    try {
      const user = await this.getCurrentUser();
      return user.role === role;
    } catch {
      return false;
    }
  }
}

export const authService = AuthService.getInstance();

/**
 * API client with authentication headers
 */
export class AuthenticatedAPI {
  static async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = authService.getAccessToken();
    
    const headers = {
      ...options.headers,
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    };

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });

    // Handle token expiry
    if (response.status === 401 && token) {
      try {
        await authService.refreshAccessToken();
        // Retry the request with new token
        const newToken = authService.getAccessToken();
        return fetch(`${API_BASE_URL}${url}`, {
          ...options,
          headers: {
            ...options.headers,
            'Authorization': `Bearer ${newToken}`,
          },
        });
      } catch {
        // Refresh failed, redirect to login
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
    }

    return response;
  }
}
