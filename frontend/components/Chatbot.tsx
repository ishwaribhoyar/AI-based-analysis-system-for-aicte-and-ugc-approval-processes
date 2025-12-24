'use client';

import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader2, Bot, User, Sparkles } from 'lucide-react';
import { chatbotApi, ChatQueryResponse } from '@/lib/api';
import ReactMarkdown from 'react-markdown';

interface ChatbotProps {
  batchId: string;
  currentPage?: string;
  comparisonBatchIds?: string[];
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  relatedBlocks?: string[];
}

export default function Chatbot({ batchId, currentPage = 'dashboard', comparisonBatchIds }: ChatbotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response: ChatQueryResponse = await chatbotApi.query({
        query: userMessage.content,
        batch_id: batchId,
        current_page: currentPage,
        comparison_batch_ids: comparisonBatchIds,
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        relatedBlocks: response.related_blocks,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chatbot error:', error);

      let errorContent = 'I apologize, but I encountered an error. Please try again.';

      if (error.response) {
        const status = error.response.status;
        if (status === 404) {
          errorContent = 'Batch not found. Please make sure you have processed documents.';
        } else if (status === 500) {
          errorContent = 'Server error. Please try again in a moment.';
        }
      } else if (error.request) {
        errorContent = 'Unable to connect. Please check if the backend is running.';
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: errorContent }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestedQuestions = [
    "What are my KPI scores?",
    "How is FSR calculated?",
    "What documents am I missing?",
    "How can I improve my scores?"
  ];

  return (
    <>
      {/* Floating Button - Premium gradient design */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-gradient-to-br from-blue-600 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white rounded-full p-4 shadow-xl transition-all duration-300 hover:scale-110 hover:shadow-2xl group"
          aria-label="Open AI Assistant"
        >
          <div className="relative">
            <MessageCircle className="w-6 h-6" />
            <Sparkles className="w-3 h-3 absolute -top-1 -right-1 text-yellow-300 animate-pulse" />
          </div>
        </button>
      )}

      {/* Chat Window - Modern glass-morphism design */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[400px] h-[550px] bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl flex flex-col border border-gray-200/50 overflow-hidden">

          {/* Header - Gradient with blur */}
          <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 text-white px-5 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
                <Bot className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">Smart Approval AI</h3>
                <p className="text-xs text-blue-100">Ask anything about your data</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="w-8 h-8 flex items-center justify-center hover:bg-white/20 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 bg-gradient-to-b from-gray-50 to-white">

            {/* Welcome Message */}
            {messages.length === 0 && (
              <div className="space-y-4">
                <div className="text-center py-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                    <Bot className="w-8 h-8 text-blue-600" />
                  </div>
                  <h4 className="font-semibold text-gray-800 mb-1">Hello! I'm your AI Assistant</h4>
                  <p className="text-sm text-gray-500">
                    I can help you understand your KPIs, approval status, and more.
                  </p>
                </div>

                {/* Suggested Questions */}
                <div className="space-y-2">
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide px-1">Try asking:</p>
                  <div className="grid grid-cols-1 gap-2">
                    {suggestedQuestions.map((q, i) => (
                      <button
                        key={i}
                        onClick={() => { setInput(q); inputRef.current?.focus(); }}
                        className="text-left text-sm px-3 py-2 bg-white border border-gray-200 rounded-xl hover:border-blue-300 hover:bg-blue-50 transition-all text-gray-700 hover:text-blue-700"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Chat Messages */}
            {messages.map((message, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gradient-to-br from-gray-100 to-gray-200 text-gray-600'
                  }`}>
                  {message.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Message Bubble */}
                <div
                  className={`max-w-[75%] rounded-2xl px-4 py-3 ${message.role === 'user'
                      ? 'bg-blue-600 text-white rounded-br-md'
                      : 'bg-white text-gray-800 border border-gray-100 shadow-sm rounded-bl-md'
                    }`}
                  style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}
                >
                  {message.role === 'user' ? (
                    <p className="text-sm leading-relaxed">{message.content}</p>
                  ) : (
                    <div className="text-sm leading-relaxed prose prose-sm max-w-none overflow-hidden">
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1 text-gray-700">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                          li: ({ children }) => <li className="ml-1">{children}</li>,
                          code: ({ children }) => (
                            <code className="bg-gray-100 text-blue-700 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
                          ),
                          strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                          h1: ({ children }) => <h1 className="text-base font-bold mb-2 text-gray-900">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-sm font-bold mb-2 text-gray-900">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-sm font-semibold mb-1 text-gray-800">{children}</h3>,
                          blockquote: ({ children }) => (
                            <blockquote className="border-l-3 border-blue-400 pl-3 italic my-2 text-gray-600">{children}</blockquote>
                          ),
                          table: ({ children }) => (
                            <div className="overflow-x-auto my-2">
                              <table className="w-full border-collapse text-xs">{children}</table>
                            </div>
                          ),
                          th: ({ children }) => <th className="border border-gray-200 px-2 py-1 bg-gray-50 font-semibold text-left">{children}</th>,
                          td: ({ children }) => <td className="border border-gray-200 px-2 py-1">{children}</td>,
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>

                      {/* Citations */}
                      {message.citations && message.citations.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-gray-100">
                          <p className="text-xs font-medium text-gray-400 mb-1">Sources</p>
                          <div className="flex flex-wrap gap-1">
                            {message.citations.map((citation, cIdx) => (
                              <span
                                key={cIdx}
                                className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full"
                              >
                                {citation}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-gray-600" />
                </div>
                <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    <span className="text-sm text-gray-500">Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area - Clean design */}
          <div className="px-4 py-3 border-t border-gray-100 bg-white">
            <div className="flex gap-2 items-center">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question..."
                className="flex-1 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm placeholder:text-gray-400 transition-all"
                disabled={loading}
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="w-10 h-10 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 text-white rounded-xl flex items-center justify-center transition-all disabled:cursor-not-allowed shadow-sm hover:shadow-md"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
