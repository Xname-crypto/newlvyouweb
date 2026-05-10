<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ImagePlus,
  MoreHorizontal,
  Plus,
  Save,
  Search,
  SlidersHorizontal,
  X,
  XCircle,
} from 'lucide-vue-next'
import { commerceService, getProductImage as resolveProductImage, getProductImages, type Product } from '@/services/commerceService'

type ProductForm = {
  title: string
  stockStatus: string
  price: number | null
  availableQuantity: number | null
  category: string
  slug: string
  sku: string
  description: string
  imageUrl: string
  colors: string[]
  sizes: string[]
  requiresColor: boolean
  requiresSize: boolean
  isActive: boolean
}

const SIZE_OPTIONS = ['S', 'M', 'L', 'XL', 'XXL']
const COLOR_OPTIONS: string[] = []
const PAGE_SIZE = 8
const DEFAULT_CATEGORY_OPTIONS = ['\u660e\u4fe1\u7247', '\u670d\u9970', '\u914d\u9970', '\u6587\u521b', '\u7eaa\u5ff5\u54c1']
const STOCK_IN = '有库存'
const STOCK_OUT = '缺货'

const products = ref<Product[]>([])
const loading = ref(false)
const saving = ref(false)
const errorMessage = ref('')
const searchQuery = ref('')
const currentPage = ref(1)
const viewMode = ref<'list' | 'form'>('list')
const selectedId = ref<number | null>(null)
const imageInputRef = ref<HTMLInputElement | null>(null)
const categorySelectRef = ref<HTMLElement | null>(null)
const stockStatusSelectRef = ref<HTMLElement | null>(null)
const selectedImages = ref<{ id: string; url: string }[]>([])
const activePreviewIndex = ref(0)
const colorInput = ref('')
const categoryOpen = ref(false)
const stockStatusOpen = ref(false)
const skuTouched = ref(false)
const slugTouched = ref(false)

const form = reactive<ProductForm>({
  title: '',
  stockStatus: STOCK_IN,
  price: null,
  availableQuantity: null,
  category: '',
  slug: '',
  sku: '',
  description: '',
  imageUrl: '',
  colors: [],
  sizes: [],
  requiresColor: false,
  requiresSize: false,
  isActive: true,
})

const normalizeStockStatus = (status?: unknown) => {
  const value = String(status || '').trim()
  if (!value) return STOCK_IN
  if (['In Stock', 'instock', 'in_stock', '有库存', '现货'].includes(value)) return STOCK_IN
  if (['Out of Stock', 'out_of_stock', 'sold_out', '缺货', '售罄'].includes(value)) return STOCK_OUT
  return value
}

watch(
  () => form.stockStatus,
  (status) => {
    if (normalizeStockStatus(status) === STOCK_OUT) {
      form.availableQuantity = 0
    }
  },
)

watch(
  () => form.requiresSize,
  (requiresSize) => {
    if (!requiresSize) {
      form.sizes = []
    }
  },
)

watch(
  () => form.requiresColor,
  (requiresColor) => {
    if (!requiresColor) {
      form.colors = []
    }
  },
)

const slugify = (value: string) => value
  .normalize('NFKD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, '-')
  .replace(/^-+|-+$/g, '')

const getCategoryCode = (category: string) => {
  const normalized = category.trim().toLowerCase()
  if (!normalized) return 'ITEM'
  if (normalized.includes('postcard') || category.includes('\u660e\u4fe1\u7247')) return 'POSTCARD'
  if (normalized.includes('cloth') || normalized.includes('dress') || normalized.includes('shirt') || category.includes('\u670d\u9970')) return 'APPAREL'
  if (normalized.includes('accessory') || category.includes('\u914d\u9970')) return 'ACCESSORY'
  if (category.includes('\u6587\u521b')) return 'CREATIVE'
  if (category.includes('\u7eaa\u5ff5')) return 'SOUVENIR'
  return slugify(category).slice(0, 12).toUpperCase() || 'ITEM'
}

const getNextSkuNumber = (prefix: string) => {
  const maxNumber = products.value.reduce((max, product) => {
    const match = String(product.sku || '').match(new RegExp(`^${prefix}-(\\d+)$`, 'i'))
    return match ? Math.max(max, Number(match[1])) : max
  }, 0)
  return String(maxNumber + 1).padStart(3, '0')
}

const buildAutoSku = () => `${getCategoryCode(form.category)}-${getNextSkuNumber(getCategoryCode(form.category))}`

const buildAutoSlug = () => {
  const titleSlug = slugify(form.title)
  if (titleSlug) return titleSlug
  const categorySlug = slugify(form.category)
  if (categorySlug) return `${categorySlug}-${Date.now().toString().slice(-6)}`
  return `product-${Date.now().toString().slice(-6)}`
}

const isLegacyColorValue = (value: string) => /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(value.trim())

const normalizeColorLabels = (values: unknown) => {
  if (!Array.isArray(values)) return []
  return Array.from(new Set(values.map((item) => String(item).trim()).filter((item) => item && !isLegacyColorValue(item))))
}

watch(
  () => [form.title, form.category],
  () => {
    if (selectedId.value) return
    if (!form.title.trim() && !form.category.trim()) {
      if (!skuTouched.value) form.sku = ''
      if (!slugTouched.value) form.slug = ''
      return
    }
    if (!skuTouched.value) form.sku = buildAutoSku()
    if (!slugTouched.value) form.slug = buildAutoSlug()
  },
)

const selectedProduct = computed(() => products.value.find((item) => item.id === selectedId.value) || null)

const categoryOptions = computed(() => {
  const values = new Set<string>(DEFAULT_CATEGORY_OPTIONS)
  products.value.forEach((product) => {
    const value = String(product.category || '').trim()
    if (value) values.add(value)
  })
  return Array.from(values)
})

const filteredCategoryOptions = computed(() => {
  const query = form.category.trim().toLowerCase()
  if (!query) return categoryOptions.value
  return categoryOptions.value.filter((category) => category.toLowerCase().includes(query))
})

const getProductStockStatus = (product: Product) => {
  if (!product.is_active || Number(product.available_stock || 0) <= 0) return STOCK_OUT
  const metadataStatus = product.metadata?.stock_status
  if (metadataStatus) return normalizeStockStatus(metadataStatus)
  return STOCK_IN
}

const sortProductsByStock = (items: Product[]) =>
  [...items].sort((a, b) => {
    const stockRankA = getProductStockStatus(a) === STOCK_OUT ? 1 : 0
    const stockRankB = getProductStockStatus(b) === STOCK_OUT ? 1 : 0
    if (stockRankA !== stockRankB) return stockRankA - stockRankB
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })

const filteredProducts = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return sortProductsByStock(products.value)

  return sortProductsByStock(products.value.filter((product) => {
    const metadata = product.metadata || {}
    return [
      product.name,
      product.sku,
      product.category,
      product.description,
      metadata.slug,
      metadata.stock_status,
      normalizeStockStatus(metadata.stock_status),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
      .includes(query)
  }))
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredProducts.value.length / PAGE_SIZE)))

