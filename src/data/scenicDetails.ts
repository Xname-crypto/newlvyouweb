export type ScenicFactIconKey =
  | 'duration'
  | 'activity'
  | 'intensity'
  | 'group'
  | 'age'
  | 'season'

export interface ScenicDetailGalleryItem {
  src: string
  alt: string
  label?: string
}

export interface ScenicDetailFact {
  label: string
  value: string
  icon: ScenicFactIconKey
}

export interface ScenicDetailDay {
  id: string
  title: string
  summary: string
  media?: ScenicDetailGalleryItem
  mapLabel?: string
  accommodation?: {
    description: string
    sharedRoom?: string
    doubleRoom?: string
    singleRoom?: string
    roomImages?: ScenicDetailGalleryItem[]
  }
}

export interface ScenicReview {
  id: string
  author: string
  avatar: string
  dateLabel: string
  title: string
  content: string
  rating: number
}

export interface ScenicFaq {
  id: string
  question: string
  answer: string
}

export interface ScenicSimilarTour {
  id: string
  title: string
  subtitle: string
  image: string
  price: string
  badgeText?: string
}

export interface ScenicDetailData {
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
  gallery: ScenicDetailGalleryItem[]
  overview: {
    description: string
    facts: ScenicDetailFact[]
  }
  bookingPanel: {
    dateOptions: string[]
    travelerSummary: string
    selectionHint: string
    contactHint: string
    reserveNote: string
  }
  itineraryDays: ScenicDetailDay[]
  includes: string[]
  excludes: string[]
  reviews: ScenicReview[]
  faqs: ScenicFaq[]
  essentialInfo: string[]
  similarTours: ScenicSimilarTour[]
}

interface ScenicSeed {
  id: string
  title: string
  subtitle: string
  locationLabel: string
  currentPrice: string
  previousPrice: string
  discountLabel: string
  reviewScore: number
  reviewCount: number
  gallery: ScenicDetailGalleryItem[]
  description: string
  activityLabel: string
  intensityLabel: string
  groupLabel: string
  ageLabel: string
  seasonLabel: string
  itineraryFocus: string[]
  includes: string[]
  excludes: string[]
  essentialInfo: string[]
  similarIds: string[]
}

const roomImages: ScenicDetailGalleryItem[] = [
  {
    src: 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1200&auto=format&fit=crop',
    alt: '海景双床房',
  },
  {
    src: 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=900&auto=format&fit=crop',
    alt: '山景大床房',
  },
  {
    src: 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?q=80&w=1000&auto=format&fit=crop',
    alt: '家庭套房',
  },
]

