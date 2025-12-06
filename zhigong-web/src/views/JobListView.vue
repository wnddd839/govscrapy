<template>
  <div class="jobs-container">
    <div class="filter-bar">
      <el-form :inline="true" class="search-form">
        <el-form-item label="专业">
          <el-input v-model="major" placeholder="请输入您的专业，如：会计、计算机" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="学历">
          <el-select v-model="degree" placeholder="不限" clearable style="width: 140px">
            <el-option v-for="d in degreeOptions" :key="d" :label="d" :value="d" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="q" placeholder="岗位或单位关键词" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">搜索</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="result-list" v-loading="loading">
      <el-empty v-if="!loading && total === 0" description="未找到相关岗位，尝试简化专业名称，例如搜‘计算机’而不是‘计算机应用技术’" />

      <div class="card-grid">
        <el-card v-for="item in list" :key="item.id" class="job-card" shadow="hover">
          <div class="job-header">
            <div class="job-title">{{ item.jobName }}</div>
            <el-tag type="success">招{{ item.count }}人</el-tag>
          </div>
          <div class="job-dept">{{ item.department }}</div>
          <div class="job-reqs">
            <el-tag type="info" effect="plain" class="req-tag">专业：{{ item.majorReq }}</el-tag>
            <el-tag type="warning" effect="plain" class="req-tag">学历：{{ item.degreeReq }}</el-tag>
            <span v-if="item.otherReq" class="other-req">{{ item.otherReq }}</span>
          </div>
          <div class="job-actions">
            <el-button type="primary" @click="viewDetail(item)">查看公告</el-button>
          </div>
        </el-card>
      </div>
    </div>

    <div class="pagination-container" v-if="total > 0">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
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
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { searchJobs } from '../api/job'

const router = useRouter()
const route = useRoute()

const major = ref('')
const degree = ref('')
const q = ref('')
const page = ref(1)
const size = ref(20)
const total = ref(0)
const list = ref([])
const loading = ref(false)

const degreeOptions = ['不限', '大专', '本科', '硕士', '博士']

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      major: major.value || undefined,
      degree: degree.value && degree.value !== '不限' ? degree.value : undefined,
      q: q.value || undefined,
      page: page.value - 1,
      size: size.value,
      source: 'mysql' // 指定走MySQL数据源
    }
    const res = await searchJobs(params)
    const data = res && res.data ? res : { data: res, total: 0, page: 0, size: size.value }
    list.value = data.data || []
    total.value = data.total || 0
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  page.value = 1
  fetchData()
}

const handleSizeChange = () => {
  page.value = 1
  fetchData()
}

const handleCurrentChange = () => {
  fetchData()
}

const viewDetail = (item) => {
  router.push({
    name: 'detail',
    params: { id: item.sourceInfoId },
    state: { item: { id: item.sourceInfoId } }
  })
}

onMounted(() => {
  if (route.query.major) major.value = route.query.major
  if (route.query.degree) degree.value = route.query.degree
  if (route.query.q) q.value = route.query.q
  fetchData()
})
</script>

<style scoped>
.jobs-container {
  max-width: 1100px;
  margin: 0 auto;
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  min-height: 500px;
}
.filter-bar {
  margin-bottom: 20px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}
.search-form :deep(.el-input) {
  width: 360px;
}
.search-form :deep(.el-input__wrapper) {
  transition: none;
  box-shadow: none;
}
.result-list {
  margin-top: 10px;
}
.card-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.job-card {
  min-height: 140px;
}
.job-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.job-title {
  font-size: 18px;
  font-weight: 600;
}
.job-dept {
  margin-top: 6px;
  color: #909399;
  font-size: 14px;
}
.job-reqs {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.req-tag {
  background-color: #ecf5ff;
}
.other-req {
  color: #606266;
}
.job-actions {
  margin-top: 12px;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>