const pagedProducts = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredProducts.value.slice(start, start + PAGE_SIZE)
})

const visiblePages = computed(() => {
  if (totalPages.value <= 5) {
    return Array.from({ length: totalPages.value }, (_, index) => String(index + 1))
  }
  if (currentPage.value <= 3) return ['1', '2', '3', '...', String(totalPages.value)]
  if (currentPage.value >= totalPages.value - 2) {
    return ['1', '...', String(totalPages.value - 2), String(totalPages.value - 1), String(totalPages.value)]
  }
  return ['1', '...', String(currentPage.value), '...', String(totalPages.value)]
})

const getProductImage = (product: Product) => {
  return resolveProductImage(product)
}

const formatPrice = (product: Product) => `￥${product.price || ((product.price_cents || 0) / 100).toFixed(2)}`

const previewImages = computed(() => {
  if (selectedImages.value.length) return selectedImages.value
  if (form.imageUrl.trim()) return [{ id: 'url-preview', url: form.imageUrl.trim() }]
  return []
})

const activePreviewImage = computed(() => previewImages.value[activePreviewIndex.value]?.url || '')

const resetForm = () => {
  selectedId.value = null
  form.title = ''
  form.stockStatus = STOCK_IN
  form.price = null
  form.availableQuantity = null
  form.category = ''
  form.slug = ''
  form.sku = ''
  form.description = ''
  form.imageUrl = ''
  form.colors = []
  form.sizes = []
  form.requiresColor = false
  form.requiresSize = false
  form.isActive = true
  colorInput.value = ''
  selectedImages.value = []
  activePreviewIndex.value = 0
  skuTouched.value = false
  slugTouched.value = false
  if (imageInputRef.value) imageInputRef.value.value = ''
}

const setAdminSubPageTitle = (title: string) => {
  window.dispatchEvent(new CustomEvent('admin-layout:set-subpage-title', { detail: title }))
}

const openAddForm = () => {
  resetForm()
  viewMode.value = 'form'
  errorMessage.value = ''
  setAdminSubPageTitle('添加商品')
}

const backToList = () => {
  viewMode.value = 'list'
  selectedId.value = null
  errorMessage.value = ''
  setAdminSubPageTitle('')
}

const populateProductForm = (product: Product) => {
  const metadata = product.metadata || {}
  const images = getProductImages(product)

  selectedId.value = product.id
  form.title = product.name
  form.stockStatus = normalizeStockStatus(metadata.stock_status || getProductStockStatus(product))
  form.price = Number(product.price || 0)
  form.availableQuantity = product.stock_total
  form.category = product.category
  form.slug = String(metadata.slug || '')
  form.sku = product.sku
  form.description = product.description
  form.imageUrl = images[0] || ''
  selectedImages.value = images.map((url, index) => ({ id: `existing-${product.id}-${index}`, url }))
  activePreviewIndex.value = 0
  form.colors = normalizeColorLabels(metadata.colors)
  form.requiresColor = metadata.requires_color === true && form.colors.length > 0
  colorInput.value = ''
  form.requiresSize = metadata.requires_size !== false && Array.isArray(metadata.sizes) && metadata.sizes.length > 0
  form.sizes = form.requiresSize && Array.isArray(metadata.sizes) && metadata.sizes.length ? metadata.sizes.map(String) : []
  form.isActive = product.is_active
  skuTouched.value = true
  slugTouched.value = true
  viewMode.value = 'form'
  errorMessage.value = ''
  setAdminSubPageTitle('编辑商品')
}

const editProduct = async (product: Product) => {
  errorMessage.value = ''
  try {
    populateProductForm(await commerceService.getProductForEdit(product.id))
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || 'Failed to load product')
  }
}

const loadProducts = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    products.value = await commerceService.listProducts(true)
    currentPage.value = Math.min(currentPage.value, totalPages.value)
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '商品加载失败')
  } finally {
    loading.value = false
  }
}

