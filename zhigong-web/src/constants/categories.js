import { User, Document, Reading, Bell } from '@element-plus/icons-vue'

export const CATEGORY_MAP = [
  { code: 'policy', name: '政策法规', icon: Document },
  { code: 'personnel', name: '人事信息', icon: User },
  { code: 'planning', name: '规划计划', icon: Reading },
  { code: 'exam', name: '公考资讯', icon: Reading },
  { code: 'tender', name: '招标采购', icon: Bell }
]

export const getCategoryName = (code) => {
  const cat = CATEGORY_MAP.find(c => c.code === code)
  return cat ? cat.name : code
}

export const getCategoryCode = (name) => {
    const cat = CATEGORY_MAP.find(c => c.name === name)
    return cat ? cat.code : name
}
