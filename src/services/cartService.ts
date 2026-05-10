export interface CartItem {
  id: string
  productId: number | null
  name: string
  sku?: string
  meta: string
  size?: string
  color?: string
  price: string
  image: string
  quantity: number
  currency?: string
  shippingCents?: number
  productSnapshot?: Record<string, any>
}

const CART_KEY = 'ct_cart_items'
export const CART_UPDATED_EVENT = 'ct-cart-updated'
const PRODUCT_LIST_CACHE_KEYS = ['lvyou_public_products_cache', 'lvyou_public_products_cache_v2']
const RECENTLY_VIEWED_KEY = 'lvyou_recently_viewed_products'
const CART_ITEM_LIMIT = 30
const CART_TEXT_LIMIT = 120
const CART_META_LIMIT = 160
const CART_IMAGE_LIMIT = 1000

const notifyCartUpdated = () => {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(CART_UPDATED_EVENT))
}

const trimStoredText = (value: unknown, maxLength = CART_TEXT_LIMIT) => String(value || '').slice(0, maxLength)

const normalizeStoredImage = (value: unknown) => {
  const image = trimStoredText(value, CART_IMAGE_LIMIT)
  if (image.startsWith('data:')) return ''
  return image
}

export const getCartItemImage = (item: Partial<CartItem>) => {
  const image = normalizeStoredImage(item.image || item.productSnapshot?.image_url)
  return image
}

const normalizeProductSnapshot = (snapshot: Record<string, any> | undefined, item: Partial<CartItem>) => {
  if (!snapshot && !item.productId) return undefined

  const metadata = snapshot?.metadata || {}
  return {
    id: Number(snapshot?.id || item.productId || 0) || null,
    sku: trimStoredText(snapshot?.sku || item.sku),
    name: trimStoredText(snapshot?.name || item.name),
    image_url: getCartItemImage({ ...item, productSnapshot: snapshot }),
    price_cents: Number(snapshot?.price_cents || 0) || 0,
    currency: trimStoredText(snapshot?.currency || item.currency || 'CNY', 12),
    metadata: {
      shipping_cents: Number(metadata.shipping_cents || item.shippingCents || 0) || 0,
      requires_size: metadata.requires_size === true,
      requires_color: metadata.requires_color === true,
    },
  }
}

export const normalizeCartItem = (item: CartItem): CartItem | null => {
  const id = trimStoredText(item?.id, CART_META_LIMIT)
  if (!id) return null

  const quantity = Math.min(99, Math.max(1, Number(item.quantity || 1) || 1))
  const normalized: CartItem = {
    id,
    productId: item.productId ? Number(item.productId) : null,
    name: trimStoredText(item.name),
    sku: trimStoredText(item.sku),
    meta: trimStoredText(item.meta, CART_META_LIMIT),
    size: trimStoredText(item.size, 32),
    color: trimStoredText(item.color, 32),
    price: trimStoredText(item.price, 32),
    image: getCartItemImage(item),
    quantity,
    currency: trimStoredText(item.currency || 'CNY', 12),
    shippingCents: Number(item.shippingCents || item.productSnapshot?.metadata?.shipping_cents || 0) || 0,
  }
  normalized.productSnapshot = normalizeProductSnapshot(item.productSnapshot, normalized)
  return normalized
}

export const normalizeCartItems = (items: CartItem[]) => items
  .map(normalizeCartItem)
  .filter((item): item is CartItem => !!item)
  .slice(0, CART_ITEM_LIMIT)

export const readCartItems = (): CartItem[] => {
  if (typeof window === 'undefined') return []
  try {
    const raw = window.localStorage.getItem(CART_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? normalizeCartItems(parsed) : []
  } catch {
    try {
      window.localStorage.removeItem(CART_KEY)
    } catch {
      // Ignore storage access failures.
    }
    return []
  }
}

export const writeCartItems = (items: CartItem[]) => {
  if (typeof window === 'undefined') return
  const normalizedItems = normalizeCartItems(items)
  const compactItems = normalizedItems.map((item) => ({
    ...item,
    productSnapshot: item.productSnapshot ? normalizeProductSnapshot(item.productSnapshot, item) : undefined,
  }))

  const payloads = [
    normalizedItems,
    compactItems,
    compactItems.slice(0, Math.max(1, Math.floor(CART_ITEM_LIMIT / 2))),
  ]

  for (const payload of payloads) {
    try {
      window.localStorage.setItem(CART_KEY, JSON.stringify(payload))
      notifyCartUpdated()
      return
    } catch {
      // Try a smaller payload before giving up.
    }
  }

  try {
    PRODUCT_LIST_CACHE_KEYS.forEach((key) => window.localStorage.removeItem(key))
    window.localStorage.removeItem(RECENTLY_VIEWED_KEY)
    window.localStorage.removeItem(CART_KEY)
  } catch {
    // Continue to the final write attempts.
  }

  for (const payload of payloads) {
    try {
      window.localStorage.setItem(CART_KEY, JSON.stringify(payload))
      notifyCartUpdated()
      return
    } catch {
      // Storage is still unavailable.
    }
  }

  try {
    window.localStorage.removeItem(CART_KEY)
  } catch {
    // Ignore quota, private mode, or disabled storage failures.
  }
  notifyCartUpdated()
}

export const addCartItem = (item: CartItem) => {
  const items = readCartItems()
  const existing = items.find((entry) => entry.id === item.id)

  if (existing) {
    existing.quantity = Math.min(99, existing.quantity + item.quantity)
    writeCartItems([...items])
    return existing
  }

  writeCartItems([item, ...items])
  return item
}

export const removeCartItem = (id: string) => {
  writeCartItems(readCartItems().filter((item) => item.id !== id))
}

export const removeCartItems = (ids: string[]) => {
  const idSet = new Set(ids)
  writeCartItems(readCartItems().filter((item) => !idSet.has(item.id)))
}

export const clearCartItems = () => {
  writeCartItems([])
}
