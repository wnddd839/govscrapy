<template>
  <div class="home-container">
    <div class="main-search-wrapper">
      <h1 class="brand-title">知公</h1>
      <p class="brand-subtitle">一站式政务信息聚合平台</p>
      
      <div class="search-container">
        <!-- 分类导航 (替代搜索框) -->
        <div class="category-nav">
          <div 
            v-for="category in categories" 
            :key="category.name"
            class="category-card"
            @click="handleCategoryClick(category.name)"
          >
            <el-icon class="category-icon" :size="32">
              <component :is="category.icon" />
            </el-icon>
            <span class="category-name">{{ category.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="content-feed">
      <div class="feed-header">
        <span class="feed-title">热门推荐</span>
        <span class="feed-subtitle">今日最受关注的政务动态</span>
      </div>
      
      <div v-loading="loading" class="feed-list">
        <el-empty v-if="!loading && latestList.length === 0" description="暂无最新内容" />
        
        <div v-for="item in latestList" :key="item.id" class="feed-card" @click="goToDetail(item)">
          <h3 class="feed-title">{{ item.title }}</h3>
          <div class="feed-meta">
            <span class="meta-tag source-tag">{{ item.sourceOrg || item.source_org || '政务发布' }}</span>
            <span class="meta-dot" v-if="item.region">·</span>
            <span class="meta-text" v-if="item.region">{{ item.region }}</span>
            <div class="flex-grow" style="flex-grow: 1;"></div>
            <span class="meta-text date-text">{{ formatDate(item.publishDate || item.publish_date) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Document, Reading, DataBoard, Bell } from '@element-plus/icons-vue'
import { getHotInfo } from '../api/publicInfo'

const router = useRouter()
const latestList = ref([])
const loading = ref(false)

// 定义分类及图标
const categories = [
  { name: '政策法规', icon: Document },
  { name: '人事信息', icon: User },
  { name: '规划计划', icon: Reading },
  { name: '财政预决算', icon: DataBoard },
  { name: '招标采购', icon: Bell }
]

// 点击分类跳转到分类子页面
const handleCategoryClick = (categoryName) => {
  router.push(`/category/${categoryName}`)
}

// 加载热门信息
const loadLatestInfo = async () => {
  loading.value = true
  try {
    // API might return array directly or wrapped.
    // Doc says: Response: PublicInfo[] (default latest 10)
    const data = await getHotInfo()
    if (Array.isArray(data)) {
      latestList.value = data
    } else if (data.data) {
        latestList.value = data.data
    }
  } catch (error) {
    console.error('Failed to load hot info', error)
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

onMounted(() => {
  loadLatestInfo()
})
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.main-search-wrapper {
  text-align: center;
  padding: 60px 0 40px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
  border-radius: 16px;
  margin-bottom: 40px;
}

.brand-title {
  font-size: 3rem;
  color: #303133;
  margin-bottom: 10px;
  letter-spacing: 4px;
}

.brand-subtitle {
  font-size: 1.2rem;
  color: #606266;
  margin-bottom: 40px;
}

.search-container {
  max-width: 800px;
  margin: 0 auto;
}

.category-nav {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.category-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  width: 100px;
  height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.category-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  color: #409EFF;
}

.category-icon {
  margin-bottom: 10px;
}

.category-name {
  font-size: 0.9rem;
  font-weight: 500;
}

.content-feed {
  background: white;
  border-radius: 16px;
  padding: 30px;
  min-height: 400px;
}

.feed-header {
  margin-bottom: 20px;
  border-left: 4px solid #409EFF;
  padding-left: 15px;
}

.feed-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #303133;
  margin-right: 15px;
}

.feed-subtitle {
  color: #909399;
  font-size: 0.9rem;
}

.feed-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
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

.feed-card:last-child {
  border-bottom: none;
}

.feed-title {
  font-size: 1.1rem;
  color: #303133;
  margin: 0 0 10px 0;
  font-weight: 500;
}

.feed-meta {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  color: #909399;
}

.meta-tag {
  background-color: #f0f2f5;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 10px;
  color: #606266;
}

.source-tag {
  background-color: #e6f7ff;
  color: #1890ff;
}

.meta-dot {
  margin: 0 5px;
}

.date-text {
  color: #c0c4cc;
}
</style>
