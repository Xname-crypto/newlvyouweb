export interface ScenicSearchFiltersState {
  travelDate: string
  sort: string
  popularTags: string[]
  minPrice: number
  maxPrice: number
  duration: string
  minRating: number
  ageGroup: number | null
  specialKeys: string[]
}

export interface ScenicPriceBounds {
  min: number
  max: number
}

export interface ScenicOption {
  key: string
  label: string
}

export interface ScenicAgeOption {
  value: number
  label: string
}

export interface ScenicRatingOption {
  value: number
  stars: number
}

export interface ScenicSearchCardData {
  id: string
  title: string
  subtitle: string
  image: string
  badgeText: string
  displayPrice: string
  reviewSummary: string
  featureLabels: string[]
  rating: number
  openingHours?: string
  visitDuration?: string
  bookingRequired?: string
  address?: string
  spotKey?: string
  recentlyViewedLabel?: string
}
