import { supabase } from '@/utils/supabase';

export const interactionService = {
  /**
   * Fetch interaction stats for a post (likes, collects) and current user status
   */
  async fetchInteractions(postId: number) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      // Get counts
      const { count: likesCount } = await supabase
        .from('interactions')
        .select('*', { count: 'exact', head: true })
        .eq('post_id', postId)
        .eq('type', 'like');

      const { count: collectsCount } = await supabase
        .from('interactions')
        .select('*', { count: 'exact', head: true })
        .eq('post_id', postId)
        .eq('type', 'collect');

      let isLiked = false;
      let isCollected = false;

      // Get user status if logged in
      if (user) {
        const { data: userInteractions } = await supabase
          .from('interactions')
          .select('type')
          .eq('post_id', postId)
          .eq('user_id', user.id);

        if (userInteractions) {
          isLiked = userInteractions.some(i => i.type === 'like');
          isCollected = userInteractions.some(i => i.type === 'collect');
        }
      }

      return {
        likes: likesCount || 0,
        collects: collectsCount || 0,
        isLiked,
        isCollected
      };
    } catch (error) {
      console.error('Error fetching interactions:', error);
      return { likes: 0, collects: 0, isLiked: false, isCollected: false };
    }
  },

  /**
   * Toggle interaction (like/collect) for a post
   */
  async toggleInteraction(postId: number, type: 'like' | 'collect') {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      // Check if already exists (ensure comment_id is null for post interactions)
      const { data: existing } = await supabase
        .from('interactions')
        .select('id')
        .eq('post_id', postId)
        .is('comment_id', null) 
        .eq('user_id', user.id)
        .eq('type', type)
        .single();

      if (existing) {
        // Remove interaction
        await supabase
          .from('interactions')
          .delete()
          .eq('id', existing.id);
        return false; // Removed
      } else {
        // Add interaction
        await supabase
          .from('interactions')
          .insert({
            post_id: postId,
            user_id: user.id,
            type: type
          });
        return true; // Added
      }
    } catch (error) {
      console.error(`Error toggling ${type}:`, error);
      throw error;
    }
  },

  /**
   * Toggle like for a comment
   */
  async toggleCommentLike(commentId: number) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('User not authenticated');

      // Check if already exists
      const { data: existing } = await supabase
        .from('interactions')
        .select('id')
        .eq('comment_id', commentId)
        .eq('user_id', user.id)
        .eq('type', 'like')
        .single();

      if (existing) {
        // Remove like
        await supabase
          .from('interactions')
          .delete()
          .eq('id', existing.id);
        return false; // Removed
      } else {
        // Add like
        await supabase
          .from('interactions')
          .insert({
            comment_id: commentId,
            user_id: user.id,
            type: 'like'
            // post_id is optional/nullable now, we can leave it null for comment likes
          });
        return true; // Added
      }
    } catch (error) {
      console.error('Error toggling comment like:', error);
      throw error;
    }
  }
};
