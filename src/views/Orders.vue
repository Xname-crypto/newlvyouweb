<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CreditCard, Package, RefreshCw, RotateCcw } from 'lucide-vue-next'
import Navigation from '@/components/Navigation.vue'
import Footer from '@/components/Footer.vue'
import { commerceService, type CommerceOrder } from '@/services/commerceService'

const router = useRouter()
const orders = ref<CommerceOrder[]>([])
const loading = ref(false)
const errorMessage = ref('')

const statusLabel: Record<string, string> = {
  pending_payment: 'Pending payment',
  payment_created: 'Payment created',
  paid: 'Paid',
  payment_failed: 'Payment failed',
  canceled: 'Canceled',
  expired: 'Expired',
}

const activeOrders = computed(() => orders.value.filter((order) => ['pending_payment', 'payment_created'].includes(order.status)))
const completedOrders = computed(() => orders.value.filter((order) => !['pending_payment', 'payment_created'].includes(order.status)))

const loadOrders = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    orders.value = await commerceService.listCheckoutOrders()
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || 'Failed to load orders.')
  } finally {
    loading.value = false
  }
}

const continuePay = (order: CommerceOrder) => {
  router.push(`/checkout/payment?order=${order.id}`)
}

const syncOrder = async (order: CommerceOrder) => {
  try {
    const next = await commerceService.syncCheckoutOrder(order.id)
    orders.value = orders.value.map((item) => (item.id === next.id ? next : item))
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || 'Failed to refresh order status.')
  }
}

onMounted(loadOrders)
</script>

<template>
  <div class="min-h-screen bg-[#f8faf7] text-[#1f2f25]">
    <Navigation variant="solid-light" show-cart />

    <main class="mx-auto max-w-[1120px] px-6 pb-20 pt-[128px] lg:px-10">
      <div class="mb-8 flex items-center justify-between gap-4">
        <div>
          <p class="text-xs font-black uppercase tracking-[0.28em] text-[#b28c4b]">Orders</p>
          <h1 class="mt-3 text-4xl font-semibold">My Checkout Orders</h1>
        </div>
        <button
          class="inline-flex items-center gap-2 border border-[#d7dfd2] bg-white px-5 py-3 text-sm font-bold"
          type="button"
          @click="loadOrders"
        >
          <RefreshCw :size="16" />
          Refresh
        </button>
      </div>

      <div v-if="errorMessage" class="mb-6 border border-[#f0c7bd] bg-[#fff3ef] px-5 py-4 text-sm font-semibold text-[#b24c37]">
        {{ errorMessage }}
      </div>

      <div v-if="loading" class="flex min-h-[260px] items-center justify-center text-[#647266]">
        <RefreshCw class="mr-3 animate-spin" :size="20" />
        Loading your orders...
      </div>

      <template v-else-if="orders.length">
        <section v-if="activeOrders.length" class="mb-10">
          <h2 class="mb-4 text-sm font-black uppercase tracking-[0.22em] text-[#93a08f]">Open Orders</h2>
          <div class="space-y-4">
            <article v-for="order in activeOrders" :key="order.id" class="border border-[#e3e9df] bg-white p-6">
              <div class="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-3">
                    <h3 class="text-lg font-black">{{ order.order_no }}</h3>
                    <span class="border border-[#d7dfd2] px-3 py-1 text-xs font-black">{{ statusLabel[order.status] || order.status }}</span>
                  </div>
                  <p class="mt-2 text-sm text-[#647266]">
                    {{ order.items.length }} item{{ order.items.length > 1 ? 's' : '' }} · {{ order.payment_method.toUpperCase() }}
                  </p>
                  <div class="mt-4 flex flex-wrap gap-4 text-sm text-[#526052]">
                    <div
                      v-for="item in order.items.slice(0, 3)"
                      :key="item.id"
                      class="inline-flex items-center gap-3 border border-[#edf0eb] px-3 py-2"
                    >
                      <img :src="item.image_url" :alt="item.name" class="h-12 w-10 object-cover" />
                      <div class="min-w-0">
                        <p class="truncate font-semibold">{{ item.name }}</p>
                        <p class="text-xs text-[#7e8a81]">x{{ item.quantity }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="flex flex-col items-start gap-3 md:items-end">
                  <span class="text-2xl font-black text-[#d78368]">¥{{ order.total_amount }}</span>
                  <div class="flex flex-wrap gap-3">
                    <button
                      v-if="order.status === 'pending_payment' || order.status === 'payment_created'"
                      class="bg-[#1f2f25] px-5 py-2.5 text-sm font-black text-white"
                      type="button"
                      @click="continuePay(order)"
                    >
                      Continue Payment
                    </button>
                    <button
                      class="inline-flex items-center gap-2 border border-[#d7dfd2] bg-white px-5 py-2.5 text-sm font-bold"
                      type="button"
                      @click="syncOrder(order)"
                    >
                      <RotateCcw :size="15" />
                      Sync Status
                    </button>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section>
          <h2 class="mb-4 text-sm font-black uppercase tracking-[0.22em] text-[#93a08f]">History</h2>
          <div class="space-y-4">
            <article v-for="order in completedOrders" :key="order.id" class="border border-[#e3e9df] bg-white p-6">
              <div class="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-3">
                    <h3 class="text-lg font-black">{{ order.order_no }}</h3>
                    <span class="border border-[#d7dfd2] px-3 py-1 text-xs font-black">{{ statusLabel[order.status] || order.status }}</span>
                  </div>
                  <p class="mt-2 text-sm text-[#647266]">
                    {{ order.items.length }} item{{ order.items.length > 1 ? 's' : '' }} · Created {{ new Date(order.created_at).toLocaleString() }}
                  </p>
                </div>

                <div class="flex items-center gap-3">
                  <span class="text-2xl font-black text-[#d78368]">¥{{ order.total_amount }}</span>
                  <button
                    class="inline-flex items-center gap-2 border border-[#d7dfd2] bg-white px-5 py-2.5 text-sm font-bold"
                    type="button"
                    @click="syncOrder(order)"
                  >
                    <RotateCcw :size="15" />
                    Refresh
                  </button>
                </div>
              </div>
            </article>
          </div>
        </section>
      </template>

      <div v-else class="border border-dashed border-[#d7dfd2] bg-white px-8 py-16 text-center">
        <Package class="mx-auto text-[#b28c4b]" :size="28" />
        <p class="mt-4 text-lg font-black">No checkout orders yet</p>
        <p class="mt-2 text-sm text-[#647266]">Add real products to the cart first, then complete the new checkout flow.</p>
        <router-link to="/product-catalogue" class="mt-5 inline-flex bg-[#1f2f25] px-6 py-3 text-sm font-black text-white">
          Browse products
        </router-link>
      </div>

      <div class="mt-8 rounded-2xl border border-[#e3e9df] bg-white px-6 py-5 text-sm text-[#647266]">
        <div class="flex items-start gap-3">
          <CreditCard class="mt-0.5 text-[#b28c4b]" :size="18" />
          <p>Legacy one-click payment orders are still supported in the backend, but this page now follows the new cart-driven checkout flow.</p>
        </div>
      </div>
    </main>

    <Footer variant="white" />
  </div>
</template>
