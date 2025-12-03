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
    // 直接使用后端支持的 category 参数进行筛选
    const params = {
      page: 0,
      size: 20,
      category: categoryName.value // 传递分类名称给后端
    }
    
    const res = await getInfoList(params)
    
    if (res && res.data) {
      list.value = res.data
    } else if (Array.isArray(res)) {
      list.value = res
    }

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