const addColorLabel = () => {
  const color = colorInput.value.trim()
  if (!color || form.colors.includes(color)) {
    colorInput.value = ''
    return
  }
  form.colors = [...form.colors, color]
  colorInput.value = ''
}

const removeColorLabel = (color: string) => {
  form.colors = form.colors.filter((item) => item !== color)
}

const toggleColor = (color: string) => {
  if (form.colors.includes(color)) {
    removeColorLabel(color)
    return
  }
  form.colors = [...form.colors, color]
}

const toggleSize = (size: string) => {
  if (form.sizes.includes(size)) {
    form.sizes = form.sizes.filter((item) => item !== size)
    return
  }
  form.sizes = [...form.sizes, size]
}

const setStockStatus = (status: string) => {
  form.stockStatus = status
  stockStatusOpen.value = false
}

const selectCategory = (category: string) => {
  form.category = category
  categoryOpen.value = false
}

const markSkuTouched = () => {
  skuTouched.value = true
}

const markSlugTouched = () => {
  slugTouched.value = true
}

const handleDocumentPointerDown = (event: MouseEvent) => {
  const target = event.target as Node | null
  if (categoryOpen.value && (!target || !categorySelectRef.value?.contains(target))) {
    categoryOpen.value = false
  }
  if (stockStatusOpen.value && (!target || !stockStatusSelectRef.value?.contains(target))) {
    stockStatusOpen.value = false
  }
}

const openImagePicker = () => imageInputRef.value?.click()

const fileToDataUrl = (file: File) => new Promise<string>((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(String(reader.result || ''))
  reader.onerror = reject
  reader.readAsDataURL(file)
})

const handleImageSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  if (!files.length) return

  try {
    const nextImages = await Promise.all(files.slice(0, 5).map(async (file, index) => ({
      id: `${Date.now()}-${index}-${file.name}`,
      url: await fileToDataUrl(file),
    })))
    selectedImages.value = nextImages
    activePreviewIndex.value = 0
    form.imageUrl = nextImages[0]?.url || form.imageUrl
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '读取图片失败')
  }
}

const removeImage = (id: string) => {
  const removingIndex = selectedImages.value.findIndex((image) => image.id === id)
  selectedImages.value = selectedImages.value.filter((image) => image.id !== id)
  if (removingIndex <= activePreviewIndex.value) {
    activePreviewIndex.value = Math.max(0, activePreviewIndex.value - 1)
  }
  form.imageUrl = selectedImages.value[0]?.url || ''
  if (imageInputRef.value && !selectedImages.value.length) imageInputRef.value.value = ''
}

const selectPreviewImage = (index: number) => {
  activePreviewIndex.value = index
  form.imageUrl = previewImages.value[index]?.url || form.imageUrl
}

const saveProduct = async () => {
  if (!form.title.trim() || !form.sku.trim()) {
    errorMessage.value = '请填写商品名称和货号'
    return
  }

  saving.value = true
  errorMessage.value = ''
  try {
    const selectedStockStatus = normalizeStockStatus(form.stockStatus)
    const stockTotal = selectedStockStatus === STOCK_OUT ? 0 : Number(form.availableQuantity || 0)
    const stockStatus = stockTotal > 0 && form.isActive ? selectedStockStatus : STOCK_OUT
    const priceCents = Math.round(Number(form.price || 0) * 100)
    const images = previewImages.value.map((image) => image.url)
    const primaryImage = images[0] || form.imageUrl.trim()
    const metadata: Record<string, any> = {
      slug: form.slug.trim(),
      stock_status: stockStatus,
      requires_color: form.requiresColor,
      colors: form.requiresColor ? form.colors : [],
      requires_size: form.requiresSize,
      sizes: form.requiresSize ? form.sizes : [],
      shipping_cents: 0,
      images: primaryImage ? [primaryImage, ...images.filter((image) => image !== primaryImage)] : [],
    }

    const payload: Partial<Product> = {
      sku: form.sku.trim(),
      name: form.title.trim(),
      description: form.description.trim(),
      category: form.category.trim(),
      image_url: primaryImage,
      price_cents: priceCents,
      stock_total: stockTotal,
      is_active: form.isActive,
      metadata,
    }

    let savedProduct: Product
    if (selectedId.value) {
      savedProduct = await commerceService.updateProduct(selectedId.value, payload)
      products.value = products.value.map((product) => (product.id === savedProduct.id ? savedProduct : product))
    } else {
      savedProduct = await commerceService.createProduct(payload)
      products.value = [savedProduct, ...products.value]
      currentPage.value = 1
    }

    backToList()
  } catch (error) {
    errorMessage.value = String((error as any)?.message || error || '商品保存失败')
  } finally {
    saving.value = false
  }
}

const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

onMounted(() => {
  loadProducts()
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  setAdminSubPageTitle(viewMode.value === 'form' ? (selectedId.value ? '编辑商品' : '添加商品') : '')
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  setAdminSubPageTitle('')
})
</script>

