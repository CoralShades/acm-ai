import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';

// Register all Community modules
ModuleRegistry.registerModules([AllCommunityModule]);

// Export flag to ensure registration happens once
export const AG_GRID_INITIALIZED = true;
