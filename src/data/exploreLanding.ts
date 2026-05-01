export type ExploreDestination = {
  name: string
  subtitle: string
}

export type ExploreHeroSlide = {
  eyebrow: string
  titleTop: string
  titleMain: string
  description: string
  backgroundImage: string
  destinations: ExploreDestination[]
}

export type ExploreActivity = {
  title: string
  caption: string
  description: string
  image: string
}

export type ExplorePrinciple = {
  index: string
  title: string
  description: string
}

export type ExploreStay = {
  name: string
  location: string
  price: string
  rating: string
  image: string
}

export type ExplorePartner = {
  name: string
  logo: 'microsoft' | 'magento' | 'lakehouse' | 'midea'
}

export type ExploreTestimonial = {
  name: string
  role: string
  quote: string
  avatar: string
}

export const exploreHero = {
  eyebrow: 'EXPLORE',
  titleTop: '去更辽阔的地方',
  titleMain: '探索北境',
  description:
    '椿天社以清冷山海、静谧城镇与缓慢行旅为线索，把一次出发重新整理成值得停留、值得记录、也值得回望的旅程。',
  backgroundImage:
    'https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=2200&auto=format&fit=crop',
  destinations: [
    { name: '罗弗敦群岛', subtitle: '适合海岸漫游' },
    { name: '峡湾山谷', subtitle: '适合留宿与拍照' },
    { name: '湖岸小镇', subtitle: '适合放慢节奏' },
  ] as ExploreDestination[],
}

export const exploreHeroSlides: ExploreHeroSlide[] = [
  exploreHero,
  {
    eyebrow: 'EXPLORE',
    titleTop: '把视线交给湖与山',
    titleMain: '峡湾',
    description:
      '从冷蓝色海面到被云层压低的山脊，把抵达这件事做得更慢一点，也更值得停留一点。',
    backgroundImage:
      'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=2200&auto=format&fit=crop',
    destinations: [
      { name: 'Geirangerfjord', subtitle: '适合看峡湾弧线' },
      { name: 'Andenes', subtitle: '适合住进海风里' },
      { name: 'Senja', subtitle: '适合黄昏公路' },
    ],
  },
  {
    eyebrow: 'EXPLORE',
    titleTop: '沿着更安静的边界前行',
    titleMain: '湖谷',
    description:
      '不追求更满的清单，而是让湖岸、雪线与山谷之间的停顿，构成旅途最值得记住的部分。',
    backgroundImage:
      'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?q=80&w=2200&auto=format&fit=crop',
    destinations: [
      { name: 'Lofoten', subtitle: '适合海边慢住' },
      { name: 'Trondheim', subtitle: '适合城市过渡' },
      { name: 'Nordland', subtitle: '适合高处看海' },
    ],
  },
  {
    eyebrow: 'EXPLORE',
    titleTop: '在更轻的光线里出发',
    titleMain: '北海',
    description:
      '让风景从“看过”变成“住过、走过、再想回去”，把旅途做成更清透的连续镜头。',
    backgroundImage:
      'https://images.unsplash.com/photo-1470770841072-f978cf4d019e?q=80&w=2200&auto=format&fit=crop',
    destinations: [
      { name: 'Tromso', subtitle: '适合夜色停泊' },
      { name: 'Reine', subtitle: '适合码头清晨' },
      { name: 'Alesund', subtitle: '适合山海同框' },
    ],
  },
]