const scenicSeeds: ScenicSeed[] = [
  {
    id: 'card-1',
    title: '文化古迹环线之旅',
    subtitle: '徒步之旅 | 厦门大学与沙坡尾',
    locationLabel: '福建省 · 厦门市',
    currentPrice: '¥1799',
    previousPrice: '¥2399',
    discountLabel: '立减25%',
    reviewScore: 4.9,
    reviewCount: 108,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=1800&auto=format&fit=crop',
        alt: '厦门海岸与沙滩',
      },
      {
        src: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=900&auto=format&fit=crop',
        alt: '海岸步道航拍',
      },
      {
        src: 'https://images.unsplash.com/photo-1528127269322-539801943592?q=80&w=900&auto=format&fit=crop',
        alt: '海岛近景',
      },
      {
        src: 'https://images.unsplash.com/photo-1518509562904-e7ef99cdcc86?q=80&w=900&auto=format&fit=crop',
        alt: '城市海滨日落',
      },
      {
        src: 'https://images.unsplash.com/photo-1493558103817-58b2924bce98?q=80&w=900&auto=format&fit=crop',
        alt: '街区人文细节',
      },
    ],
    description:
      '这条线路把校园、海岸、人文街区和城市夜景串成一条完整体验线，适合第一次来厦门、又不想只停留在打卡层面的游客。白天看海、傍晚进城、夜里逛街，节奏轻松但内容完整。',
    activityLabel: '城市步行',
    intensityLabel: '轻松',
    groupLabel: '2-10人',
    ageLabel: '7岁以上',
    seasonLabel: '全年可行',
    itineraryFocus: ['厦门大学', '南普陀', '沙坡尾', '环岛路', '中山路', '八市'],
    includes: ['中文向导服务', '行程中景点讲解', '首晚欢迎饮品', '城市慢行路线规划', '基础保险'],
    excludes: ['往返交通', '个人消费', '部分景区预约费用', '行程外餐饮', '小费及额外服务'],
    essentialInfo: ['建议穿轻便步行鞋。', '夏季日照强，需准备防晒。', '校区及宗教场所有着装要求，请避免过于随意。'],
    similarIds: ['card-2', 'card-3', 'card-6'],
  },
  {
    id: 'card-2',
    title: '鼓浪屿落日漫游',
    subtitle: '老城人文 | 鼓浪屿与鹭江夜色',
    locationLabel: '福建省 · 厦门市',
    currentPrice: '¥1599',
    previousPrice: '¥2080',
    discountLabel: '立减23%',
    reviewScore: 4.8,
    reviewCount: 76,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?q=80&w=1800&auto=format&fit=crop',
        alt: '鼓浪屿海岸线',
      },
      {
        src: 'https://images.unsplash.com/photo-1493558103817-58b2924bce98?q=80&w=900&auto=format&fit=crop',
        alt: '老街立面',
      },
      {
        src: 'https://images.unsplash.com/photo-1519046904884-53103b34b206?q=80&w=900&auto=format&fit=crop',
        alt: '港湾码头',
      },
      {
        src: 'https://images.unsplash.com/photo-1521295121783-8a321d551ad2?q=80&w=900&auto=format&fit=crop',
        alt: '海边日落',
      },
    ],
    description:
      '主打岛屿慢节奏和傍晚光线，从白天的历史建筑到夜晚的沿海步道，路线更偏散步、拍照和感受生活氛围。适合情侣、朋友和喜欢城市故事的人。',
    activityLabel: '岛屿漫游',
    intensityLabel: '轻松',
    groupLabel: '2-8人',
    ageLabel: '6岁以上',
    seasonLabel: '3月-11月',
    itineraryFocus: ['轮渡码头', '龙头路', '最美转角', '菽庄花园', '鹭江道'],
    includes: ['上岛路线建议', '漫游讲解卡片', '日落摄影点位推荐', '下午茶体验'],
    excludes: ['轮渡票', '个人购物', '行程外门票', '夜宵与酒水'],
    essentialInfo: ['节假日轮渡预约紧张，建议提前确认。', '鼓浪屿石板路较多，行李不宜过大。', '傍晚风大，建议带薄外套。'],
    similarIds: ['card-1', 'card-4', 'card-8'],
  },
  {
    id: 'card-3',
    title: '山海步道轻徒步',
    subtitle: '山海线 | 东坪山到曾厝垵',
    locationLabel: '福建省 · 厦门市',
    currentPrice: '¥1399',
    previousPrice: '¥1880',
    discountLabel: '立减26%',
    reviewScore: 4.7,
    reviewCount: 61,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=1800&auto=format&fit=crop',
        alt: '山海步道视角',
      },
      {
        src: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?q=80&w=900&auto=format&fit=crop',
        alt: '山野步道',
      },
      {
        src: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=900&auto=format&fit=crop',
        alt: '海岸远景',
      },
      {
        src: 'https://images.unsplash.com/photo-1473116763249-2faaef81ccda?q=80&w=900&auto=format&fit=crop',
        alt: '山顶营地',
      },
    ],
    description:
      '适合喜欢轻徒步的人，一路从城市边缘走进山海开阔地带，既有爬升，也有连续海景。体验重点是过程本身，不追求极限，更注重轻松节奏和沿途风景。',
    activityLabel: '轻徒步',
    intensityLabel: '中等',
    groupLabel: '4-12人',
    ageLabel: '10岁以上',
    seasonLabel: '10月-4月',
    itineraryFocus: ['东坪山', '山海健康步道', '观景平台', '曾厝垵'],
    includes: ['徒步领队', '补给包', '线路安全提示', '集合点接驳'],
    excludes: ['专业登山装备', '个人零食补给', '行程外交通'],
    essentialInfo: ['建议穿防滑运动鞋。', '下雨天部分路段会湿滑。', '有轻微爬升，不建议穿拖鞋。'],
    similarIds: ['card-1', 'card-6', 'card-9'],
  },
  {
    id: 'card-4',
    title: '海湾帆影半日游',
    subtitle: '亲水体验 | 五缘湾轻奢时段',
    locationLabel: '福建省 · 厦门市',
    currentPrice: '¥1899',
    previousPrice: '¥2480',
    discountLabel: '立减24%',
    reviewScore: 4.9,
    reviewCount: 52,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1519046904884-53103b34b206?q=80&w=1800&auto=format&fit=crop',
        alt: '海湾帆船',
      },
      {
        src: 'https://images.unsplash.com/photo-1483683804023-6ccdb62f86ef?q=80&w=900&auto=format&fit=crop',
        alt: '港湾与游艇',
      },
      {
        src: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=900&auto=format&fit=crop',
        alt: '海面远景',
      },
      {
        src: 'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?q=80&w=900&auto=format&fit=crop',
        alt: '滨海天际线',
      },
    ],
    description:
      '如果你希望这次出行更轻松、更体面，这条半日线更合适。重点不在密集打卡，而是把海上视角、午后时光和城市舒适感组合起来，适合度假式体验。',
    activityLabel: '海上体验',
    intensityLabel: '轻松',
    groupLabel: '2-6人',
    ageLabel: '5岁以上',
    seasonLabel: '4月-10月',
    itineraryFocus: ['五缘湾', '游艇港', '滨海观景带', '海风下午茶'],
    includes: ['基础帆船体验', '岸上茶点', '摄影点位推荐', '救生装备'],
    excludes: ['私人包船升级', '专业跟拍', '个人消费'],
    essentialInfo: ['遇强风天气可能调整时间。', '建议穿浅色速干衣物。', '晕船体质建议提前准备。'],
    similarIds: ['card-2', 'card-5', 'card-10'],
  },
  {
    id: 'card-5',
    title: '茶园村落体验线',
    subtitle: '慢生活 | 集美周边茶园与古厝',
    locationLabel: '福建省 · 厦门市',
    currentPrice: '¥1260',
    previousPrice: '¥1680',
    discountLabel: '立减25%',
    reviewScore: 4.6,
    reviewCount: 43,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1464207687429-7505649dae38?q=80&w=1800&auto=format&fit=crop',
        alt: '茶园山坡',
      },
      {
        src: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=900&auto=format&fit=crop',
        alt: '村落道路',
      },
      {
        src: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=900&auto=format&fit=crop',
        alt: '森林与湖面',
      },
      {
        src: 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=900&auto=format&fit=crop',
        alt: '乡野观景台',
      },
    ],
    description:
      '这是更偏休闲和在地生活的线路。没有太强烈的运动感，重点在于茶园、古厝、村落散步和慢节奏用餐体验，适合带家人一起出行。',
    activityLabel: '乡野漫游',
    intensityLabel: '轻松',
    groupLabel: '2-12人',
    ageLabel: '全年龄',
    seasonLabel: '全年可行',
    itineraryFocus: ['集美学村', '村落步道', '茶园观景台', '古厝餐厅'],
    includes: ['茶园体验', '村落导览', '特色午餐', '伴手礼小样'],
    excludes: ['往返接送升级', '个人购物', '额外酒水'],
    essentialInfo: ['乡野路段日晒明显。', '如同行长者，建议备好遮阳伞。', '周末车流较大，需预留机动时间。'],
    similarIds: ['card-4', 'card-7', 'card-8'],
  },
  {
    id: 'card-6',
    title: '环岛骑行看海线',
    subtitle: '活力体验 | 环岛路晨光骑行',
    locationLabel: '福建省 · 厦门市',
    currentPrice: '¥1499',
    previousPrice: '¥1980',
    discountLabel: '立减24%',
    reviewScore: 4.8,
    reviewCount: 69,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1483683804023-6ccdb62f86ef?q=80&w=1800&auto=format&fit=crop',
        alt: '环岛骑行路段',
      },
      {
        src: 'https://images.unsplash.com/photo-1521295121783-8a321d551ad2?q=80&w=900&auto=format&fit=crop',
        alt: '海边晨光',
      },
      {
        src: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=900&auto=format&fit=crop',
        alt: '海浪岸边',
      },
      {
        src: 'https://images.unsplash.com/photo-1473116763249-2faaef81ccda?q=80&w=900&auto=format&fit=crop',
        alt: '沿海观景点',
      },
    ],
    description:
      '清晨出发、顺海而行，是这条线路最有记忆点的部分。运动强度适中，停留点多，适合拍照、呼吸海风，也适合把城市从动态视角再看一遍。',
    activityLabel: '骑行体验',
    intensityLabel: '中等',
    groupLabel: '4-10人',
    ageLabel: '12岁以上',
    seasonLabel: '10月-5月',
    itineraryFocus: ['白城沙滩', '环岛路', '音乐广场', '黄厝海滩'],
    includes: ['单车租赁', '头盔', '线路领骑', '能量补给'],
    excludes: ['专业骑行鞋服', '个人饮品', '行程外打车费用'],
    essentialInfo: ['日出场次需早起集合。', '建议轻装出发。', '雨天路线将切换为城市慢游版本。'],
    similarIds: ['card-1', 'card-3', 'card-10'],
  },
  {
    id: 'card-7',
    title: '滨海夜色摄影团',
    subtitle: '城市夜景 | 光影与街区捕捉',
    locationLabel: '福建省 · 厦门市',
    currentPrice: '¥1320',
    previousPrice: '¥1760',
    discountLabel: '立减25%',
    reviewScore: 4.7,
    reviewCount: 38,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1518509562904-e7ef99cdcc86?q=80&w=1800&auto=format&fit=crop',
        alt: '夜色海岸',
      },
      {
        src: 'https://images.unsplash.com/photo-1493558103817-58b2924bce98?q=80&w=900&auto=format&fit=crop',
        alt: '街区灯光',
      },
      {
        src: 'https://images.unsplash.com/photo-1521295121783-8a321d551ad2?q=80&w=900&auto=format&fit=crop',
        alt: '黄昏天际线',
      },
      {
        src: 'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?q=80&w=900&auto=format&fit=crop',
        alt: '海港夜景',
      },
    ],
    description:
      '适合喜欢记录城市的人。我们把傍晚蓝调时刻、夜间街区、海岸灯光都串起来，让一条夜线兼顾画面和步行舒适度，不追赶节奏，只挑重点光影。',
    activityLabel: '城市摄影',
    intensityLabel: '轻松',
    groupLabel: '2-8人',
    ageLabel: '14岁以上',
    seasonLabel: '全年可行',
    itineraryFocus: ['演武大桥观景', '沙坡尾夜街', '双子塔外景', '鹭江道'],
    includes: ['摄影向导', '拍摄机位建议', '夜间热饮', '小团路线规划'],
    excludes: ['相机设备租赁', '后期修图服务', '额外交通'],
    essentialInfo: ['建议带稳定性较好的镜头。', '夜间步行请轻装。', '下雨天也可成行，但会调整点位。'],
    similarIds: ['card-5', 'card-8', 'card-9'],
  },
  {
    id: 'card-8',
    title: '古厝人文探索日',
    subtitle: '建筑与故事 | 老街区深度步行',
    locationLabel: '福建省 · 泉州市',
    currentPrice: '¥1420',
    previousPrice: '¥1890',
    discountLabel: '立减25%',
    reviewScore: 4.8,
    reviewCount: 57,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=1800&auto=format&fit=crop',
        alt: '古厝街巷',
      },
      {
        src: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=900&auto=format&fit=crop',
        alt: '古城步道',
      },
      {
        src: 'https://images.unsplash.com/photo-1493558103817-58b2924bce98?q=80&w=900&auto=format&fit=crop',
        alt: '建筑细部',
      },
      {
        src: 'https://images.unsplash.com/photo-1518509562904-e7ef99cdcc86?q=80&w=900&auto=format&fit=crop',
        alt: '古城黄昏',
      },
    ],
    description:
      '如果你更在意建筑、故事和城市性格，这条线路会比普通观光更有意思。重点是边走边看、边听边理解，让历史街区从背景板变成可感知的现场。',
    activityLabel: '人文步行',
    intensityLabel: '轻松',
    groupLabel: '2-12人',
    ageLabel: '8岁以上',
    seasonLabel: '9月-5月',
    itineraryFocus: ['古厝街巷', '传统市场', '老剧场外景', '城墙边界'],
    includes: ['在地讲解', '步行路线图', '特色小吃试吃', '古建筑导览'],
    excludes: ['大交通', '个人采购', '行程外门票'],
    essentialInfo: ['部分街巷地面不平整。', '适合慢速步行，不建议赶时间。', '午后较热，建议带水。'],
    similarIds: ['card-2', 'card-5', 'card-7'],
  },
  {
    id: 'card-9',
    title: '湿地观鸟自然行',
    subtitle: '生态探索 | 滨海湿地轻观察',
    locationLabel: '福建省 · 漳州市',
    currentPrice: '¥1180',
    previousPrice: '¥1580',
    discountLabel: '立减25%',
    reviewScore: 4.6,
    reviewCount: 29,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1800&auto=format&fit=crop',
        alt: '湿地与湖面',
      },
      {
        src: 'https://images.unsplash.com/photo-1464207687429-7505649dae38?q=80&w=900&auto=format&fit=crop',
        alt: '观景步道',
      },
      {
        src: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?q=80&w=900&auto=format&fit=crop',
        alt: '自然保护区远景',
      },
      {
        src: 'https://images.unsplash.com/photo-1501785888041-af3ef285b470?q=80&w=900&auto=format&fit=crop',
        alt: '沿湖栈道',
      },
    ],
    description:
      '路线整体较安静，节奏慢，适合想从城市切换到自然状态的人。重点不是“打卡”，而是看风、看水、看鸟群活动，让体验更沉浸。',
    activityLabel: '自然观察',
    intensityLabel: '轻松',
    groupLabel: '2-10人',
    ageLabel: '6岁以上',
    seasonLabel: '11月-3月',
    itineraryFocus: ['湿地栈道', '观鸟台', '湖畔草地', '生态教育点'],
    includes: ['望远镜借用', '自然讲解', '热饮补给', '基础保险'],
    excludes: ['长焦器材', '私人交通', '额外活动体验'],
    essentialInfo: ['建议穿不太鲜艳的衣物。', '早晨体验最佳。', '请勿高声喧哗或投喂动物。'],
    similarIds: ['card-3', 'card-7', 'card-10'],
  },
  {
    id: 'card-10',
    title: '海峡晨光观景线',
    subtitle: '看海发呆 | 海边日出与早午餐',
    locationLabel: '福建省 · 平潭综合实验区',
    currentPrice: '¥1680',
    previousPrice: '¥2240',
    discountLabel: '立减25%',
    reviewScore: 4.9,
    reviewCount: 84,
    gallery: [
      {
        src: 'https://images.unsplash.com/photo-1521295121783-8a321d551ad2?q=80&w=1800&auto=format&fit=crop',
        alt: '海峡清晨',
      },
      {
        src: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=900&auto=format&fit=crop',
        alt: '海浪与白沙',
      },
      {
        src: 'https://images.unsplash.com/photo-1519046904884-53103b34b206?q=80&w=900&auto=format&fit=crop',
        alt: '海湾码头',
      },
      {
        src: 'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?q=80&w=900&auto=format&fit=crop',
        alt: '海上晨色',
      },
    ],
    description:
      '这条线路适合真正想放松的人。最大的亮点不是密度，而是节奏感: 早起去看日出，白天以海边停留和慢餐为主，把时间留给风景本身。',
    activityLabel: '海边度假',
    intensityLabel: '轻松',
    groupLabel: '2-8人',
    ageLabel: '全年龄',
    seasonLabel: '4月-10月',
    itineraryFocus: ['日出观景点', '海边步道', '礁石海湾', '海景早午餐'],
    includes: ['日出点位安排', '早午餐', '海边接驳', '摄影建议'],
    excludes: ['异地交通', '旅拍服务', '额外餐食'],
    essentialInfo: ['日出时间会随季节变化。', '海边风大，请备薄外套。', '天气不佳时会调整为同区域观景方案。'],
    similarIds: ['card-4', 'card-6', 'card-9'],
  },
]

