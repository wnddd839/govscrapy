/**
 * 格式化时间：YYYY-MM-DD
 * 支持直接调用 formatTime(timeStr)
 * 也支持 Element Plus formatter: formatTime(row, column, cellValue)
 */
export const formatTime = (arg1, arg2, arg3) => {
  let val = arg1
  
  // 判断是否为 Element Plus formatter 调用 (row, column, cellValue)
  // arg2 是 column 对象 (有 property 属性)
  if (arg2 && typeof arg2 === 'object' && arg2.property) {
    val = arg3
  }
  
  if (!val) return ''
  
  try {
    const date = new Date(val)
    // 如果是无效日期，尝试简单的字符串处理
    if (isNaN(date.getTime())) {
      const str = String(val)
      return str.split('T')[0].split(' ')[0]
    }
    
    const year = date.getFullYear()
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    return `${year}-${month}-${day}`
  } catch (e) {
    console.warn('Date format error:', e)
    return val
  }
}

/**
 * 格式化完整时间：YYYY-MM-DD HH:mm:ss
 */
export const formatFullTime = (val) => {
  if (!val) return ''
  
  try {
    const date = new Date(val)
    if (isNaN(date.getTime())) {
      return String(val).replace('T', ' ')
    }
    
    const year = date.getFullYear()
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    const seconds = date.getSeconds().toString().padStart(2, '0')
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  } catch (e) {
    return val
  }
}
