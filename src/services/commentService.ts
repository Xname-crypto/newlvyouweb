import { supabase } from '@/utils/supabase';

export interface Comment {
  id: number;
  post_id: number;
  user_id: string;
  content: string;
  created_at: string;
  profiles?: {
    username: string;
    avatar_url: string;
  };
}

export const commentService = {
  /**
   * Fetch comments for a specific post
   */
  async fetchComments(postId: number) {
    try {
      console.log('Fetching comments for post:', postId);
      const { data: { user } } = await supabase.auth.getUser();

      const { data, error } = await supabase
        .from('comments')
        .select(`
          *,
          profiles:user_id (
            username,
            avatar_url
          ),
          likes:interactions(count)
        `)
        .eq('post_id', postId)
        .eq('interactions.type', 'like') // Only count likes
        .order('created_at', { ascending: true });

      if (error) throw error;

      // Transform data to include like count and user status
      const commentIds = data.map(c => c.id);
      let userLikes = new Set();

      if (user && commentIds.length > 0) {
        const { data: likes } = await supabase
          .from('interactions')
          .select('comment_id')
          .in('comment_id', commentIds)
          .eq('user_id', user.id)
          .eq('type', 'like');
        
        if (likes) {
            likes.forEach(l => userLikes.add(l.comment_id));
        }
      }

      const enrichedData = data.map((comment: any) => {
        const likeCount = comment.likes?.[0]?.count || 0;
        return {
          ...comment,
          like_count: likeCount,
          is_liked: userLikes.has(comment.id)
        };
      });

      console.log('Fetched comments:', enrichedData);
      return enrichedData;
    } catch (error) {
      console.error('Error fetching comments:', error);
      return [];
    }
  },

  /**
   * Add a new comment to a post
   */
  async addComment(postId: number, content: string, parentId?: number) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { data, error } = await supabase
        .from('comments')
        .insert({
          post_id: postId,
          user_id: user.id,
          content: content,
          parent_id: parentId || null
        })
        .select(`
          *,
          profiles:user_id (
            username,
            avatar_url
          )
        `)
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error adding comment:', error);
      throw error;
    }
  },

  /**
   * Delete a comment (Soft Delete)
   */
  async deleteComment(commentId: number) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      const { error } = await supabase
        .from('comments')
        .update({ 
          is_deleted: true,
          deleted_at: new Date().toISOString(),
          deleted_by: user.id
        })
        .eq('id', commentId);

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error deleting comment:', error);
      throw error;
    }
  }
};
