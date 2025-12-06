<template>
  <div class="list-container">
    <div class="filter-bar">
      <el-form :inline="true" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchParams.q" placeholder="搜索标题或正文" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="地区">
          <el-select v-model="searchParams.region" placeholder="全部" clearable style="width: 120px">
            <el-option label="北京" value="北京" />
            <el-option label="上海" value="上海" />
            <el-option label="广东" value="广东" />
            <el-option label="海南" value="海南" />
             <!-- Add more as needed -->
          </el-select>
        </el-form-item>
        <el-form-item label="发布时间">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">搜索</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="result-list" v-loading="loading">
      <el-empty v-if="!loading && total === 0" description="未找到相关信息" />
      
      <div v-for="item in list" :key="item.id" class="list-item" @click="goToDetail(item)">
        <h3 class="item-title" v-html="highlight(item.title)"></h3>
        <div class="item-snippet" v-if="item.contentText || item.content_text">
            {{ (item.contentText || item.content_text).substring(0, 150) }}...
        </div>
        <div class="item-meta">
          <span class="tag region" v-if="item.region">{{ item.region }}</span>
          <span class="tag source">{{ item.sourceOrg || item.source_org || '政务发布' }}</span>
          <span class="date">{{ formatDate(item.publishDate || item.publish_date) }}</span>
        </div>
      </div>
    </div>

    <div class="pagination-container" v-if="total > 0">
      <el-pagination
        v-model:current-page="searchParams.page"
        v-model:page-size="searchParams.size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getInfoList } from '../api/publicInfo'

const route = useRoute()
const router = useRouter()

const searchParams = reactive({
  q: '',
  region: '',
  page: 1, // Element Plus pagination starts at 1, backend at 0 usually? Doc says "page (from 0)"
  size: 20
})
const dateRange = ref([])
const list = ref([])
const total = ref(0)
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      q: searchParams.q,
      region: searchParams.region,
      page: searchParams.page - 1, // Convert to 0-based for backend
      size: searchParams.size,
      startDate: dateRange.value ? dateRange.value[0] : undefined,
      endDate: dateRange.value ? dateRange.value[1] : undefined,
      source: 'mysql' // 指定走MySQL数据源
    }
    
    const res = await getInfoList(params)
    // Doc says response: { data: [...], page: 0, size: 10, total: 100 }
    if (res) {
        list.value = res.data || []
        total.value = res.total || 0
    }
  } catch (error) {
    console.error('Fetch error', error)
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  searchParams.page = 1
  fetchData()
  // Update URL query
  router.push({
      query: {
          ...route.query,
          q: searchParams.q,
          region: searchParams.region,
          page: 1
      }
  })
}

const handleSizeChange = (val) => {
  searchParams.size = val
  fetchData()
}

const handleCurrentChange = (val) => {
  searchParams.page = val
  fetchData()
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

// Simple highlight function
const highlight = (text) => {
    if (!searchParams.q || !text) return text
    const reg = new RegExp(searchParams.q, 'gi')
    return text.replace(reg, match => `<span style="color: #f56c6c; font-weight: bold;">${match}</span>`)
}

onMounted(() => {
  // Init from route query
  if (route.query.q) searchParams.q = route.query.q
  if (route.query.region) searchParams.region = route.query.region
  // if (route.query.page) searchParams.page = parseInt(route.query.page)
  
  fetchData()
})

// Watch route changes (e.g. back button)
watch(() => route.query, (newQuery) => {
    if (newQuery.q !== undefined) searchParams.q = newQuery.q
    if (newQuery.region !== undefined) searchParams.region = newQuery.region
    fetchData()
})
</script>

<style scoped>
.list-container {
  max-width: 1000px;
  margin: 0 auto;
  background: white;
  padding: 20px;
  border-radius: 8px;
  min-height: 500px;
}
.filter-bar {
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}
/* 修复输入框交互导致按钮抖动问题 */
.search-form :deep(.el-form-item) {
  margin-right: 12px;
}
.search-form :deep(.el-input) {
  width: 320px;
}
.search-form :deep(.el-input__wrapper) {
  transition: none !important;
  box-shadow: none !important;
  padding: 0 11px !important; /* 保持交互前后一致，避免宽度变化 */
}
.search-form :deep(.el-input__wrapper:hover),
.search-form :deep(.el-input__wrapper.is-focus) {
  transition: none !important;
  box-shadow: none !important;
  padding: 0 11px !important;
}
.list-item {
  padding: 15px 0;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: background 0.3s;
}
.list-item:hover {
  background-color: #f9fafc;
}
.item-title {
  margin: 0 0 10px;
  font-size: 1.2rem;
  color: #303133;
}
.item-snippet {
  font-size: 0.9rem;
  color: #606266;
  margin-bottom: 10px;
  line-height: 1.5;
}
.item-meta {
  font-size: 0.85rem;
  color: #909399;
}
.tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 10px;
  font-size: 0.8rem;
}
.tag.region {
  background-color: #ecf5ff;
  color: #409EFF;
}
.tag.source {
  background-color: #f4f4f5;
  color: #909399;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