const travelerDates = ['05月03日 周五', '05月10日 周五', '05月17日 周五', '05月24日 周五']

const reviewerPool = [
  {
    author: '林知夏',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=200&auto=format&fit=crop',
    title: '体验节奏很舒服',
    content: '路线不赶，讲解点和休息点分配得很合理，既能拍照也能真正逛进去，适合第一次来这座城市的人。',
  },
  {
    author: '周屿川',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=200&auto=format&fit=crop',
    title: '比预期更完整',
    content: '原本担心只是普通打卡，实际安排比较连贯，景点之间过渡自然，导览信息也很清楚。',
  },
  {
    author: '许安宁',
    avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=200&auto=format&fit=crop',
    title: '适合朋友同行',
    content: '路线轻松，拍照点位多，吃饭和休息安排也比较友好。对不想做太多攻略的人很省心。',
  },
]

const baseFaqs: ScenicFaq[] = [
  {
    id: 'faq-1',
    question: '这条线路适合穿什么衣服？',
    answer: '建议穿轻便、透气、方便步行的衣物和鞋子。如果是海边或清晨场次，备一件薄外套会更稳妥。',
  },
  {
    id: 'faq-2',
    question: '老人和小朋友能参加吗？',
    answer: '大多数线路适合体能正常的老人和儿童参加，但具体还要看页面中的年龄建议和活动强度说明。',
  },
  {
    id: 'faq-3',
    question: '遇到下雨会取消吗？',
    answer: '轻雨通常不影响成行，主办方会根据风力、能见度和安全情况调整点位或出发时间。',
  },
  {
    id: 'faq-4',
    question: '可以只预订一部分项目吗？',
    answer: '当前页面展示的是整套线路模板。后续接入真实数据后，可按具体产品支持不同套餐和可选项。',
  },
  {
    id: 'faq-5',
    question: '下单后如何联系工作人员？',
    answer: '右侧预订卡会保留咨询入口。当前是静态演示，后续真实版本会接入客服或商家联系方式。',
  },
  {
    id: 'faq-6',
    question: '当天临时改人数可以吗？',
    answer: '静态页阶段不处理库存和人数变更。真实数据接入后，会根据供应商规则决定是否支持调整。',
  },
]

