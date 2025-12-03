<template>
  <NavBar />
  <router-view class="main-content" />
</template>

<script setup>
import NavBar from './components/NavBar.vue'
</script>

<style>
body {
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}
.main-content {
  min-height: calc(100vh - 60px);
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
