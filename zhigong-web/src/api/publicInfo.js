import request from './request'

export function getHotInfo(region) {
  return request({
    url: '/public-info/hot',
    method: 'get',
    params: { region }
  })
}

export function getInfoList(params) {
  // params: { q, region, startDate, endDate, page, size }
  return request({
    url: '/public-info/list',
    method: 'get',
    params
  })
}

export function getInfoDetail(id) {
  return request({
    url: `/public-info/detail/${id}`,
    method: 'get'
  })
}

// Assuming the backend returns a string URL or an object containing the URL
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
