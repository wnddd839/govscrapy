<template>
  <div class="detail-container" v-loading="isLoading">
    <el-breadcrumb separator="/" class="breadcrumb" v-if="detailData">
      <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item :to="{ path: '/category', query: { categoryTag: detailData.category_tag } }">
        {{ detailData.category_tag }}
      </el-breadcrumb-item>
      <el-breadcrumb-item>详情</el-breadcrumb-item>
    </el-breadcrumb>
    <!-- 占位符面包屑，防止布局跳动 -->
    <el-breadcrumb separator="/" class="breadcrumb" v-else>
      <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
      <el-breadcrumb-item>加载中...</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 详情内容 -->
    <div class="detail-content" v-if="!isLoading && detailData">
      <h1 class="detail-title">{{ detailData.title }}</h1>
      <div class="detail-meta">
        <span class="meta-item">
          <el-icon><el-icon-office-building /></el-icon>
          发布单位：{{ detailData.publish_dept || '未知' }}
        </span>
        <span class="meta-item">
          <el-icon><el-icon-clock /></el-icon>
          发布时间：{{ formatTime(detailData.publish_time) }}
        </span>
        <span class="meta-item">
          <el-icon><el-icon-link /></el-icon>
          来源网站：{{ detailData.source_website || '未知' }}
        </span>
        <el-button 
          type="primary" 
          link
          size="small"
          @click="openSourceUrl"
          class="source-url-btn"
        >
          查看原文
        </el-button>
      </div>
      <div class="detail-body">
        <div v-if="formattedContent" v-html="formattedContent" class="text-content"></div>
        <el-empty v-else description="暂无正文内容" />
      </div>

      <!-- 附件区域 -->
      <div class="attachments-section" v-if="detailData.attachments && detailData.attachments.length > 0">
        <h3 class="attach-title">附件下载</h3>
        <ul class="attach-list">
          <li v-for="(file, index) in detailData.attachments" :key="index" class="attach-item">
            <div class="file-info">
              <el-icon class="file-icon"><el-icon-document /></el-icon>
              <span class="file-name">{{ file.name || '未知文件名' }}</span>
              <span class="file-size" v-if="file.size">{{ formatSize(file.size) }}</span>
            </div>
            <div class="file-actions">
              <el-button 
                v-if="canPreview(file)"
                type="primary" 
                link 
                size="small" 
                @click="handlePreview(file)"
              >
                预览
              </el-button>
              <el-button 
                type="primary" 
                link 
                size="small" 
                @click="handleDownload(file)"
              >
                下载
              </el-button>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- 数据加载失败或不存在 -->
    <el-empty v-if="!isLoading && !detailData" description="未找到相关数据，请检查数据源配置" />

    <!-- 加载状态 - 已通过 v-loading 实现 -->

    <!-- 错误状态 -->
    <div v-if="!isLoading && (!detailData || Object.keys(detailData).length === 0)" class="error-state">
      <el-empty description="信息加载失败或暂无内容" />
      <el-button type="primary" @click="fetchDetailData">重试</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElBreadcrumb, ElBreadcrumbItem, ElButton, ElIcon, ElLoading, ElEmpty, ElMessage } from 'element-plus'
import { Link as ElIconLink, Document as ElIconDocument, OfficeBuilding as ElIconOfficeBuilding, Clock as ElIconClock } from '@element-plus/icons-vue'
import { publicInfoApi, getFilePreviewUrl } from '../api/publicInfo'
import { formatTime } from '../utils/date'

const route = useRoute()
const router = useRouter()
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

// 数据状态
const detailData = ref(null) // Initialize as null to distinguish from empty object
const isLoading = ref(true)
const dataId = ref(route.params.id || '')

// 将纯文本转换为带段落标签的 HTML
const formattedContent = computed(() => {
  if (!detailData.value) return ''
  // 尝试获取各种可能的内容字段
  const text = detailData.value.content_text || 
               detailData.value.contentText || 
               detailData.value.content || 
               detailData.value.body ||
               detailData.value.text ||
               detailData.value.summary // Fallback to summary if content is missing
               
  if (!text) return ''
  
  // 如果内容包含 HTML 标签，则直接返回（认为是 HTML）
  if (/<[a-z][\s\S]*>/i.test(text)) {
    return text
  }
  
  // 1. 将文本按换行符分割
  // 2. 过滤掉空行
  // 3. 将每一段包裹在 <p> 标签中，并添加缩进样式
  return text.split(/\n+/).map(p => p.trim()).filter(p => p).map(p => `<p>${p}</p>`).join('')
})

// 页面挂载时加载详情
onMounted(() => {
  fetchDetailData()
})

// 获取详情数据
const fetchDetailData = async () => {
  if (!dataId.value) return
  
  isLoading.value = true
  detailData.value = null
  try {
    const source = route.query.source
    const res = await publicInfoApi.getDetail(dataId.value, source)
    if (res && Object.keys(res).length > 0) {
      detailData.value = res
    } else {
      detailData.value = null
    }
  } catch (error) {
    console.error('获取详情数据失败：', error)
    detailData.value = null
  } finally {
    isLoading.value = false
  }
}

// 打开来源原文链接
const openSourceUrl = () => {
  if (detailData.value.source_url) {
    window.open(detailData.value.source_url, '_blank')
  } else {
    ElMessage.warning('暂无原文链接')
  }
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
    let downloadUrl = file.original_url || file.url
    
    if (downloadUrl) {
        // Handle relative URLs
        if (!downloadUrl.startsWith('http')) {
             // If it starts with /, prepend origin
             if (downloadUrl.startsWith('/')) {
                 downloadUrl = window.location.origin + downloadUrl
             } else {
                 // Otherwise assume it's relative to current path or API base, 
                 // but for safety let's assume it needs a leading slash and origin
                 downloadUrl = window.location.origin + '/' + downloadUrl
             }
        }
        window.open(downloadUrl, '_blank')
    } else {
        ElMessage.warning('暂无下载链接')
    }
}
</script>

<style scoped>
.detail-container {
  max-width: 900px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.95);
  padding: 40px;
  border-radius: 12px;
  min-height: 600px;
  box-shadow: 0 4px 15px rgba(255, 192, 203, 0.15);
}
.detail-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: #303133;
  margin: 10px 0 20px;
  text-align: center;
  line-height: 1.4;
}

.detail-meta {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  color: #909399;
  font-size: 0.9rem;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 192, 203, 0.3);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
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
.text-content {
  font-size: 1.1rem;
  line-height: 1.8;
  color: #333;
  margin-bottom: 40px;
  padding: 10px;
}
:deep(.text-content p) {
  text-indent: 2em;
  margin-bottom: 1.5em;
  min-height: 1em;
}
:deep(.text-content img) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 10px auto;
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
  padding: 12px;
  background-color: #fff0f5; /* Light pink background */
  border: 1px solid rgba(255, 192, 203, 0.5);
  border-radius: 6px;
  margin-bottom: 10px;
  justify-content: space-between;
  transition: all 0.3s ease;
}
.attach-item:hover {
  background-color: #ff69b4;
  border-color: #ff1493;
}
.attach-item:hover .file-name,
.attach-item:hover .file-size,
.attach-item:hover .file-icon {
  color: white;
}
.file-info {
    display: flex;
    align-items: center;
    gap: 10px;
}
.file-icon {
  font-size: 1.2rem;
  color: #ff69b4;
}
.file-name {
  color: #606266;
  font-weight: 500;
}
.file-size {
    color: #909399;
    font-size: 0.9rem;
}
</style>