<template>
  <section class="product-manager-root min-h-full text-slate-950">
    <div v-if="viewMode === 'list'" class="product-list-page">
      <header class="list-hero">
        <div>
          <p class="list-kicker">E Commerce / Product</p>
          <h1>商品管理</h1>
          <span>管理商品资料、库存状态、价格和分类信息。</span>
        </div>
      </header>

      <div v-if="errorMessage" class="product-alert">{{ errorMessage }}</div>

      <section class="product-list-card">
        <header class="product-toolbar">
          <div>
            <h2>商品列表</h2>
            <p>{{ filteredProducts.length }} 个匹配结果</p>
          </div>
          <div class="product-toolbar__actions">
            <div class="list-summary list-summary--inline">
              <strong>{{ products.length }}</strong>
              <span>全部商品</span>
            </div>
            <button class="add-product-btn" type="button" @click="openAddForm">
              <span>添加商品</span>
              <Plus class="h-4 w-4" />
            </button>
            <label class="product-search">
              <Search class="h-5 w-5 text-slate-500" />
              <input v-model="searchQuery" type="search" placeholder="搜索商品" @input="currentPage = 1" />
            </label>
          </div>
        </header>

        <div class="product-table-wrap">
          <table class="product-table">
            <thead>
              <tr>
                <th class="w-16 text-center">
                  <SlidersHorizontal class="mx-auto h-4 w-4 text-slate-500" />
                </th>
                <th>商品名称</th>
                <th>货号</th>
                <th>价格</th>
                <th>库存状态</th>
                <th>分类</th>
                <th class="text-center">操作</th>
              </tr>
            </thead>
            <tbody v-if="pagedProducts.length">
              <tr v-for="product in pagedProducts" :key="product.id">
                <td class="text-center">
                  <div class="product-thumb">
                    <img v-if="getProductImage(product)" :src="getProductImage(product)" :alt="product.name" />
                  </div>
                </td>
                <td>
                  <button class="product-name" type="button" @click="editProduct(product)">
                    {{ product.name }}
                  </button>
                </td>
                <td>{{ product.sku }}</td>
                <td>{{ formatPrice(product) }}</td>
                <td>
                  <span class="stock-pill" :class="{ 'stock-pill--out': getProductStockStatus(product) === STOCK_OUT }">
                    {{ getProductStockStatus(product) }}
                  </span>
                </td>
                <td>{{ product.category || '-' }}</td>
                <td class="text-center">
                  <button class="action-btn" type="button" title="编辑商品" @click="editProduct(product)">
                    <MoreHorizontal class="h-5 w-5" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-if="!pagedProducts.length" class="list-empty-state">
            <div class="list-empty-icon">
              <ImagePlus class="h-7 w-7" />
            </div>
            <strong>{{ loading ? '商品加载中...' : '暂无商品' }}</strong>
            <span>{{ searchQuery ? '换个关键词试试，或新增一个商品。' : '点击添加商品，创建你的第一个商品条目。' }}</span>
            <button v-if="!loading" class="empty-add-btn" type="button" @click="openAddForm">
              <Plus class="h-4 w-4" />
              添加商品
            </button>
          </div>
        </div>

        <footer class="product-pagination" aria-label="商品分页">
          <button class="page-arrow" type="button" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">
            <ChevronLeft class="h-5 w-5" />
          </button>
          <button
            v-for="page in visiblePages"
            :key="page"
            class="page-number"
            :class="{ 'page-number--active': page === String(currentPage), 'page-number--ellipsis': page === '...' }"
            :disabled="page === '...'"
            type="button"
            @click="page !== '...' && changePage(Number(page))"
          >
            {{ page }}
          </button>
          <button class="page-arrow" type="button" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">
            <ChevronRight class="h-5 w-5" />
          </button>
        </footer>
      </section>
    </div>

    <div v-else class="product-editor-page">
      <header class="editor-hero">
        <div>
          <button class="editor-back-btn" type="button" @click="backToList">
            <ChevronLeft class="h-4 w-4" />
            返回商品列表
          </button>
          <h1>{{ selectedProduct ? '编辑商品' : '添加商品' }}</h1>
          <p>上传商品图片，完善售价、库存、分类、货号和规格信息。</p>
        </div>
      </header>

      <div v-if="errorMessage" class="product-alert editor-alert">{{ errorMessage }}</div>

      <form class="product-editor-card" @submit.prevent="saveProduct">
        <section class="editor-gallery">
          <div class="gallery-rail">
            <button class="rail-arrow" type="button" aria-label="上一张图片">
              <ChevronLeft class="h-7 w-7 rotate-90" />
            </button>
            <button
              v-for="(image, index) in previewImages"
              :key="image.id"
              class="rail-thumb"
              :class="{ 'rail-thumb--active': index === activePreviewIndex }"
              type="button"
              @click="selectPreviewImage(index)"
            >
              <img :src="image.url" alt="" />
              <span class="rail-remove" @click.stop="removeImage(image.id)">
                <X class="h-3 w-3" />
              </span>
            </button>
            <button class="rail-thumb rail-thumb--add" type="button" @click="openImagePicker">
              <ImagePlus class="h-5 w-5" />
              <span>上传</span>
            </button>
            <button class="rail-arrow" type="button" aria-label="下一张图片">
              <ChevronRight class="h-7 w-7 rotate-90" />
            </button>
          </div>

          <div class="gallery-main" :class="{ 'gallery-main--empty': !activePreviewImage }" @click="openImagePicker">
            <img v-if="activePreviewImage" :src="activePreviewImage" alt="商品预览图" />
            <div v-else class="gallery-placeholder">
              <ImagePlus class="h-10 w-10" />
              <strong>上传商品主图</strong>
              <span>支持选择多张图片，第一张将作为主图</span>
            </div>
          </div>
          <input ref="imageInputRef" class="sr-only" type="file" accept="image/*" multiple @change="handleImageSelect" />
        </section>

        <section class="editor-fields">
          <label class="editor-field editor-field--full">
            <span>商品名称</span>
            <input v-model="form.title" type="text" placeholder="请输入商品名称" />
          </label>

          <label class="editor-field editor-field--full">
            <span>商品描述</span>
            <div v-if="false" class="rich-toolbar">
              <button type="button"><Type class="h-4 w-4" /></button>
              <button type="button"><strong>B</strong></button>
              <button type="button"><em>I</em></button>
              <button type="button"><u>U</u></button>
              <button type="button"><AlignLeft class="h-4 w-4" /></button>
              <button type="button"><AlignCenter class="h-4 w-4" /></button>
              <button type="button"><AlignRight class="h-4 w-4" /></button>
            </div>
            <textarea v-model="form.description" placeholder="请输入商品详情"></textarea>
          </label>

          <label class="editor-field editor-field--full">
            <span>分类</span>
            <div ref="categorySelectRef" class="select-shell category-select">
              <input v-model="form.category" type="text" placeholder="请输入或选择分类" @focus="categoryOpen = true" @input="categoryOpen = true" />
              <button class="category-select__toggle" type="button" :aria-expanded="categoryOpen" aria-haspopup="listbox" @click.stop="categoryOpen = !categoryOpen">
                <ChevronDown class="h-4 w-4" />
              </button>
              <div v-if="categoryOpen" class="category-select__menu" role="listbox">
                <button
                  v-for="category in filteredCategoryOptions"
                  :key="category"
                  class="category-select__option"
                  :class="{ 'category-select__option--active': form.category === category }"
                  type="button"
                  role="option"
                  @click.stop="selectCategory(category)"
                >
                  {{ category }}
                </button>
                <div v-if="!filteredCategoryOptions.length" class="category-select__empty">没有匹配的分类，可以直接输入新分类</div>
              </div>
            </div>
          </label>

          <label class="editor-field">
            <span>价格</span>
            <div class="input-affix">
              <b>￥</b>
              <input v-model.number="form.price" min="0" step="0.01" type="number" placeholder="0.00" />
            </div>
          </label>

          <label class="editor-field">
            <span>可售数量</span>
            <input v-model.number="form.availableQuantity" min="0" type="number" placeholder="0" />
          </label>

          <label class="editor-field">
            <span>库存状态</span>
            <div ref="stockStatusSelectRef" class="stock-select">
              <button
                class="stock-select__trigger"
                type="button"
                :aria-expanded="stockStatusOpen"
                aria-haspopup="listbox"
                @click="stockStatusOpen = !stockStatusOpen"
              >
                <span>{{ form.stockStatus }}</span>
                <ChevronDown class="h-4 w-4" :class="{ 'rotate-180': stockStatusOpen }" />
              </button>
              <div v-if="stockStatusOpen" class="stock-select__menu" role="listbox">
                <button class="stock-select__option" :class="{ 'stock-select__option--active': form.stockStatus === STOCK_IN }" type="button" role="option" @click="setStockStatus(STOCK_IN)">
                  有库存
                </button>
                <button class="stock-select__option" :class="{ 'stock-select__option--active': form.stockStatus === STOCK_OUT }" type="button" role="option" @click="setStockStatus(STOCK_OUT)">
                  缺货
                </button>
              </div>
            </div>
          </label>

          <label class="editor-field">
            <span>货号</span>
            <input v-model="form.sku" type="text" placeholder="请输入 SKU" @input="markSkuTouched" />
          </label>

          <label class="editor-field editor-field--full">
            <span>链接别名</span>
            <input v-model="form.slug" type="text" placeholder="例如：black-dress" @input="markSlugTouched" />
          </label>

          <fieldset class="editor-choice editor-field--full">
            <legend>颜色</legend>
            <label class="editor-check-row">
              <input v-model="form.requiresColor" type="checkbox" />
              <span>该商品需要选择颜色</span>
            </label>
            <div v-if="form.requiresColor" class="editor-color-row editor-color-row--text">
              <div class="color-input-shell">
                <input v-model="colorInput" type="text" placeholder="输入颜色，例如：黑色、白色、杏色" @keydown.enter.prevent="addColorLabel" />
                <button type="button" @click="addColorLabel">添加</button>
              </div>
              <div v-if="form.colors.length" class="color-tag-row">
                <span v-for="color in form.colors" :key="color" class="color-tag">
                  {{ color }}
                  <button type="button" :aria-label="`删除颜色 ${color}`" @click="removeColorLabel(color)">
                    <XCircle class="h-4 w-4" />
                  </button>
                </span>
              </div>
              <button
                v-for="color in COLOR_OPTIONS"
                :key="color"
                class="editor-color-dot"
                :class="{ 'editor-color-dot--active': form.colors.includes(color) }"
                :style="{ backgroundColor: color }"
                type="button"
                :aria-label="`切换颜色 ${color}`"
                @click="toggleColor(color)"
              ></button>
            </div>
          </fieldset>

          <fieldset class="editor-choice editor-field--full">
            <legend>规格尺码</legend>
            <label class="editor-check-row">
              <input v-model="form.requiresSize" type="checkbox" />
              <span>该商品需要选择尺码</span>
            </label>
            <div v-if="form.requiresSize" class="editor-size-row">
              <button
                v-for="size in SIZE_OPTIONS"
                :key="size"
                class="editor-size-chip"
                :class="{ 'editor-size-chip--active': form.sizes.includes(size) }"
                :disabled="!form.requiresSize"
                type="button"
                @click="toggleSize(size)"
              >
                {{ size }}
              </button>
            </div>
          </fieldset>

          <label class="editor-field editor-field--full">
            <span>图片链接</span>
            <input v-model="form.imageUrl" type="text" placeholder="也可以粘贴图片链接" />
          </label>

          <div class="editor-actions">
            <button class="cancel-editor-btn" type="button" @click="backToList">取消</button>
            <button class="save-editor-btn" :disabled="saving" type="submit">
              <Save class="h-4 w-4" />
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </section>
      </form>
    </div>
  </section>
