<template>
  <div class="home-container">
    <!-- 顶部 Banner 区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">政务公开信息整合平台</h1>
        <p class="hero-subtitle">汇聚最新政策、人事、项目与采购信息，为您提供一站式政务服务</p>
      </div>
    </section>

    <div class="main-content-wrapper">
      <!-- 分类专区 -->
      <section class="category-section">
        <div class="section-header">
          <h2 class="section-title">分类专区</h2>
          <span class="section-subtitle">快速定位您关注的领域</span>
        </div>
        
        <div class="category-grid">
          <div v-if="isCategoryLoading" class="loading-container">
            <el-skeleton :rows="3" animated :count="4" />
          </div>
          
          <div 
            v-for="(category, index) in categoryList" 
            :key="index"
            class="category-card"
            :class="`category-card-${index % 6}`"
            @click="goToCategory(category)"
          >
            <div class="card-icon-wrapper">
              <el-icon class="card-icon">
                <el-icon-user v-if="category === '人事任免'" />
                <el-icon-collection v-else-if="category === '招考招聘'" />
                <el-icon-notification v-else-if="category === '干部公示'" />
                <el-icon-more v-else />
              </el-icon>
            </div>
            <h3 class="card-title">{{ category }}</h3>
            <div class="card-hover-bg"></div>
          </div>
        </div>
      </section>

      <!-- 热门政务信息 -->
      <section class="hot-section">
        <div class="section-header">
          <h2 class="section-title">热门政务信息</h2>
          <div class="header-actions">
            <el-button type="primary" link @click="refreshHotData" :loading="isHotLoading">
              <el-icon><el-icon-refresh /></el-icon> 刷新
            </el-button>
          </div>
        </div>

        <div v-loading="isHotLoading" class="hot-grid">
          <el-empty v-if="!isHotLoading && hotList.length === 0" description="暂无热门政务信息" />
          
          <div v-for="(item, index) in hotList" :key="index" class="hot-card" @click="goToDetail(item, 'redis')">
            <div class="hot-card-body">
              <div class="hot-tag" :class="getCategoryColorClass(item.category_tag)">
                {{ item.category_tag || '政务' }}
              </div>
              <h3 class="hot-title" :title="item.title">{{ item.title }}</h3>
              <p class="hot-summary" v-if="item.summary">{{ item.summary }}</p>
              <div class="hot-meta">
                <span class="meta-item"><el-icon><el-icon-office-building /></el-icon> {{ item.publish_dept || '政务发布' }}</span>
                <span class="meta-item"><el-icon><el-icon-clock /></el-icon> {{ formatTime(item.publish_time || item.publishDate) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElIcon, ElButton, ElSkeleton, ElEmpty } from 'element-plus'
import {
  Document as ElIconDocument,
  User as ElIconUser,
  Collection as ElIconCollection,
  Money as ElIconMoney,
  Trophy as ElIconTrophy,
  ShoppingCart as ElIconShoppingCart,
  Notification as ElIconNotification,
  More as ElIconMore,
  Refresh as ElIconRefresh,
  ArrowRight as ElIconArrowRight,
  OfficeBuilding as ElIconOfficeBuilding,
  Clock as ElIconClock
} from '@element-plus/icons-vue'
import { publicInfoApi } from '../api/publicInfo'
import { formatTime } from '../utils/date'

const router = useRouter()
const route = useRoute()
// 分类相关状态
const categoryList = ref([])
const isCategoryLoading = ref(true)
// 热门数据相关状态
const hotList = ref([])
const isHotLoading = ref(true)

// 页面挂载时加载数据
onMounted(() => {
  fetchCategoryList()
  fetchHotList()
})

// 监听路由 query 变化，实现刷新功能
watch(() => route.query.t, () => {
  fetchCategoryList()
  fetchHotList()
})

// 获取分类列表
const fetchCategoryList = async () => {
  isCategoryLoading.value = true
  // 默认固定分类，防止接口异常导致菜单消失
  const defaultCategories = ['人事任免', '招考招聘', '干部公示']
  
  try {
    // 尝试从后端获取
    const res = await publicInfoApi.getCategoryList()
    // 确保返回的是数组且有内容
    if (Array.isArray(res) && res.length > 0) {
      categoryList.value = res
    } else {
      console.warn('Backend returned empty or invalid category list, using defaults')
      categoryList.value = defaultCategories
    }
  } catch (error) {
    console.error('获取分类列表失败，使用默认分类：', error)
    categoryList.value = defaultCategories
  } finally {
    isCategoryLoading.value = false
  }
}

// 获取热门数据
const fetchHotList = async () => {
  isHotLoading.value = true
  try {
    const res = await publicInfoApi.getHotList()
    hotList.value = res || []
  } catch (error) {
    console.error('获取热门数据失败：', error)
    hotList.value = []
  } finally {
    isHotLoading.value = false
  }
}

// 刷新热门数据
const refreshHotData = () => {
  fetchHotList()
}

// 跳转到分类页
const goToCategory = (category) => {
  router.push({
    path: `/category/${category}`
  })
}

// 跳转到详情页
const goToDetail = (row, source) => {
  const dataId = row.dataId || row.data_id || row.id
  if (!dataId) {
    console.error('Invalid dataId for detail navigation')
    return
  }
  router.push({
    name: 'detail',
    params: { id: dataId },
    query: source ? { source } : {}
  })
}

// 获取分类对应的颜色类名
const getCategoryColorClass = (category) => {
  const map = {
    '人事任免': 'tag-pink',
    '招考招聘': 'tag-pink',
    '干部公示': 'tag-pink'
  }
  return map[category] || 'tag-pink'
}
</script>

<style scoped>
.home-container {
  width: 100%;
  min-height: 100vh;
}

/* Hero Section */
.hero-section {
  background: linear-gradient(135deg, #fff0f5 0%, #ffe4e1 100%);
  padding: 80px 20px;
  color: #2c3e50;
  text-align: center;
  margin-bottom: 60px;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, transparent 60%);
  opacity: 0.5;
  pointer-events: none;
}

.hero-title {
  font-size: 42px;
  font-weight: 800;
  margin: 0 0 20px;
  letter-spacing: 2px;
  background: linear-gradient(45deg, #2c3e50, #d63384);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0px 4px 10px rgba(255, 182, 193, 0.3);
  position: relative;
}

.hero-subtitle {
  font-size: 20px;
  opacity: 0.8;
  margin: 0;
  font-weight: 400;
  color: #5e6d82;
  position: relative;
}

.main-content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px;
}

/* Section Common */
.category-section, .hot-section {
  margin-bottom: 60px;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  border-bottom: 2px solid rgba(255, 192, 203, 0.3);
  padding-bottom: 10px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 16px 0 0;
  position: relative;
}

.section-subtitle {
  font-size: 14px;
  color: #909399;
}

.header-actions {
  margin-left: auto;
}

/* Category Grid - Minimalist */
.category-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
}

