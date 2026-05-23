import { supabase } from '@/utils/supabase';
import { apiUrl } from '@/utils/apiBase';

export interface PublishPostParams {
  title: string;
  content?: string;
  type: 'video' | 'image' | 'article';
  files?: File[];
  media_urls?: string[]; // For existing files or pre-uploaded files
  status?: 'published' | 'draft';
  id?: string; // For updates
}

export const publishService = {
  async authHeaders(includeJson = true) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error('User not authenticated');
    return {
      ...(includeJson ? { 'Content-Type': 'application/json' } : {}),
      Authorization: `Bearer ${session.access_token}`,
    };
  },

  /**
   * Uploads a file through the Django API so file type, size and content are
   * validated server-side before storage.
   */
  async uploadFile(file: File): Promise<string | null> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch(apiUrl('/api/community/media/'), {
        method: 'POST',
        headers: await this.authHeaders(false),
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `Upload failed: ${response.status}`);
      }

      const data = await response.json();
      return data.urls?.[0] || data.items?.[0]?.url || null;
    } catch (error) {
      console.error('Error uploading file:', error);
      return null;
    }
  },

  /**
   * Creates or updates a post in the database
   */
  async createPost(params: PublishPostParams) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      // 1. Upload new files if any
      const mediaUrls: string[] = params.media_urls || [];
      if (params.files && params.files.length > 0) {
        for (const file of params.files) {
          const url = await this.uploadFile(file);
          if (url) mediaUrls.push(url);
        }
      }

      const postData = {
        title: params.title,
        content: params.content,
        type: params.type,
        media_urls: mediaUrls,
        status: params.status || 'published',
      };

      let response: Response;
      
      if (params.id) {
        response = await fetch(apiUrl(`/api/community/posts/${params.id}/`), {
          method: 'PATCH',
          headers: await this.authHeaders(),
          body: JSON.stringify(postData),
        });
      } else {
        response = await fetch(apiUrl('/api/community/posts/'), {
          method: 'POST',
          headers: await this.authHeaders(),
          body: JSON.stringify(postData),
        });
      }

      const result = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(result?.error || `Post save failed: ${response.status}`);
      }
      return result;
    } catch (error) {
      console.error('Error creating/updating post:', error);
      throw error;
    }
  },

  /**
   * Fetches all published posts with user profiles (for community feed)
   */
  async fetchPosts() {
    try {
      const { data, error } = await supabase
        .from('posts')
        .select(`
          *,
          profiles:user_id (
            username,
            avatar_url
          )
        `)
        .eq('status', 'published') // Only fetch published posts
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching posts:', error);
      return [];
    }
  },

  /**
   * Fetches posts for the current user (published and drafts)
   */
  async fetchUserPosts() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { data, error } = await supabase
        .from('posts')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching user posts:', error);
      return [];
    }
  },

  /**
   * Fetches a single post by ID
   */
  async getPostById(id: string) {
    try {
      const { data, error } = await supabase
        .from('posts')
        .select('*')
        .eq('id', id)
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching post:', error);
      return null;
    }
  },

  /**
   * Deletes a post
   */
  async deletePost(id: string) {
    try {
      const response = await fetch(apiUrl(`/api/community/posts/${id}/`), {
        method: 'DELETE',
        headers: await this.authHeaders(false),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || `Delete failed: ${response.status}`);
      }
      return true;
    } catch (error) {
      console.error('Error deleting post:', error);
      return false;
    }
  }
};
