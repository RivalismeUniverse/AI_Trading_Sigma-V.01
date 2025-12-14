// ===== FILE: frontend/src/components/ai/AIChat.jsx =====
import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, X } from 'lucide-react';
import Button from '../common/Button';
import ChatMessage from './ChatMessage';
import api from '../../services/api';
import toast from 'react-hot-toast';

const AIChat = ({ isOpen, onClose }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! I\'m your AI trading assistant. How can I help you today?', timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.sendChatMessage(input.trim());
      
      const aiMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      toast.error('Failed to get AI response');
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-96 bg-dark-900 border-l border-dark-700 shadow-2xl z-40 flex flex-col animate-slide-in-right">
      {/* Header */}
      <div className="p-4 border-b border-dark-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary-500" />
          <h2 className="font-semibold">AI Assistant</h2>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-dark-800 rounded transition-colors">
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} />
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-900/50 flex items-center justify-center">
              <Bot className="h-5 w-5 text-primary-400" />
            </div>
            <div className="flex-1">
              <div className="inline-block px-4 py-3 bg-dark-800 border border-dark-700 rounded-lg">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></span>
                  <span className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></span>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-dark-700">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything..."
            disabled={loading}
            rows={3}
            className="flex-1 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm resize-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors"
          />
          <Button
            variant="primary"
            size="md"
            icon={Send}
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="self-end"
          />
        </div>
      </div>
    </div>
  );
};

export default AIChat;
