import { supabase } from '@/utils/supabase';

export const notificationService = {
  /**
   * Fetch likes and collects on current user's posts AND comments
   */
  async fetchLikesAndCollects() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      // 1. Get user's post IDs
      const { data: posts } = await supabase
        .from('posts')
        .select('id')
        .eq('user_id', user.id);
      
      const postIds = posts ? posts.map(p => p.id) : [];

      // 2. Get user's comment IDs
      const { data: comments } = await supabase
        .from('comments')
        .select('id')
        .eq('user_id', user.id);
      
      const commentIds = comments ? comments.map(c => c.id) : [];

      // 3. Get interactions:
      // - Likes/Collects on user's posts
      // - Likes on user's comments
      // Excluding self-interactions
      const { data, error } = await supabase
        .from('interactions')
        .select(`
          *,
          profiles:user_id (username, avatar_url),
          posts:post_id (title, media_urls),
          comments:comment_id (content)
        `)
        .or(`post_id.in.(${postIds.length ? postIds.join(',') : '0'}),comment_id.in.(${commentIds.length ? commentIds.join(',') : '0'})`)
        .neq('user_id', user.id) // Filter out self-interactions
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data || [];
    } catch (error) {
      console.error('Error fetching interactions:', error);
      return [];
    }
  },

  /**
   * Fetch comments on current user's posts or replies to user
   */
  async fetchCommentsAndMentions() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      // 1. Get user's post IDs
      const { data: posts } = await supabase
        .from('posts')
        .select('id')
        .eq('user_id', user.id);
      
      const postIds = posts ? posts.map(p => p.id) : [];

      // 2. Fetch comments where:
      // - post_id is in user's posts (someone commented on my post)
      // - OR parent_id is one of user's comments (someone replied to me)
      
      // Get IDs of comments made by the user
      const { data: myComments } = await supabase
        .from('comments')
        .select('id')
        .eq('user_id', user.id);
        
      const myCommentIds = myComments ? myComments.map(c => c.id) : [];

      const { data, error } = await supabase
        .from('comments')
        .select(`
          *,
          profiles:user_id (username, avatar_url),
          posts:post_id (title, media_urls)
        `)
        .or(`post_id.in.(${postIds.length ? postIds.join(',') : '0'}),parent_id.in.(${myCommentIds.length ? myCommentIds.join(',') : '0'})`)
        .neq('user_id', user.id) // Filter out self-comments
        .order('created_at', { ascending: false });

      if (error) throw error;
      
      // Mark replies specifically
      const enhancedData = data?.map(comment => ({
          ...comment,
          is_reply: myCommentIds.includes(comment.parent_id)
      }));

      return enhancedData || [];
    } catch (error) {
      console.error('Error fetching comments:', error);
      return [];
    }
  },

  /**
   * Fetch new followers
   */
  async fetchNewFollowers() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return [];

      const { data, error } = await supabase
        .from('follows')
        .select(`
          *,
          profiles:follower_id (id, username, avatar_url, bio)
        `)
        .eq('following_id', user.id)
        .order('created_at', { ascending: false });

      if (error) throw error;

      // Check if I am following them back
      // Get list of users I follow
      const { data: myFollowing } = await supabase
        .from('follows')
        .select('following_id')
        .eq('follower_id', user.id);
      
      const myFollowingIds = new Set(myFollowing?.map(f => f.following_id));

      const enhancedData = data?.map(follow => ({
          ...follow,
          is_following: myFollowingIds.has(follow.follower_id)
      }));

      return enhancedData || [];
    } catch (error) {
      console.error('Error fetching followers:', error);
      return [];
    }
  },

  /**
   * Fetch unread counts
   */
  async fetchUnreadCounts() {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return { total: 0, likes: 0, comments: 0, follows: 0 };

      const { data, error } = await supabase
        .from('notifications')
        .select('type')
        .eq('user_id', user.id)
        .eq('is_read', false);

      if (error) throw error;

      const counts = {
        total: data.length,
        likes: data.filter(n => n.type === 'like' || n.type === 'collect').length,
        comments: data.filter(n => n.type === 'comment').length,
        follows: data.filter(n => n.type === 'follow').length
      };

      return counts;
    } catch (error) {
      console.error('Error fetching unread counts:', error);
      return { total: 0, likes: 0, comments: 0, follows: 0 };
    }
  },

  /**
   * Mark notifications as read
   */
  async markAsRead(type?: 'like' | 'comment' | 'follow') {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      let query = supabase
        .from('notifications')
        .update({ is_read: true })
        .eq('user_id', user.id)
        .eq('is_read', false);

      if (type) {
        if (type === 'like') {
           query = query.in('type', ['like', 'collect']);
        } else {
           query = query.eq('type', type);
        }
      }

      const { error } = await query;
      if (error) throw error;
    } catch (error) {
      console.error('Error marking notifications as read:', error);
    }
  },

  /**
   * Follow a user
   */
  async followUser(userId: string) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { error } = await supabase
        .from('follows')
        .insert({
          follower_id: user.id,
          following_id: userId
        });

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error following user:', error);
      throw error;
    }
  },

  /**
   * Unfollow a user
   */
  async unfollowUser(userId: string) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error('Not authenticated');

      const { error } = await supabase
        .from('follows')
        .delete()
        .eq('follower_id', user.id)
        .eq('following_id', userId);

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error unfollowing user:', error);
      throw error;
    }
  },

  /**
   * Check if user is following another user
   */
  async checkFollowStatus(userId: string) {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return false;

      const { data, error } = await supabase
        .from('follows')
        .select('id')
        .eq('follower_id', user.id)
        .eq('following_id', userId)
        .single();

      if (error && error.code !== 'PGRST116') throw error;
      return !!data;
    } catch (error) {
      console.error('Error checking follow status:', error);
      return false;
    }
  }
};