</template>

<style scoped>
.product-manager-root {
  min-height: calc(100vh - 4rem);
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  color: #0f172a;
}

.product-list-page {
  min-height: calc(100vh - 8rem);
  padding-bottom: 1.5rem;
}

.list-hero {
  min-height: 8.5rem;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
}

.list-kicker {
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.list-hero h1 {
  margin-top: 0.8rem;
  color: #0f172a;
  font-size: clamp(2rem, 4vw, 2.6rem);
  line-height: 1;
  font-weight: 800;
}

.list-hero span {
  display: inline-block;
  margin-top: 0.75rem;
  color: #64748b;
  font-size: 0.875rem;
}

.list-summary {
  min-width: 8.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: #ffffff;
  padding: 1rem 1.25rem;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
}

.list-summary strong,
.list-summary span {
  display: block;
}

.list-summary strong {
  color: #0f172a;
  font-size: 1.75rem;
  line-height: 1;
}

.list-summary span {
  margin-top: 0.45rem;
  color: #64748b;
  font-size: 0.8125rem;
  font-weight: 700;
}

.list-summary--inline {
  min-width: auto;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.95rem;
  border-radius: 0.875rem;
  box-shadow: none;
}

.list-summary--inline strong,
.list-summary--inline span {
  margin: 0;
}

.list-summary--inline strong {
  font-size: 1.125rem;
  line-height: 1;
}

.list-summary--inline span {
  font-size: 0.75rem;
  white-space: nowrap;
}

.product-list-card {
  min-height: 44rem;
  display: flex;
  flex-direction: column;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: #ffffff;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.product-toolbar {
  min-height: 5.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  padding: 0 2rem;
  background: rgba(248, 250, 252, 0.7);
}

.product-toolbar h2 {
  color: #0f172a;
  font-size: 1.125rem;
  font-weight: 700;
}

.product-toolbar p {
  margin-top: 0.35rem;
  color: #64748b;
  font-size: 0.8125rem;
  font-weight: 600;
}

.product-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}

