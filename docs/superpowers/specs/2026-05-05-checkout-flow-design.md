# Checkout Flow Design

Date: 2026-05-05

## Goal

Build a complete product checkout flow that matches the provided design drafts and uses real backend product data as the source of truth. The flow covers cart review, shipping address entry, order confirmation, Alipay QR payment, payment pending, and payment success.

## Decisions

- Product data must be driven by backend `Product` records.
- The frontend cart remains a temporary local store, but checkout must validate every cart item against the backend before creating an order.
- Items without a valid backend `product_id` cannot enter payment. The UI should ask the user to re-add the product from the catalogue.
- The checkout payment method is Alipay through the existing zpay integration.
- The order model should be a normal commerce order: one main order with many order items.
- The existing `PaymentOrder` model should become a payment record linked to the main commerce order, not the only source of order truth.

## Existing Context

The current cart is stored in `localStorage` by `src/services/cartService.ts`. Each cart item currently stores a product snapshot with fields like name, image, price, quantity, and optional `productId`.

The current product detail page can build product display data from route query parameters. This makes it possible for a cart item to exist without a reliable backend product record. That is acceptable for visual prototyping, but it is not acceptable for a real checkout flow because price, stock, and product status cannot be trusted.

The backend already has:

- `Product`
- `PaymentOrder`
- `PaymentEvent`
- zpay payment creation, query, and notify helpers

The backend does not yet have a commerce order model that supports multiple items, shipping address, shipping method, discount totals, and a clean separation between order state and payment state.

## Recommended Architecture

Add a new commerce order layer and keep the current payment layer.

### CommerceOrder

Represents the customer's business order.

Suggested fields:

- `order_no`
- `user_id`
- `status`
- `subtotal_cents`
- `shipping_cents`
- `discount_cents`
- `total_amount_cents`
- `currency`
- `payment_method`
- `shipping_method`
- `shipping_address`
- `contact_email`
- `contact_phone`
- `note`
- `created_at`
- `updated_at`
- `paid_at`

### CommerceOrderItem

Represents one purchased product line.

Suggested fields:

- `order`
- `product`
- `product_snapshot`
- `sku`
- `name`
- `image_url`
- `unit_price_cents`
- `quantity`
- `line_total_cents`
- `selected_size`
- `selected_color`
- `metadata`

### PaymentOrder

Represents one zpay payment attempt or payment record. It should link back to `CommerceOrder`.

Suggested change:

- Add nullable `commerce_order` foreign key.
- Preserve existing single-product fields for backward compatibility during migration.
- For the new checkout flow, build zpay payloads from the linked `CommerceOrder`.

## Product Data Rules

Checkout must treat backend product data as authoritative.

When creating an order:

1. Receive cart item payloads from the frontend.
2. Require every item to include a valid `product_id`.
3. Fetch all products by ID from the backend.
4. Reject missing, inactive, or out-of-stock products.
5. Use backend `price_cents`, `currency`, `name`, `sku`, and `image_url` when writing order items.
6. Keep frontend-selected size and color as order item metadata.
7. Ignore frontend-submitted price for calculation. It may be used only for display before server validation.

This prevents URL-edited prices or stale cart snapshots from producing invalid orders.

## Frontend Flow

### `/cart`

Review cart items. The visual style should follow the supplied cart/payment design draft:

- Product image, name, price, selected size, selected color, quantity controls, delete button.
- Subtotal section.
- Right-side checkout/payment summary on desktop.
- Proceed button to checkout information.

Before proceeding, validate that every cart item has a valid `productId`. If not, show an inline message and ask the user to re-add the product.

### `/checkout/information`

Collect contact and shipping address:

- First name
- Last name
- Address
- Apartment or suite
- City
- Country
- Post code
- Phone
- Email or logged-in contact email

Keep the checkout draft in `sessionStorage` so refreshes do not lose the user's progress.

### `/checkout/confirmation`

Show:

- Contact
- Shipping address
- Shipping method
- Payment method: Alipay
- Order summary
- Total amount

Clicking confirm creates the backend `CommerceOrder` and its related `CommerceOrderItem` records.

### `/checkout/payment`

Create or reuse the linked `PaymentOrder`, call zpay, and display the Alipay QR payment area:

- Alipay label
- Amount
- QR code or payment link
- Countdown
- Order summary

If zpay returns a direct payment URL instead of an image QR code, show a QR generated from the URL when feasible and provide a payment button as fallback.

### `/checkout/pending`

Poll order/payment status every 3 to 5 seconds.

When paid:

- Navigate to `/checkout/success?order=<id>`.
- Clear only the cart items included in the paid order.

When failed or canceled:

- Show a recoverable message and allow returning to payment.

### `/checkout/success`

Show:

- Success check mark
- Order number
- Customer information
- Shipping address
- Payment method
- Order summary
- Recommended products section

This page should match the supplied success and confirmation design drafts.

## API Design

Add checkout-specific endpoints instead of overloading the current single-product order endpoint.

- `POST /api/checkout/orders/`
- `GET /api/checkout/orders/`
- `GET /api/checkout/orders/{id}/`
- `POST /api/checkout/orders/{id}/pay/`
- `POST /api/checkout/orders/{id}/sync/`
- `POST /api/checkout/orders/{id}/cancel/`

The existing `/api/orders/` endpoints can remain for backward compatibility while the new checkout flow moves to `/api/checkout/orders/`.

## Order Statuses

Suggested main order statuses:

- `pending_payment`
- `payment_created`
- `paid`
- `payment_failed`
- `canceled`

Payment success should update both records:

- `PaymentOrder.status = paid`
- `CommerceOrder.status = paid`

## Error Handling

The UI should handle these cases:

- Empty cart
- Cart item missing `productId`
- Product not found
- Product inactive
- Product out of stock
- Price changed since item was added to cart
- zpay not configured
- zpay payment creation failed
- Payment pending timeout
- Payment failed or canceled

For price changes, show the refreshed backend price and ask the user to review the cart again.

## Testing Plan

Backend:

- Create a multi-item order from valid products.
- Reject missing product IDs.
- Reject inactive or out-of-stock products.
- Ignore frontend-submitted prices during total calculation.
- Create zpay payment for a commerce order.
- Sync paid status into both `PaymentOrder` and `CommerceOrder`.
- Process zpay notify into both records.

Frontend:

- Cart renders real product-backed items.
- Checkout blocks invalid cart items.
- Address form validates required fields.
- Confirmation creates a real order.
- Payment page displays zpay result.
- Pending page polls and redirects after payment.
- Success page renders paid order details.
- Paid items are removed from local cart.

## Implementation Notes

Keep the implementation incremental:

1. Add backend models, serializers, viewsets, routes, and migrations.
2. Update zpay helpers to support commerce orders while preserving current behavior.
3. Update `commerceService.ts` with checkout APIs.
4. Strengthen `cartService.ts` so cart items keep structured `productId`, size, color, and snapshot fields.
5. Ensure catalogue and detail pages use backend `Product` data before items can be added to cart.
6. Build the checkout pages and route them through Vue Router.
7. Keep `PaymentResult.vue` as a compatibility page that can redirect into the new checkout status pages.

## Open Scope

The design does not include refunds, coupons beyond a display-only discount area, shipment tracking, split fulfillment, or multi-payment retry history. Those can be added after the core checkout flow is stable.
