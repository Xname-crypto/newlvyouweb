<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight, ShoppingBag, Trash2 } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import CheckoutSteps from '@/components/CheckoutSteps.vue'
import { CART_UPDATED_EVENT, getCartItemImage, readCartItems, removeCartItem, writeCartItems, type CartItem } from '@/services/cartService'
import { createEmptyCheckoutDraft, writeCheckoutDraft } from '@/services/checkoutService'
import { commerceService, getProductImage } from '@/services/commerceService'

const router = useRouter()
const items = ref<CartItem[]>([])
const errorMessage = ref('')

const loadItems = () => {
  items.value = readCartItems()
}

const hideBrokenCartImage = (event: Event) => {
  const image = event.currentTarget as HTMLImageElement | null
  if (!image) return
  image.removeAttribute('src')
  image.classList.add('hidden')
}

const refreshItemsFromProducts = async () => {
  const productIds = Array.from(new Set(items.value.map((item) => item.productId).filter(Boolean))) as number[]
  if (!productIds.length) return

  const products = await commerceService.listProducts()
  const productById = new Map(products.map((product) => [product.id, product]))
  const nextItems = items.value.map((item) => {
    if (!item.productId) return item
    const product = productById.get(item.productId)
    if (!product) return item
    const productImage = getProductImage(product)
    const requiresSize = product.metadata?.requires_size !== false && Array.isArray(product.metadata?.sizes) && product.metadata.sizes.length > 0
    return {
      ...item,
      size: requiresSize ? item.size : '',
      meta: [requiresSize ? item.size : '', item.color].filter(Boolean).join(' / ') || product.category || product.sku,
      price: product.price || ((product.price_cents || 0) / 100).toFixed(2),
      image: getCartItemImage({ ...item, image: productImage }),
      productSnapshot: {
        ...(item.productSnapshot || {}),
        id: product.id,
        sku: product.sku,
        name: product.name,
        image_url: getCartItemImage({ ...item, image: productImage }),
        price_cents: product.price_cents,
        currency: product.currency,
        metadata: {
          shipping_cents: Number(item.shippingCents || item.productSnapshot?.metadata?.shipping_cents || 0) || 0,
          requires_size: requiresSize,
          requires_color: product.metadata?.requires_color === true,
        },
      },
    }
  })
  writeCartItems(nextItems)
  items.value = nextItems
}

const parsePrice = (price: string) => Number(String(price).replace(/[^\d.]/g, ''))
const formatMoney = (value: number) => `CNY ${value.toFixed(2)}`

const subtotalValue = computed(() => items.value.reduce((sum, item) => {
  const numeric = parsePrice(item.price)
  return sum + (Number.isFinite(numeric) ? numeric * item.quantity : 0)
}, 0))

const subtotal = computed(() => formatMoney(subtotalValue.value))
const total = computed(() => formatMoney(subtotalValue.value))

const removeItem = (id: string) => {
  removeCartItem(id)
  loadItems()
}

const goCheckout = () => {
  const invalidItem = items.value.find((item) => !item.productId)
  if (invalidItem) {
    errorMessage.value = `Product "${invalidItem.name}" is missing backend product data. Please add it again from the product catalogue.`
    return
  }

  const draft = createEmptyCheckoutDraft()
  draft.items = items.value
  writeCheckoutDraft(draft)
  router.push('/checkout/information')
}

onMounted(() => {
  loadItems()
  refreshItemsFromProducts()
  window.addEventListener(CART_UPDATED_EVENT, loadItems)
})

onUnmounted(() => {
  window.removeEventListener(CART_UPDATED_EVENT, loadItems)
})
</script>

<template>
  <div class="min-h-screen bg-[#fffdf9] text-[#2f2c27]">
    <Navigation variant="solid-light" show-cart />

    <main class="mx-auto max-w-[1280px] px-6 pb-24 pt-[124px] lg:px-10">
      <CheckoutSteps current="cart" />
      <div class="mt-8 grid gap-10 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section>
          <h1 class="text-[34px] font-semibold tracking-tight">My Cart</h1>

          <div v-if="errorMessage" class="mt-6 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
            {{ errorMessage }}
          </div>

          <div v-if="items.length" class="mt-8 space-y-6">
            <article
              v-for="item in items"
              :key="item.id"
              class="grid gap-5 border-b border-[#ece6de] pb-6 md:grid-cols-[122px_minmax(0,1fr)_28px]"
            >
              <img v-if="item.image" :src="item.image" :alt="item.name" class="h-[148px] w-[122px] object-cover" @error="hideBrokenCartImage" />
              <div class="flex flex-col justify-between">
                <div>
                  <div class="flex flex-wrap items-center gap-3">
                    <p class="text-[30px] font-semibold text-[#d78368]">CNY {{ parsePrice(item.price).toFixed(2) }}</p>
                  </div>
                  <h2 class="mt-2 text-lg font-medium">{{ item.name }}</h2>
                </div>

                <div class="mt-4 flex flex-wrap gap-6 text-sm text-[#766d64]">
                  <span v-if="item.size">Size: {{ item.size }}</span>
                  <span v-if="item.color">Color: {{ item.color }}</span>
                  <span>Q-ty: {{ item.quantity }}</span>
                </div>
              </div>

              <button
                type="button"
                class="mt-2 inline-flex h-8 w-8 items-center justify-center text-[#8c867d] transition-colors hover:text-[#d78368]"
                aria-label="Remove item"
                @click="removeItem(item.id)"
              >
                <Trash2 :size="16" />
              </button>
            </article>

            <div class="flex items-center justify-between border-t border-[#ece6de] pt-6">
              <p class="text-xl font-black">Sub-total</p>
              <p class="text-2xl font-black">{{ subtotal }}</p>
            </div>
          </div>

          <section v-else class="mt-10 border border-dashed border-[#ddd5c9] bg-white px-8 py-16 text-center">
            <ShoppingBag class="mx-auto text-[#d19a84]" :size="34" />
            <p class="mt-4 text-lg font-semibold">Your cart is empty.</p>
            <router-link
              to="/product-catalogue"
              class="mt-6 inline-flex bg-[#2f2c27] px-6 py-3 text-sm font-black text-white transition-colors hover:bg-[#d78368]"
            >
              Continue shopping
            </router-link>
          </section>
        </section>

        <aside class="h-fit border border-[#ece6de] bg-white p-7">
          <p class="text-sm font-black uppercase tracking-[0.16em] text-[#b98d79]">Summary</p>
          <div class="mt-6 space-y-4 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-[#7f756b]">Subtotal</span>
              <span class="font-black">{{ subtotal }}</span>
            </div>
            <div class="flex items-center justify-between border-t border-[#ece6de] pt-4 text-base">
              <span class="font-black">Total</span>
              <span class="text-[28px] font-semibold text-[#d78368]">{{ total }}</span>
            </div>
          </div>

          <button
            type="button"
            class="mt-8 inline-flex w-full items-center justify-center gap-2 bg-[#eca37f] px-5 py-4 text-sm font-black uppercase tracking-[0.08em] text-white transition-colors hover:bg-[#d78368] disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!items.length"
            @click="goCheckout"
          >
            Proceed to checkout
            <ChevronRight :size="16" />
          </button>
        </aside>
      </div>
    </main>

    <Footer variant="white" />
  </div>
</template>