.add-product-btn {
  height: 2.625rem;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  border-radius: 0.75rem;
  background: #0f172a;
  color: #ffffff;
  padding: 0 1.125rem;
  font-size: 0.875rem;
  font-weight: 700;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.14);
}

.product-search {
  width: 16.25rem;
  height: 2.625rem;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 0 0.875rem;
  color: #6b7280;
  background: #f8fafc;
}

.product-search input {
  min-width: 0;
  flex: 1;
  border: 0;
  outline: 0;
  color: #0f172a;
  font-size: 0.875rem;
  background: transparent;
}

.product-search input::placeholder {
  color: #94a3b8;
}

.product-alert {
  margin: 1rem 0;
  border: 1px solid #fecdd3;
  background: #fff1f2;
  color: #be123c;
  border-radius: 0.875rem;
  padding: 0.875rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
}

.product-table-wrap {
  position: relative;
  flex: 1;
  overflow-x: auto;
}

.product-table {
  width: 100%;
  min-width: 58rem;
  border-collapse: collapse;
  color: #475569;
  font-size: 0.875rem;
}

.product-table th {
  height: 4rem;
  border-bottom: 1px solid #e2e8f0;
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  text-align: left;
  white-space: nowrap;
  background: rgba(248, 250, 252, 0.7);
}

.product-table td {
  height: 5rem;
  border-bottom: 1px solid #f1f5f9;
  font-weight: 600;
  vertical-align: middle;
}

.product-table tr:last-child td {
  border-bottom: 0;
}

.product-thumb {
  width: 3rem;
  height: 3rem;
  margin: 0 auto;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.product-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-name {
  color: #0f172a;
  font-weight: 700;
  text-align: left;
}

.product-name:hover,
.action-btn:hover {
  color: #0f172a;
}

.action-btn {
  width: 2.25rem;
  height: 2.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  color: #64748b;
  background: #f8fafc;
}

.stock-pill {
  display: inline-flex;
  align-items: center;
  min-height: 1.875rem;
  border-radius: 999px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
  color: #16a35f;
  padding: 0 0.875rem;
  font-size: 0.75rem;
  font-weight: 700;
}

.stock-pill--out {
  border-color: #fecdd3;
  background: #fff1f2;
  color: #e11d48;
}

.list-empty-state {
  min-height: 26rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: #64748b;
  text-align: center;
}

.list-empty-icon {
  width: 4.25rem;
  height: 4.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
  border-radius: 1.25rem;
  background: #f8fafc;
  color: #0f172a;
}

.list-empty-state strong {
  color: #0f172a;
  font-size: 1.125rem;
}

.list-empty-state span {
  max-width: 20rem;
  font-size: 0.875rem;
  line-height: 1.6;
}

.empty-add-btn {
  height: 2.5rem;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  border-radius: 0.75rem;
  background: #0f172a;
  color: #ffffff;
  padding: 0 1rem;
  font-size: 0.8125rem;
  font-weight: 700;
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.14);
}

.product-pagination {
  margin-top: auto;
  min-height: 5.5rem;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  color: #64748b;
  border-top: 1px solid #e2e8f0;
  padding: 0 2rem;
}

