'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  type?: 'text' | 'health-data' | 'recommendations' | 'notification';
  healthData?: {
    title: string;
    metrics: {
      name: string;
      value: string;
      status?: 'normal' | 'warning' | 'critical';
      change?: number;
    }[];
  };
  recommendations?: {
    category: string;
    items: string[];
  }[];
}

const ChatComponent = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m your Advanced Health AI Assistant. I can help analyze your health data, provide personalized insights, and answer questions about your wellbeing. How can I assist you today?',
      isUser: false,
      timestamp: new Date(),
      type: 'text'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [showHealthSummary, setShowHealthSummary] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Generate a random session ID when the component mounts
  useEffect(() => {
    setSessionId(`session-${Math.random().toString(36).substring(2, 9)}`);
  }, []);

  // Auto-scroll to the bottom of the chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize input field
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      isUser: true,
      timestamp: new Date(),
      type: 'text'
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setIsExpanded(false);
    
    try {
      // Make actual API call to the backend
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId
        }),
      });
      
      if (!response.ok) {
        throw new Error(`API call failed with status: ${response.status}`);
      }
      
      const data = await response.json();
      const responseText = data.response;
      
      let aiResponse: Message;
      
      // Try to detect message type from response content
      if (responseText.includes('recommendations') || responseText.includes('Recommendations')) {
        // Extract recommendations using regex or other parsing if needed
        // For now, we'll use a simple check
        const recommendationSections = responseText.split(/\d+\.\s+[A-Z]/);
        const recommendationItems: Array<{category: string, items: string[]}> = [];
        
        if (recommendationSections.length > 1) {
          // There are numbered recommendation sections
          let currentSection = '';
          for (let i = 1; i < recommendationSections.length; i++) {
            const section = recommendationSections[i];
            const categoryMatch = responseText.match(new RegExp(`\\d+\\.\\s+([A-Za-z\\s]+):`));
            const category = categoryMatch ? categoryMatch[1] : `Recommendation ${i}`;
            
            const items = section
              .split('\n')
              .filter((line: string) => line.trim().startsWith('-') || line.trim().startsWith('•'))
              .map((line: string) => line.replace(/^[-•]\s+/, '').trim())
              .filter((item: string) => item.length > 0);
            
            if (items.length > 0) {
              recommendationItems.push({
                category,
                items
              });
            }
          }
        }
        
        if (recommendationItems.length > 0) {
          aiResponse = {
            id: (Date.now() + 1).toString(),
            content: responseText.split('\n')[0] || 'Based on your health data, here are some recommendations:',
            isUser: false,
            timestamp: new Date(),
            type: 'recommendations',
            recommendations: recommendationItems
          };
        } else {
          // Fallback to text if parsing failed
          aiResponse = {
            id: (Date.now() + 1).toString(),
            content: responseText,
            isUser: false,
            timestamp: new Date(),
            type: 'text'
          };
        }
      } else if (responseText.includes('Analysis') && (responseText.includes('mg/dL') || responseText.includes('mmHg'))) {
        // Detect health data
        // Try to extract metrics
        const metrics: Array<{name: string, value: string, status?: 'normal' | 'warning' | 'critical', change?: number}> = [];
        
        const lines = responseText.split('\n');
        for (const line of lines) {
          // Match lines like "- Cholesterol: 200 mg/dL (Normal range: <200, Status: normal)"
          const metricMatch = line.match(/[-•]?\s*([^:]+):\s*([0-9.]+\s*[a-zA-Z/%]+)\s*(?:\(([^)]+)\))?/);
          if (metricMatch) {
            const name = metricMatch[1].trim();
            const value = metricMatch[2].trim();
            const details = metricMatch[3] || '';
            
            let status: 'normal' | 'warning' | 'critical' = 'normal';
            if (details.toLowerCase().includes('elevated') || details.toLowerCase().includes('high')) {
              status = 'warning';
            } else if (details.toLowerCase().includes('critical') || details.toLowerCase().includes('severe')) {
              status = 'critical';
            }
            
            metrics.push({ name, value, status });
          }
        }
        
        if (metrics.length > 0) {
          aiResponse = {
            id: (Date.now() + 1).toString(),
            content: lines[0] || 'Health Analysis:',
            isUser: false,
            timestamp: new Date(),
            type: 'health-data',
            healthData: {
              title: responseText.split('\n')[0] || 'Health Metrics Analysis',
              metrics
            }
          };
        } else {
          // Fallback to text
          aiResponse = {
            id: (Date.now() + 1).toString(),
            content: responseText,
            isUser: false,
            timestamp: new Date(),
            type: 'text'
          };
        }
      } else {
        // Regular text response
        aiResponse = {
          id: (Date.now() + 1).toString(),
          content: responseText,
          isUser: false,
          timestamp: new Date(),
          type: 'text'
        };
      }
      
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'I apologize, but I encountered an issue while processing your request. Please try again or check your connection.',
        isUser: false,
        timestamp: new Date(),
        type: 'text'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Example medical topics
  const exampleQueries = [
    "What does my recent blood test show?",
    "What health recommendations do you have?",
    "Analyze my sleep patterns",
    "How are my vital signs trending?",
    "What's my risk for heart disease?",
    "Can you explain my cholesterol levels?"
  ];

  // Render different message types
  const renderMessage = (message: Message) => {
    if (message.type === 'health-data' && message.healthData) {
      return (
        <div className="space-y-3">
          <p className="font-[350] text-[15px]">{message.content}</p>
          <div className="bg-white/50 dark:bg-neutral-800/50 rounded-xl p-3 border border-neutral-200 dark:border-neutral-700">
            <h4 className="font-medium text-sm text-neutral-900 dark:text-white mb-2">{message.healthData.title}</h4>
            <div className="space-y-2">
              {message.healthData.metrics.map((metric, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className={`w-2 h-2 rounded-full mr-2 ${
                      metric.status === 'normal' ? 'bg-green-500' : 
                      metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></span>
                    <span className="text-sm text-neutral-700 dark:text-neutral-300">{metric.name}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-sm font-medium mr-2">{metric.value}</span>
                    {metric.change !== undefined && (
                      <span className={`text-xs ${
                        metric.change > 0 ? 'text-red-500' : 'text-green-500'
                      }`}>
                        {metric.change > 0 ? `↑${metric.change}%` : `↓${Math.abs(metric.change)}%`}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    } else if (message.type === 'recommendations' && message.recommendations) {
      return (
        <div className="space-y-3">
          <p className="font-[350] text-[15px]">{message.content}</p>
          <div className="space-y-3">
            {message.recommendations.map((rec, idx) => (
              <div key={idx} className="bg-white/50 dark:bg-neutral-800/50 rounded-xl p-3 border border-neutral-200 dark:border-neutral-700">
                <h4 className="font-medium text-sm text-primary mb-2">{rec.category}</h4>
                <ul className="space-y-1.5">
                  {rec.items.map((item, itemIdx) => (
                    <li key={itemIdx} className="text-sm text-neutral-700 dark:text-neutral-300 flex items-start">
                      <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary/10 text-primary mr-2 flex-shrink-0 mt-0.5">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                          <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                        </svg>
                      </span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      );
    } else {
      return <div className="whitespace-pre-wrap font-[350] text-[15px]">{message.content}</div>;
    }
  };

  return (
    <div className="glass rounded-2xl backdrop-blur h-[calc(100vh-10rem)] md:h-[calc(100vh-12rem)] flex flex-col overflow-hidden relative">
      {/* Health Summary Panel */}
      <AnimatePresence>
        {showHealthSummary && (
          <motion.div 
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            className="absolute inset-0 bg-white dark:bg-neutral-900 z-10 flex flex-col"
          >
            <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
              <h3 className="font-semibold text-lg">Your Health Dashboard</h3>
              <button 
                onClick={() => setShowHealthSummary(false)}
                className="p-2 text-neutral-500 hover:text-primary rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4 border border-neutral-200 dark:border-neutral-700">
                  <h4 className="font-medium text-sm text-neutral-500 mb-2">Recent Trends</h4>
                  <div className="h-40 bg-neutral-100 dark:bg-neutral-700 rounded-lg flex items-center justify-center">
                    <span className="text-sm text-neutral-500">Health trend visualization</span>
                  </div>
                </div>
                <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4 border border-neutral-200 dark:border-neutral-700">
                  <h4 className="font-medium text-sm text-neutral-500 mb-2">Key Metrics</h4>
                  <div className="space-y-2">
                    {[
                      { name: 'Blood Glucose', value: '102 mg/dL', status: 'warning' },
                      { name: 'Blood Pressure', value: '122/78 mmHg', status: 'normal' },
                      { name: 'Resting Heart Rate', value: '68 bpm', status: 'normal' },
                      { name: 'Total Cholesterol', value: '195 mg/dL', status: 'normal' }
                    ].map((metric, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-neutral-50 dark:bg-neutral-700/50 rounded-lg">
                        <div className="flex items-center">
                          <span className={`w-2 h-2 rounded-full mr-2 ${
                            metric.status === 'normal' ? 'bg-green-500' : 
                            metric.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                          }`}></span>
                          <span className="text-sm text-neutral-700 dark:text-neutral-300">{metric.name}</span>
                        </div>
                        <span className="text-sm font-medium">{metric.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm p-4 border border-neutral-200 dark:border-neutral-700 md:col-span-2">
                  <h4 className="font-medium text-sm text-neutral-500 mb-2">Recent Activity</h4>
                  <div className="space-y-2">
                    {[
                      { activity: 'Morning walk', duration: '32 min', date: '2 hours ago' },
                      { activity: 'Meditation session', duration: '15 min', date: 'Yesterday' },
                      { activity: 'Blood pressure check', duration: '', date: 'Yesterday' }
                    ].map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-neutral-50 dark:bg-neutral-700/50 rounded-lg">
                        <div className="flex items-center">
                          <span className="text-sm text-neutral-700 dark:text-neutral-300">{item.activity}</span>
                          {item.duration && (
                            <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                              {item.duration}
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-neutral-500">{item.date}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Header */}
      <div className="p-4 border-b border-neutral-200 dark:border-neutral-800 flex items-center justify-between">
        <div className="flex items-center">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
              </svg>
            </div>
            <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-white dark:border-neutral-900 rounded-full"></span>
          </div>
          <div className="ml-3">
            <h2 className="font-medium text-neutral-900 dark:text-white">Health AI Assistant</h2>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">Analyzing your health data</p>
          </div>
        </div>

        <div className="flex space-x-2">
          <button 
            className="p-2 text-neutral-500 hover:text-primary rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            title="View health dashboard"
            onClick={() => setShowHealthSummary(true)}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M2.25 13.5a8.25 8.25 0 018.25-8.25.75.75 0 01.75.75v6.75H18a.75.75 0 01.75.75 8.25 8.25 0 01-16.5 0z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M12.75 3a.75.75 0 01.75-.75 8.25 8.25 0 018.25 8.25.75.75 0 01-.75.75h-7.5a.75.75 0 01-.75-.75V3z" clipRule="evenodd" />
            </svg>
          </button>
          <button 
            className="p-2 text-neutral-500 hover:text-primary rounded-full hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            title="Settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
              <path fillRule="evenodd" d="M11.078 2.25c-.917 0-1.699.663-1.85 1.567L9.05 4.889c-.02.12-.115.26-.297.348a7.493 7.493 0 00-.986.57c-.166.115-.334.126-.45.083L6.3 5.508a1.875 1.875 0 00-2.282.819l-.922 1.597a1.875 1.875 0 00.432 2.385l.84.692c.095.078.17.229.154.43a7.598 7.598 0 000 1.139c.015.2-.059.352-.153.43l-.841.692a1.875 1.875 0 00-.432 2.385l.922 1.597a1.875 1.875 0 002.282.818l1.019-.382c.115-.043.283-.031.45.082.312.214.641.405.985.57.182.088.277.228.297.35l.178 1.071c.151.904.933 1.567 1.85 1.567h1.844c.916 0 1.699-.663 1.85-1.567l.178-1.072c.02-.12.114-.26.297-.349.344-.165.673-.356.985-.57.167-.114.335-.125.45-.082l1.02.382a1.875 1.875 0 002.28-.819l.923-1.597a1.875 1.875 0 00-.432-2.385l-.84-.692c-.095-.078-.17-.229-.154-.43a7.614 7.614 0 000-1.139c-.016-.2.059-.352.153-.43l.84-.692c.708-.582.891-1.59.433-2.385l-.922-1.597a1.875 1.875 0 00-2.282-.818l-1.02.382c-.114.043-.282.031-.449-.083a7.49 7.49 0 00-.985-.57c-.183-.087-.277-.227-.297-.348l-.179-1.072a1.875 1.875 0 00-1.85-1.567h-1.843zM12 15.75a3.75 3.75 0 100-7.5 3.75 3.75 0 000 7.5z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white/5">
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!message.isUser && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex-shrink-0 flex items-center justify-center text-white mr-2">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                    <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
                  </svg>
                </div>
              )}
              
              <div
                className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                  message.isUser
                    ? 'bg-gradient-to-br from-primary to-primary-dark text-white'
                    : 'bg-white dark:bg-neutral-800 shadow-sm border border-neutral-200 dark:border-neutral-700'
                }`}
              >
                {renderMessage(message)}
                <div className={`text-xs mt-1 ${message.isUser ? 'text-white/70' : 'text-neutral-500'}`}>
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
              
              {message.isUser && (
                <div className="w-8 h-8 rounded-full bg-neutral-200 dark:bg-neutral-700 flex-shrink-0 flex items-center justify-center ml-2">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-neutral-500 dark:text-neutral-300">
                    <path fillRule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </motion.div>
          ))}
          
          {isLoading && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex-shrink-0 flex items-center justify-center text-white mr-2">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                  <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
                </svg>
              </div>
              <div className="bg-white dark:bg-neutral-800 px-4 py-3 rounded-2xl shadow-sm border border-neutral-200 dark:border-neutral-700">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '300ms' }}></div>
                  <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '600ms' }}></div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-neutral-200 dark:border-neutral-800">
        <form onSubmit={handleSendMessage} className="relative">
          <div className="flex">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onFocus={() => setIsExpanded(true)}
                placeholder="Ask about your health..."
                className="w-full border border-neutral-200 dark:border-neutral-700 rounded-2xl py-3 pl-4 pr-12 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary resize-none bg-white/50 dark:bg-neutral-800/50"
                rows={1}
                style={{ maxHeight: '150px' }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (input.trim()) handleSendMessage(e);
                  }
                }}
              />
              <button
                type="submit"
                className="absolute right-2 bottom-2 p-2 text-white bg-gradient-to-br from-primary to-primary-dark rounded-xl hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={isLoading || !input.trim()}
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                  <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                </svg>
              </button>
            </div>
            
            <button
              type="button"
              onClick={() => setIsVoiceActive(!isVoiceActive)}
              className={`ml-2 p-3 rounded-xl flex-shrink-0 focus:outline-none focus:ring-2 focus:ring-primary transition-colors ${
                isVoiceActive 
                  ? 'bg-red-500 text-white hover:bg-red-600' 
                  : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-500 hover:bg-neutral-200 dark:hover:bg-neutral-700'
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M8.25 4.5a3.75 3.75 0 117.5 0v8.25a3.75 3.75 0 11-7.5 0V4.5z" />
                <path d="M6 10.5a.75.75 0 01.75.75v1.5a5.25 5.25 0 1010.5 0v-1.5a.75.75 0 011.5 0v1.5a6.751 6.751 0 01-6 6.709v2.291h3a.75.75 0 010 1.5h-7.5a.75.75 0 010-1.5h3v-2.291a6.751 6.751 0 01-6-6.709v-1.5A.75.75 0 016 10.5z" />
              </svg>
            </button>
          </div>
          
          {/* Example queries */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 overflow-hidden"
              >
                <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-2">
                  Try asking about:
                </p>
                <div className="flex flex-wrap gap-2">
                  {exampleQueries.map((query, index) => (
                    <button
                      key={index}
                      onClick={() => setInput(query)}
                      className="text-xs py-1.5 px-3 bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-full text-neutral-700 dark:text-neutral-300 hover:bg-primary/5 hover:text-primary transition-colors"
                    >
                      {query}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </form>
      </div>
    </div>
  );
};

export default ChatComponent; 