<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { CalendarDays, ChevronLeft, ChevronRight, CreditCard, ListChecks, RefreshCw, Search, ShieldCheck } from 'lucide-vue-next'
import { commerceService, type CommerceOrder, type PaymentEvent } from '@/services/commerceService'

const orders = ref<CommerceOrder[]>([])
const events = ref<PaymentEvent[]>([])
const selectedOrderId = ref<number | null>(null)
const loading = ref(false)
const eventsLoading = ref(false)
const errorMessage = ref('')
const isPaymentLogOpen = ref(false)

const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = ref(1)
const orderNoQuery = ref('')
const orderDate = ref('')

const selectedOrder = computed(() => orders.value.find((item) => item.id === selectedOrderId.value) || null)
const selectedPaymentOrderId = computed(() => selectedOrder.value?.payment_order?.id || null)
const selectedIsCheckoutOrder = computed(() => selectedOrder.value?.order_source !== 'single_product')
const pageStart = computed(() => (total.value ? (page.value - 1) * pageSize.value + 1 : 0))
const pageEnd = computed(() => Math.min(page.value * pageSize.value, total.value))
const orderDateDisplay = computed(() => orderDate.value || '选择日期')

const statusLabel: Record<string, string> = {
  pending_payment: '待支付',
  payment_created: '已创建支付',
  paid: '已支付',
  payment_failed: '支付失败',
  canceled: '已取消',
  expired: '已超时',
}

const paymentMethodLabel: Record<string, string> = {
  alipay: '支付宝',
  wechat: '微信支付',
  card: '银行卡',
}

const shippingMethodLabel: Record<string, string> = {
  standard: '标准配送',
  express: '快递配送',
  pickup: '到店自提',
}

const eventTypeLabel: Record<string, string> = {
  notify: '支付回调',
  sync: '主动同步',
  query: '支付查询',
  create: '创建支付',
}

const formatPaymentMethod = (method: string) => paymentMethodLabel[method] || method || '未知支付方式'
const formatShippingMethod = (method: string) => shippingMethodLabel[method] || method || '未知配送方式'
const formatEventType = (eventType: string) => eventTypeLabel[eventType] || eventType || '支付事件'
const formatDateTime = (value?: string | null) => (value ? new Date(value).toLocaleString() : '-')
const statusClass = (status: string) => {
  if (status === 'paid') return 'bg-emerald-50 text-emerald-600'
  if (status === 'expired') return 'bg-amber-50 text-amber-700'
  if (status === 'payment_failed' || status === 'canceled') return 'bg-rose-50 text-rose-600'
  return 'bg-slate-100 text-slate-500'
}

const orderAddress = computed(() => {
  const address = selectedOrder.value?.shipping_address || {}
  return [
    address.province,
    address.country,
    address.city,
    address.district,
    address.post_code,
    address.address,
    address.apartment,
  ]
    .map((value) => String(value || '').trim())
    .filter(Boolean)
    .join('') || '暂无收货地址'
})

const recipientName = computed(() => {
  const address = selectedOrder.value?.shipping_address || {}
  const firstName = String(address.first_name || '').trim()
  const lastName = String(address.last_name || '').trim()
  if (!firstName && !lastName) return '未填写'
  if (!firstName) return lastName
  if (!lastName) return firstName
  return firstName === lastName ? firstName : `${lastName} ${firstName}`
})

const loadOrders = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await commerceService.listCheckoutOrdersPage({
      page: page.value,
      page_size: pageSize.value,
      order_no: orderNoQuery.value.trim(),
      date_from: orderDate.value,
      date_to: orderDate.value,
    })
    orders.value = response.results
    total.value = response.total
    totalPages.value = response.total_pages

    if (!orders.value.length) {
      selectedOrderId.value = null
      events.value = []
      return
    }

    if (!selectedOrderId.value || !orders.value.some((order) => order.id === selectedOrderId.value)) {
      selectedOrderId.value = orders.value[0].id
    }
    await loadEvents()
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '订单加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

const loadEvents = async () => {
  if (!selectedPaymentOrderId.value) {
    events.value = []
    return
  }
  eventsLoading.value = true
  try {
    events.value = await commerceService.listPaymentEvents(selectedPaymentOrderId.value)
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '支付日志加载失败，请稍后重试。')
  } finally {
    eventsLoading.value = false
  }
}

const selectOrder = async (order: CommerceOrder) => {
  selectedOrderId.value = order.id
  isPaymentLogOpen.value = false
  await loadEvents()
}

const syncOrder = async (order: CommerceOrder) => {
  try {
    if (order.order_source === 'single_product' && order.payment_order?.id) {
      await commerceService.syncOrder(order.payment_order.id)
      await loadOrders()
      return
    }

    const next = await commerceService.syncCheckoutOrder(order.checkout_order_id || order.id)
    orders.value = orders.value.map((item) => (item.id === order.id ? next : item))
    if (selectedOrderId.value === order.id) {
      await loadEvents()
    }
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '订单同步失败，请稍后重试。')
  }
}

