<template>
  <el-menu mode="horizontal" router :default-active="$route.path" :ellipsis="false" class="navbar-menu">
    <el-menu-item index="/" class="logo-item">
      <span class="logo-text">知公</span>
    </el-menu-item>
    <div class="flex-grow" />
    <el-menu-item index="/" class="nav-item">首页</el-menu-item>
    <el-menu-item index="/list" class="nav-item">发现</el-menu-item>
  </el-menu>
</template>

<style scoped>
.navbar-menu {
  border-bottom: 1px solid #f0f2f7;
  padding: 0 20px;
  box-shadow: 0 1px 3px rgba(26,26,26,.1);
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
}

.flex-grow {
  flex-grow: 1;
}

.logo-item {
  background: transparent !important;
}

.logo-text {
  font-size: 1.8rem;
  font-weight: 800; /* 加粗 */
  color: #0066ff; /* 保持品牌蓝，但更深沉一点 */
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", "Microsoft YaHei", "Source Han Sans SC", "Noto Sans CJK SC", "WenQuanYi Micro Hei", sans-serif;
  letter-spacing: -0.5px;
}

.nav-item {
  font-size: 15px;
  color: #8590a6;
  font-weight: 500;
}

.nav-item.is-active {
  color: #121212 !important; /* 选中时变黑，而不是蓝 */
  font-weight: 600;
  border-bottom: 3px solid #0066ff !important;
}

.nav-item:hover {
  color: #175199 !important;
  background: transparent !important;
}
</style>
