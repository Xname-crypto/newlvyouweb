import { ref } from 'vue';
import { safeGetSupabaseUser, supabase } from '@/utils/supabase';
import { RealtimeChannel } from '@supabase/supabase-js';

// Global state
const onlineUsers = ref(new Set<string>());
let channel: RealtimeChannel | null = null;
let isInitialized = false;

export function usePresence() {
  /**
   * Initialize presence tracking.
   * Should be called once in App.vue or a root layout.
   */
  const initPresence = async () => {
    const user = await safeGetSupabaseUser();
    
    // Only track if user is logged in
    if (!user) {
      cleanupPresence();
      return;
    }

    // If already initialized, check if it's for the same user
    if (isInitialized && channel) {
        // If we could check the key, we would. 
        // For now, let's assume if it's initialized, it's fine unless explicitly cleaned up.
        // But to be safe against user switching without page reload:
        return; 
    }
    
    // If there is an existing channel but we are re-initializing (maybe isInitialized was false but channel existed?)
    if (channel) {
        await supabase.removeChannel(channel)
    }

    // Create channel with user-specific config
    channel = supabase.channel('online-users', {
      config: {
        presence: {
          key: user.id,
        },
      },
    });

    channel
      .on('presence', { event: 'sync' }, () => {
        const state = channel?.presenceState() || {};
        const ids = new Set<string>();
        Object.keys(state).forEach(id => ids.add(id));
        onlineUsers.value = ids;
      })
      .subscribe(async (status) => {
        if (status === 'SUBSCRIBED') {
          await channel?.track({
            user_id: user.id,
            online_at: new Date().toISOString(),
          });
        }
      });
      
    isInitialized = true;
  };

  /**
   * Clean up presence channel.
   * Should be called on logout or app unmount.
   */
  const cleanupPresence = () => {
    if (channel) {
      supabase.removeChannel(channel);
      channel = null;
    }
    onlineUsers.value = new Set();
    isInitialized = false;
  };

  return {
    onlineUsers,
    initPresence,
    cleanupPresence
  };
}
