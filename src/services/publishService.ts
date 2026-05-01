import { supabase } from '@/utils/supabase';

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
  /**
   * Uploads a file to Supabase Storage
   */
  async uploadFile(file: File): Promise<string | null> {
    try {
      const fileExt = file.name.split('.').pop();
      const fileName = `${Date.now()}-${Math.random()}.${fileExt}`;
      const filePath = `${fileName}`;

      const { error: uploadError } = await supabase.storage
        .from('media') // Ensure 'media' bucket exists
        .upload(filePath, file);

      if (uploadError) throw uploadError;

      const { data } = supabase.storage.from('media').getPublicUrl(filePath);
      return data.publicUrl;
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
        user_id: user.id,
        title: params.title,
        content: params.content,
        type: params.type,
        media_urls: mediaUrls,
        status: params.status || 'published',
      };

      let result;
      
      if (params.id) {
        // Update existing post
        const { data, error } = await supabase
          .from('posts')
          .update(postData)
          .eq('id', params.id)
          .select()
          .single();
          
        if (error) throw error;
        result = data;
      } else {
        // Create new post
        const { data, error } = await supabase
          .from('posts')
          .insert(postData)
          .select()
          .single();
          
        if (error) throw error;
        result = data;
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
      const { error } = await supabase
        .from('posts')
        .delete()
        .eq('id', id);

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error deleting post:', error);
      return false;
    }
  }
};
