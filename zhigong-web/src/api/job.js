import request from './request'

export const searchJobs = (params) => {
  // params: { major, degree, q, page, size, source }
  return request({
    url: '/jobs/search',
    method: 'get',
    params
  })
}