const buildFacts = (seed: ScenicSeed): ScenicDetailFact[] => [
  { label: '行程时长', value: '2天', icon: 'duration' },
  { label: '活动类型', value: seed.activityLabel, icon: 'activity' },
  { label: '体力要求', value: seed.intensityLabel, icon: 'intensity' },
  { label: '成团人数', value: seed.groupLabel, icon: 'group' },
  { label: 'Age', value: seed.ageLabel, icon: 'age' },
  { label: '适合季节', value: seed.seasonLabel, icon: 'season' },
]

const buildItineraryDays = (seed: ScenicSeed): ScenicDetailDay[] =>
  seed.itineraryFocus.slice(0, 6).map((focus, index) => ({
    id: `day-${index + 1}`,
    title: `第 ${index + 1} 天`,
    summary:
      index === 0
        ? `从 ${focus} 开始进入这条路线的核心体验，先用轻松步行或短接驳熟悉环境，再逐步展开人文、景观和停留点。`
        : `围绕 ${focus} 展开更深入的体验，保留足够自由时间拍照、休息和感受当地氛围，不把行程压得太满。`,
    media: seed.gallery[(index + 1) % seed.gallery.length],
    mapLabel: '查看地图',
    accommodation:
      index === 0
        ? {
            description:
              '优先安排交通便利、步行即可回到主线路的舒适型酒店，方便晚间自由活动和第二天衔接。',
            sharedRoom: '双床房',
            doubleRoom: '大床房',
            singleRoom: '单人入住补差',
            roomImages,
          }
        : undefined,
  }))

