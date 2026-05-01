<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import { 
  X, Heart, Star, MessageCircle, Share2, 
  MapPin, Calendar, MoreHorizontal, Send, Loader2,
  Play, Pause, Volume2, VolumeX, Maximize, RotateCcw,
  ChevronLeft, ChevronRight
} from 'lucide-vue-next';
import { commentService } from '@/services/commentService';
import { interactionService } from '@/services/interactionService';
import { notificationService } from '@/services/notificationService';
import { supabase } from '@/utils/supabase';
import { useToast } from '@/composables/useToast';
import { DEFAULT_AVATAR } from '@/utils/avatar';

interface Post {
  id: number;
  title: string;
  image: string;
  images?: string[];
  type?: 'image' | 'video'; // Added type
  content?: string;
  tags?: string[];
  location?: string;
  date?: string;
  user: {
    id?: string;
    name: string;
    avatar: string;
    isFollowing?: boolean;
  };
  likes: number;
  stars?: number;
  comments?: number;
  isLiked?: boolean;
  isStarred?: boolean;
}

const props = defineProps<{
  post: Post;
  isOpen: boolean;
}>();

// Helper to check if url is video
const isVideo = (url: string) => {
    return url?.match(/\.(mp4|webm|ogg)$/i);
};

const DEFAULT_MEDIA_RATIO = 3 / 4;
const DESKTOP_SIDE_PANEL_WIDTH = 440;
const DESKTOP_MODAL_MARGIN = 48;
const DESKTOP_MIN_MEDIA_WIDTH = 380;

// Video controls state
const videoRef = ref<HTMLVideoElement | null>(null);
const isPlaying = ref(false); // Changed to false initially to respect autoplay policies
const isEnded = ref(false); 
const isMuted = ref(true); // Start muted to ensure autoplay works
const playbackRate = ref(1.0);
const showSpeedMenu = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const progress = ref(0);
const imageFit = ref<'contain' | 'cover'>('contain');
const currentMediaRatio = ref(DEFAULT_MEDIA_RATIO);
const viewportWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1440);
const viewportHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 900);

const imageRatioCache = new Map<string, number>();

const playbackRates = [2.0, 1.5, 1.0, 0.75, 0.5];

const updateViewport = () => {
  if (typeof window === 'undefined') return;
  viewportWidth.value = window.innerWidth;
  viewportHeight.value = window.innerHeight;
};

const readImageAspectRatio = (src: string) => new Promise<number>((resolve, reject) => {
  const image = new Image();

  image.onload = () => {
    if (image.naturalWidth && image.naturalHeight) {
      resolve(image.naturalWidth / image.naturalHeight);
      return;
    }

    resolve(DEFAULT_MEDIA_RATIO);
  };

  image.onerror = reject;
  image.src = src;
});

const setPlaybackRate = (rate: number) => {
  if (!videoRef.value) return;
  videoRef.value.playbackRate = rate;
  playbackRate.value = rate;
  showSpeedMenu.value = false;
};

const toggleFullscreen = () => {
  if (!videoRef.value) return;
  if (!document.fullscreenElement) {
    videoRef.value.requestFullscreen().catch(err => {
      console.error(`Error attempting to enable fullscreen: ${err.message}`);
    });
  } else {
    document.exitFullscreen();
  }
};

const togglePlay = () => {
  if (!videoRef.value) return;
  
  if (isEnded.value) {
    // Replay
    videoRef.value.currentTime = 0;
    videoRef.value.play();
    isEnded.value = false;
    isPlaying.value = true;
    return;
  }

  if (videoRef.value.paused) {
    videoRef.value.play();
    isPlaying.value = true;
  } else {
    videoRef.value.pause();
    isPlaying.value = false;
  }
};

const handleEnded = () => {
    isEnded.value = true;
    isPlaying.value = false;
};

const toggleMute = () => {
  if (!videoRef.value) return;
  videoRef.value.muted = !videoRef.value.muted;
  isMuted.value = videoRef.value.muted;
};

const handleVideoMount = () => {
    if (videoRef.value) {
        // Attempt to play immediately
        const playPromise = videoRef.value.play();
        if (playPromise !== undefined) {
            playPromise.then(() => {
                isPlaying.value = true;
            }).catch(error => {
                console.log("Autoplay prevented:", error);
                isPlaying.value = false;
                // If failed, user interaction will be required
            });
        }
    }
};

const resetMediaState = () => {
  currentImage.value = 0;
  imageFit.value = 'contain';
  showSpeedMenu.value = false;
  currentTime.value = 0;
  duration.value = 0;
  progress.value = 0;
  currentMediaRatio.value = DEFAULT_MEDIA_RATIO;
};

