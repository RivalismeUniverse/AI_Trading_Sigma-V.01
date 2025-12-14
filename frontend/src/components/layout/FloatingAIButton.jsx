// ===== FILE: frontend/src/components/layout/FloatingAIButton.jsx =====
import React from 'react';
import { MessageCircle, X } from 'lucide-react';

const FloatingAIButton = ({ isOpen, onClick }) => {
  return (
    <button
      onClick={onClick}
      className={`fixed bottom-6 right-6 z-50 p-4 rounded-full shadow-glow-lg transition-all duration-300 ${
        isOpen 
          ? 'bg-danger-600 hover:bg-danger-700 rotate-90' 
          : 'bg-primary-600 hover:bg-primary-700 floating'
      }`}
    >
      {isOpen ? (
        <X className="h-6 w-6 text-white" />
      ) : (
        <MessageCircle className="h-6 w-6 text-white" />
      )}
      
      {!isOpen && (
        <span className="absolute -top-1 -right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-success-500"></span>
        </span>
      )}
    </button>
  );
};

export default FloatingAIButton;
