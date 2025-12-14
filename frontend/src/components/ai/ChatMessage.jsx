// ===== FILE: frontend/src/components/ai/ChatMessage.jsx =====
import React from 'react';
import { Bot, User } from 'lucide-react';
import { formatRelativeTime } from '../../utils/formatters';

const ChatMessage = ({ message }) => {
  const isAI = message.role === 'assistant';

  return (
    <div className={`flex gap-3 ${isAI ? '' : 'flex-row-reverse'}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isAI ? 'bg-primary-900/50 text-primary-400' : 'bg-dark-700 text-gray-400'
      }`}>
        {isAI ? <Bot className="h-5 w-5" /> : <User className="h-5 w-5" />}
      </div>
      
      <div className={`flex-1 ${isAI ? '' : 'flex flex-col items-end'}`}>
        <div className={`inline-block px-4 py-3 rounded-lg ${
          isAI 
            ? 'bg-dark-800 border border-dark-700' 
            : 'bg-primary-600 text-white'
        }`}>
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>
        
        {message.timestamp && (
          <p className="text-xs text-gray-500 mt-1">
            {formatRelativeTime(message.timestamp)}
          </p>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