.page-arrow,
.page-number {
  width: 2.25rem;
  height: 2.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  background: #ffffff;
  font-size: 0.8125rem;
  font-weight: 700;
}

.page-number--active {
  border-color: #0f172a;
  background: #0f172a;
  color: #ffffff;
}

.page-number--ellipsis {
  cursor: default;
}

.page-arrow:disabled,
.page-number:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.product-editor-page {
  min-height: calc(100vh - 8rem);
  padding-bottom: 1.5rem;
  color: #0f172a;
}

.editor-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  min-height: 8.5rem;
}

.editor-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 1rem;
  color: #64748b;
  font-size: 0.8125rem;
  font-weight: 700;
}

.editor-hero h1 {
  font-size: clamp(2rem, 4vw, 2.6rem);
  line-height: 1;
  font-weight: 800;
  color: #0f172a;
}

.editor-hero p {
  margin-top: 0.75rem;
  color: #64748b;
  font-size: 0.875rem;
}

.editor-alert {
  margin-bottom: 1rem;
}

.product-editor-card {
  display: grid;
  grid-template-columns: minmax(20rem, 1.05fr) minmax(25rem, 0.95fr);
  gap: clamp(2rem, 5vw, 4.5rem);
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: #ffffff;
  padding: clamp(2rem, 4vw, 3.5rem);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
}

.editor-gallery {
  display: grid;
  grid-template-columns: 8rem minmax(18rem, 1fr);
  gap: 1.875rem;
  align-content: start;
  align-items: start;
  min-width: 0;
}

.gallery-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
}

.rail-arrow {
  width: 3rem;
  height: 2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #0f172a;
}

.rail-thumb {
  position: relative;
  width: 5.875rem;
  height: 6.875rem;
  border: 2px solid transparent;
  border-radius: 0.75rem;
  background: #f8fafc;
  overflow: visible;
}

.rail-thumb img {
  width: 100%;
  height: 100%;
  border-radius: 0.625rem;
  object-fit: cover;
}

.rail-thumb--active {
  border-color: #0f172a;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.12);
}

.rail-thumb--add {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 700;
}

.rail-remove {
  position: absolute;
  top: -0.45rem;
  right: -0.45rem;
  width: 1.1rem;
  height: 1.1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #ffffff;
  color: #64748b;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.12);
}

.gallery-main {
  width: fit-content;
  max-width: 100%;
  max-height: 36rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  background: #f8fafc;
  cursor: pointer;
  overflow: hidden;
}

.gallery-main--empty {
  width: 100%;
  min-height: 30rem;
}

.gallery-main img {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 36rem;
  object-fit: contain;
}

.gallery-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  color: #64748b;
  text-align: center;
}

.gallery-placeholder strong {
  color: #0f172a;
  font-size: 1.125rem;
}

.gallery-placeholder span {
  max-width: 14rem;
  font-size: 0.8125rem;
  line-height: 1.6;
}

.editor-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-content: start;
  gap: 1.35rem 2rem;
}

.editor-field,
.editor-choice {
  min-width: 0;
}

.editor-field--full {
  grid-column: 1 / -1;
}

.editor-field > span,
.editor-choice legend {
  display: block;
  margin-bottom: 0.75rem;
  color: #475569;
  font-size: 0.9375rem;
  font-weight: 700;
}

.editor-field input,
.editor-field select,
.editor-field textarea,
.select-shell,
.input-affix {
  width: 100%;
  border: 0;
  background: #f8fafc;
  color: #0f172a;
  outline: none;
  font-size: 1rem;
}

.editor-field input,
.editor-field select,
.input-affix,
.select-shell {
  height: 3.75rem;
}

.editor-field input,
.editor-field select {
  padding: 0 1.25rem;
}

.editor-field input::placeholder,
.editor-field textarea::placeholder {
  color: #94a3b8;
}

.editor-field textarea {
  min-height: 8.5rem;
  resize: vertical;
  padding: 1.25rem;
  line-height: 1.7;
}

.select-shell,
.input-affix {
  display: flex;
  align-items: center;
  background: #f8fafc;
}

.select-shell input,
.select-shell select,
.input-affix input {
  flex: 1;
  min-width: 0;
  background: transparent;
  appearance: none;
}

.select-shell svg {
  flex: 0 0 auto;
  margin-right: 1rem;
  color: #94a3b8;
  transition: transform 0.18s ease, color 0.18s ease;
}

.select-shell:focus-within svg {
  color: #0f172a;
  transform: rotate(180deg);
}

.category-select {
  position: relative;
}

.category-select__toggle {
  width: 2.75rem;
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  color: #94a3b8;
}

.category-select__toggle svg {
  margin-right: 0;
}

.category-select__toggle[aria-expanded='true'] svg {
  color: #0f172a;
  transform: rotate(180deg);
}

.category-select__menu {
  position: absolute;
  z-index: 30;
  top: calc(100% + 0.35rem);
  left: 0;
  right: 0;
  max-height: 13rem;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  box-shadow: 0 18px 38px rgba(15, 23, 42, 0.14);
  overflow-y: auto;
}

.category-select__option {
  width: 100%;
  min-height: 2.75rem;
  display: flex;
  align-items: center;
  padding: 0 1.25rem;
  color: #0f172a;
  font-size: 0.95rem;
  text-align: left;
  transition: background-color 0.16s ease;
}

.category-select__option:hover,
.category-select__option--active {
  background: #f1f5f9;
}

.category-select__empty {
  padding: 0.9rem 1.25rem;
  color: #64748b;
  font-size: 0.875rem;
  line-height: 1.5;
}