const submitSearch = () => {
  page.value = 1
  loadOrders()
}

const resetSearch = () => {
  orderNoQuery.value = ''
  orderDate.value = ''
  page.value = 1
  loadOrders()
}

const goPage = (nextPage: number) => {
  if (nextPage < 1 || nextPage > totalPages.value || nextPage === page.value) return
  page.value = nextPage
  loadOrders()
}

onMounted(loadOrders)
</script>

<template>
  <div class="grid min-h-[calc(100vh-120px)] gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
    <section class="min-w-0">
      <div class="mb-6 flex items-center justify-between gap-4">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">订单中心</p>
          <h1 class="mt-2 text-2xl font-bold text-slate-950">订单管理</h1>
        </div>
        <button
          class="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
          type="button"
          @click="loadOrders"
        >
          <RefreshCw :class="loading ? 'animate-spin' : ''" class="h-4 w-4" />
          刷新
        </button>
      </div>

      <div class="mb-4 rounded-2xl border border-slate-100 bg-white p-4">
        <div class="grid gap-3 lg:grid-cols-[minmax(260px,1fr)_190px_auto_auto]">
          <label class="block">
            <span class="mb-1 block text-xs font-bold text-slate-400">订单号</span>
            <div class="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2">
              <Search class="h-4 w-4 text-slate-400" />
              <input v-model="orderNoQuery" class="w-full bg-transparent text-sm outline-none" placeholder="输入完整或部分订单号" @keyup.enter="submitSearch" />
            </div>
          </label>
          <label class="block">
            <span class="mb-1 block text-xs font-bold text-slate-400">订单日期</span>
            <div class="relative">
              <span
                class="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-sm"
                :class="orderDate ? 'text-slate-900' : 'text-slate-400'"
              >
                {{ orderDateDisplay }}
              </span>
              <CalendarDays class="pointer-events-none absolute right-3 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                v-model="orderDate"
                type="date"
                class="order-date-input absolute inset-0 z-20 h-full w-full cursor-pointer opacity-0"
              />
              <div class="pointer-events-none h-[38px] rounded-xl border border-slate-200 bg-white"></div>
            </div>
          </label>
          <button class="self-end rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-bold text-white" type="button" @click="submitSearch">查询</button>
          <button class="self-end rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-bold text-slate-600" type="button" @click="resetSearch">重置</button>
        </div>
      </div>

      <div v-if="errorMessage" class="mb-4 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm font-semibold text-rose-600">
        {{ errorMessage }}
      </div>

      <div class="overflow-hidden rounded-2xl border border-slate-100 bg-white">
        <div class="max-h-[620px] overflow-auto">
          <table class="w-full min-w-[980px] text-left text-sm">
            <thead class="sticky top-0 z-10 bg-slate-50 text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <th class="px-5 py-4">订单号</th>
                <th class="px-5 py-4">客户</th>
                <th class="px-5 py-4">商品</th>
                <th class="px-5 py-4">金额</th>
                <th class="px-5 py-4">状态</th>
                <th class="px-5 py-4 text-right">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="order in orders"
                :key="order.id"
                class="cursor-pointer hover:bg-slate-50/70"
                :class="selectedOrderId === order.id ? 'bg-slate-50' : ''"
                @click="selectOrder(order)"
              >
                <td class="px-5 py-4">
                  <div class="font-mono text-xs font-bold text-slate-900">{{ order.order_no }}</div>
                  <div class="mt-1 text-xs text-slate-400">{{ formatDateTime(order.created_at) }}</div>
                </td>
                <td class="px-5 py-4">
                  <div class="font-bold text-slate-900">{{ order.contact_email || order.contact_phone || order.user_id }}</div>
                  <div class="mt-1 text-xs text-slate-400">{{ formatPaymentMethod(order.payment_method) }} · {{ formatShippingMethod(order.shipping_method) }}</div>
                </td>
                <td class="px-5 py-4">
                  <div class="font-bold text-slate-900">共 {{ order.items.length }} 件商品</div>
                  <div class="mt-1 text-xs text-slate-400">{{ order.items[0]?.name || '暂无商品' }}</div>
                </td>
                <td class="px-5 py-4 font-bold text-slate-900">¥{{ order.total_amount }}</td>
                <td class="px-5 py-4">
                  <span class="rounded-full px-3 py-1 text-xs font-bold" :class="statusClass(order.status)">
                    {{ statusLabel[order.status] || order.status }}
                  </span>
                </td>
                <td class="px-5 py-4 text-right">
                  <button class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-700" type="button" @click.stop="syncOrder(order)">
                    同步
                  </button>
                </td>
              </tr>
              <tr v-if="!orders.length && !loading">
                <td colspan="6" class="px-5 py-12 text-center text-slate-400">没有找到符合条件的订单。</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-4 text-sm text-slate-500">
          <span>显示 {{ pageStart }}-{{ pageEnd }} 条，共 {{ total }} 条</span>
          <div class="flex items-center gap-2">
            <button class="rounded-lg border border-slate-200 p-2 disabled:opacity-40" type="button" :disabled="page <= 1" @click="goPage(page - 1)">
              <ChevronLeft class="h-4 w-4" />
            </button>
            <span class="px-2 font-semibold text-slate-700">第 {{ page }} / {{ totalPages }} 页</span>
            <button class="rounded-lg border border-slate-200 p-2 disabled:opacity-40" type="button" :disabled="page >= totalPages" @click="goPage(page + 1)">
              <ChevronRight class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </section>

    <aside class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <div class="mb-5 flex items-center gap-3">
        <ShieldCheck class="h-5 w-5 text-emerald-600" />
        <h2 class="text-lg font-bold text-slate-950">订单详情</h2>
      </div>

      <div v-if="selectedOrder" class="space-y-5">
        <div class="rounded-xl bg-slate-50 p-4 text-sm">
          <p class="font-bold text-slate-900">{{ selectedOrder.order_no }}</p>
          <p class="mt-1 text-xs text-slate-500">{{ selectedOrder.payment_order?.out_trade_no || '暂无支付单号' }}</p>
          <div class="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-500">
            <p>总计：¥{{ selectedOrder.total_amount }}</p>
            <p>状态：{{ statusLabel[selectedOrder.status] || selectedOrder.status }}</p>
            <p>创建：{{ formatDateTime(selectedOrder.created_at) }}</p>
            <p>支付截止：{{ formatDateTime(selectedOrder.expires_at) }}</p>
          </div>
        </div>

        <div>
          <h3 class="mb-3 text-sm font-bold text-slate-900">收货信息</h3>
          <div class="rounded-xl border border-slate-100 p-4 text-sm leading-7 text-slate-500">
            <p><span class="font-bold text-slate-800">{{ recipientName }}</span> {{ selectedOrder.contact_phone }}</p>
            <p>{{ selectedOrder.contact_email || '暂无邮箱' }}</p>
            <p>{{ orderAddress }}</p>
          </div>
        </div>

        <div>
          <h3 class="mb-3 text-sm font-bold text-slate-900">商品</h3>
          <div class="space-y-3">
            <article v-for="item in selectedOrder.items" :key="item.id" class="flex gap-3 rounded-xl border border-slate-100 p-3">
              <img :src="item.image_url" :alt="item.name" class="h-14 w-14 rounded-lg object-cover" />
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-bold text-slate-900">{{ item.name }}</p>
                <p class="mt-1 text-xs text-slate-400">数量 {{ item.quantity }} · ¥{{ item.line_total }}</p>
              </div>
            </article>
          </div>
        </div>

        <div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-4 text-xs text-slate-500">
          <div class="flex items-start gap-2">
            <CreditCard class="mt-0.5 h-4 w-4 text-slate-400" />
            <p>支付日志用于排查“用户已付款但订单未更新”、签名异常、金额不匹配等问题。日常查看订单时可以保持折叠。</p>
          </div>
        </div>

        <div class="border-t border-slate-100 pt-5">
          <button class="flex w-full items-center justify-between text-left text-sm font-bold text-slate-900" type="button" @click="isPaymentLogOpen = !isPaymentLogOpen">
            <span class="inline-flex items-center gap-2"><ListChecks class="h-4 w-4" /> 支付日志</span>
            <span class="text-xs text-slate-400">{{ isPaymentLogOpen ? '收起' : `展开 (${events.length})` }}</span>
          </button>

          <div v-if="isPaymentLogOpen" class="mt-4 space-y-3">
            <div v-if="eventsLoading" class="rounded-xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-400">
              正在加载支付日志...
            </div>

            <article v-for="event in events" v-else :key="event.id" class="rounded-xl border border-slate-100 p-4">
              <div class="flex items-center justify-between gap-3">
                <span class="text-xs font-bold uppercase tracking-[0.16em] text-slate-400">{{ formatEventType(event.event_type) }}</span>
                <span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="event.processed ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'">
                  {{ event.processed ? '已处理' : '已记录' }}
                </span>
              </div>
              <div class="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-500">
                <span>签名：{{ event.signature_valid ? '有效' : '无效' }}</span>
                <span>金额：{{ event.amount_matches ? '匹配' : '不匹配' }}</span>
              </div>
              <p class="mt-3 text-xs text-slate-500">{{ event.message || '暂无事件消息。' }}</p>
              <p class="mt-2 text-[11px] text-slate-400">{{ formatDateTime(event.created_at) }}</p>
            </article>

            <div v-if="!eventsLoading && !events.length" class="rounded-xl border border-dashed border-slate-200 px-4 py-8 text-center text-sm text-slate-400">
              当前订单暂无支付日志。
            </div>
          </div>
        </div>
      </div>

      <div v-else class="rounded-xl border border-dashed border-slate-200 px-4 py-14 text-center text-sm text-slate-400">
        请选择一条订单查看详情。
      </div>
    </aside>
  </div>
</template>

<style scoped>
.order-date-input {
  color-scheme: light;
}
</style>
