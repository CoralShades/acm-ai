/**
 * Pure API Helper Functions for Open Notebook
 *
 * These are framework-agnostic pure functions that can be:
 * 1. Used directly in unit tests
 * 2. Wrapped in Playwright fixtures
 * 3. Called from any test context
 *
 * Pattern: Pure function first, fixture wrapper second
 */

const API_URL = process.env.API_URL || 'http://localhost:5055/api';

// Types matching Open Notebook backend models
export interface Notebook {
  id: string;
  name: string;
  description?: string;
  archived?: boolean;
  created: string;
  updated: string;
}

export interface Source {
  id: string;
  title?: string;
  full_text?: string;
  topics?: string[];
  created: string;
  updated: string;
}

export interface Note {
  id: string;
  title?: string;
  content?: string;
  summary?: string;
  created: string;
  updated: string;
}

/**
 * Create a notebook via API
 */
export async function createNotebook(
  data: Partial<Notebook> = {}
): Promise<Notebook> {
  const response = await fetch(`${API_URL}/notebooks/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: data.name || `Test Notebook ${Date.now()}`,
      description: data.description || 'Created by E2E test',
      ...data,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create notebook: ${response.status}`);
  }

  return response.json();
}

/**
 * Delete a notebook via API
 */
export async function deleteNotebook(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/notebooks/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Failed to delete notebook: ${response.status}`);
  }
}

/**
 * List all notebooks
 */
export async function listNotebooks(): Promise<Notebook[]> {
  const response = await fetch(`${API_URL}/notebooks/`);

  if (!response.ok) {
    throw new Error(`Failed to list notebooks: ${response.status}`);
  }

  return response.json();
}

/**
 * Create a note via API
 */
export async function createNote(
  data: Partial<Note> & { notebook_id?: string } = {}
): Promise<Note> {
  const response = await fetch(`${API_URL}/notes/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: data.title || `Test Note ${Date.now()}`,
      content: data.content || 'Created by E2E test',
      ...data,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create note: ${response.status}`);
  }

  return response.json();
}

/**
 * Delete a note via API
 */
export async function deleteNote(id: string): Promise<void> {
  const response = await fetch(`${API_URL}/notes/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok && response.status !== 404) {
    throw new Error(`Failed to delete note: ${response.status}`);
  }
}

/**
 * Get available models from API
 */
export async function getModels(): Promise<unknown[]> {
  const response = await fetch(`${API_URL}/models/`);

  if (!response.ok) {
    throw new Error(`Failed to get models: ${response.status}`);
  }

  return response.json();
}

/**
 * Health check for API
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL.replace('/api', '')}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
