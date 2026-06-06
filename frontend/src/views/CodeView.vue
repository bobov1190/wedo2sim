<script setup>
import { useRoute, useRouter } from 'vue-router'
import { onMounted } from 'vue'
const route = useRoute(), router = useRouter()
onMounted(() => router.replace({ name: 'simulator', params: { id: route.params.id } }))
</script>
<template><div></div></template>
