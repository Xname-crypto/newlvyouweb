import { supabase } from '@/utils/supabase';
import { apiUrl } from '@/utils/apiBase';

export interface UpdateProfileParams {
  username?: string;
  bio?: string;
  avatar_url?: string;
  job?: string;
}

export const profileService = {
  /**
   * Uploads an avatar image to Supabase Storage
   */
  async uploadAvatar(file: File): Promise<string | null> {
    try {
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
      if (!response.ok) throw new Error(data?.error || `Avatar upload failed: ${response.status}`);

      return data.urls?.[0] || data.items?.[0]?.url || null;
    } catch (error) {
      console.error('Error uploading avatar:', error);
      throw error;
    }
  },

  /**
   * Updates the user's profile
   */
  async updateProfile(userId: string, updates: UpdateProfileParams) {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .update(updates)
        .eq('id', userId)
        .select()
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error updating profile:', error);
      throw error;
    }
  },

  /**
   * Fetches profile for a specific user
   */
  async fetchProfile(userId: string) {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching profile:', error);
      return null;
    }
  },

  /**
   * Fetches posts for a specific user
   */
  async fetchUserPosts(userId: string) {
    try {
      const { data, error } = await supabase
        .from('posts')
        .select('*')
        .eq('user_id', userId)
        .order('created_at', { ascending: false });

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching user posts:', error);
      return [];
    }
  },

  /**
   * Fetches posts collected by a user
   */
  async fetchCollectedPosts(userId: string) {
    try {
      const { data, error } = await supabase
        .from('interactions')
        .select(`
            post_id,
            posts:post_id (*)
        `)
        .eq('user_id', userId)
        .eq('type', 'collect')
        .order('created_at', { ascending: false });

      if (error) throw error;
      
      // Filter out null posts (in case post was deleted) and extract post data
      return data
        .filter((item: any) => item.posts)
        .map((item: any) => item.posts);
    } catch (error) {
      console.error('Error fetching collected posts:', error);
      return [];
    }
  },

  /**
   * Fetches posts liked by a user
   */
  async fetchLikedPosts(userId: string) {
    try {
      const { data, error } = await supabase
        .from('interactions')
        .select(`
            post_id,
            posts:post_id (*)
        `)
        .eq('user_id', userId)
        .eq('type', 'like')
        .order('created_at', { ascending: false });

      if (error) throw error;
      
      // Filter out null posts (in case post was deleted) and extract post data
      return data
        .filter((item: any) => item.posts)
        .map((item: any) => item.posts);
    } catch (error) {
      console.error('Error fetching liked posts:', error);
      return [];
    }
  },

  /**
   * Fetches user statistics (followers, following, likes, collects)
   */
  async fetchUserStats(userId: string) {
    try {
      // Fetch follows count (following)
      const { count: followingCount, error: followingError } = await supabase
        .from('follows')
        .select('*', { count: 'exact', head: true })
        .eq('follower_id', userId);

      if (followingError) throw followingError;

      // Fetch followers count
      const { count: followersCount, error: followersError } = await supabase
        .from('follows')
        .select('*', { count: 'exact', head: true })
        .eq('following_id', userId);

      if (followersError) throw followersError;

      // Fetch total likes received on user's posts
      // This is complex in Supabase without a join or view, so we'll approximate or fetch all user posts first
      // A better way is to have a 'likes_count' on posts table and sum it up, OR
      // query interactions table where post_id IN (user_posts_ids) AND type = 'like'
      
      // Step 1: Get user's post IDs
      const { data: userPosts, error: postsError } = await supabase
        .from('posts')
        .select('id')
        .eq('user_id', userId);
        
      if (postsError) throw postsError;
      
      const postIds = userPosts.map(p => p.id);
      
      let totalLikes = 0;
      let totalCollects = 0;
      
      if (postIds.length > 0) {
          // Step 2: Count likes for these posts
          const { count: likesCount, error: likesError } = await supabase
            .from('interactions')
            .select('*', { count: 'exact', head: true })
            .in('post_id', postIds)
            .eq('type', 'like');
            
          if (likesError) throw likesError;
          totalLikes = likesCount || 0;

          // Step 3: Count collects for these posts
          const { count: collectsCount, error: collectsError } = await supabase
            .from('interactions')
            .select('*', { count: 'exact', head: true })
            .in('post_id', postIds)
            .eq('type', 'collect');
            
          if (collectsError) throw collectsError;
          totalCollects = collectsCount || 0;
      }

      // Step 4: Get more detailed stats for dashboard
      let totalViews = 0; // In a real app, this would be summed from a 'views' column on posts
      let totalComments = 0; // Count from comments table where post_id IN user_posts
      let totalShares = 0; // Count from interactions where type = 'share'

      if (postIds.length > 0) {
          // Count comments
          const { count: commentsCount, error: commentsError } = await supabase
            .from('comments')
            .select('*', { count: 'exact', head: true })
            .in('post_id', postIds)
            .eq('is_deleted', false);
            
          if (commentsError) throw commentsError;
          totalComments = commentsCount || 0;

          // Count shares (assuming 'share' is an interaction type)
          const { count: sharesCount, error: sharesError } = await supabase
            .from('interactions')
            .select('*', { count: 'exact', head: true })
            .in('post_id', postIds)
            .eq('type', 'share');
            
          if (sharesError) throw sharesError;
          totalShares = sharesCount || 0;
      }

      // Step 5: Get follower growth stats from history (last 7 days by default)
      let newFollowers = 0;
      let unfollows = 0;
      
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      
      const { data: historyData, error: historyError } = await supabase
        .from('follows_history')
        .select('event_type')
        .eq('following_id', userId)
        .gte('created_at', sevenDaysAgo.toISOString());
        
      if (!historyError && historyData) {
        newFollowers = historyData.filter((h: any) => h.event_type === 'follow').length;
        unfollows = historyData.filter((h: any) => h.event_type === 'unfollow').length;
      }

      return {
        following: followingCount || 0,
        followers: followersCount || 0,
        likesAndCollects: totalLikes + totalCollects,
        likes: totalLikes,
        collects: totalCollects,
        comments: totalComments,
        shares: totalShares,
        views: totalViews,
        newFollowers: newFollowers,
        netFollowers: newFollowers - unfollows,
        ctr: '0%',
        completionRate: '0%',
        unfollows: unfollows,
        profileVisits: 0
      };
    } catch (error) {
      console.error('Error fetching user stats:', error);
      return {
        following: 0,
        followers: 0,
        likesAndCollects: 0,
        likes: 0,
        collects: 0,
        comments: 0,
        shares: 0,
        views: 0,
        newFollowers: 0,
        netFollowers: 0,
        ctr: '0%',
        completionRate: '0%',
        unfollows: 0,
        profileVisits: 0
      };
    }
  }
};
