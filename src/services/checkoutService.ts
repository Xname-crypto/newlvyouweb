import { normalizeCartItems, type CartItem } from '@/services/cartService'
import type { CommerceOrder } from '@/services/commerceService'

export interface CheckoutDraftAddress {
  first_name: string
  last_name: string
  address: string
  apartment: string
  city: string
  country: string
  post_code: string
  phone: string
  email?: string
}

export interface CheckoutDraft {
  orderId?: number
  orderNo?: string
  cachedOrder?: CommerceOrder
  checkoutPayUrl?: string
  items: CartItem[]
  shippingAddress: CheckoutDraftAddress
  shippingMethod: string
  paymentMethod: 'alipay'
  contactEmail: string
  contactPhone: string
  note: string
}

const CHECKOUT_DRAFT_KEY = 'ct_checkout_draft'
const RECOMMENDATION_CACHE_KEY = 'ct_checkout_recommendations'
const DRAFT_TEXT_LIMIT = 200

const emptyAddress = (): CheckoutDraftAddress => ({
  first_name: '',
  last_name: '',
  address: '',
  apartment: '',
  city: '',
  country: '',
  post_code: '',
  phone: '',
  email: '',
})

export const createEmptyCheckoutDraft = (): CheckoutDraft => ({
  items: [],
  shippingAddress: emptyAddress(),
  shippingMethod: 'standard',
  paymentMethod: 'alipay',
  contactEmail: '',
  contactPhone: '',
  note: '',
})

export const readCheckoutDraft = (): CheckoutDraft => {
  if (typeof window === 'undefined') return createEmptyCheckoutDraft()
  try {
    const raw = window.sessionStorage.getItem(CHECKOUT_DRAFT_KEY)
    if (!raw) return createEmptyCheckoutDraft()
    const parsed = JSON.parse(raw)
    return {
      ...createEmptyCheckoutDraft(),
      ...parsed,
      cachedOrder: undefined,
      shippingAddress: {
        ...emptyAddress(),
        ...(parsed?.shippingAddress || {}),
      },
      items: Array.isArray(parsed?.items) ? normalizeCartItems(parsed.items) : [],
      note: String(parsed?.note || '').slice(0, DRAFT_TEXT_LIMIT),
    }
  } catch {
    try {
      window.sessionStorage.removeItem(CHECKOUT_DRAFT_KEY)
    } catch {
      // Ignore storage access failures.
    }
    return createEmptyCheckoutDraft()
  }
}

const compactCheckoutDraft = (draft: CheckoutDraft): CheckoutDraft => ({
  ...createEmptyCheckoutDraft(),
  orderId: draft.orderId,
  orderNo: draft.orderNo,
  checkoutPayUrl: draft.checkoutPayUrl,
  items: normalizeCartItems(draft.items || []),
  shippingAddress: {
    ...emptyAddress(),
    ...(draft.shippingAddress || {}),
  },
  shippingMethod: draft.shippingMethod || 'standard',
  paymentMethod: 'alipay',
  contactEmail: String(draft.contactEmail || '').slice(0, DRAFT_TEXT_LIMIT),
  contactPhone: String(draft.contactPhone || '').slice(0, DRAFT_TEXT_LIMIT),
  note: String(draft.note || '').slice(0, DRAFT_TEXT_LIMIT),
})

export const writeCheckoutDraft = (draft: CheckoutDraft) => {
  if (typeof window === 'undefined') return
  const compactDraft = compactCheckoutDraft(draft)
  const payloads = [
    compactDraft,
    {
      ...compactDraft,
      checkoutPayUrl: '',
      note: '',
    },
  ]

  for (const payload of payloads) {
    try {
      window.sessionStorage.setItem(CHECKOUT_DRAFT_KEY, JSON.stringify(payload))
      return
    } catch {
      // Try smaller payloads below.
    }
  }

  try {
    window.sessionStorage.removeItem(RECOMMENDATION_CACHE_KEY)
    window.sessionStorage.removeItem(CHECKOUT_DRAFT_KEY)
  } catch {
    // Continue to final write attempts.
  }

  for (const payload of payloads) {
    try {
      window.sessionStorage.setItem(CHECKOUT_DRAFT_KEY, JSON.stringify(payload))
      return
    } catch {
      // Storage is still unavailable.
    }
  }
}

export const clearCheckoutDraft = () => {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(CHECKOUT_DRAFT_KEY)
}
