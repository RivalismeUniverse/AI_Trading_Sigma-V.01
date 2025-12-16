import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './Header';
import Sidebar from './Sidebar';

const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background-dark dark:bg-background-light transition-colors duration-300">
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          />
        )}
      </AnimatePresence>

      <div className="flex">
        {/* Sidebar - Desktop */}
        <div className="hidden lg:flex lg:flex-shrink-0">
          <motion.div
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <Sidebar />
          </motion.div>
        </div>

        {/* Sidebar - Mobile */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ duration: 0.3 }}
              className="fixed inset-y-0 left-0 z-50 w-64 lg:hidden"
            >
              <Sidebar onClose={() => setSidebarOpen(false)} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          <Header onMenuClick={() => setSidebarOpen(true)} />
          
          <main className="flex-1 overflow-y-auto">
            <div className="py-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <Outlet />
              </motion.div>
            </div>
          </main>

          {/* Footer */}
          <footer className="border-t border-border dark:border-gray-200 py-4 px-6">
            <div className="flex flex-col md:flex-row justify-between items-center space-y-2 md:space-y-0">
              <div className="text-sm text-text-dark/70 dark:text-text-light/70">
                © {new Date().getFullYear()} Sigma AI Trading Platform. All rights reserved.
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-xs font-orbitron font-medium text-primary">
                  v{process.env.REACT_APP_VERSION || '1.0.0'}
                </span>
                <div className="h-2 w-2 rounded-full bg-success animate-pulse"></div>
                <span className="text-xs text-success">System Active</span>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
};

export default MainLayout;
