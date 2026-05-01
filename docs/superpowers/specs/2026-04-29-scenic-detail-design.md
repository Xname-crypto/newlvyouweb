# Scenic Detail Page Design

Date: 2026-04-29

## Summary

Build a reusable scenic detail page template for the Vue frontend. Users enter from the scenic search card list and land on a dedicated detail route. The first iteration uses static mock data, but the page contract must be structured so real scenic data can replace the mock source later with minimal component changes.

## Goals

- Add a dedicated scenic detail page reached by clicking a scenic card in `/scenic-search`.
- Recreate the screenshot's main body layout as closely as practical while keeping the existing shared `Navigation` and `Footer`.
- Drive the page from a normalized data object rather than hardcoded copy inside the view.
- Keep the transition path to real backend data simple: replace local mock lookup with async fetching by scenic id.

## Non-Goals

- No backend integration in this iteration.
- No payment, booking submission, or inventory logic.
- No redesign of shared header or footer.
- No attempt to preserve the screenshot's exact text content; only the structure and visual hierarchy need to match.

## Entry Flow

1. User opens `/scenic-search`.
2. User clicks the body of a scenic card.
3. Router navigates to `/scenic-detail/:id` and preserves existing search context in query params, such as `date`, `province`, and `spot`.
4. Detail page reads `route.params.id`, resolves a detail record from local mock data, and renders the shared detail template.

The favorite button on the card remains independent and must not trigger navigation.

## Routing

Add a new route:

- `path`: `/scenic-detail/:id`
- `name`: `scenic-detail`
- `component`: `ScenicDetail.vue`

The route should support direct visits. If the id does not exist, the page should render a friendly empty state with a link back to `/scenic-search`.

## Data Contract

Create a dedicated mock data module, for example `src/data/scenicDetails.ts`, keyed by scenic id. The page consumes a single normalized detail object.

Suggested structure:

```ts
type ScenicDetail = {
  id: string
  title: string
  subtitle: string
  locationLabel: string
  breadcrumb: string[]
  reviewCount: number
  reviewScore: number
  price: {
    current: string
    previous?: string
    discountLabel?: string
    note?: string
  }
  gallery: {
    src: string
    alt: string
    label?: string
  }[]
  overview: {
    description: string
    facts: { label: string; value: string; icon?: string }[]
  }
  bookingPanel: {
    dateOptions: string[]
    travelerSummary: string
    selectionHint: string
    contactHint: string
  }
  itineraryDays: {
    id: string
    title: string
    summary: string
    media?: { src: string; alt: string }
    mapLabel?: string
    accommodation?: {
      description: string
      sharedRoom?: string
      doubleRoom?: string
      singleRoom?: string
      roomImages?: { src: string; alt: string }[]
    }
  }[]
  includes: string[]
  excludes: string[]
  reviews: {
    id: string
    author: string
    avatar: string
    dateLabel: string
    title: string
    content: string
    rating: number
  }[]
  faqs: {
    id: string
    question: string
    answer: string
  }[]
  similarTours: {
    id: string
    title: string
    subtitle: string
    image: string
    price: string
    badgeText?: string
  }[]
}
```

This shape intentionally mirrors the UI sections so later API integration can map backend fields into this view model without rewriting the template.

## Page Composition

Implement the first version in `ScenicDetail.vue`, backed by a separate mock data module. Section boundaries inside the template and state should stay clear enough for later extraction if the file grows.

Main sections:

1. Hero gallery
   - Vertical thumbnail rail on desktop.
   - Large main image with left/right controls.
   - Photo count badge overlay.

2. Title and pricing row
   - Breadcrumb
   - Scenic title and location line
   - Rating/favorite affordances
   - Right-side booking summary with current price, previous price, and discount badge

3. Content tabs
   - Visual tabs matching the screenshot: overview, inclusions, reviews, FAQ, essential info
   - First iteration should scroll to matching sections in-page rather than acting as placeholder buttons

4. Overview section
   - Description copy
   - Fact grid for duration, activity, physical level, group size, age, and season

5. Itinerary accordion
   - Multiple day items
   - First day expanded by default
   - Each day supports summary text, optional image, optional map CTA, and optional accommodation block

6. Includes and excludes
   - Separate positive and negative bullet lists

7. Reviews
   - Stacked review cards with avatar, date label, title, rating stars, and body text

8. FAQ
   - Accordion list

9. Similar tours
   - Three-card recommendation strip that reuses the same detail route pattern

## Interaction Design

- Card body click navigates to scenic detail.
- Favorite icon click toggles favorite only.
- Thumbnail click updates the hero image.
- Hero arrows cycle through gallery images.
- Itinerary days expand and collapse.
- FAQ items expand and collapse.
- Similar tour cards navigate to another scenic detail id.
- Booking panel fields are local state only in this phase.

## Error Handling

- Invalid scenic id: render a centered empty state with a back-to-search action.
- Missing image: fall back to a safe default image.
- Missing optional section data: hide that subsection instead of rendering broken placeholders.
- Query params missing: page still loads using only the route id.

## Responsive Behavior

- Desktop target matches the screenshot's two-column detail layout.
- Tablet and mobile collapse to one column.
- Thumbnail rail can convert to horizontal strip on smaller widths.
- Booking panel moves below the main content on smaller screens.
- Long text must wrap without breaking cards or controls.

## Implementation Notes

- Prefer a dedicated data module over hardcoding long mock content inside `ScenicDetail.vue`.
- Reuse existing shared `Navigation` and `Footer`.
- Reuse the scenic card model id where possible so list-to-detail navigation remains stable.
- Keep route query passthrough so later the product can support return context and analytics.

## Testing Strategy

Verify at minimum:

1. Clicking a scenic card body from `/scenic-search` navigates to `/scenic-detail/:id`.
2. Clicking the heart icon still only toggles favorite state.
3. Valid ids render unique detail content from mock data.
4. Invalid ids render the empty state without runtime errors.
5. Gallery switching, itinerary accordion, and FAQ accordion work.
6. Similar tour cards navigate correctly.
7. The layout remains usable on desktop and mobile widths.

## Transition To Real Data

When real scenic data is ready:

1. Keep the route and page structure unchanged.
2. Replace local mock lookup with a detail service fetch by scenic id.
3. Map backend response fields into the `ScenicDetail` view model.
4. Preserve the empty/error/loading states already introduced in the mock phase.

This keeps the current implementation a real scaffold rather than a throwaway prototype.