// Add watch for isOpen to trigger play when modal opens
watch(() => props.isOpen, (isOpen) => {
    if (isOpen) {
        resetMediaState();
    }

    if (isOpen && (props.post.type === 'video' || isVideo(props.post.image))) {
        // Reset state
        isEnded.value = false;
        isMuted.value = true; // Ensure muted for autoplay
        
        // Use nextTick to ensure video element is rendered
        setTimeout(handleVideoMount, 100);
    } else {
        videoRef.value?.pause();
        isPlaying.value = false; // Stop playing when closed
        showSpeedMenu.value = false;
    }
});

const handleTimeUpdate = () => {
  if (!videoRef.value) return;
  currentTime.value = videoRef.value.currentTime;
  progress.value = (videoRef.value.currentTime / videoRef.value.duration) * 100;
};

const handleLoadedMetadata = () => {
  if (!videoRef.value) return;
  duration.value = videoRef.value.duration;
  if (videoRef.value.videoWidth && videoRef.value.videoHeight) {
    currentMediaRatio.value = videoRef.value.videoWidth / videoRef.value.videoHeight;
  }
};

const handleSeek = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (!videoRef.value) return;
  const time = (parseFloat(target.value) / 100) * videoRef.value.duration;
  videoRef.value.currentTime = time;
};

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const emit = defineEmits(['close']);
const { showToast } = useToast();

const toggleImageFit = () => {
  imageFit.value = imageFit.value === 'contain' ? 'cover' : 'contain';
};

// Image swipe state
const currentImage = ref(0);
const imageList = computed(() => props.post.images && props.post.images.length > 0 ? props.post.images : (props.post.image ? [props.post.image] : []));
const displayedImage = computed(() => imageList.value[currentImage.value] || '');
const isVideoPost = computed(() => props.post.type === 'video' || isVideo(props.post.image));
const hasMultipleMedia = computed(() => imageList.value.length > 1);
const mediaCounterLabel = computed(() => hasMultipleMedia.value ? `${currentImage.value + 1} / ${imageList.value.length}` : '');
const desktopMediaWidth = computed(() => {
  if (viewportWidth.value < 768) return null;

  const modalHeight = viewportHeight.value * 0.85;
  const idealMediaWidth = modalHeight * currentMediaRatio.value;
  const maxModalWidth = Math.max(760, viewportWidth.value - DESKTOP_MODAL_MARGIN);
  const availableMediaWidth = Math.max(320, maxModalWidth - DESKTOP_SIDE_PANEL_WIDTH);
  const preferredMinWidth = Math.min(DESKTOP_MIN_MEDIA_WIDTH, availableMediaWidth);

  return Math.round(Math.min(Math.max(idealMediaWidth, preferredMinWidth), availableMediaWidth));
});
const desktopMediaStyle = computed(() => {
  if (!desktopMediaWidth.value) return undefined;
  return { width: `${desktopMediaWidth.value}px` };
});
const desktopSideStyle = computed(() => {
  if (viewportWidth.value < 768) return undefined;
  return { width: `${DESKTOP_SIDE_PANEL_WIDTH}px` };
});
const desktopModalStyle = computed(() => {
  if (!desktopMediaWidth.value) return undefined;
  return { width: `${desktopMediaWidth.value + DESKTOP_SIDE_PANEL_WIDTH}px` };
});

const syncImageRatio = async (src: string) => {
  if (!src) {
    currentMediaRatio.value = DEFAULT_MEDIA_RATIO;
    return;
  }

  if (imageRatioCache.has(src)) {
    currentMediaRatio.value = imageRatioCache.get(src)!;
    return;
  }

  try {
    const ratio = await readImageAspectRatio(src);
    imageRatioCache.set(src, ratio);

    if (displayedImage.value === src) {
      currentMediaRatio.value = ratio;
    }
  } catch {
    currentMediaRatio.value = DEFAULT_MEDIA_RATIO;
  }
};

watch([displayedImage, isVideoPost, () => props.isOpen], async ([src, video, isOpen]) => {
  if (!isOpen || video || !src) return;
  await syncImageRatio(src);
}, { immediate: true });

const goPrev = () => {
  if (imageList.value.length <= 1) return;
  currentImage.value = (currentImage.value - 1 + imageList.value.length) % imageList.value.length;
};
const goNext = () => {
  if (imageList.value.length <= 1) return;
  currentImage.value = (currentImage.value + 1) % imageList.value.length;
};

const touchStartX = ref<number | null>(null);
const touchDeltaX = ref(0);
const onTouchStart = (e: TouchEvent) => {
  touchStartX.value = e.touches[0].clientX;
  touchDeltaX.value = 0;
};
const onTouchMove = (e: TouchEvent) => {
  if (touchStartX.value === null) return;
  touchDeltaX.value = e.touches[0].clientX - touchStartX.value;
};
const onTouchEnd = () => {
  const threshold = 50; // px
  if (touchDeltaX.value > threshold) {
    goPrev();
  } else if (touchDeltaX.value < -threshold) {
    goNext();
  }
  touchStartX.value = null;
  touchDeltaX.value = 0;
};

const commentText = ref('');
const comments = ref<any[]>([]);
const isLoadingComments = ref(false);
const isSubmitting = ref(false);
const currentUser = ref<any>(null);

const interactionStats = ref({
  likes: 0,
  collects: 0,
  isLiked: false,
  isCollected: false,
  isFollowed: false
});

const fetchComments = async () => {
  if (!props.post?.id) return;
  
  isLoadingComments.value = true;
  const data = await commentService.fetchComments(props.post.id);
  
  if (data) {
    // Process comments to create nested structure
    const commentMap = new Map();
    const rootComments: any[] = [];

    // First pass: Create objects and map them
    data.forEach((comment: any) => {
      const formattedComment = {
        id: comment.id,
        userId: comment.user_id, // Added userId for permission checks
        user: comment.profiles?.username || '未知用户',
        avatar: comment.profiles?.avatar_url || DEFAULT_AVATAR,
        content: comment.content,
        time: new Date(comment.created_at).toLocaleDateString(),
        likes: comment.like_count || 0,
        isLiked: comment.is_liked || false,
        replies: [],
        parent_id: comment.parent_id,
        isExpanded: false // Collapsed by default
      };
      commentMap.set(comment.id, formattedComment);
    });

      // Second pass: Organize into tree
      data.forEach((comment: any) => {
        const formattedComment = commentMap.get(comment.id);
        if (comment.parent_id) {
          // If parent exists in map, add to its replies
          const parent = commentMap.get(comment.parent_id);
          if (parent) {
            parent.replies.push(formattedComment);
          } else {
            // If parent is not in current set (maybe pagination issue), treat as root
            rootComments.push(formattedComment);
          }
        } else {
          rootComments.push(formattedComment);
        }
      });

    comments.value = rootComments;
  }
  isLoadingComments.value = false;
};

const fetchInteractions = async () => {
  if (!props.post?.id) return;
  const stats = await interactionService.fetchInteractions(props.post.id);
  
  // Check follow status
  let isFollowed = false;
  if (props.post.user?.id) { // Assuming user object has id, if not we need to fetch it or rely on parent passing it
      // Wait, post.user usually just has name/avatar in the current mock/interface. 
      // We need the user_id of the post author.
      // Let's check the Post interface. It has user: { name, avatar, isFollowing }.
      // But for real data, we need the UUID.
      // interactionService.fetchInteractions might return it? No.
      // We need to ensure props.post includes user_id or we fetch it.
      // For now, let's try to use notificationService if we can get the ID.
      // Actually, commentService.fetchComments returns user_id in comments.
      // But for the post author...
      // Let's assume the parent component passes a post object that might have user_id.
      // If not, we might need to fetch post details again or adjust the interface.
      
      // Let's look at the Post interface again:
      // user: { name: string; avatar: string; isFollowing?: boolean; }
      // It doesn't have ID. We should probably add it to the interface and ensure it's passed.
      // However, if we can't change the parent right now, we might be stuck.
      // BUT, fetchInteractions is called. 
      
      // Let's assume we can get it from the post object if we update the interface in this file.
      // And we'll update the fetch logic to check if we can get it.
  }
  
  // WORKAROUND: We need the post author's ID to check follow status.
  // We'll fetch the post details from Supabase to get the author ID if it's missing.
  let authorId = (props.post as any).user_id || (props.post as any).userId;
  if (!authorId && props.post.id) {
      const { data } = await supabase.from('posts').select('user_id').eq('id', props.post.id).single();
      if (data) authorId = data.user_id;
  }

  if (authorId) {
      isFollowed = await notificationService.checkFollowStatus(authorId);
  }

  interactionStats.value = { ...stats, isFollowed };
};

const handleFollow = async () => {
  if (!currentUser.value) {
    showToast('请先登录', 'warning');
    return;
  }

  // We need author ID
  let authorId = (props.post as any).user_id || (props.post as any).userId;
  if (!authorId && props.post.id) {
      const { data } = await supabase.from('posts').select('user_id').eq('id', props.post.id).single();
      if (data) authorId = data.user_id;
  }
  
  if (!authorId) {
      showToast('无法获取作者信息', 'error');
      return;
  }

  if (authorId === currentUser.value.id) {
      showToast('不能关注自己', 'warning');
      return;
  }

  try {
    // Optimistic update
    interactionStats.value.isFollowed = !interactionStats.value.isFollowed;

    if (interactionStats.value.isFollowed) {
        await notificationService.followUser(authorId);
        showToast('已关注', 'success');
    } else {
        await notificationService.unfollowUser(authorId);
        showToast('已取消关注', 'success');
    }
  } catch (error) {
    // Revert
    interactionStats.value.isFollowed = !interactionStats.value.isFollowed;
    showToast('操作失败', 'error');
  }
};

const handleInteraction = async (type: 'like' | 'collect') => {
  if (!currentUser.value) {
    showToast('请先登录', 'warning');
    return;
  }

  try {
    // Optimistic update
    if (type === 'like') {
      interactionStats.value.isLiked = !interactionStats.value.isLiked;
      interactionStats.value.likes += interactionStats.value.isLiked ? 1 : -1;
    } else {
      interactionStats.value.isCollected = !interactionStats.value.isCollected;
      interactionStats.value.collects += interactionStats.value.isCollected ? 1 : -1;
    }

    await interactionService.toggleInteraction(props.post.id, type);
  } catch (error) {
    // Revert on error
    if (type === 'like') {
      interactionStats.value.likes += interactionStats.value.isLiked ? -1 : 1;
      interactionStats.value.isLiked = !interactionStats.value.isLiked;
    } else {
      interactionStats.value.collects += interactionStats.value.isCollected ? -1 : 1;
      interactionStats.value.isCollected = !interactionStats.value.isCollected;
    }
    showToast('操作失败，请重试', 'error');
  }
};

const replyTo = ref<{ id: number; username: string } | null>(null);

const handleCommentLike = async (comment: any) => {
  if (!currentUser.value) {
    showToast('请先登录', 'warning');
    return;
  }

  try {
    // Optimistic update
    comment.isLiked = !comment.isLiked;
    comment.likes += comment.isLiked ? 1 : -1;

    await interactionService.toggleCommentLike(comment.id);
  } catch (error) {
    // Revert
    comment.likes += comment.isLiked ? -1 : 1;
    comment.isLiked = !comment.isLiked;
    showToast('操作失败', 'error');
  }
};

const handleReply = (commentId: number, username: string) => {
  replyTo.value = { id: commentId, username };
  commentText.value = ''; // Clear previous text
  // Focus logic would go here if we had a ref to the input
};

const cancelReply = () => {
  replyTo.value = null;
  commentText.value = '';
};

const submitComment = async () => {
  if (!commentText.value.trim()) return;
  
  if (!currentUser.value) {
    showToast('请先登录', 'warning');
    return;
  }

  try {
    isSubmitting.value = true;
    
    // Prefix content with "Reply @user: " if replying
    let finalContent = commentText.value;
    if (replyTo.value) {
        finalContent = `回复 @${replyTo.value.username}：${commentText.value}`;
    }

    const tempComment = {
      id: Date.now(),
      user: currentUser.value.user_metadata?.full_name || currentUser.value.email || '我',
      avatar: currentUser.value.user_metadata?.avatar_url || DEFAULT_AVATAR,
      content: finalContent,
      time: '刚刚',
      likes: 0,
      parent_id: replyTo.value?.id || null
    };
    
    // Optimistic update logic
    if (replyTo.value) {
       // Find parent and add to replies
       const parent = comments.value.find(c => c.id === replyTo.value!.id);
       if (parent) {
           if (!parent.replies) parent.replies = [];
           parent.replies.push(tempComment);
           parent.isExpanded = true; // Auto expand
       }
    } else {
       comments.value.push(tempComment);
    }

    const textToSend = finalContent;
    const parentIdToSend = replyTo.value?.id;
    
    commentText.value = '';
    replyTo.value = null; // Reset reply state

    await commentService.addComment(props.post.id, textToSend, parentIdToSend);
    await fetchComments(); // Force refresh from server
    showToast('评论成功', 'success');
  } catch (error: any) {
    // Revert optimistic update (simplified)
    await fetchComments(); 
    showToast('评论失败: ' + error.message, 'error');
  } finally {
    isSubmitting.value = false;
  }
};

const handleDelete = async (commentId: number) => {
  if (!confirm('确定要删除这条评论吗？')) return;
  
  try {
    // Optimistic update: remove from list immediately
    const removeComment = (list: any[]) => {
      const index = list.findIndex(c => c.id === commentId);
      if (index !== -1) {
        list.splice(index, 1);
        return true;
      }
      for (const item of list) {
        if (item.replies && removeComment(item.replies)) return true;
      }
      return false;
    };
    
    removeComment(comments.value);
    
    await commentService.deleteComment(commentId);
    showToast('评论已删除', 'success');
    await fetchComments(); // Refresh to be sure
  } catch (error: any) {
    showToast('删除失败: ' + error.message, 'error');
    await fetchComments(); // Revert on error
  }
};

const handleClose = () => {
  emit('close');
};

// Watch for post changes or modal open to fetch comments
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen) {
    // Reset state immediately
    comments.value = [];
    interactionStats.value = { likes: 0, collects: 0, isLiked: false, isCollected: false, isFollowed: false };
    
    if (props.post?.id) {
      await Promise.all([fetchComments(), fetchInteractions()]);
      
      // Subscribe to new comments (INSERT, DELETE, UPDATE)
      const channel = supabase
        .channel(`public:comments:post_id=eq.${props.post.id}`)
        .on(
          'postgres_changes',
          {
            event: '*', // Listen to all events
            schema: 'public',
            table: 'comments',
            filter: `post_id=eq.${props.post.id}`
          },
          () => {
            fetchComments();
          }
        )
        .subscribe();
        
      // Cleanup subscription when modal closes
      const cleanup = watch(() => props.isOpen, (newVal) => {
        if (!newVal) {
          supabase.removeChannel(channel);
          cleanup(); // Stop watching
        }
      });
    }
  }
}, { immediate: true }); // Ensure it runs if initially true

// Also watch for post ID changes while open
watch(() => props.post.id, async (newId) => {
  if (newId && props.isOpen) {
    resetMediaState();
    comments.value = []; // Reset on post switch
    await Promise.all([fetchComments(), fetchInteractions()]);
  }
});

onMounted(async () => {
  updateViewport();
  window.addEventListener('resize', updateViewport);
  const { data: { session } } = await supabase.auth.getSession();
  if (session) {
    currentUser.value = session.user;
  }
});

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateViewport);
  }
});
</script>

<template>
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 sm:p-6" @click.self="handleClose">
      <!-- Modal Container -->
      <div 
        class="relative flex h-[85vh] w-full overflow-hidden rounded-2xl bg-white shadow-2xl transition-[width] duration-300 ease-out animate-scale-up md:w-auto md:max-w-[calc(100vw-3rem)]"
        :style="desktopModalStyle"
      >
        <!-- Close Button (Mobile Floating) -->
        <button 
          @click="handleClose"
          class="absolute top-4 left-4 z-20 p-2 bg-black/20 hover:bg-black/40 rounded-full text-white backdrop-blur-md md:hidden"
        >
          <X class="w-5 h-5" />
        </button>

        <!-- Left Side: Media -->
        <div class="group relative h-full w-full overflow-hidden border-b border-[#f0ebe4] bg-[#f6f3ee] md:flex-none md:border-b-0 md:border-r" :style="desktopMediaStyle">
          <div
            v-if="hasMultipleMedia"
            class="absolute right-4 top-4 z-20 rounded-full bg-black/38 px-3 py-1 text-[11px] font-medium tracking-[0.18em] text-white backdrop-blur-md"
          >
            {{ mediaCounterLabel }}
          </div>

          <div v-if="isVideoPost" class="group/video relative flex h-full w-full items-center justify-center overflow-hidden">
            <video
              ref="videoRef"
              :src="post.image"
              class="h-full w-full bg-[#f6f3ee] object-contain select-none"
              autoplay
              :muted="isMuted"
              @timeupdate="handleTimeUpdate"
              @loadedmetadata="handleLoadedMetadata"
              @click="togglePlay"
              @ended="handleEnded"
            ></video>
            
            <!-- Custom Controls Overlay -->
            <div class="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-black/55 via-black/8 to-transparent transition-opacity duration-300" :class="{ 'opacity-0 group-hover/video:opacity-100': !isEnded && isPlaying, 'opacity-100': isEnded || !isPlaying }">
                <!-- Center Play/Pause Button -->
                <button
                    class="absolute left-1/2 top-1/2 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-black/38 text-white shadow-[0_18px_45px_rgba(0,0,0,0.22)] backdrop-blur-md transition-transform duration-200 active:scale-95"
                    @click="togglePlay"
                    aria-label="toggle-play"
                >
                    <RotateCcw v-if="isEnded" class="h-7 w-7" />
                    <Play v-else-if="!isPlaying" class="h-7 w-7 fill-white" />
                    <Pause v-else class="h-7 w-7 fill-white" />
                </button>

                <!-- Bottom Controls Bar -->
                <div class="p-4 pb-5 md:p-5 md:pb-6">
                    <!-- Progress Bar -->
                    <div class="group/progress relative mb-3 h-1 cursor-pointer rounded-full bg-white/25">
                        <div 
                            class="absolute top-0 left-0 h-full bg-white rounded-full transition-all duration-100"
                            :style="{ width: `${progress}%` }"
                        >
                            <div class="absolute right-0 top-1/2 h-3 w-3 -translate-y-1/2 rounded-full bg-white opacity-0 shadow-sm transition-opacity group-hover/progress:opacity-100"></div>
                        </div>
                        <input 
                            type="range" 
                            min="0" 
                            max="100" 
                            step="0.1"
                            :value="progress"
                            @input="handleSeek"
                            class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                        />
                    </div>

                    <div class="flex items-center justify-between text-xs font-medium text-white">
                        <div class="flex items-center space-x-4">
                            <span class="text-white/90">{{ formatTime(currentTime) }} / {{ formatTime(duration) }}</span>
                        </div>
                        
                        <div class="flex items-center space-x-4">
                            <button @click="toggleMute" class="rounded-full bg-white/12 p-2 transition-colors hover:bg-white/18" aria-label="toggle-mute">
                                <VolumeX v-if="isMuted" class="h-4 w-4" />
                                <Volume2 v-else class="h-4 w-4" />
                            </button>
                            <div class="relative">
                                <button 
                                    class="rounded-full border border-white/25 bg-white/12 px-2.5 py-1 text-[11px] transition-colors hover:bg-white/18"
                                    @click.stop="showSpeedMenu = !showSpeedMenu"
                                >
                                    <span class="hidden">
                                        {{ playbackRate === 1 ? '倍速' : `${playbackRate}x` }}
                                    </span><span>{{ playbackRate === 1 ? '1x' : `${playbackRate}x` }}</span>
                                </button>
                                
                                <!-- Speed Menu -->
                                <div 
                                    v-if="showSpeedMenu"
                                    class="absolute bottom-full right-0 mb-2 overflow-hidden rounded-2xl bg-black/80 py-1 backdrop-blur-md"
                                    @click.stop
                                >
                                    <button 
                                        v-for="rate in playbackRates" 
                                        :key="rate"
                                        @click="setPlaybackRate(rate)"
                                        class="block w-full px-3 py-1.5 text-xs transition-colors hover:bg-white/12"
                                        :class="playbackRate === rate ? 'font-semibold text-white' : 'text-white/70'"
                                    >
                                        {{ rate }}x
                                    </button>
                                </div>
                            </div>
                            <button @click="toggleFullscreen" class="rounded-full bg-white/12 p-2 transition-colors hover:bg-white/18" aria-label="fullscreen">
                                <Maximize class="h-4 w-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
          </div>
          <div 
            v-else 
            class="relative flex h-full w-full items-center justify-center overflow-hidden touch-pan-y bg-[#f6f3ee]"
            @touchstart.passive="onTouchStart"
            @touchmove.passive="onTouchMove"
            @touchend.passive="onTouchEnd"
          >
            <img
              :src="displayedImage"
              :alt="post.title"
              class="h-full w-full select-none bg-[#f6f3ee] transition-[transform,filter] duration-500"
              :class="imageFit === 'cover' ? 'object-cover' : 'object-contain'"
              @dblclick="toggleImageFit"
              draggable="false"
            />
            <button
              v-if="hasMultipleMedia"
              class="absolute left-4 top-1/2 z-20 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full bg-white/92 text-slate-700 shadow-[0_14px_30px_rgba(15,23,42,0.14)] transition-all duration-200 hover:bg-white md:opacity-0 md:group-hover:opacity-100"
              @click.stop="goPrev"
              aria-label="prev"
            >
              <ChevronLeft class="h-5 w-5" />
            </button>
            <button
              v-if="hasMultipleMedia"
              class="absolute right-4 top-1/2 z-20 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-full bg-white/92 text-slate-700 shadow-[0_14px_30px_rgba(15,23,42,0.14)] transition-all duration-200 hover:bg-white md:opacity-0 md:group-hover:opacity-100"
              @click.stop="goNext"
              aria-label="next"
            >
              <ChevronRight class="h-5 w-5" />
            </button>
            <div 
              v-if="hasMultipleMedia"
              class="absolute bottom-5 left-1/2 z-20 flex -translate-x-1/2 items-center gap-2 rounded-full bg-black/30 px-3 py-2 backdrop-blur-md"
            >
              <span 
                v-for="(img, idx) in imageList" 
                :key="idx"
                class="h-1.5 rounded-full transition-all duration-300"
                :class="idx === currentImage ? 'w-5 bg-white' : 'w-1.5 bg-white/45'"
              ></span>
            </div>
            <button
              class="absolute bottom-5 right-5 z-20 rounded-full bg-white/92 p-2 text-slate-700 shadow-[0_14px_30px_rgba(15,23,42,0.12)] transition-colors hover:bg-white"
              @click="toggleImageFit"
              aria-label="toggle-fit"
            >
              <Maximize class="h-4 w-4" />
            </button>
          </div>
          <!-- Navigation Arrows could go here -->
        </div>

        <!-- Right Side: Content -->
        <div class="relative flex h-full w-full flex-col bg-white md:w-auto md:flex-none" :style="desktopSideStyle">
          <!-- Header: User Info -->
          <div class="flex items-center justify-between p-5 border-b border-gray-100 sticky top-0 bg-white z-10">
            <div class="flex items-center space-x-3">
              <img
                :src="post.user.avatar"
                :alt="post.user.name"
                class="w-10 h-10 rounded-full object-cover border border-gray-100"
              />
              <div>
                <div class="text-sm font-semibold text-gray-900">{{ post.user.name }}</div>
                <!-- <div class="text-xs text-gray-500">发布于 {{ post.location || '未知地点' }}</div> -->
              </div>
            </div>
            
            <div class="flex items-center space-x-3">
              <button 
                class="px-4 py-1.5 text-sm font-medium rounded-full transition-colors"
                :class="interactionStats.isFollowed ? 'text-gray-500 bg-gray-100 hover:bg-gray-200' : 'text-white bg-red-500 hover:bg-red-600'"
                @click="handleFollow"
              >
                {{ interactionStats.isFollowed ? '已关注' : '关注' }}
              </button>
              <button class="text-gray-400 hover:text-gray-600">
                <Share2 class="w-5 h-5" />
              </button>
              <button class="hidden md:block text-gray-400 hover:text-gray-600" @click="handleClose">
                 <X class="w-6 h-6" />
              </button>
            </div>
          </div>

          <!-- Scrollable Content -->
          <div class="flex-1 overflow-y-auto p-5 scrollbar-thin scrollbar-thumb-gray-200">
            <!-- Post Info -->
            <div class="mb-6">
              <h1 class="text-xl font-bold text-gray-900 mb-3 leading-snug">{{ post.title }}</h1>
              <p class="text-gray-700 text-sm leading-relaxed whitespace-pre-line mb-4">
                {{ post.content || '这里是详细的内容描述...' }}
              </p>
              
              <!-- Tags -->
              <div class="flex flex-wrap gap-2 mb-4 text-blue-600 text-sm">
                <span v-for="tag in post.tags" :key="tag">#{{ tag }}</span>
              </div>

              <!-- Meta -->
              <div class="flex items-center text-xs text-gray-400 space-x-4">
                <span>{{ post.date || '04-12' }}</span>
                <span v-if="post.location" class="flex items-center">
                    <MapPin class="w-3 h-3 mr-1" />
                    {{ post.location }}
                </span>
              </div>
            </div>

            <!-- Comments Section -->
            <div class="border-t border-gray-100 pt-5">
              <div class="text-sm text-gray-500 mb-4">共 {{ comments.length }} 条评论</div>
              
              <div v-if="isLoadingComments" class="flex justify-center py-8">
                  <Loader2 class="w-6 h-6 animate-spin text-gray-400" />
              </div>

              <div v-else-if="comments.length === 0" class="flex flex-col items-center justify-center py-8 text-gray-400">
                  <MessageCircle class="w-8 h-8 mb-2 opacity-50" />
                  <p class="text-xs">还没有评论，快来抢沙发吧~</p>
              </div>

              <div v-else class="space-y-6">
                <div v-for="comment in comments" :key="comment.id" class="flex space-x-3">
                  <img :src="comment.avatar" class="w-8 h-8 rounded-full flex-shrink-0" />
                  <div class="flex-1">
                    <!-- Main Comment -->
                    <div class="flex items-center space-x-2">
                        <span class="text-sm font-medium text-gray-600">{{ comment.user }}</span>
                        <span v-if="comment.user === post.user.name" class="px-1.5 py-0.5 bg-gray-100 text-gray-500 text-[10px] rounded">作者</span>
                    </div>
                    <p class="text-sm text-gray-800 mt-1">{{ comment.content }}</p>
                    <div class="flex items-center mt-2 space-x-4 text-xs text-gray-400">
                      <span>{{ comment.time }}</span>
                      <button 
                        class="hover:text-gray-600"
                        @click="handleReply(comment.id, comment.user)"
                      >回复</button>
                      <!-- Delete button for own comments -->
                      <button 
                        v-if="currentUser && comment.userId === currentUser.id"
                        class="hover:text-red-500"
                        @click="handleDelete(comment.id)"
                      >删除</button>
                      <div class="flex items-center space-x-1 cursor-pointer hover:text-red-500" @click="handleCommentLike(comment)">
                        <Heart class="w-3 h-3" :class="{ 'fill-current text-red-500': comment.isLiked }" />
                        <span v-if="comment.likes">{{ comment.likes }}</span>
                      </div>
                    </div>

                    <!-- Nested Replies -->
                    <div v-if="comment.replies && comment.replies.length > 0" class="mt-2 pl-8 space-y-3">
                      <!-- Collapsed View: Show Expand Button -->
                      <button 
                        v-if="!comment.isExpanded" 
                        @click="comment.isExpanded = true"
                        class="flex items-center space-x-1 text-xs font-medium text-blue-600 hover:text-blue-700 transition-colors group"
                      >
                        <div class="w-6 h-[1px] bg-gray-300 mr-2 group-hover:bg-blue-400"></div>
                        展开 {{ comment.replies.length }} 条回复
                        <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      <!-- Expanded View: Show Replies -->
                      <div v-else class="space-y-4 animate-scale-up origin-top">
                        <div v-for="reply in comment.replies" :key="reply.id" class="flex space-x-2">
                          <img :src="reply.avatar" class="w-6 h-6 rounded-full flex-shrink-0 mt-0.5" />
                          <div class="flex-1">
                            <div class="flex items-center space-x-2">
                                <span class="text-xs font-medium text-gray-600">{{ reply.user }}</span>
                                <span v-if="reply.user === post.user.name" class="px-1.5 py-0.5 bg-white text-gray-500 text-[10px] rounded border border-gray-100">作者</span>
                            </div>
                            <p class="text-sm text-gray-800 mt-0.5">
                              <span v-if="reply.content.startsWith('回复 @')" class="text-blue-500 mr-1">回复 {{ reply.content.split('：')[0].replace('回复 ', '') }}</span>
                              <span>{{ reply.content.includes('：') ? reply.content.split('：')[1] : reply.content }}</span>
                            </p>
                            <div class="flex items-center mt-1.5 space-x-4 text-[10px] text-gray-400">
                              <span>{{ reply.time }}</span>
                              <div class="flex items-center space-x-1 cursor-pointer hover:text-red-500" @click="handleCommentLike(reply)">
                                <Heart class="w-3 h-3" :class="{ 'fill-current text-red-500': reply.isLiked }" />
                                <span v-if="reply.likes">{{ reply.likes }}</span>
                              </div>
                              <button 
                                class="hover:text-gray-600"
                                @click="handleReply(comment.id, reply.user)"
                              >回复</button>
                              <!-- Delete button for own replies -->
                              <button 
                                v-if="currentUser && reply.userId === currentUser.id"
                                class="hover:text-red-500"
                                @click="handleDelete(reply.id)"
                              >删除</button>
                            </div>
                          </div>
                        </div>
                        
                        <!-- Collapse Button -->
                        <button 
                          @click="comment.isExpanded = false"
                          class="text-xs text-gray-400 font-medium mt-2 hover:text-gray-600 flex items-center ml-8"
                        >
                          收起回复
                          <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Action Bar -->
          <div class="border-t border-gray-100 p-4 bg-white">
            <div class="flex items-center justify-between mb-4">
               <div class="flex items-center space-x-6 text-gray-600">
                  <button 
                    @click="handleInteraction('like')"
                    class="flex items-center space-x-1.5 group transition-colors"
                    :class="interactionStats.isLiked ? 'text-red-500' : 'text-gray-600 hover:text-red-500'"
                  >
                    <Heart class="w-6 h-6" :class="{ 'fill-current': interactionStats.isLiked }" />
                    <span class="text-sm font-medium">{{ interactionStats.likes }}</span>
                  </button>
                  <button 
                    @click="handleInteraction('collect')"
                    class="flex items-center space-x-1.5 group transition-colors"
                    :class="interactionStats.isCollected ? 'text-yellow-500' : 'text-gray-600 hover:text-yellow-500'"
                  >
                    <Star class="w-6 h-6" :class="{ 'fill-current': interactionStats.isCollected }" />
                    <span class="text-sm font-medium">{{ interactionStats.collects }}</span>
                  </button>
                  <button class="flex items-center space-x-1.5 group hover:text-blue-500 transition-colors">
                    <MessageCircle class="w-6 h-6" />
                    <span class="text-sm font-medium">{{ comments.length }}</span>
                  </button>
               </div>
            </div>

            <!-- Comment Input -->
            <div class="relative">
                <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                     <div class="w-6 h-6 rounded-full bg-gray-200 overflow-hidden">
                        <img :src="currentUser?.user_metadata?.avatar_url || DEFAULT_AVATAR" />
                     </div>
                </div>
                <input 
                    v-model="commentText"
                    type="text" 
                    :placeholder="replyTo ? `回复 @${replyTo.username}：` : '说点什么...'"
                    class="w-full pl-12 pr-12 py-2.5 bg-gray-100 rounded-full text-sm focus:outline-none focus:bg-gray-50 focus:ring-1 focus:ring-gray-200 transition-colors placeholder-gray-400"
                    @keydown.enter="submitComment"
                    :disabled="isSubmitting"
                    @blur="!commentText && cancelReply()" 
                >
                <button 
                    class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-blue-500 hover:bg-blue-50 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                    :disabled="!commentText.trim() || isSubmitting"
                    @click="submitComment"
                >
                    <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
                    <Send v-else class="w-4 h-4" />
                </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* Hide scrollbar for Chrome, Safari and Opera */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 20px;
}
.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: #d1d5db;
}

.animate-scale-up {
    animation: scaleUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes scaleUp {
    from {
        opacity: 0;
        transform: scale(0.95);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}
</style>
