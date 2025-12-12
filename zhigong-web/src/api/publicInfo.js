import request from './request'

// Field Adapter: Maps backend camelCase fields to frontend snake_case fields
const adaptPublicInfo = (item) => {
  if (!item) return {}
  
  // DEBUG: Log raw item to check attachment fields
  console.log('adaptPublicInfo raw item:', item)

  // Try to find attachment list from various possible fields
  let attachments = item.attachments || item.attachmentList || item.files || item.fileList || item.enclosures || item.appendix || item.attachment || []
  
  // If it's a string, try to parse it
  if (typeof attachments === 'string') {
    try {
      attachments = JSON.parse(attachments)
    } catch (e) {
      console.error('Failed to parse attachments string:', e)
      attachments = []
    }
  }
  
  // Ensure it's an array
   if (!Array.isArray(attachments)) {
     if (attachments && typeof attachments === 'object') {
        // Handle single object case
        console.log('Attachments is a single object, wrapping in array', attachments)
        attachments = [attachments]
     } else {
        console.warn('Attachments is not an array or object after processing:', attachments)
        attachments = []
     }
   } else {
     console.log('Found attachments:', attachments)
   }

  // Normalize attachment objects
  attachments = attachments.map(file => {
    if (typeof file === 'string') {
      const fileName = file.split('/').pop() || '未知附件'
      const fileType = fileName.split('.').pop()?.toLowerCase() || ''
      return {
        name: fileName,
        url: file,
        type: fileType,
        size: 0
      }
    }
    
    // Normalize object fields
    return {
      ...file,
      name: file.name || file.fileName || file.title || '未知附件',
      url: file.url || file.path || file.filePath || file.downloadUrl || file.fileUrl || '',
      size: file.size || file.fileSize || 0,
      type: file.type || file.fileType || (file.url || file.path || '').split('.').pop()?.toLowerCase() || ''
    }
  })

  return {
    ...item,
    dataId: item.dataId || item.id,
    title: item.title || item.name || '',
    publish_dept: item.sourceOrg || item.sourceWebsite || item.publish_dept || '',
    publish_time: item.publishTime || item.publish_time || '',
    category_tag: item.category || item.categoryTag || item.category_tag || '',
    summary: item.contentText || item.summary || '',
    source_website: item.sourceWebsite || item.source_website || '',
    source_url: item.sourceUrl || item.source_url || '',
    content: item.contentText || item.content || '',
    content_text: item.contentText || item.content_text || '',
    attachments: attachments
  }
}

// 政务信息核心API
export const publicInfoApi = {
  // 1. 获取所有分类标签
  // Old: /gov/category/list -> New: /public-info/category/list
  getCategoryList: () => request({
    url: '/public-info/category/list',
    method: 'get'
  }),
  
  // 2. 获取热门数据
  // Old: /public-info/hot -> New: /public-info/hot/list
  // No need for source=redis param
  getHotList: async () => {
    const res = await request({
      url: '/public-info/hot/list',
      method: 'get'
    })
    // Map response list
    if (Array.isArray(res)) {
      return res.map(adaptPublicInfo)
    }
    return res
  },
  
  // 3. 获取分类数据（分页）
  // Old: /public-info/list -> New: /public-info/category/data
  // Param: category -> categoryTag
  getCategoryData: async (params) => {
    // Transform params
    const apiParams = {
      ...params,
      categoryTag: params.category || params.categoryTag
    }
    delete apiParams.category // Remove old param if exists

    // Filter out empty params (fix for backend treating empty strings as strict filters)
    Object.keys(apiParams).forEach(key => {
      if (apiParams[key] === '' || apiParams[key] === null || apiParams[key] === undefined) {
        delete apiParams[key]
      }
    })

    const res = await request({
      url: '/public-info/category/data',
      method: 'get',
      params: apiParams
    })
    
    // Normalize response to { list, total } structure for UI components
    let list = []
    let total = 0

    if (Array.isArray(res)) {
      list = res.map(adaptPublicInfo)
      total = list.length
    } else if (res) {
      // Handle various pagination structures
      const rawList = res.content || res.records || res.list || res.data || []
      list = Array.isArray(rawList) ? rawList.map(adaptPublicInfo) : []
      total = res.totalElements || res.total || res.totalRow || list.length
    }
    
    return { list, total }
  },
  
  // 4. 获取信息详情
  // Old: /gov/detail -> New: /public-info/detail/data/{dataId}
  getDetail: async (dataId, source) => {
    const params = source ? { source } : {}
    const res = await request({
      url: `/public-info/detail/data/${dataId}`,
      method: 'get',
      params
    })
    return adaptPublicInfo(res)
  }
}

// 兼容旧代码 helper functions
export function getHotInfo(region) {
  return publicInfoApi.getHotList()
}

export function getInfoList(params) {
  const newParams = {
    q: params.q,
    categoryTag: params.category || params.categoryTag,
    region: params.region,
    page: params.page !== undefined ? params.page : 0,
    size: params.size || 20,
    startDate: params.startDate,
    endDate: params.endDate
  }
  return publicInfoApi.getCategoryData(newParams)
}

export function getInfoDetail(id) {
  return publicInfoApi.getDetail(id)
}

export function getFilePreviewUrl(objectName) {
  return request({
    url: `/file/preview/${objectName}`,
    method: 'get'
  })
}

export function getHealthCheck() {
  return request({
    url: '/_health/db',
    method: 'get'
  })
}

export default publicInfoApi
