import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Layout Components
import MainLayout from './components/layout/MainLayout';

// Pages
import Dashboard from './pages/Dashboard';
import Trading from './pages/Trading';
import Performance from './pages/Performance';
import CircuitBreaker from './pages/CircuitBreaker';
import Settings from './pages/Settings';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import ForgotPassword from './pages/auth/ForgotPassword';

// Contexts
import { useTheme } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background-dark flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-text-dark/70">Initializing Sigma AI...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Public Route Component (for auth pages)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background-dark flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function AppContent() {
  const { theme } = useTheme();

  return (
    <div className={theme}>
      <Toaster
        position="top-right"
        toastOptions={{
          className: 'glass-card',
          style: {
            background: theme === 'dark' ? '#141420' : '#ffffff',
            color: theme === 'dark' ? '#e2e8f0' : '#1f2937',
            border: `1px solid ${theme === 'dark' ? '#2a2a3a' : '#e5e7eb'}`,
          },
        }}
      />
      
      <Routes>
        {/* Auth Routes */}
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />
        <Route path="/register" element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        } />
        <Route path="/forgot-password" element={
          <PublicRoute>
            <ForgotPassword />
          </PublicRoute>
        } />

        {/* Protected Routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="trading" element={<Trading />} />
          <Route path="performance" element={<Performance />} />
          <Route path="circuit-breaker" element={<CircuitBreaker />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* 404 Route */}
        <Route path="*" element={
          <div className="min-h-screen bg-background-dark flex items-center justify-center">
            <div className="text-center">
              <h1 className="text-6xl font-orbitron font-bold text-primary mb-4">404</h1>
              <p className="text-xl text-text-dark/80 mb-8">Page not found</p>
              <a 
                href="/dashboard" 
                className="inline-block bg-primary hover:bg-primary-dark text-black font-semibold py-2 px-6 rounded-lg transition-colors"
              >
                Back to Dashboard
              </a>
            </div>
          </div>
        } />
      </Routes>

      {/* React Query Devtools (only in development) */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
