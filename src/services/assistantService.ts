import { supabase } from '@/utils/supabase';
import { apiUrl } from '@/utils/apiBase';

const runtimeEnv = (globalThis as any).__APP_ENV__ || {}
const supabaseUrl = () => runtimeEnv.VITE_SUPABASE_URL || import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = () => runtimeEnv.VITE_SUPABASE_ANON_KEY || import.meta.env.VITE_SUPABASE_ANON_KEY
const edgeFunctionHeaders = (accessToken: string) => {
  const anonKey = supabaseAnonKey()
  return {
    'Content-Type': 'application/json',
    ...(anonKey ? { apikey: anonKey } : {}),
    Authorization: `Bearer ${accessToken}`,
  }
}

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

  async deleteSession(sessionId: string) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('User not logged in');

    const response = await fetch(apiUrl(`/api/assistant/sessions/${sessionId}/`), {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });

    if (!response.ok) {
      let message = `Delete session failed: ${response.status}`;
      try {
        const text = await response.text();
        if (text) {
          try {
            const data = JSON.parse(text);
            message = data.error || data.detail || text;
          } catch {
            message = text;
          }
        }
      } catch {
        // Keep fallback message.
      }
      throw new Error(message);
    }
  },

  async generateImage(prompt: string, model?: string) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('User not logged in');

    try {
      const response = await fetch(apiUrl('/api/assistant/generate-image/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ prompt, model }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Image generation failed: ${response.status} ${response.statusText} - ${errorText}`);
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

    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(apiUrl('/api/community/media/'), {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
      body: formData,
    });

    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.error || `Image upload failed: ${response.status}`);

    return data.urls?.[0] || data.items?.[0]?.url;
  },

  async analyzeImage(imageUrl: string, prompt?: string) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('User not logged in');

    const functionUrl = import.meta.env.DEV 
      ? '/functions/v1/analyze-image' 
      : `${supabaseUrl()}/functions/v1/analyze-image`;

    const response = await fetch(functionUrl, {
      method: 'POST',
      headers: edgeFunctionHeaders(session.access_token),
      body: JSON.stringify({ imageUrl, prompt }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Analyze function failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    return data.content;
  },

  async chat(messages: { role: string; content: string }[], model?: string, enableKnowledgeBase: boolean = false, providerId?: string) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('User not logged in');

    const anonKey = supabaseAnonKey();
    
    try {
      // 1. 调用 Supabase Edge Function (而不是直接调用智谱AI)
      // 注意：本地开发时如果使用 Vite 代理，可以使用 /functions/v1/chat
      // 如果已部署到线上，则使用 import.meta.env.VITE_SUPABASE_URL + /functions/v1/chat
      
      // FIX: 强制使用 Django 后端的 RAG 接口
      const functionUrl = apiUrl('/api/rag/chat/'); 
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
          enableKnowledgeBase
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
