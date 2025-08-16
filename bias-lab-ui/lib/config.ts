// API Configuration
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Endpoints
export const endpoints = {
  articles: `${API_URL}/articles`,
  articleDetail: (id: string) => `${API_URL}/articles/${id}`,
  narratives: `${API_URL}/narratives`,
  health: `${API_URL}/health`,
};

// Fetch with error handling
export async function fetchAPI(endpoint: string) {
  try {
    const response = await fetch(endpoint);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Fetch Error:', error);
    throw error;
  }
}