.stock-select {
  position: relative;
  width: 100%;
}

.stock-select__trigger {
  width: 100%;
  height: 3.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  background: #f8fafc;
  padding: 0 1.25rem;
  color: #0f172a;
  font-size: 1rem;
  text-align: left;
}

.stock-select__trigger svg {
  color: #94a3b8;
  transition: transform 0.18s ease, color 0.18s ease;
}

.stock-select__trigger[aria-expanded='true'] svg {
  color: #0f172a;
}

.stock-select__menu {
  position: absolute;
  z-index: 30;
  top: calc(100% + 0.35rem);
  left: 0;
  right: 0;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  box-shadow: 0 18px 38px rgba(15, 23, 42, 0.14);
  overflow: hidden;
}

.stock-select__option {
  width: 100%;
  height: 3rem;
  display: flex;
  align-items: center;
  padding: 0 1.25rem;
  color: #0f172a;
  font-size: 0.95rem;
  text-align: left;
  transition: background-color 0.16s ease;
}

.stock-select__option:hover,
.stock-select__option--active {
  background: #f1f5f9;
}

.input-affix b {
  padding-left: 1.25rem;
  color: #475569;
  font-size: 1.05rem;
}

.editor-choice {
  border: 0;
  padding: 0;
}

.editor-color-row,
.editor-size-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.875rem;
  min-height: 3.75rem;
  background: #f8fafc;
  border-radius: 0.875rem;
  padding: 0 1rem;
}

.editor-color-row--text {
  align-items: stretch;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
}

.color-input-shell {
  display: flex;
  min-height: 3rem;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  background: #ffffff;
}

.color-input-shell input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  padding: 0 1rem;
  outline: none;
}

.color-input-shell button {
  flex: 0 0 auto;
  padding: 0 1.1rem;
  background: #0f172a;
  color: #ffffff;
  font-size: 0.9rem;
  font-weight: 700;
}

.color-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.color-tag {
  display: inline-flex;
  min-height: 2.25rem;
  align-items: center;
  gap: 0.5rem;
  background: #e2e8f0;
  padding: 0 0.7rem 0 0.9rem;
  color: #0f172a;
  font-size: 0.92rem;
  font-weight: 700;
}

.color-tag button {
  display: inline-flex;
  color: #64748b;
}

.color-tag button:hover {
  color: #0f172a;
}

.editor-color-dot {
  width: 1.45rem;
  height: 1.45rem;
  border-radius: 999px;
  border: 2px solid transparent;
}

.editor-color-dot--active {
  box-shadow: 0 0 0 3px #ffffff, 0 0 0 5px rgba(15, 23, 42, 0.18);
}

.editor-size-chip {
  min-width: 2.5rem;
  height: 2rem;
  border-radius: 0.625rem;
  background: #e2e8f0;
  color: #475569;
  font-size: 0.8125rem;
  font-weight: 700;
}

.editor-size-chip--active {
  background: #0f172a;
  color: #ffffff;
}

.editor-size-chip:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.editor-check-row {
  display: inline-flex;
  align-items: center;
  gap: 0.625rem;
  margin-bottom: 0.75rem;
  color: #475569;
  font-size: 0.875rem;
  font-weight: 700;
}

.editor-check-row input {
  width: 1rem;
  height: 1rem;
  accent-color: #0f172a;
}

.editor-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: flex-end;
  gap: 0.875rem;
  padding-top: 1rem;
}

.save-editor-btn,
.cancel-editor-btn {
  height: 3.75rem;
  min-width: 8.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  border-radius: 0.75rem;
  font-size: 1rem;
  font-weight: 700;
}

.save-editor-btn {
  background: #0f172a;
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.14);
}

.save-editor-btn:disabled {
  opacity: 0.64;
  cursor: wait;
}

.cancel-editor-btn {
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #475569;
}

@media (max-width: 1200px) {
  .product-editor-card {
    grid-template-columns: 1fr;
  }

  .editor-gallery {
    grid-template-columns: 7rem minmax(0, 1fr);
  }
}

@media (max-width: 900px) {
  .list-hero {
    align-items: flex-start;
    flex-direction: column;
    padding: 1.5rem 0;
  }

  .list-summary {
    width: 100%;
  }

  .product-toolbar {
    align-items: flex-start;
    flex-direction: column;
    padding: 1.25rem;
  }

  .product-toolbar__actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .product-search {
    flex: 1;
    min-width: 14rem;
  }

  .product-editor-card {
    padding: 1.25rem;
  }

  .editor-gallery,
  .editor-fields {
    grid-template-columns: 1fr;
  }

  .gallery-rail {
    flex-direction: row;
    overflow-x: auto;
    justify-content: flex-start;
  }

  .rail-arrow {
    display: none;
  }

  .gallery-main {
    width: 100%;
    max-height: 28rem;
  }

  .gallery-main--empty {
    min-height: 22rem;
  }

  .gallery-main img {
    max-height: 28rem;
  }
}

@media (max-width: 520px) {
  .gallery-main {
    width: 100%;
  }

  .gallery-main img {
    max-height: 24rem;
  }

  .gallery-main--empty {
    min-height: 18rem;
  }
}

@media (max-width: 640px) {
  .product-toolbar__actions,
  .editor-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .add-product-btn,
  .product-search,
  .save-editor-btn,
  .cancel-editor-btn {
    width: 100%;
  }

  .product-pagination {
    justify-content: center;
    flex-wrap: wrap;
    padding: 1rem;
  }
}
</style>
