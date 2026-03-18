/**
 * Dashboard Guard
 * 
 * Protege a página do dashboard
 * Requer autenticação e workspace selecionado
 */

import { AuthGuard } from '../guards/authGuard.js';

// Proteger página
try {
  AuthGuard.protectPage({
    requireAuth: true,
    requireWorkspace: true
  });
  
  console.log('Dashboard: Access granted');
} catch (error) {
  console.error('Dashboard: Access denied');
  // Página será redirecionada pelo guard
}

// Exportar para uso em outros scripts
export { AuthGuard };
