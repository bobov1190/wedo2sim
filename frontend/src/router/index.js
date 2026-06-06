import { createRouter, createWebHistory } from 'vue-router'
import ProjectsView from '../views/ProjectsView.vue'
import SimulatorView from '../views/SimulatorView.vue'
import CodeView from '../views/CodeView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'projects', component: ProjectsView },
    { path: '/sim/:id', name: 'simulator', component: SimulatorView },
    { path: '/code/:id', name: 'code', component: CodeView },
  ]
})