export const exploreActivities: ExploreActivity[] = [
  {
    title: '湖岸徒步',
    caption: '256 条体验路线',
    description: '沿着云层压低的湖谷慢行，适合清晨与傍晚出发。',
    image:
      'https://images.pexels.com/photos/27776931/pexels-photo-27776931.jpeg?auto=compress&cs=tinysrgb&w=1200&h=1800&dpr=1',
  },
  {
    title: '峡湾航行',
    caption: '112 条近海路线',
    description: '在冷蓝色水域里穿行，近距离看见悬崖与雪脊。',
    image:
      'https://images.unsplash.com/photo-1749888224349-febe51bddf63?fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=3000',
  },
  {
    title: '雪岭观景',
    caption: '87 个停驻点',
    description: '为高处停留而设计，适合在日落前抵达。',
    image:
      'https://images.unsplash.com/photo-1667759318388-fa707058f74b?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=3000',
  },
  {
    title: '北港夜泊',
    caption: '64 条夜色提案',
    description: '小尺度、低噪声，适合围炉与夜海一起出现。',
    image:
      'https://images.unsplash.com/photo-1714292806947-7b70469190c3?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=3000',
  },
  {
    title: '森林慢骑',
    caption: '92 条轻户外路线',
    description: '从山脚进入松林，再回到被风整理过的海边小路。',
    image:
      'https://images.pexels.com/photos/28223585/pexels-photo-28223585.jpeg?auto=compress&cs=tinysrgb&w=1200&h=1800&dpr=1',
  },
  {
    title: '玻璃湖露营',
    caption: '41 处安静营地',
    description: '适合两天一夜，不急着安排满行程。',
    image:
      'https://images.unsplash.com/photo-1741619508843-ce7afc97a573?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=3000',
  },
]

export const explorePrinciples: ExplorePrinciple[] = [
  {
    index: '01',
    title: '轻度可持续',
    description: '选择更少打扰环境的出行节奏，把目的地当作需要被尊重的生活现场，而不是匆忙消耗的景观。',
  },
  {
    index: '02',
    title: '共享在地感受',
    description: '把路线、住处、餐食与停留方式整理成可复用的经验，让下一次出发拥有更清晰的参考。',
  },
  {
    index: '03',
    title: '重视真实体验',
    description: '比起堆砌清单，我们更在意抵达时的光线、风声、步速与停留后的记忆密度。',
  },
]

export const exploreStays: ExploreStay[] = [
  {
    name: '雾港木屋',
    location: '海湾边的安静住处',
    price: '¥1280 / 晚',
    rating: '4.9',
    image:
      'https://images.pexels.com/photos/33895839/pexels-photo-33895839.jpeg?cs=srgb&dl=pexels-nguyen-ngoc-tien-1321490019-33895839.jpg&fm=jpg',
  },
  {
    name: '雪线观景屋',
    location: '靠近山谷入口',
    price: '¥980 / 晚',
    rating: '4.8',
    image:
      'https://images.pexels.com/photos/5529123/pexels-photo-5529123.jpeg?cs=srgb&dl=pexels-sinileunen-5529123.jpg&fm=jpg',
  },
  {
    name: '湖畔白屋',
    location: '适合慢住两晚',
    price: '¥1160 / 晚',
    rating: '4.9',
    image:
      'https://images.pexels.com/photos/14730099/pexels-photo-14730099.jpeg?cs=srgb&dl=pexels-eberhardgross-14730099.jpg&fm=jpg',
  },
]

export const explorePartners: ExplorePartner[] = [
  { name: 'Microsoft', logo: 'microsoft' },
  { name: 'Magento', logo: 'magento' },
  { name: 'Lakehouse', logo: 'lakehouse' },
  { name: 'Midea', logo: 'midea' },
]

export const exploreTestimonials: ExploreTestimonial[] = [
  {
    name: '林清和',
    role: '独立摄影师',
    quote: '不是那种把景点排满的攻略页，更像有人已经替你筛过一次，只留下真正值得出发的地方。',
    avatar:
      'https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=300&auto=format&fit=crop',
  },
  {
    name: '周以衡',
    role: '旅行写作者',
    quote: '页面节奏很克制，像一本慢慢展开的旅途样刊，让人愿意往下读，也愿意继续往下走。',
    avatar:
      'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=300&auto=format&fit=crop',
  },
  {
    name: '陈知予',
    role: '山海路线策划',
    quote: '它没有急着告诉你买什么，而是先帮你确定想去哪里、想过怎样的一次停留。',
    avatar:
      'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=300&auto=format&fit=crop',
  },
]
