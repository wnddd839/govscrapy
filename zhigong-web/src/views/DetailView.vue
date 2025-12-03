<template>
  <div class="detail-container" v-loading="loading">
    <div v-if="detail">
      <h1 class="title">{{ detail.title }}</h1>
      
      <div class="meta-info">
        <div class="meta-item">
          <a :href="detail.sourceUrl || detail.url" target="_blank" class="source-link">
            <el-icon><Link /></el-icon>
            查看原文
          </a>
        </div>
        <div class="meta-item">
          <span>发布日期：{{ formatDate(detail.publishDate || detail.publish_date) }}</span>
        </div>
        <div class="meta-item" v-if="detail.sourceOrg || detail.source_org">
          <span>来源：{{ detail.sourceOrg || detail.source_org }}</span>
        </div>
      </div>

      <div class="article-content">
        <div v-if="formattedContent" v-html="formattedContent" class="text-content"></div>
        <div v-else-if="detail.contentHtml || detail.content_html" v-html="detail.contentHtml || detail.content_html" class="html-content"></div>
        <el-empty v-else description="暂无正文内容" />
      </div>

      <!-- 附件区域 -->
      <div class="attachments-section" v-if="detail.attachments && detail.attachments.length > 0">
        <h3 class="attach-title">附件下载</h3>
        <ul class="attach-list">
          <li v-for="(file, index) in detail.attachments" :key="index" class="attach-item">
            <div class="file-info">
              <el-icon class="file-icon"><Document /></el-icon>
              <span class="file-name" :title="file.name">{{ file.name }}</span>
              <span class="file-size" v-if="file.size">{{ formatSize(file.size) }}</span>
            </div>
            <div class="file-actions">
              <el-button 
                v-if="canPreview(file)" 
                type="primary" 
                link 
                @click="handlePreview(file)"
              >
                预览PDF
              </el-button>
              <el-button 
                type="success" 
                link 
                @click="handleDownload(file)"
              >
                下载原附件
              </el-button>
            </div>
          </li>
        </ul>
      </div>
    </div>
    <el-empty v-else-if="!loading && !error" description="未找到相关信息" />
    <el-empty v-else-if="!loading && error" description="加载失败，请稍后再试">
      <el-button type="primary" @click="loadDetail">重试</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Link, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getInfoDetail, getFilePreviewUrl } from '../api/publicInfo'

const route = useRoute()
const detail = ref(null)
const loading = ref(false)
const error = ref(false)

// 将纯文本转换为带段落标签的 HTML
const formattedContent = computed(() => {
  if (!detail.value) return ''
  const text = detail.value.contentText || detail.value.content_text
  if (!text) return ''
  
  // 1. 将文本按换行符分割
  // 2. 过滤掉空行
  // 3. 将每一段包裹在 <p> 标签中，并添加缩进样式
  return text.split(/\n+/).map(p => p.trim()).filter(p => p).map(p => `<p>${p}</p>`).join('')
})

const loadDetail = async () => {
  const id = route.params.id
  if (!id) return
  
  // 优先从路由状态中获取数据
  if (history.state && history.state.item && String(history.state.item.id) === String(id)) {
    console.log('Using cached item from history state')
    detail.value = history.state.item
    return
  }
  
  loading.value = true
  error.value = false
  try {
    const res = await getInfoDetail(id)
    // 检测后端是否返回了错误的ID
    if (res && res.id && String(res.id) !== String(id)) {
        console.error(`Backend returned wrong ID: requested ${id}, got ${res.id}`)
    }
    detail.value = res
  } catch (err) {
    console.error('Failed to load detail', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${year}/${month}/${day}`
}

const formatSize = (bytes) => {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const canPreview = (file) => {
    return !!file.pdf_url || file.type === 'pdf' || !!file.pdf_path
}

const handlePreview = async (file) => {
    let url = file.pdf_url || file.pdf_path || (file.type === 'pdf' ? file.url : null)
    
    if (url && !url.startsWith('http')) {
        try {
            const res = await getFilePreviewUrl(url)
            url = typeof res === 'string' ? res : res.url
        } catch (e) {
            console.error('Failed to get preview url', e)
            ElMessage.warning('获取预览链接失败')
            return
        }
    }

    if (url) {
        window.open(url, '_blank')
    } else {
        ElMessage.warning('暂无预览链接')
    }
}

const handleDownload = (file) => {
    const downloadUrl = file.original_url || file.url
    if (downloadUrl) {
        window.open(downloadUrl, '_blank')
    } else {
        ElMessage.warning('暂无下载链接')
    }
}

onMounted(() => {
  loadDetail()
})
</script>

<style scoped>
.detail-container {
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  padding: 40px;
  border-radius: 8px;
  min-height: 600px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
.title {
  font-size: 2rem;
  color: #303133;
  margin-bottom: 20px;
  text-align: center;
}
.meta-info {
  display: flex;
  justify-content: center;
  gap: 30px;
  color: #909399;
  margin-bottom: 30px;
  flex-wrap: wrap;
}
.meta-item {
  display: flex;
  align-items: center;
}
.source-link {
  color: #409EFF;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
}
.article-content {
  font-size: 1.2rem;
  line-height: 2;
  color: #333;
  margin-bottom: 40px;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 30px;
  background-color: #fff;
}
:deep(.text-content p) {
  text-indent: 2em;
  margin-bottom: 1.5em;
  min-height: 1em;
}
.attachments-section {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}
.attach-title {
  font-size: 1.1rem;
  margin-bottom: 15px;
  color: #303133;
}
.attach-list {
  list-style: none;
  padding: 0;
}
.attach-item {
  display: flex;
  align-items: center;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 10px;
  justify-content: space-between;
}
.file-info {
    display: flex;
    align-items: center;
    gap: 10px;
}
.file-icon {
    font-size: 1.2rem;
    color: #909399;
}
.file-name {
    color: #606266;
}
.file-size {
    color: #909399;
    font-size: 0.9rem;
}
</style>
