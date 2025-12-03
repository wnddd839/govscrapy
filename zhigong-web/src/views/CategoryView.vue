<template>
  <div class="category-container">
    <div class="category-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>{{ categoryName }}</el-breadcrumb-item>
      </el-breadcrumb>
      <h2 class="category-title">{{ categoryName }}</h2>
    </div>

    <div v-loading="loading" class="feed-list">
      <el-empty v-if="!loading && list.length === 0" description="暂无相关内容" />
      
      <div v-for="item in list" :key="item.id" class="feed-card" @click="goToDetail(item)">
        <h3 class="feed-title">{{ item.title }}</h3>
        <div class="feed-meta">
          <span class="meta-tag source-tag">{{ item.sourceOrg || item.source_org || '政务发布' }}</span>
          <span class="meta-dot" v-if="item.region">·</span>
          <span class="meta-text" v-if="item.region">{{ item.region }}</span>
          <div style="flex-grow: 1;"></div>
          <span class="meta-text">{{ formatDate(item.publishDate || item.publish_date) }}</span>
        </div>
      </div>
      
      <!-- 分页或其他加载更多逻辑可以在这里添加 -->
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getInfoList } from '../api/publicInfo'

const route = useRoute()
const router = useRouter()
const categoryName = ref('')
const list = ref([])
const loading = ref(false)

const loadCategoryData = async () => {
  categoryName.value = route.params.name
  loading.value = true
  list.value = []
  
  try {
    // 由于后端更新分类字段失败（权限受限），回退到前端关键词搜索合并逻辑
    let keywords = []
    
    // 根据新的分类名称映射关键词，并尝试通过更精准的关键词组合来减少误判
    if (categoryName.value === '政策法规') {
      // 政策法规排除“公示”、“名单”、“中标”等明显属于其他类别的词
      keywords = ['办法', '规定', '条例', '法律', '法规', '决定', '意见', '措施', '细则']
    } else if (categoryName.value === '人事信息') {
      // 增加“拟聘用”、“资格审查”等更具体的词
      keywords = ['录用', '撤职', '任免', '名单', '公示', '招聘', '考试', '岗位', '公考', '面试', '成绩', '人员', '拟聘用', '资格审查']
    } else if (categoryName.value === '规划计划') {
      keywords = ['规划', '计划', '纲要', '方案', '年度计划', '发展规划', '专项规划']
    } else if (categoryName.value === '财政预决算') {
      keywords = ['预算', '决算', '财政', '资金', '经费', '三公']
    } else if (categoryName.value === '招标采购') {
      keywords = ['招标', '采购', '中标', '成交', '单一来源', '竞争性磋商', '询价']
    } else {
      // 默认获取全部
      const res = await getInfoList({ page: 0, size: 20 })
      if (res && res.data) list.value = res.data
      else if (Array.isArray(res)) list.value = res
      return
    }

    // 并行请求每个关键词的数据并合并
    const promises = keywords.map(kw => getInfoList({ 
      page: 0, 
      size: 10, // 每个关键词取前10条
      q: kw 
    }))

    const results = await Promise.all(promises)
    
    let allItems = []
    results.forEach(res => {
      const items = (res && res.data) ? res.data : (Array.isArray(res) ? res : [])
      allItems = allItems.concat(items)
    })

    // 去重 (根据ID)
    const uniqueItems = []
    const seenIds = new Set()
    
    allItems.forEach(item => {
      if (!seenIds.has(item.id)) {
        seenIds.add(item.id)
        uniqueItems.push(item)
      }
    })

    // 按发布时间倒序排序
    uniqueItems.sort((a, b) => {
      const dateA = new Date(a.publishDate || a.publish_date || 0)
      const dateB = new Date(b.publishDate || b.publish_date || 0)
      return dateB - dateA
    })

    list.value = uniqueItems

  } catch (error) {
    console.error('Failed to load category data', error)
  } finally {
    loading.value = false
  }
}

const goToDetail = (item) => {
  router.push({
    name: 'detail',
    params: { id: item.id },
    state: { item: JSON.parse(JSON.stringify(item)) }
  })
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const year = d.getFullYear()
  const month = d.getMonth() + 1
  const day = d.getDate()
  return `${year}/${month}/${day}`
}

watch(() => route.params.name, () => {
  loadCategoryData()
})

onMounted(() => {
  loadCategoryData()
})
</script>

<style scoped>
.category-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.category-header {
  margin-bottom: 30px;
}

.category-title {
  font-size: 2rem;
  color: #303133;
  margin-top: 20px;
}

.feed-list {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  min-height: 400px;
}

.feed-card {
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.feed-card:hover {
  background-color: #f9fafc;
}

.feed-title {
  font-size: 1.2rem;
  color: #303133;
  margin-bottom: 10px;
  font-weight: 500;
}

.feed-meta {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  color: #909399;
}

.meta-tag {
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 10px;
  font-size: 0.8rem;
}

.source-tag {
  background-color: #e6f7ff;
  color: #1890ff;
}

.meta-dot {
  margin: 0 5px;
}
</style>
