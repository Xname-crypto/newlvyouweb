import { supabase } from '@/utils/supabase';

export interface AssistantSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface AssistantMessage {
  id: number;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  imageUrl?: string;
  created_at: string;
  latency?: number;
}

export const assistantService = {
  async getSessions() {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return [];

    const { data, error } = await supabase
      .from('assistant_sessions')
      .select('*')
      .eq('user_id', user.id)
      .order('updated_at', { ascending: false });

    if (error) {
      console.error('Error fetching sessions:', error);
      return [];
    }
    return data as AssistantSession[];
  },

  async getMessages(sessionId: string) {
    const { data, error } = await supabase
      .from('assistant_messages')
      .select('*')
      .eq('session_id', sessionId)
      .order('created_at', { ascending: true });

    if (error) {
      console.error('Error fetching messages:', error);
      return [];
    }
    return data.map((msg: any) => ({
      ...msg,
      imageUrl: msg.image_url
    })) as AssistantMessage[];
  },

  async createSession(title: string) {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) throw new Error('User not logged in');

    const { data, error } = await supabase
      .from('assistant_sessions')
      .insert({ user_id: user.id, title })
      .select()
      .single();

    if (error) throw error;
    return data as AssistantSession;
  },

  async generateImage(prompt: string, model?: string) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('User not logged in');

    // Use raw fetch with proxy to bypass CORS
    // const supabaseUrl = import.meta.env.VITE_SUPABASE_URL; // Don't use absolute URL
    const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
    
    try {
      // Use relative path so Vite proxy can handle it
      // NOTE: We need to use /functions/v1 prefix which is what we configured in vite.config.ts
      const response = await fetch(`/functions/v1/generate-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${supabaseAnonKey}`,
        },
        body: JSON.stringify({ prompt, model }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Function failed: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      return data.url;
    } catch (error) {
      console.error('Raw Fetch Error:', error);
      throw error;
    }
  },

  async uploadImage(file: File) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('User not logged in');

    // Make sure to handle non-ASCII characters in filename
    const safeName = file.name.replace(/[^\x00-\x7F]/g, "img");
    const fileName = `${session.user.id}/${Date.now()}-${safeName}`;
    
    const { data, error } = await supabase.storage
      .from('media') 
      .upload(fileName, file);

    if (error) throw error;

    const { data: { publicUrl } } = supabase.storage
      .from('media')
      .getPublicUrl(fileName);

    return publicUrl;
  },

  async analyzeImage(imageUrl: string, prompt?: string) {
    const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
    const functionUrl = import.meta.env.DEV 
      ? '/functions/v1/analyze-image' 
      : `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/analyze-image`;

    const response = await fetch(functionUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${supabaseAnonKey}`,
      },
      body: JSON.stringify({ imageUrl, prompt }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Analyze function failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    return data.content;
  },

  async chat(messages: { role: string; content: string }[], model?: string, enableWebSearch: boolean = false, providerId?: string) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('User not logged in');

    const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
    
    try {
      // 1. 调用 Supabase Edge Function (而不是直接调用智谱AI)
      // 注意：本地开发时如果使用 Vite 代理，可以使用 /functions/v1/chat
      // 如果已部署到线上，则使用 import.meta.env.VITE_SUPABASE_URL + /functions/v1/chat
      
      // FIX: 强制使用 Django 后端的 RAG 接口
      const functionUrl = '/api/rag/chat/'; 
      // const functionUrl = import.meta.env.DEV 
      //   ? '/functions/v1/chat' 
      //   : `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/chat`;

      const response = await fetch(functionUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': `Bearer ${supabaseAnonKey}`, // Django 不需要 Supabase Key，需要自己的 Auth
          'Authorization': `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`
        },
        // 适配 Django 接口参数: user_input, user_id
        body: JSON.stringify({ 
          user_input: messages[messages.length - 1].content,
          user_id: session?.user?.id || 'anonymous_user',
          messages, 
          model,
          provider_id: providerId,
          enableWebSearch
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Chat function failed: ${response.status} ${response.statusText} - ${errorText}`);
      }

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      
      return {
        content: data.response, // Django 返回的是 response
        imageUrl: undefined, // Django 暂时没返回图片
        personality: data.personality // 额外返回个性化信息
      };
    } catch (error) {
      console.error('Chat API Error:', error);
      throw error;
    }
  },

  // ... existing saveMessage method ...
  async saveMessage(sessionId: string, role: 'user' | 'assistant', content: string, imageUrl?: string) {
    const { data, error } = await supabase
      .from('assistant_messages')
      .insert({ session_id: sessionId, role, content, image_url: imageUrl }) // Note: You might need to add image_url column to DB
      .select()
      .single();

    if (error) throw error;
    
    // Update session updated_at
    await supabase
      .from('assistant_sessions')
      .update({ updated_at: new Date().toISOString() })
      .eq('id', sessionId);

    return { ...data, imageUrl: data.image_url } as AssistantMessage;
  }
};
