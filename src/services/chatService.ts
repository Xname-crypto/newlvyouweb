// src/services/chatService.ts
import { supabase } from '@/utils/supabase';

export interface Message {
  id: number;
  sender_id: string;
  receiver_id: string;
  content: string;
  type: 'text' | 'image';
  created_at: string;
  is_read?: boolean;
}

export const chatService = {
  /**
   * Subscribe to new messages for a specific user
   */
  subscribeToMessages(userId: string, callback: (msg: Message) => void) {
    return supabase
      .channel(`chat:${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
          filter: `receiver_id=eq.${userId}`
        },
        (payload) => {
          callback(payload.new as Message);
        }
      )
      .subscribe();
  },

  /**
   * Send a message (text or image)
   */
  async sendMessage(receiverId: string, content: string, type: 'text' | 'image' = 'text') {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('Not authenticated');

    return await supabase
      .from('messages')
      .insert({
        sender_id: user.id,
        receiver_id: receiverId,
        content,
        type
      })
      .select()
      .single();
  },

  /**
   * Get message history with a specific user
   */
  async getMessages(otherUserId: string) {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return [];

    const { data, error } = await supabase
      .from('messages')
      .select('*')
      .or(`and(sender_id.eq.${user.id},receiver_id.eq.${otherUserId}),and(sender_id.eq.${otherUserId},receiver_id.eq.${user.id})`)
      .order('created_at', { ascending: true });

    if (error) throw error;
    return data as Message[];
  },

  /**
   * Mark messages as read from a specific sender
   */
  async markAsRead(senderId: string) {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    await supabase
      .from('messages')
      .update({ is_read: true })
      .eq('sender_id', senderId)
      .eq('receiver_id', user.id)
      .eq('is_read', false);
  },

  /**
   * Get unread message counts grouped by sender
   */
  async getUnreadCounts() {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return {};

    const { data, error } = await supabase
      .from('messages')
      .select('sender_id')
      .eq('receiver_id', user.id)
      .eq('is_read', false);

    if (error) {
      console.error('Error fetching unread counts:', error);
      return {};
    }

    const counts: Record<string, number> = {};
    data.forEach((msg: any) => {
      counts[msg.sender_id] = (counts[msg.sender_id] || 0) + 1;
    });
    return counts;
  },

  /**
   * Get the last message for contacts efficiently
   * Fetches the most recent 500 messages for the current user and groups them by contact
   */
  async getLastMessagesEfficiently(contactIds: string[]) {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return {};

    // Fetch recent messages involving the current user
    const { data, error } = await supabase
      .from('messages')
      .select('*')
      .or(`sender_id.eq.${user.id},receiver_id.eq.${user.id}`)
      .order('created_at', { ascending: false })
      .limit(500); // Reasonable limit to get recent conversations

    if (error) {
      console.error('Error fetching recent messages:', error);
      return {};
    }

    const lastMessages: Record<string, Message> = {};
    const processedContacts = new Set<string>();

    // Process messages to find the latest one for each contact
    data.forEach((msg: Message) => {
      const contactId = msg.sender_id === user.id ? msg.receiver_id : msg.sender_id;
      
      // Only process if it's one of our target contacts and we haven't found their last message yet
      if (contactIds.includes(contactId) && !processedContacts.has(contactId)) {
        lastMessages[contactId] = msg;
        processedContacts.add(contactId);
      }
    });

    return lastMessages;
  },

  /**
   * Get all staff users (admin and moderator) for chat list
   */
  async getContacts() {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return [];

    const { data, error } = await supabase
      .from('profiles')
      .select('id, username, avatar_url, job, role')
      .neq('id', user.id) // Exclude self
      .in('role', ['admin', 'moderator']) // Only fetch staff
      .limit(50);

    if (error) throw error;
    return data;
  }
};
