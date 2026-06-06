import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useProjectStore = defineStore('project', () => {
  const project = ref(null)
  const saveStatus = ref('saved') // 'saved' | 'saving' | 'error'
  let saveTimer = null

  async function loadProject(id) {
    const res = await fetch(`/api/projects/${id}`)
    if (!res.ok) throw new Error('Not found')
    project.value = await res.json()
  }

  async function saveProject(patch = {}) {
    if (!project.value) return
    saveStatus.value = 'saving'
    try {
      const body = {
        name: project.value.name,
        code_state: project.value.code_state,
        lego_state: project.value.lego_state,
        ...patch
      }
      const res = await fetch(`/api/projects/${project.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (!res.ok) throw new Error('Save failed')
      const updated = await res.json()
      project.value.updated_at = updated.updated_at
      saveStatus.value = 'saved'
    } catch (e) {
      saveStatus.value = 'error'
    }
  }

  function scheduleSave() {
    clearTimeout(saveTimer)
    saveStatus.value = 'saving'
    saveTimer = setTimeout(() => saveProject(), 2000)
  }

  function markDirty() {
    scheduleSave()
  }

  return { project, saveStatus, loadProject, saveProject, markDirty }
})
