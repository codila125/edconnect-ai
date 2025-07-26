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
    return <div>Loading chat...</div>;
  }

  return (
    <div>
      <h3>Class Chat - {classId}</h3>
      
      <div>
        {messages.length === 0 ? (
          <p>No messages yet. Start the conversation!</p>
        ) : (
          messages.map((msg) => (
            <div key={msg.id}>
              <strong>
                {msg.user_id === currentUserId ? 'You' : (msg.user_name || `User ${msg.user_id.slice(0, 8)}`)}
              </strong>
              <small> ({formatTime(msg.created_at)})</small>
              <p>{msg.message}</p>
              <hr />
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage}>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type your message..."
          maxLength={500}
        />
        <button type="submit" disabled={!newMessage.trim()}>
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatModule;