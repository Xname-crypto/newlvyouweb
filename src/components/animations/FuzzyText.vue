<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface Props {
  text: string
  fontSize?: number
  fontWeight?: number | string
  fontFamily?: string
  color?: string
  baseIntensity?: number
  hoverIntensity?: number
  enableHover?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fontSize: 32,
  fontWeight: 900,
  fontFamily: 'inherit',
  color: '#ffffff',
  baseIntensity: 0.18,
  hoverIntensity: 0.5,
  enableHover: true,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
const isHovered = ref(false)
const reduceMotion = ref(false)
let animationFrame = 0

const fontFamily = computed(() => {
  if (props.fontFamily !== 'inherit') {
    return props.fontFamily
  }

  if (typeof window === 'undefined') {
    return 'sans-serif'
  }

  return window.getComputedStyle(document.body).fontFamily || 'sans-serif'
})

const draw = () => {
  const canvas = canvasRef.value
  if (!canvas) return

  const dpr = Math.max(1, window.devicePixelRatio || 1)
  const font = `${props.fontWeight} ${props.fontSize}px ${fontFamily.value}`
  const measureCanvas = document.createElement('canvas')
  const measureCtx = measureCanvas.getContext('2d')
  if (!measureCtx) return

  measureCtx.font = font
  const metrics = measureCtx.measureText(props.text)
  const padding = Math.ceil(props.fontSize * 0.45)
  const width = Math.ceil(metrics.width + padding * 2)
  const height = Math.ceil(props.fontSize * 1.55)

  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`
  canvas.width = Math.ceil(width * dpr)
  canvas.height = Math.ceil(height * dpr)

  const baseCanvas = document.createElement('canvas')
  baseCanvas.width = canvas.width
  baseCanvas.height = canvas.height
  const baseCtx = baseCanvas.getContext('2d')
  const ctx = canvas.getContext('2d')
  if (!baseCtx || !ctx) return

  baseCtx.scale(dpr, dpr)
  baseCtx.font = font
  baseCtx.fillStyle = props.color
  baseCtx.textBaseline = 'middle'
  baseCtx.textAlign = 'left'
  baseCtx.fillText(props.text, padding, height / 2)

  const intensity = props.enableHover && isHovered.value ? props.hoverIntensity : props.baseIntensity
  const sliceHeight = Math.max(1, Math.round(dpr))
  const maxOffset = reduceMotion.value ? 0 : intensity * props.fontSize * 0.48 * dpr

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  for (let y = 0; y < canvas.height; y += sliceHeight) {
    const offset = (Math.random() - 0.5) * maxOffset * 2
    ctx.drawImage(baseCanvas, 0, y, canvas.width, sliceHeight, offset, y, canvas.width, sliceHeight)
  }
}

const animate = () => {
  draw()
  if (!reduceMotion.value) {
    animationFrame = window.requestAnimationFrame(animate)
  }
}

const restart = async () => {
  window.cancelAnimationFrame(animationFrame)
  await nextTick()
  animate()
}

onMounted(async () => {
  reduceMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (document.fonts?.ready) {
    await document.fonts.ready
  }
  animate()
})

onBeforeUnmount(() => {
  window.cancelAnimationFrame(animationFrame)
})

watch(() => props.text, restart)
watch(() => props.fontSize, restart)
</script>

<template>
  <canvas
    ref="canvasRef"
    class="fuzzy-text"
    :aria-label="text"
    role="img"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  />
</template>

<style scoped>
.fuzzy-text {
  display: block;
  max-width: 100%;
}
</style>