.category-card {
  flex: 0 0 auto;
  width: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 20px 10px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.category-card:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.card-icon-wrapper {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 15px rgba(255, 182, 193, 0.2);
}

.category-card:hover .card-icon-wrapper {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0,0,0,0.1);
}

.card-icon {
  font-size: 32px;
  color: #d63384; /* Pink default color */
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

/* Colorful Icons but cleaner */
.category-card-0 .card-icon { color: #d63384; }
.category-card-1 .card-icon { color: #d63384; }
.category-card-2 .card-icon { color: #d63384; }
.category-card-3 .card-icon { color: #d63384; }
.category-card-4 .card-icon { color: #d63384; }
.category-card-5 .card-icon { color: #d63384; }

/* Hot Grid - Grid Style */
.hot-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

@media (max-width: 1024px) {
  .hot-grid {
    grid-template-columns: 1fr;
  }
}

.hot-card {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 20px rgba(255, 192, 203, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  height: 100%;
  box-sizing: border-box;
}

.hot-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: transparent;
  transition: background 0.3s;
}

.hot-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

.hot-card:hover::before {
  background: #ff69b4;
}

.hot-card-body {
  position: relative;
  z-index: 1;
}

.hot-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 16px;
  letter-spacing: 0.5px;
}

/* Tag Colors - Soft Pastels */
.tag-blue { background: #e8f3ff; color: #409eff; }
.tag-green { background: #eaf8e3; color: #67c23a; }
.tag-orange { background: #fff3e0; color: #e6a23c; }
.tag-purple { background: #f4f4f5; color: #909399; }
.tag-cyan { background: #e0f7fa; color: #40c9c6; }
.tag-red { background: #fde2e2; color: #f56c6c; }
.tag-pink { background: rgba(255, 192, 203, 0.2); color: #d63384; }
.tag-default { background: rgba(255, 192, 203, 0.2); color: #d63384; }

.hot-title {
  font-size: 18px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 12px;
  line-height: 1.6;
}

.hot-summary {
  font-size: 14px;
  color: #5e6d82;
  margin: 0 0 20px;
  line-height: 1.8;
  display: -webkit-box;
  line-clamp: 3;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hot-meta {
  display: flex;
  align-items: center;
  gap: 20px;
  font-size: 13px;
  color: #909399;
  border-top: 1px solid #f5f7fa;
  padding-top: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Responsive */
@media (max-width: 768px) {
  .hero-title { font-size: 32px; }
  .hero-subtitle { font-size: 16px; }
  .category-grid { justify-content: center; }
  .category-card { min-width: 100px; flex: 0 0 30%; }
}
</style>
