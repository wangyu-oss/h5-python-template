<template>
  <el-result icon="warning" title="403" sub-title="没有权限访问这个页面">
    <template #extra><el-button type="primary" @click="$router.push('/dashboard')">返回概览</el-button></template>
  </el-result>
</template>
