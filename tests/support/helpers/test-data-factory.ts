/**
 * Test Data Factory for Open Notebook
 *
 * Creates test data with automatic cleanup tracking.
 * Pattern: Factory creates → tracks → cleanup deletes
 *
 * Usage:
 *   const factory = new TestDataFactory();
 *   const notebook = await factory.createNotebook({ name: 'Test' });
 *   // ... test ...
 *   await factory.cleanup(); // Deletes all created resources
 */

import {
  createNotebook,
  deleteNotebook,
  createNote,
  deleteNote,
  type Notebook,
  type Note,
} from './api-helpers';

export class TestDataFactory {
  private createdNotebooks: string[] = [];
  private createdNotes: string[] = [];

  /**
   * Create a notebook and track for cleanup
   */
  async createNotebook(overrides: Partial<Notebook> = {}): Promise<Notebook> {
    const notebook = await createNotebook({
      name: `E2E Test ${Date.now()}`,
      description: 'Created by E2E test - will be cleaned up',
      ...overrides,
    });
    this.createdNotebooks.push(notebook.id);
    return notebook;
  }

  /**
   * Create a note and track for cleanup
   */
  async createNote(
    overrides: Partial<Note> & { notebook_id?: string } = {}
  ): Promise<Note> {
    const note = await createNote({
      title: `E2E Test Note ${Date.now()}`,
      content: 'Created by E2E test - will be cleaned up',
      ...overrides,
    });
    this.createdNotes.push(note.id);
    return note;
  }

  /**
   * Create a notebook with notes (common pattern)
   */
  async createNotebookWithNotes(
    notebookOverrides: Partial<Notebook> = {},
    noteCount = 2
  ): Promise<{ notebook: Notebook; notes: Note[] }> {
    const notebook = await this.createNotebook(notebookOverrides);
    const notes: Note[] = [];

    for (let i = 0; i < noteCount; i++) {
      const note = await this.createNote({
        title: `Note ${i + 1}`,
        notebook_id: notebook.id,
      });
      notes.push(note);
    }

    return { notebook, notes };
  }

  /**
   * Clean up all created resources
   * Called automatically in fixture teardown
   */
  async cleanup(): Promise<void> {
    // Delete notes first (may have notebook references)
    for (const noteId of this.createdNotes) {
      try {
        await deleteNote(noteId);
      } catch (error) {
        console.warn(`Failed to cleanup note ${noteId}:`, error);
      }
    }
    this.createdNotes = [];

    // Delete notebooks
    for (const notebookId of this.createdNotebooks) {
      try {
        await deleteNotebook(notebookId);
      } catch (error) {
        console.warn(`Failed to cleanup notebook ${notebookId}:`, error);
      }
    }
    this.createdNotebooks = [];
  }

  /**
   * Get count of tracked resources
   */
  get trackedCount(): { notebooks: number; notes: number } {
    return {
      notebooks: this.createdNotebooks.length,
      notes: this.createdNotes.length,
    };
  }
}
