/**
 * CrisisLens App — React Router + React Query Provider.
 */
import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import DashboardLayout from './layouts/DashboardLayout';

const HomePage = lazy(() => import('./pages/HomePage'));
const RiskMonitorPage = lazy(() => import('./pages/RiskMonitorPage'));
const AlertsPage = lazy(() => import('./pages/AlertsPage'));
const WorldMapPage = lazy(() => import('./pages/WorldMapPage'));
const CrossMarketPage = lazy(() => import('./pages/CrossMarketPage'));
const ModelPerformancePage = lazy(() => import('./pages/ModelPerformancePage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 30_000, // Poll every 30s
      staleTime: 15_000,
      retry: 2,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<div style={{height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-3)'}}>Loading application module...</div>}>
          <Routes>
            <Route element={<DashboardLayout />}>
              <Route index element={<HomePage />} />
              <Route path="/risk" element={<RiskMonitorPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/map" element={<WorldMapPage />} />
              <Route path="/cross-market" element={<CrossMarketPage />} />
              <Route path="/performance" element={<ModelPerformancePage />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