const buildReviews = (seed: ScenicSeed): ScenicReview[] =>
  reviewerPool.map((reviewer, index) => ({
    id: `${seed.id}-review-${index + 1}`,
    author: reviewer.author,
    avatar: reviewer.avatar,
    dateLabel: index === 0 ? '评价于 11月24日' : index === 1 ? '评价于 11月23日' : '评价于 11月22日',
    title: reviewer.title,
    content: reviewer.content,
    rating: Math.max(4, Math.round(seed.reviewScore)),
  }))

const createDetail = (seed: ScenicSeed): ScenicDetailData => ({
  id: seed.id,
  title: seed.title,
  subtitle: seed.subtitle,
  locationLabel: seed.locationLabel,
  breadcrumb: ['目的地', seed.locationLabel, seed.title],
  reviewCount: seed.reviewCount,
  reviewScore: seed.reviewScore,
  price: {
    current: seed.currentPrice,
    previous: seed.previousPrice,
    discountLabel: seed.discountLabel,
    note: '价格会根据出发日期与人数略有浮动',
  },
  gallery: seed.gallery,
  overview: {
    description: seed.description,
    facts: buildFacts(seed),
  },
  bookingPanel: {
    dateOptions: travelerDates,
    travelerSummary: '2位成人，1位儿童',
    selectionHint: 'Flight, hotel, car etc.',
    contactHint: 'If you have questions about this tour, please feel free to call.',
    reserveNote: '*当前展示内容为静态示例数据，后续可替换为真实供应商数据',
  },
  itineraryDays: buildItineraryDays(seed),
  includes: seed.includes,
  excludes: seed.excludes,
  reviews: buildReviews(seed),
  faqs: baseFaqs,
  essentialInfo: seed.essentialInfo,
  similarTours: [],
})

const detailsById = Object.fromEntries(
  scenicSeeds.map((seed) => [seed.id, createDetail(seed)]),
) as Record<string, ScenicDetailData>

for (const seed of scenicSeeds) {
  detailsById[seed.id].similarTours = seed.similarIds.reduce<ScenicSimilarTour[]>(
    (list, similarId) => {
      const target = detailsById[similarId]
      if (!target) {
        return list
      }

      list.push({
        id: target.id,
        title: target.title,
        subtitle: target.subtitle,
        image: target.gallery[0]?.src || '',
        price: target.price.current,
        badgeText: target.price.discountLabel,
      })

      return list
    },
    [],
  )
}

export const scenicDetails = detailsById

export const getScenicDetailById = (id: string) => scenicDetails[id] ?? null
