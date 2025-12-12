<template>
  <div class="category-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>{{ currentCategory }}</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title">{{ currentCategory }} - 政务信息列表</h1>
    </div>

    <!-- 筛选区域 -->
    <div class="search-filter-section">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input v-model="searchForm.q" placeholder="搜索标题/内容" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="地区">
          <el-input v-model="searchForm.region" placeholder="请输入地区" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :loading="isLoading">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 筛选与分页控制 -->
    <div class="filter-pagination">
      <div class="filter-group">
        <el-select 
          v-model="pageSize" 
          placeholder="每页条数" 
          size="small"
          @change="fetchCategoryData"
        >
          <el-option label="10条/页" :value="10"></el-option>
          <el-option label="20条/页" :value="20"></el-option>
          <el-option label="50条/页" :value="50"></el-option>
        </el-select>
      </div>
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[10, 20, 50]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        small
      />
    </div>

    <!-- 分类数据列表 -->
    <el-table
      :data="categoryDataList"
      border
      stripe
      :loading="isLoading"
      class="category-table"
      @row-click="goToDetail"
    >
      <el-table-column
        label="标题"
        prop="title"
        min-width="400"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="发布单位"
        prop="publish_dept"
        width="180"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="发布时间"
        prop="publish_time"
        width="180"
        :formatter="formatTime"
      />
      <el-table-column
        label="操作"
        width="100"
        fixed="right"
      >
        <template #default="scope">
          <el-button 
            type="text" 
            size="small"
            @click.stop="goToDetail(scope.row)"
          >
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 空状态 -->
    <div v-if="categoryDataList.length === 0 && !isLoading" class="empty-state">
      <el-empty description="暂无该分类下的政务信息" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ElTable, ElTableColumn, ElPagination, ElBreadcrumb, ElBreadcrumbItem, 
  ElSelect, ElOption, ElButton, ElEmpty, ElForm, ElFormItem, ElInput, ElDatePicker 
} from 'element-plus'
import { publicInfoApi } from '../api/publicInfo'
import { formatTime } from '../utils/date'

const route = useRoute()
const router = useRouter()

// 分类标签（从路由参数获取）
const currentCategory = ref(route.params.name || '政务信息')
// 分页参数
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
// 数据状态
const allCategoryData = ref([]) // 所有加载的数据（用于前端排序和搜索）
const categoryDataList = ref([]) // 当前页显示的数据
const isLoading = ref(true)

// 搜索参数
const searchForm = ref({
  q: '',
  region: '',
  dateRange: []
})

// 处理本地数据：排序、搜索、分页
const processLocalData = () => {
  let processed = [...allCategoryData.value]
  
  // 1. 本地搜索（关键词匹配标题）
  if (searchForm.value.q) {
    const keyword = searchForm.value.q.toLowerCase()
    processed = processed.filter(item => 
      (item.title && item.title.toLowerCase().includes(keyword)) ||
      (item.content && item.content.toLowerCase().includes(keyword))
    )
  }
  
  // 2. 本地排序（按发布时间倒序）
  processed.sort((a, b) => {
    const timeA = new Date(a.publish_time || 0).getTime()
    const timeB = new Date(b.publish_time || 0).getTime()
    return timeB - timeA // 倒序
  })
  
  // 更新总数
  total.value = processed.length
  
  // 3. 本地分页
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  categoryDataList.value = processed.slice(start, end)
}

// 获取分类数据
const fetchCategoryData = async () => {
  isLoading.value = true
  try {
    const backendCategoryTag = currentCategory.value
    console.log(`Frontend Category: ${currentCategory.value}, Backend Tag: ${backendCategoryTag}`)

    // 一次性获取大量数据用于前端处理
    const params = {
      categoryTag: backendCategoryTag, 
      source: 'mysql', 
      page: 1, 
      size: 1000, // 获取足够多的数据
      // 不传搜索参数给后端，改为前端过滤
      q: '',
      region: '' 
    }

    const res = await publicInfoApi.getCategoryData(params)
    allCategoryData.value = res.list || []
    
    // 处理数据
    processLocalData()
    
  } catch (error) {
    console.error('获取分类数据失败：', error)
    allCategoryData.value = []
    categoryDataList.value = []
    total.value = 0
  } finally {
    isLoading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  processLocalData() // 仅触发本地处理
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1 // 重置到第一页
  processLocalData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  processLocalData()
}

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    q: '',
    region: '',
    dateRange: []
  }
  handleSearch()
}

// 监听路由参数变化（支持切换分类）
watch(
  () => route.params.name,
  (newVal) => {
    if (newVal) {
      currentCategory.value = newVal
      // 切换分类重置页码和搜索
      currentPage.value = 1 
      searchForm.value = {
        q: '',
        region: '',
        dateRange: []
      }
      fetchCategoryData()
    }
  },
  { immediate: true }
)

// 跳转到详情页
const goToDetail = (row) => {
  router.push({
    name: 'detail',
    params: { id: row.data_id || row.dataId },
    query: { source: 'mysql' }
  })
}
</script>

<style scoped>
.category-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(255, 192, 203, 0.15);
  min-height: 600px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-top: 15px;
  margin-bottom: 0;
}

.search-filter-section {
  background: #fff0f5; /* 浅粉色背景 */
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 192, 203, 0.3);
}

.filter-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 10px 0;
}

.filter-group {
  display: flex;
  gap: 16px;
}

.category-table {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

/* 表格行悬停效果 */
:deep(.el-table__row:hover) {
  background-color: #fff0f5 !important; /* 粉色悬停 */
}
</style>
