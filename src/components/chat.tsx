import React, { useState, useEffect, useRef } from 'react';
import { supabase } from '@/lib/supabase';

interface ChatMessage {
  id: string;
  message: string;
  user_id: string;
  class_id: string;
  created_at: string;
  user_name?: string;
}

interface ChatModuleProps {
  classId: string;
  currentUserId: string;
  currentUserName?: string;
}

const ChatModule: React.FC<ChatModuleProps> = ({
  classId,
  currentUserId,
  currentUserName = 'User'
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch existing messages
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const { data, error } = await supabase
          .from('chat_messages')
          .select('*')
          .eq('class_id', classId)
          .order('created_at', { ascending: true });

        if (error) throw error;
        setMessages(data || []);
      } catch (error) {
        console.error('Error fetching messages:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMessages();
  }, [classId]);

  // Set up realtime subscription
  useEffect(() => {
    const channel = supabase
      .channel(`chat_${classId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'chat_messages',
          filter: `class_id=eq.${classId}`,
        },
        (payload) => {
          const newMessage = payload.new as ChatMessage;
          setMessages(prev => [...prev, newMessage]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [classId]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      const { error } = await supabase
        .from('chat_messages')
        .insert({
          message: newMessage.trim(),
          user_id: currentUserId,
          class_id: classId,
          user_name: currentUserName,
        });

      if (error) throw error;
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message');
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="w-8 h-8 border-3 border-slate-200 rounded-full"></div>
              <div className="absolute top-0 left-0 w-8 h-8 border-3 border-emerald-600 rounded-full animate-spin border-t-transparent"></div>
            </div>
          </div>
          <p className="text-slate-500 text-sm">Loading chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-96">
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto mb-4 bg-slate-50/50 rounded-xl p-4 border border-slate-200">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <svg className="w-12 h-12 text-slate-300 mx-auto mb-3" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4v3c0 .6.4 1 1 1 .2 0 .5-.1.7-.3L16.4 18H20c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
              </svg>
              <p className="text-slate-400 text-sm">No messages yet. Start the conversation!</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {messages.map((msg) => (
              <div 
                key={msg.id} 
                className={`flex ${msg.user_id === currentUserId ? 'justify-end' : 'justify-start'}`}
              >
                <div 
                  className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                    msg.user_id === currentUserId
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-md'
                      : 'bg-white border border-slate-200 text-slate-800 rounded-bl-md'
                  }`}
                >
                  {/* Message Header */}
                  <div className="flex items-center justify-between mb-1">
                    <span 
                      className={`text-xs font-medium ${
                        msg.user_id === currentUserId 
                          ? 'text-blue-100' 
                          : 'text-slate-500'
                      }`}
                    >
                      {msg.user_id === currentUserId 
                        ? 'You' 
                        : (msg.user_name || `User ${msg.user_id.slice(0, 8)}`)
                      }
                    </span>
                    <span 
                      className={`text-xs ${
                        msg.user_id === currentUserId 
                          ? 'text-blue-100' 
                          : 'text-slate-400'
                      }`}
                    >
                      {formatTime(msg.created_at)}
                    </span>
                  </div>
                  
                  {/* Message Content */}
                  <p className={`text-sm leading-relaxed ${
                    msg.user_id === currentUserId ? 'text-white' : 'text-slate-700'
                  }`}>
                    {msg.message}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Input */}
      <div className="bg-white/80 backdrop-blur-sm rounded-xl border border-white/20 p-4">
        <div className="flex space-x-3">
          <div className="flex-1">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(e as any);
                }
              }}
              placeholder="Type your message..."
              maxLength={500}
              className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all duration-300 placeholder-slate-400"
            />
          </div>
          
          <button
            onClick={sendMessage}
            disabled={!newMessage.trim()}
            className="group relative overflow-hidden bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 disabled:from-slate-300 disabled:to-slate-400 text-white px-6 py-3 rounded-xl font-medium transition-all duration-300 ease-out transform hover:scale-[1.02] hover:shadow-lg active:scale-[0.98] disabled:cursor-not-allowed disabled:transform-none disabled:hover:shadow-none"
          >
            <div className="absolute inset-0 bg-white/10 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-out group-disabled:hidden"></div>
            <div className="relative flex items-center space-x-2">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
              <span className="hidden sm:inline">Send</span>
            </div>
          </button>
        </div>
        
        {/* Character Counter */}
        <div className="flex justify-between items-center mt-2 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span>Live chat</span>
          </div>
          <span>{newMessage.length}/500</span>
        </div>
      </div>
    </div>
  );
};

export default ChatModule;