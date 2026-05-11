import { safeGetSupabaseSession } from '@/utils/supabase'
import { apiUrl } from '@/utils/apiBase'

export interface Product {
  id: number
  sku: string
  name: string
  description: string
  category: string
  image_url: string
  price_cents: number
  price: string
  currency: string
  is_active: boolean
  stock_total: number
  stock_reserved: number
  stock_sold: number
  available_stock: number
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

const normalizeProductImageValue = (value: unknown) => String(value || '').trim()

const BACKEND_IMAGE_PATH_PREFIXES = ['/api/', '/media/']

export const resolveProductImageUrl = (value: unknown) => {
  const image = normalizeProductImageValue(value)
  if (!image) return ''
  if (/^(https?:|data:|blob:)/i.test(image) || image.startsWith('//')) return image

  const path = image.startsWith('/') ? image : `/${image}`
  if (BACKEND_IMAGE_PATH_PREFIXES.some((prefix) => path.startsWith(prefix))) {
    return apiUrl(path)
  }

  return path
}

export const isInlineProductImage = (value: unknown) => normalizeProductImageValue(value).startsWith('data:')

export const isUsableProductImage = (value: unknown) => {
  const image = normalizeProductImageValue(value)
  return !!image
}

const getProductMetadataImages = (product: Partial<Product>) => {
  const metadata = product.metadata || {}
  const images = Array.isArray(metadata.images) ? metadata.images : []
  return images.map(resolveProductImageUrl).filter(isUsableProductImage)
}

export const getProductImages = (product: Partial<Product>) => {
  const images = [
    resolveProductImageUrl(product.image_url),
    ...getProductMetadataImages(product),
  ].filter(isUsableProductImage)

  return Array.from(new Set(images))
}

export const getProductImage = (product: Partial<Product>) => getProductImages(product)[0] || ''

export interface PaymentOrder {
  id: number
  user_id: string
  commerce_order: number | null
  commerce_order_no: string
  product: number | null
  product_name: string
  product_snapshot: Record<string, any>
  quantity: number
  unit_price_cents: number
  unit_price: string
  total_amount_cents: number
  total_amount: string
  currency: string
  status: string
  payment_provider: string
  payment_type: 'alipay' | 'wxpay'
  out_trade_no: string
  zpay_trade_no: string
  zpay_order_id: string
  pay_url: string
  client_request_id: string
  paid_at: string | null
  expires_at: string | null
  created_at: string
  updated_at: string
}

export interface CommerceOrderItem {
  id: number
  product: number | null
  product_snapshot: Record<string, any>
  sku: string
  name: string
  image_url: string
  unit_price_cents: number
  unit_price: string
  quantity: number
  line_total_cents: number
  line_total: string
  selected_size: string
  selected_color: string
  cart_item_id: string
  metadata: Record<string, any>
  created_at: string
}

export interface CommerceOrder {
  id: number
  order_source?: 'checkout' | 'single_product'
  checkout_order_id?: number | null
  order_no: string
  user_id: string
  status: string
  subtotal_cents: number
  subtotal: string
  shipping_cents: number
  shipping: string
  discount_cents: number
  discount: string
  total_amount_cents: number
  total_amount: string
  currency: string
  payment_method: 'alipay'
  shipping_method: string
  shipping_address: Record<string, any>
  contact_email: string
  contact_phone: string
  note: string
  paid_at: string | null
  expires_at: string | null
  created_at: string
  updated_at: string
  items: CommerceOrderItem[]
  payment_order: PaymentOrder | null
}

export interface PaymentEvent {
  id: number
  order: number | null
  source: string
  event_type: string
  signature_valid: boolean
  amount_matches: boolean
  processed: boolean
  payload: Record<string, any>
  message: string
  created_at: string
}

export interface PaginatedCommerceOrders {
  results: CommerceOrder[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

interface RequestOptions extends RequestInit {
  body?: any
  requireAuth?: boolean
}

const getToken = async () => {
  const session = await safeGetSupabaseSession()
  return session?.access_token || ''
}

const request = async <T>(url: string, options: RequestOptions = {}): Promise<T> => {
  const token = await getToken()
  if (options.requireAuth && !token) {
    throw new Error('请先登录后再继续购买')
  }

  const response = await fetch(apiUrl(url), {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!response.ok) {
    let message = `Request failed: ${response.status}`
    try {
      const text = await response.text()
      if (text) {
        try {
          const data = JSON.parse(text)
          message = data.error || data.detail || text
        } catch {
          message = text
        }
      }
    } catch {
      // Keep fallback.
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

const PRODUCT_LIST_CACHE_MS = 30_000
const PRODUCT_LIST_STORAGE_KEY = 'lvyou_public_products_cache_v2'
const LEGACY_PRODUCT_LIST_STORAGE_KEYS = ['lvyou_public_products_cache']
let productListCache: { expiresAt: number; data: Product[] } | null = null
let productListRequest: Promise<Product[]> | null = null

const compactCachedProduct = (product: Product): Product => {
  const metadata = product.metadata || {}
  const cacheableImageUrl = isInlineProductImage(product.image_url) ? '' : String(product.image_url || '')
  const cacheableImages = getProductMetadataImages(product).filter((image) => !isInlineProductImage(image)).slice(0, 8)
  return {
    ...product,
    description: String(product.description || '').slice(0, 240),
    image_url: cacheableImageUrl,
    metadata: {
      type: metadata.type,
      product_type: metadata.product_type,
      old_price_cents: metadata.old_price_cents,
      requires_size: metadata.requires_size,
      requires_color: metadata.requires_color,
      sizes: Array.isArray(metadata.sizes) ? metadata.sizes.slice(0, 8) : undefined,
      colors: Array.isArray(metadata.colors) ? metadata.colors.slice(0, 12) : undefined,
      images: cacheableImages.length ? cacheableImages : undefined,
    },
  }
}

const readStoredProductList = () => {
  if (typeof localStorage === 'undefined') return null
  try {
    const parsed = JSON.parse(localStorage.getItem(PRODUCT_LIST_STORAGE_KEY) || 'null')
    if (!parsed || !Array.isArray(parsed.data) || Number(parsed.expiresAt || 0) <= Date.now()) return null
    return parsed as { expiresAt: number; data: Product[] }
  } catch {
    return null
  }
}

const writeStoredProductList = (data: Product[]) => {
  if (typeof localStorage === 'undefined') return
  const hasInlineImages = data.some((product) => getProductImages(product).some(isInlineProductImage))
  try {
    LEGACY_PRODUCT_LIST_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key))
    if (hasInlineImages) {
      localStorage.removeItem(PRODUCT_LIST_STORAGE_KEY)
      return
    }
    localStorage.setItem(PRODUCT_LIST_STORAGE_KEY, JSON.stringify({
      data: data.map(compactCachedProduct),
      expiresAt: Date.now() + PRODUCT_LIST_CACHE_MS,
    }))
  } catch {
    // Ignore storage quota or private mode failures.
  }
}

const clearProductListCache = () => {
  productListCache = null
  productListRequest = null
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem(PRODUCT_LIST_STORAGE_KEY)
    LEGACY_PRODUCT_LIST_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key))
  }
}

const normalizeSnapshotImages = (snapshot: Record<string, any>) => {
  if (!snapshot || typeof snapshot !== 'object') return snapshot

  const metadata = snapshot.metadata && typeof snapshot.metadata === 'object'
    ? {
        ...snapshot.metadata,
        images: Array.isArray(snapshot.metadata.images)
          ? snapshot.metadata.images.map(resolveProductImageUrl).filter(isUsableProductImage)
          : snapshot.metadata.images,
      }
    : snapshot.metadata

  return {
    ...snapshot,
    image_url: resolveProductImageUrl(snapshot.image_url),
    metadata,
  }
}

const normalizePaymentOrderImages = (order: PaymentOrder): PaymentOrder => ({
  ...order,
  product_snapshot: normalizeSnapshotImages(order.product_snapshot),
})

const normalizeCommerceOrderImages = (order: CommerceOrder): CommerceOrder => ({
  ...order,
  items: Array.isArray(order.items)
    ? order.items.map((item) => ({
        ...item,
        image_url: resolveProductImageUrl(item.image_url),
        product_snapshot: normalizeSnapshotImages(item.product_snapshot),
      }))
    : order.items,
  payment_order: order.payment_order ? normalizePaymentOrderImages(order.payment_order) : order.payment_order,
})

const listPublicProducts = () => {
  const now = Date.now()
  if (productListCache && productListCache.expiresAt > now) {
    return Promise.resolve(productListCache.data)
  }
  const storedCache = readStoredProductList()
  if (storedCache) {
    productListCache = storedCache
    return Promise.resolve(storedCache.data)
  }
  if (productListRequest) return productListRequest

  productListRequest = request<Product[]>('/api/products/')
    .then((data) => {
      productListCache = {
        data,
        expiresAt: Date.now() + PRODUCT_LIST_CACHE_MS,
      }
      writeStoredProductList(data)
      return data
    })
    .finally(() => {
      productListRequest = null
    })

  return productListRequest
}

export const commerceService = {
  getCachedProducts() {
    const now = Date.now()
    if (productListCache && productListCache.expiresAt > now) return productListCache.data
    const storedCache = readStoredProductList()
    if (!storedCache) return []
    productListCache = storedCache
    return storedCache.data
  },

  listProducts(admin = false) {
    if (admin) return request<Product[]>('/api/products/?all=1')
    return listPublicProducts()
  },

  getProduct(id: number | string) {
    return request<Product>(`/api/products/${id}/`)
  },

  getProductForEdit(id: number | string) {
    return request<Product>(`/api/products/${id}/?full=1`, {
      requireAuth: true,
    })
  },

  createProduct(payload: Partial<Product>) {
    clearProductListCache()
    return request<Product>('/api/products/', {
      method: 'POST',
      body: payload,
      requireAuth: true,
    })
  },

  updateProduct(id: number | string, payload: Partial<Product>) {
    clearProductListCache()
    return request<Product>(`/api/products/${id}/`, {
      method: 'PATCH',
      body: payload,
      requireAuth: true,
    })
  },

  listOrders(admin = false) {
    return request<PaymentOrder[]>(admin ? '/api/orders/?all=1' : '/api/orders/', {
      requireAuth: true,
    }).then((orders) => orders.map(normalizePaymentOrderImages))
  },

  getOrder(id: number | string) {
    return request<PaymentOrder>(`/api/orders/${id}/`, {
      requireAuth: true,
    }).then(normalizePaymentOrderImages)
  },

  createOrder(payload: { product_id: number; quantity: number; payment_type: 'alipay' | 'wxpay'; client_request_id?: string }) {
    return request<PaymentOrder>('/api/orders/', {
      method: 'POST',
      body: payload,
      requireAuth: true,
    }).then(normalizePaymentOrderImages)
  },

  createZpayPayment(orderId: number | string) {
    return request<{ order: PaymentOrder; pay_url: string }>(`/api/orders/${orderId}/zpay/`, {
      method: 'POST',
      requireAuth: true,
    }).then((result) => ({ ...result, order: normalizePaymentOrderImages(result.order) }))
  },

  syncOrder(orderId: number | string) {
    return request<PaymentOrder>(`/api/orders/${orderId}/sync/`, {
      requireAuth: true,
    }).then(normalizePaymentOrderImages)
  },

  cancelOrder(orderId: number | string) {
    return request<PaymentOrder>(`/api/orders/${orderId}/cancel/`, {
      method: 'POST',
      requireAuth: true,
    }).then(normalizePaymentOrderImages)
  },

  listPaymentEvents(orderId?: number | string) {
    const suffix = orderId ? `?order=${encodeURIComponent(String(orderId))}` : ''
    return request<PaymentEvent[]>(`/api/payment-events/${suffix}`, {
      requireAuth: true,
    })
  },

  listCheckoutOrders(admin = false) {
    return request<CommerceOrder[]>(admin ? '/api/checkout/orders/?all=1' : '/api/checkout/orders/', {
      requireAuth: true,
    }).then((orders) => orders.map(normalizeCommerceOrderImages))
  },

  listCheckoutOrdersPage(params: {
    page?: number
    page_size?: number
    order_no?: string
    date_from?: string
    date_to?: string
  } = {}) {
    const query = new URLSearchParams({ all: '1' })
    if (params.page) query.set('page', String(params.page))
    if (params.page_size) query.set('page_size', String(params.page_size))
    if (params.order_no) query.set('order_no', params.order_no)
    if (params.date_from) query.set('date_from', params.date_from)
    if (params.date_to) query.set('date_to', params.date_to)
    return request<PaginatedCommerceOrders>(`/api/checkout/orders/?${query.toString()}`, {
      requireAuth: true,
    }).then((page) => ({
      ...page,
      results: Array.isArray(page.results) ? page.results.map(normalizeCommerceOrderImages) : page.results,
    }))
  },

  getCheckoutOrder(id: number | string) {
    return request<CommerceOrder>(`/api/checkout/orders/${id}/`, {
      requireAuth: true,
    }).then(normalizeCommerceOrderImages)
  },

  createCheckoutOrder(payload: {
    items: Array<{
      id?: string
      cart_item_id?: string
      product_id: number
      quantity: number
      selected_size?: string
      selected_color?: string
      size?: string
      color?: string
      metadata?: Record<string, any>
    }>
    shipping_address: Record<string, any>
    shipping_method?: string
    payment_method?: 'alipay'
    contact_email?: string
    contact_phone?: string
    note?: string
    client_request_id?: string
  }) {
    return request<CommerceOrder>('/api/checkout/orders/', {
      method: 'POST',
      body: payload,
      requireAuth: true,
    }).then(normalizeCommerceOrderImages)
  },

  createCheckoutPayment(orderId: number | string) {
    return request<{ order: CommerceOrder; pay_url: string }>(`/api/checkout/orders/${orderId}/pay/`, {
      method: 'POST',
      requireAuth: true,
    }).then((result) => ({ ...result, order: normalizeCommerceOrderImages(result.order) }))
  },

  syncCheckoutOrder(orderId: number | string) {
    return request<CommerceOrder>(`/api/checkout/orders/${orderId}/sync/`, {
      method: 'POST',
      requireAuth: true,
    }).then(normalizeCommerceOrderImages)
  },

  cancelCheckoutOrder(orderId: number | string) {
    return request<CommerceOrder>(`/api/checkout/orders/${orderId}/cancel/`, {
      method: 'POST',
      requireAuth: true,
    }).then(normalizeCommerceOrderImages)
  },
}
