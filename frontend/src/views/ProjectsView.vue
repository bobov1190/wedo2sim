<template>
  <div class="projects-page">
    <!-- Header -->
    <header class="header">
      <div class="logo">
        <span class="logo-dot"></span>
        WeDo 2.0 Studio
      </div>
      <button class="primary" @click="createProject">+ Новый проект</button>
    </header>

    <!-- Content -->
    <main class="content">
      <div v-if="loading" class="loading">Загрузка...</div>

      <div v-else-if="projects.length === 0" class="empty">
        <div class="empty-icon">📦</div>
        <p>Нет проектов. Создай первый!</p>
        <button class="primary" @click="createProject">Создать проект</button>
      </div>

      <div v-else class="grid">
        <div
          v-for="p in projects"
          :key="p.id"
          class="card"
          @click="openProject(p)"
        >
          <div class="card-thumb">
            <img v-if="p.thumbnail" :src="p.thumbnail" alt="" />
            <div v-else class="card-thumb-placeholder">
              <span>🤖</span>
            </div>
          </div>
          <div class="card-body">
            <div class="card-name">{{ p.name }}</div>
            <div class="card-meta">
              {{ p.piece_count }} деталей · {{ formatDate(p.updated_at) }}
            </div>
            <div class="card-actions" @click.stop>
              <button class="sm" @click="openCode(p)">Код</button>
              <button class="sm" @click="openSim(p)">Симулятор</button>
              <button class="sm danger" @click="deleteProject(p)">✕</button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Toast -->
    <div v-if="toast" :class="['toast', toast.type]">{{ toast.msg }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const projects = ref([])
const loading = ref(true)
const toast = ref(null)

function showToast(msg, type = 'success') {
  toast.value = { msg, type }
  setTimeout(() => toast.value = null, 2500)
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

async function loadProjects() {
  loading.value = true
  try {
    const res = await fetch('/api/projects')
    projects.value = await res.json()
  } catch (e) {
    showToast('Ошибка загрузки', 'error')
  } finally {
    loading.value = false
  }
}

async function createProject() {
  try {
    const res = await fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Новый проект' })
    })
    const p = await res.json()
    router.push({ name: 'code', params: { id: p.id } })
  } catch (e) {
    showToast('Ошибка создания', 'error')
  }
}

function openProject(p) {
  router.push({ name: 'code', params: { id: p.id } })
}

function openCode(p) {
  router.push({ name: 'code', params: { id: p.id } })
}

function openSim(p) {
  router.push({ name: 'simulator', params: { id: p.id } })
}

async function deleteProject(p) {
  if (!confirm(`Удалить "${p.name}"?`)) return
  await fetch(`/api/projects/${p.id}`, { method: 'DELETE' })
  projects.value = projects.value.filter(x => x.id !== p.id)
  showToast('Удалено')
}

onMounted(loadProjects)
</script>

<style scoped>
.projects-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  border-bottom: 1px solid var(--border);
  background: var(--bg2);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
}

.logo-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  display: inline-block;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 24px;
}

.loading, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  height: 60vh;
  color: var(--text2);
}
.empty-icon { font-size: 48px; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color 0.15s, transform 0.1s;
}
.card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.card-thumb {
  height: 140px;
  background: var(--bg3);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.card-thumb img { width: 100%; height: 100%; object-fit: cover; }
.card-thumb-placeholder { font-size: 40px; }

.card-body {
  padding: 12px 14px;
}

.card-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  font-size: 12px;
  color: var(--text3);
  margin-bottom: 10px;
}

.card-actions {
  display: flex;
  gap: 6px;
}
</style>
