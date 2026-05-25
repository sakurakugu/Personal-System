export interface SponsorMethod {
  name: string
  icon: string
  qrCode?: string
  link?: string
  description?: string
  enabled: boolean
}

export interface SponsorItem {
  name: string
  amount?: string
  date?: string
}

export interface SponsorConfig {
  title: string
  description: string
  usage: string
  showSponsorsList: boolean
  showButtonInPost: boolean
  methods: SponsorMethod[]
  sponsors: SponsorItem[]
}

export const sponsorConfig: SponsorConfig = {
  title: '',
  description: '',
  usage: '您的赞助将用于服务器维护、内容创作和功能开发，帮助我持续提供优质内容。',
  showSponsorsList: true,
  showButtonInPost: true,
  methods: [
    {
      name: '支付宝',
      icon: 'fa6-brands:alipay',
      qrCode: '/sponsor/alipay.png',
      description: '使用 支付宝 扫码赞助',
      enabled: true,
    },
    {
      name: '微信',
      icon: 'fa6-brands:weixin',
      qrCode: '/sponsor/wechat.png',
      description: '使用 微信 扫码赞助',
      enabled: true,
    },
    {
      name: 'ko-fi',
      icon: 'simple-icons:kofi',
      link: '',
      description: 'Buy a Coffee for Firefly',
      enabled: true,
    },
    {
      name: '爱发电',
      icon: 'simple-icons:afdian',
      link: '',
      description: '通过 爱发电 进行赞助',
      enabled: true,
    },
  ],
  sponsors: [
    // {
    //   name: '测试者A',
    //   amount: '¥50',
    //   date: '2026-05-24',
    // },
    // {
    //   name: '匿名用户',
    //   amount: '¥20',
    //   date: '2026-05-23',
    // },
  ],
}
