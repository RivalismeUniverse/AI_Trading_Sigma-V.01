import React from 'react';
import { MessageSquare } from 'lucide-react';

function FloatingAIButton({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 bg-primary-500 hover:bg-primary-600 text-white rounded-full p-4 shadow-glow transition-all z-50"
      aria-label="Open AI Chat"
    >
      <MessageSquare className="w-6 h-6" />
    </button>
  );
}

export default FloatingAIButton;
