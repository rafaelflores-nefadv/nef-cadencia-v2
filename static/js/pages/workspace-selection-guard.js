/**
 * Workspace Selection Guard
 * 
 * Protege a página de seleção de workspace
 * Requer autenticação mas não requer workspace (pois é onde seleciona)
 */

import { AuthGuard } from '../guards/authGuard.js';

// Proteger página
try {
  AuthGuard.protectPage({
    requireAuth: true,
    requireWorkspace: false
  });
  
  console.log('Workspace Selection: Access granted');
} catch (error) {
  console.error('Workspace Selection: Access denied');
  // Página será redirecionada pelo guard
}

// Exportar para uso em outros scripts
export { AuthGuard };
