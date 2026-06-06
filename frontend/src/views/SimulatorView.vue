<template>
  <div class="ws">

    <!-- HEADER -->
    <header class="ws-hdr">
      <button class="back-btn" @click="router.push({name:'projects'})">← Назад</button>
      <input v-model="pname" class="pname" @blur="saveName" />
      <div class="save-pill" :class="store.saveStatus">
        <span class="sdot"></span>{{ slabel }}
      </div>
      <div class="hbts">
        <template v-if="mode==='code'">
          <button class="btn-run" :disabled="running" @click="runCode">▶ Запустить</button>
          <button class="btn-stop" :disabled="!running" @click="stopCode">■ Стоп</button>
        </template>
        <button class="btn-icon" @click="mode==='code'?clearCanvas():clearBuilder()">✕</button>
        <button class="btn-icon" @click="saveNow">💾</button>
      </div>
      <div v-if="mode==='code'" class="mbadge" :class="{on:motorOn}">
        <span v-if="motorOn" class="mpulse"></span>
        Мотор {{ motorOn ? motorPow+'%' : 'СТОП' }}
      </div>
    </header>

    <!-- MODE NAV -->
    <div class="mode-nav">
      <button class="panel-toggle" @click="panelOpen=!panelOpen">
        {{ panelOpen ? '◀' : '▶' }}
      </button>
      <div class="mode-tabs">
        <button :class="['mode-tab',{active:mode==='code'}]" @click="mode='code'">
          <span class="mt-pip" style="background:#ef4444"></span>Код
        </button>
        <button :class="['mode-tab',{active:mode==='build'}]" @click="mode='build'">
          <span class="mt-pip" style="background:#3b82f6"></span>Конструктор
        </button>
      </div>
      <div class="mode-extras">
        <template v-if="mode==='code'">
          <span class="ct-info">{{ totalBlocks }} блоков</span>
          <button class="ct-btn" @click="zoom=Math.min(2,+(zoom+0.1).toFixed(1))">＋</button>
          <button class="ct-btn" @click="zoom=Math.max(0.3,+(zoom-0.1).toFixed(1))">－</button>
          <button class="ct-btn" @click="zoom=1;panX=0;panY=0">↺</button>
        </template>
        <template v-else>
          <span class="ct-info">{{ legoCount }} дет.</span>
          <button class="ct-btn" @click="rotateSel" title="R — повернуть">↻</button>
          <button class="ct-btn" @click="delSelPiece" style="color:#ef4444" title="Del — удалить">✕</button>
        </template>
      </div>
    </div>

    <!-- BODY -->
    <div class="ws-body">

      <!-- LEFT PANEL -->
      <aside v-show="panelOpen" class="ws-panel">

        <!-- CODE PALETTE -->
        <template v-if="mode==='code'">
          <div class="cats">
            <button v-for="cat in categories" :key="cat.id"
              :class="['cat-btn',{active:activeCat===cat.id}]"
              :style="activeCat===cat.id?{background:cat.color+'22',borderLeft:'3px solid '+cat.color}:{borderLeft:'3px solid transparent'}"
              @click="activeCat=cat.id">
              {{ cat.icon }} {{ cat.name }}
            </button>
          </div>
          <div class="blocks-list">
            <div v-for="blk in currentCatBlocks" :key="blk.type"
              class="palette-block"
              :style="{background:blk.color}"
              draggable="true"
              @dragstart="onPaletteDragStart($event,blk)"
              @click="addBlockToCanvas(blk)">
              <span class="pb-ico">{{ blk.icon }}</span>
              {{ blk.label }}
              <span class="pb-add">+</span>
            </div>
          </div>
        </template>

        <!-- BUILD PALETTE -->
        <template v-else>
          <div class="cats">
            <button v-for="cat in legoCats" :key="cat.id"
              :class="['cat-btn',{active:activeLegoCat===cat.id}]"
              @click="activeLegoCat=cat.id">
              {{ cat.icon }} {{ cat.name }}
            </button>
          </div>
          <div class="parts-list">
            <div v-for="part in currentLegoParts" :key="part.type"
              :class="['palette-part', {active: placingType===part.type}]"
              @click="setPlacing(placingType===part.type ? null : part.type)">
              <span class="p-icon">{{ part.icon }}</span>
              <div>
                <div class="pp-lbl">{{ part.label }}</div>
                <div class="pp-sub">{{ part.sub }}</div>
              </div>
            </div>
          </div>
        </template>

      </aside>

      <!-- MAIN -->
      <main class="ws-main">

        <!-- CODE CANVAS -->
        <div v-if="mode==='code'" ref="canvasRef" class="code-canvas"
          @dragover.prevent
          @drop="onCanvasDrop"
          @mousedown="onCanvasMousedown"
          @wheel.prevent="onWheel">
          <div class="cc-inner" :style="{transform:`translate(${panX}px,${panY}px) scale(${zoom})`}">
            <div v-for="chain in chains" :key="chain.id"
              class="block-chain"
              :style="{left:chain.x+'px',top:chain.y+'px'}"
              @mousedown.stop="startChainDrag($event,chain)">

              <div v-for="(blk,bi) in chain.blocks" :key="blk.id"
                class="prog-block"
                :class="{running:runStep===blk.id}"
                :style="{background:getBlkDef(blk.type).color}">
                <div class="blk-hdr">
                  <span class="blk-ico">{{ getBlkDef(blk.type).icon }}</span>
                  <span class="blk-lbl">{{ getBlkDef(blk.type).label }}</span>
                  <button class="blk-del" @click.stop="removeBlock(chain.id,bi)">✕</button>
                </div>
                <div v-if="getBlkDef(blk.type).params" class="blk-params">
                  <div v-for="p in getBlkDef(blk.type).params" :key="p.key" class="blk-param">
                    <label>{{ p.label }}</label>
                    <input v-if="p.type==='number'" type="number" v-model.number="blk.params[p.key]"
                      :min="p.min" :max="p.max" :step="p.step||1" />
                    <select v-else-if="p.type==='select'" v-model="blk.params[p.key]">
                      <option v-for="o in p.options" :key="o.v" :value="o.v">{{ o.l }}</option>
                    </select>
                    <input v-else v-model="blk.params[p.key]" />
                  </div>
                </div>
              </div>

              <div class="chain-drop"
                @dragover.prevent
                @drop.stop="onChainDrop($event,chain.id)">+ блок</div>
            </div>
          </div>
          <div v-if="chains.length===0" class="canvas-hint">Перетащи или нажми блок</div>
        </div>

        <!-- LEGO 3D CANVAS -->
        <div v-else ref="legoRef" class="lego-wrap">
          <canvas ref="threeCanvas" class="three-canvas"></canvas>
          <div v-if="placingType" class="placing-banner">
            ✚ Ставим: {{ PDEF[placingType]?.label }}
            <span class="hint-esc">[ESC — отмена] [R — повернуть]</span>
          </div>
          <div v-if="legoCount===0 && !placingType" class="lego-hint">
            Выбери деталь в палитре → кликни на сцену
          </div>
          <div class="controls-hint-3d">
            <span><span class="key3d">ПКМ</span> орбита</span>
            <span><span class="key3d">СКМ</span> пан</span>
            <span><span class="key3d">↕</span> зум</span>
            <span><span class="key3d">R</span> повернуть</span>
            <span><span class="key3d">Del</span> удалить</span>
          </div>
        </div>

      </main>

      <!-- RIGHT SIM PANEL (code mode only) -->
      <aside v-if="mode==='code'" class="ws-sim">
        <div class="sim-section">
          <div class="sim-title">МОТОР А</div>
          <div class="sim-row">
            <button :class="['sim-btn',{active:motorOn&&motorDir==='fwd'}]" @click="simMotorFwd">▶ Вперёд</button>
            <button :class="['sim-btn',{active:motorOn&&motorDir==='bwd'}]" @click="simMotorBwd">◀ Назад</button>
          </div>
          <div class="sim-row">
            <input type="range" min="0" max="100" v-model.number="motorPow" class="sim-slider" />
            <span class="sim-val">{{ motorPow }}%</span>
          </div>
        </div>
        <div class="sim-section">
          <div class="sim-title">ДИСПЛЕЙ</div>
          <div class="sim-display" :style="{color:displayColor}">{{ displayText||'[ ]' }}</div>
          <div class="sim-row"><span class="sim-lbl">Цвет</span><span :style="{color:displayColor}">{{ displayColor }}</span></div>
          <div class="sim-row"><span class="sim-lbl">Текст</span><span>{{ displayText||'—' }}</span></div>
        </div>
        <div class="sim-section">
          <div class="sim-title">СЕНСОРЫ</div>
          <div class="sim-row">
            <span class="ss-dot" :class="{active:motionDetected}"></span>
            <button class="sim-btn sm" @click="triggerMotion">Движение</button>
          </div>
          <div class="sim-row">
            <span class="sim-lbl">Наклон</span>
            <select v-model="tiltDir" class="sim-select">
              <option value="none">Нет</option>
              <option value="forward">Вперёд</option>
              <option value="backward">Назад</option>
              <option value="left">Влево</option>
              <option value="right">Вправо</option>
            </select>
          </div>
          <div class="sim-row">
            <span class="sim-lbl">Дистанция</span>
            <input type="number" v-model.number="distance" min="0" max="300" class="sim-num" />
          </div>
          <div class="sim-row">
            <span class="sim-lbl">Яркость</span>
            <input type="number" v-model.number="lightLevel" min="0" max="100" class="sim-num" />
          </div>
        </div>
        <div class="sim-section sim-log-sec">
          <div class="sim-title">ЛОГ</div>
          <div class="sim-log" ref="logRef">
            <div v-for="(m,i) in log" :key="i" class="log-line">{{ m }}</div>
          </div>
          <button class="ct-btn" style="margin-top:4px;width:100%" @click="log=[]">Очистить</button>
        </div>
      </aside>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '../stores/project'
import * as THREE from 'three'

const route = useRoute()
const router = useRouter()
const store = useProjectStore()

// ── UI state ───────────────────────────────────────────────
const mode = ref('code')
const panelOpen = ref(true)
const pname = ref('')
const running = ref(false)
const runStep = ref(null)
let stopFlag = false

const slabel = computed(() => ({
  saved:'✓ Сохранено', saving:'⌛ Сохранение...', error:'✕ Ошибка'
}[store.saveStatus] || ''))

function saveName() { if (!store.project) return; store.project.name = pname.value; store.markDirty() }
function saveNow() { store.saveProject() }

// ── Block definitions ──────────────────────────────────────
const blockDefs = [
  { type:'start',      cat:'ctrl',   color:'#16a34a', icon:'🚀', label:'Старт',              params:null },
  { type:'when_btn',   cat:'ctrl',   color:'#15803d', icon:'🔘', label:'При нажатии кнопки', params:null },
  { type:'wait',       cat:'ctrl',   color:'#f97316', icon:'⏳', label:'Ждать',              params:[{key:'sec',label:'сек',type:'number',min:0,max:60,step:0.1}] },
  { type:'repeat',     cat:'ctrl',   color:'#ea580c', icon:'🔁', label:'Повторить',          params:[{key:'n',label:'раз',type:'number',min:1,max:100}] },
  { type:'forever',    cat:'ctrl',   color:'#c2410c', icon:'♾',  label:'Всегда',             params:null },
  { type:'stop',       cat:'ctrl',   color:'#ef4444', icon:'🛑', label:'Стоп программу',     params:null },
  { type:'if_motion',  cat:'ctrl',   color:'#b45309', icon:'👁', label:'Если движение',      params:null },
  { type:'if_tilt',    cat:'ctrl',   color:'#92400e', icon:'📐', label:'Если наклон',        params:[{key:'dir',label:'Направ.',type:'select',options:[{v:'any',l:'Любой'},{v:'forward',l:'Вперёд'},{v:'backward',l:'Назад'},{v:'left',l:'Влево'},{v:'right',l:'Вправо'}]}] },
  { type:'if_dist',    cat:'ctrl',   color:'#78350f', icon:'📏', label:'Если дистанция <',   params:[{key:'val',label:'см',type:'number',min:0,max:300}] },
  { type:'set_var',    cat:'ctrl',   color:'#713f12', icon:'📦', label:'Установить перем.',  params:[{key:'name',label:'Имя',type:'text'},{key:'val',label:'Значение',type:'number',min:-9999,max:9999}] },
  { type:'change_var', cat:'ctrl',   color:'#57534e', icon:'📈', label:'Изменить перем.',    params:[{key:'name',label:'Имя',type:'text'},{key:'delta',label:'На',type:'number',min:-9999,max:9999}] },
  { type:'motor_on',   cat:'motorA', color:'#dc2626', icon:'⚡', label:'Мотор Вкл',          params:[{key:'pow',label:'Мощн %',type:'number',min:0,max:100},{key:'dir',label:'Напр.',type:'select',options:[{v:'fwd',l:'▶ Вперёд'},{v:'bwd',l:'◀ Назад'}]}] },
  { type:'motor_off',  cat:'motorA', color:'#991b1b', icon:'⛔', label:'Мотор Выкл',         params:null },
  { type:'motor_time', cat:'motorA', color:'#b91c1c', icon:'⚡', label:'Мотор на сек',       params:[{key:'pow',label:'Мощн %',type:'number',min:0,max:100},{key:'dir',label:'Напр.',type:'select',options:[{v:'fwd',l:'▶ Вперёд'},{v:'bwd',l:'◀ Назад'}]},{key:'sec',label:'сек',type:'number',min:0,max:60,step:0.1}] },
  { type:'motor_rot',  cat:'motorA', color:'#7f1d1d', icon:'🔄', label:'Мотор оборотов',     params:[{key:'rot',label:'Об.',type:'number',min:0,max:100},{key:'dir',label:'Напр.',type:'select',options:[{v:'fwd',l:'▶ Вперёд'},{v:'bwd',l:'◀ Назад'}]}] },
  { type:'motor_pow',  cat:'motorA', color:'#881337', icon:'🎚', label:'Установить мощность',params:[{key:'pow',label:'%',type:'number',min:0,max:100}] },
  { type:'motorB_on',  cat:'motorB', color:'#9f1239', icon:'⚡', label:'Мотор Б Вкл',        params:[{key:'pow',label:'Мощн %',type:'number',min:0,max:100},{key:'dir',label:'Напр.',type:'select',options:[{v:'fwd',l:'▶ Вперёд'},{v:'bwd',l:'◀ Назад'}]}] },
  { type:'motorB_off', cat:'motorB', color:'#881337', icon:'⛔', label:'Мотор Б Выкл',       params:null },
  { type:'motorB_time',cat:'motorB', color:'#be185d', icon:'⚡', label:'Мотор Б на сек',     params:[{key:'pow',label:'Мощн %',type:'number',min:0,max:100},{key:'dir',label:'Напр.',type:'select',options:[{v:'fwd',l:'▶ Вперёд'},{v:'bwd',l:'◀ Назад'}]},{key:'sec',label:'сек',type:'number',min:0,max:60,step:0.1}] },
  { type:'motorB_rot', cat:'motorB', color:'#9d174d', icon:'🔄', label:'Мотор Б оборотов',   params:[{key:'rot',label:'Об.',type:'number',min:0,max:100},{key:'dir',label:'Напр.',type:'select',options:[{v:'fwd',l:'▶ Вперёд'},{v:'bwd',l:'◀ Назад'}]}] },
  { type:'disp_num',   cat:'disp',   color:'#1d4ed8', icon:'🔢', label:'Показать число',     params:[{key:'num',label:'Число',type:'number',min:-99,max:999}] },
  { type:'disp_text',  cat:'disp',   color:'#1e40af', icon:'🔤', label:'Показать текст',     params:[{key:'txt',label:'Текст',type:'text'}] },
  { type:'disp_img',   cat:'disp',   color:'#1e3a8a', icon:'🖼', label:'Показать картинку',  params:[{key:'img',label:'Картинка',type:'select',options:[{v:'heart',l:'❤ Сердце'},{v:'smile',l:'😊 Улыбка'},{v:'star',l:'⭐ Звезда'},{v:'arrow',l:'→ Стрелка'},{v:'x',l:'✕ Крест'}]}] },
  { type:'disp_clear', cat:'disp',   color:'#172554', icon:'🗑', label:'Очистить дисплей',   params:null },
  { type:'disp_color', cat:'disp',   color:'#312e81', icon:'🎨', label:'Цвет LED',           params:[{key:'color',label:'Цвет',type:'select',options:[{v:'#22c55e',l:'🟢 Зелёный'},{v:'#ef4444',l:'🔴 Красный'},{v:'#3b82f6',l:'🔵 Синий'},{v:'#eab308',l:'🟡 Жёлтый'},{v:'#f97316',l:'🟠 Оранжевый'},{v:'#ffffff',l:'⚪ Белый'},{v:'#000000',l:'⚫ Выкл'}]}] },
  { type:'sound_play', cat:'sound',  color:'#7c3aed', icon:'🔊', label:'Воспроизвести звук', params:[{key:'snd',label:'Звук',type:'select',options:[{v:'beep',l:'Бип'},{v:'motor',l:'Мотор'},{v:'horn',l:'Гудок'},{v:'snap',l:'Щелчок'},{v:'tada',l:'Та-дааа'},{v:'woop',l:'Вупп'}]}] },
  { type:'sound_stop', cat:'sound',  color:'#6d28d9', icon:'🔇', label:'Стоп звук',          params:null },
  { type:'sound_vol',  cat:'sound',  color:'#5b21b6', icon:'🎚', label:'Громкость',          params:[{key:'vol',label:'%',type:'number',min:0,max:100}] },
  { type:'sound_note', cat:'sound',  color:'#4c1d95', icon:'🎵', label:'Сыграть ноту',       params:[{key:'note',label:'Нота',type:'number',min:48,max:84},{key:'dur',label:'дл. (сек)',type:'number',min:0.1,max:4,step:0.1}] },
  { type:'wait_motion',cat:'sens',   color:'#059669', icon:'👁', label:'Ждать движение',     params:null },
  { type:'wait_tilt',  cat:'sens',   color:'#047857', icon:'📐', label:'Ждать наклон',       params:[{key:'dir',label:'Направ.',type:'select',options:[{v:'any',l:'Любой'},{v:'forward',l:'Вперёд'},{v:'backward',l:'Назад'},{v:'left',l:'Влево'},{v:'right',l:'Вправо'}]}] },
  { type:'wait_dist',  cat:'sens',   color:'#065f46', icon:'📏', label:'Ждать дистанция <',  params:[{key:'val',label:'см',type:'number',min:0,max:300}] },
  { type:'wait_light', cat:'sens',   color:'#064e3b', icon:'💡', label:'Ждать яркость >',    params:[{key:'val',label:'%',type:'number',min:0,max:100}] },
  { type:'log',        cat:'sens',   color:'#374151', icon:'📝', label:'Вывести в лог',      params:[{key:'msg',label:'Текст',type:'text'}] },
]

const categories = [
  { id:'ctrl',   name:'Управление', icon:'🎮', color:'#f97316' },
  { id:'motorA', name:'Мотор А',    icon:'⚡', color:'#ef4444' },
  { id:'motorB', name:'Мотор Б',    icon:'⚡', color:'#be185d' },
  { id:'disp',   name:'Дисплей',    icon:'📺', color:'#3b82f6' },
  { id:'sound',  name:'Звук',       icon:'🔊', color:'#7c3aed' },
  { id:'sens',   name:'Сенсоры',    icon:'📡', color:'#22c55e' },
]
const activeCat = ref('ctrl')
const currentCatBlocks = computed(() => blockDefs.filter(b => b.cat === activeCat.value))
function getBlkDef(type) { return blockDefs.find(b => b.type === type) || { color:'#555', icon:'?', label:type, params:null } }

// ── Chains ──────────────────────────────────────────────────
const chains = ref([])
let chainIdSeq = 1, blkIdSeq = 1

function defaultParams(def) {
  if (!def.params) return {}
  const p = {}
  def.params.forEach(param => {
    if (param.type === 'number') p[param.key] = param.min ?? 0
    else if (param.type === 'select') p[param.key] = param.options[0].v
    else p[param.key] = ''
  })
  return p
}

function addBlockToCanvas(blkDef) {
  const chain = { id: chainIdSeq++, x: 120 + Math.random()*200, y: 80 + Math.random()*150, blocks: [] }
  chain.blocks.push({ id: blkIdSeq++, type: blkDef.type, params: defaultParams(blkDef) })
  chains.value.push(chain)
  scheduleSave()
}

function removeBlock(chainId, bi) {
  const ch = chains.value.find(c => c.id === chainId); if (!ch) return
  ch.blocks.splice(bi, 1)
  if (ch.blocks.length === 0) chains.value = chains.value.filter(c => c.id !== chainId)
  scheduleSave()
}

function clearCanvas() {
  if (confirm('Очистить всё?')) { chains.value = []; scheduleSave() }
}

const totalBlocks = computed(() => chains.value.reduce((a,c) => a + c.blocks.length, 0))

// ── Drag & Drop (blocks) ────────────────────────────────────
const canvasRef = ref(null)
const zoom = ref(1)
const panX = ref(0), panY = ref(0)
let dragBlkDef = null

function onPaletteDragStart(e, blk) { dragBlkDef = blk; e.dataTransfer.effectAllowed = 'copy' }

function onCanvasDrop(e) {
  if (!dragBlkDef) return
  const rect = canvasRef.value.getBoundingClientRect()
  const x = (e.clientX - rect.left - panX.value) / zoom.value
  const y = (e.clientY - rect.top  - panY.value) / zoom.value
  const chain = { id: chainIdSeq++, x, y, blocks: [] }
  chain.blocks.push({ id: blkIdSeq++, type: dragBlkDef.type, params: defaultParams(dragBlkDef) })
  chains.value.push(chain)
  dragBlkDef = null; scheduleSave()
}

function onChainDrop(e, chainId) {
  if (!dragBlkDef) return
  const ch = chains.value.find(c => c.id === chainId)
  if (ch) ch.blocks.push({ id: blkIdSeq++, type: dragBlkDef.type, params: defaultParams(dragBlkDef) })
  dragBlkDef = null; scheduleSave()
}

// ── Canvas pan ──────────────────────────────────────────────
let panStart = null
function onCanvasMousedown(e) {
  if (e.button !== 0) return
  panStart = { x: e.clientX - panX.value, y: e.clientY - panY.value }
  const move = ev => { panX.value = ev.clientX - panStart.x; panY.value = ev.clientY - panStart.y }
  const up = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', up) }
  window.addEventListener('mousemove', move); window.addEventListener('mouseup', up)
}
function onWheel(e) {
  const delta = e.deltaY > 0 ? -0.05 : 0.05
  zoom.value = Math.min(2, Math.max(0.3, +(zoom.value + delta).toFixed(2)))
}

// ── Chain drag ──────────────────────────────────────────────
function startChainDrag(e, chain) {
  const sx=e.clientX, sy=e.clientY, ox=chain.x, oy=chain.y
  const move = ev => { chain.x = ox+(ev.clientX-sx)/zoom.value; chain.y = oy+(ev.clientY-sy)/zoom.value }
  const up = () => { window.removeEventListener('mousemove',move); window.removeEventListener('mouseup',up); scheduleSave() }
  window.addEventListener('mousemove', move); window.addEventListener('mouseup', up)
}

// ── Simulator state ─────────────────────────────────────────
const motorOn = ref(false), motorDir = ref('fwd'), motorPow = ref(75)
const displayText = ref(''), displayColor = ref('#22c55e')
const motionDetected = ref(false)
const tiltDir = ref('none')
const distance = ref(150), lightLevel = ref(50)
const log = ref([])
const logRef = ref(null)

function addLog(msg) {
  const t = new Date().toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit',second:'2-digit'})
  log.value.push(`[${t}] ${msg}`)
  if (log.value.length > 100) log.value.shift()
  nextTick(() => { if (logRef.value) logRef.value.scrollTop = logRef.value.scrollHeight })
}
function simMotorFwd() { motorOn.value=true; motorDir.value='fwd'; addLog('Мотор А вперёд '+motorPow.value+'%') }
function simMotorBwd() { motorOn.value=true; motorDir.value='bwd'; addLog('Мотор А назад '+motorPow.value+'%') }
function triggerMotion() { motionDetected.value=true; addLog('Движение обнаружено'); setTimeout(()=>motionDetected.value=false,1500) }

// ── Run engine ──────────────────────────────────────────────
const sleep = ms => new Promise(r => setTimeout(r, ms))

async function execBlock(blk) {
  if (stopFlag) return
  runStep.value = blk.id
  const p = blk.params || {}
  const def = getBlkDef(blk.type)
  addLog(def.label + (Object.keys(p).length ? ' '+JSON.stringify(p) : ''))
  switch (blk.type) {
    case 'wait': await sleep((p.sec||1)*1000); break
    case 'motor_on': case 'motorB_on':
      motorOn.value=true; motorDir.value=p.dir||'fwd'; motorPow.value=p.pow??75; break
    case 'motor_off': case 'motorB_off': motorOn.value=false; break
    case 'motor_time': case 'motorB_time':
      motorOn.value=true; motorDir.value=p.dir||'fwd'; motorPow.value=p.pow??75
      await sleep((p.sec||1)*1000); motorOn.value=false; break
    case 'disp_num': displayText.value=String(p.num??0); break
    case 'disp_text': displayText.value=p.txt||''; break
    case 'disp_img': displayText.value=p.img==='heart'?'❤':p.img==='smile'?'😊':p.img==='star'?'⭐':p.img==='arrow'?'→':'✕'; break
    case 'disp_clear': displayText.value=''; break
    case 'disp_color': displayColor.value=p.color||'#22c55e'; break
    case 'sound_play': addLog('🔊 Звук: '+p.snd); break
    case 'sound_stop': addLog('🔇 Стоп звук'); break
    case 'sound_vol':  addLog('🎚 Громкость: '+p.vol+'%'); break
    case 'log': addLog('📝 '+p.msg); break
    default: await sleep(200)
  }
  await sleep(50)
}

async function runChain(chain) {
  let i=0
  while (i < chain.blocks.length && !stopFlag) {
    const blk = chain.blocks[i]
    if (blk.type === 'forever') {
      while (!stopFlag) { for (let j=i+1; j<chain.blocks.length&&!stopFlag; j++) await execBlock(chain.blocks[j]) }
      break
    } else if (blk.type === 'repeat') {
      const n = blk.params?.n || 1
      for (let r=0; r<n&&!stopFlag; r++) { for (let j=i+1; j<chain.blocks.length&&!stopFlag; j++) await execBlock(chain.blocks[j]) }
      break
    } else if (blk.type === 'stop') { stopFlag=true; break }
    else { await execBlock(blk) }
    i++
  }
}

async function runCode() {
  if (running.value) return
  running.value=true; stopFlag=false; addLog('▶ Запуск программы')
  const startChains = chains.value.filter(c => c.blocks[0]?.type==='start'||c.blocks[0]?.type==='when_btn')
  if (startChains.length===0 && chains.value.length>0) await Promise.all(chains.value.map(ch=>runChain(ch)))
  else await Promise.all(startChains.map(ch=>runChain(ch)))
  running.value=false; runStep.value=null; addLog('■ Программа завершена')
}

function stopCode() {
  stopFlag=true; running.value=false; runStep.value=null; motorOn.value=false; addLog('■ Стоп')
}

// ── LEGO 3D definitions ─────────────────────────────────────
const PDEF = {
  smarthub:{ label:'SmartHub',   sub:'Хаб управления',   icon:'🔵', cat:'wedo',    col:0x006CB7, w:4, h:2.4, d:3, studs:true,  special:'hub'   },
  motor:   { label:'Мотор А',    sub:'WeDo 2.0 Motor',   icon:'⚙️', cat:'wedo',    col:0x0055AA, w:2, h:2.4, d:3, studs:true,  special:'motor' },
  motorB:  { label:'Мотор Б',    sub:'WeDo 2.0 Motor',   icon:'⚙️', cat:'wedo',    col:0xAA1100, w:2, h:2.4, d:3, studs:true,  special:'motor' },
  motion:  { label:'Движение',   sub:'Датчик дистанции', icon:'👁',  cat:'wedo',    col:0xDCDCDC, w:2, h:2.4, d:2, studs:false, special:'motion'},
  tilt:    { label:'Наклон',     sub:'Датчик наклона',   icon:'📐', cat:'wedo',    col:0xE0E0E0, w:2, h:2.4, d:2, studs:false, special:'tilt'  },
  plate8:  { label:'Плита 8×8',  sub:'Основание',        icon:'⬛', cat:'bricks',  col:0x006A42, w:8, h:0.4, d:8, studs:true,  isPlate:true    },
  brick2x4:{ label:'Кубик 2×4',  sub:'Стандартный',      icon:'🟥', cat:'bricks',  col:0xC91A09, w:4, h:1.2, d:2, studs:true  },
  brick2x2:{ label:'Кубик 2×2',  sub:'Стандартный',      icon:'🟨', cat:'bricks',  col:0xF2CD37, w:2, h:1.2, d:2, studs:true  },
  brick1x4:{ label:'Кубик 1×4',  sub:'Узкий',            icon:'🟩', cat:'bricks',  col:0x237841, w:4, h:1.2, d:1, studs:true  },
  brick1x2:{ label:'Кубик 1×2',  sub:'Маленький',        icon:'⬜', cat:'bricks',  col:0xF0F0F0, w:2, h:1.2, d:1, studs:true  },
  brick1x1:{ label:'Кубик 1×1',  sub:'Самый мал.',       icon:'🔲', cat:'bricks',  col:0xE040FB, w:1, h:1.2, d:1, studs:true  },
  beam5:   { label:'Балка 1×5',  sub:'Техник',           icon:'▬',  cat:'technic', col:0x9BA0A3, w:5, h:1.0, d:1, holes:true  },
  beam7:   { label:'Балка 1×7',  sub:'Техник',           icon:'▬',  cat:'technic', col:0x9BA0A3, w:7, h:1.0, d:1, holes:true  },
  beam11:  { label:'Балка 1×11', sub:'Техник',           icon:'▬',  cat:'technic', col:0x9BA0A3, w:11,h:1.0, d:1, holes:true  },
  angbeam: { label:'Угл. балка', sub:'Техник угловая',   icon:'↙',  cat:'technic', col:0x494F54, w:4, h:1.0, d:3, holes:true  },
  gear8:   { label:'Шест. 8T',   sub:'Малая',            icon:'⚙',  cat:'technic', col:0x494F54, w:1, h:0.6, d:1, isGear:true, teeth:8,  gr:0.6  },
  gear24:  { label:'Шест. 24T',  sub:'Большая',          icon:'⚙',  cat:'technic', col:0x494F54, w:3, h:0.6, d:3, isGear:true, teeth:24, gr:1.35 },
  wheel:   { label:'Колесо',     sub:'с шиной',          icon:'🔘', cat:'technic', col:0x1B2A34, w:2, h:2.0, d:2, isWheel:true },
  axle4:   { label:'Ось 4L',     sub:'Техник',           icon:'—',  cat:'technic', col:0x494F54, w:4, h:0.3, d:0.3,isAxle:true },
}

const legoCats = [
  { id:'wedo',    name:'WeDo 2.0', icon:'🤖' },
  { id:'bricks',  name:'Кирпичики', icon:'🧱' },
  { id:'technic', name:'Техник',    icon:'⚙️' },
]
const activeLegoCat = ref('wedo')
const currentLegoParts = computed(() =>
  Object.entries(PDEF)
    .filter(([,d]) => d.cat === activeLegoCat.value)
    .map(([type, d]) => ({ type, ...d }))
)

// ── Three.js helpers ────────────────────────────────────────
function lightenHex(hex, a) {
  const r=(hex>>16)&0xFF, g=(hex>>8)&0xFF, b=hex&0xFF
  return (Math.min(255,r+(255-r)*a)<<16)|(Math.min(255,g+(255-g)*a)<<8)|Math.min(255,b+(255-b)*a)
}
function darkenHex(hex, a) {
  const r=(hex>>16)&0xFF, g=(hex>>8)&0xFF, b=hex&0xFF
  return (Math.round(r*(1-a))<<16)|(Math.round(g*(1-a))<<8)|Math.round(b*(1-a))
}

function buildMesh(type, ghost=false) {
  const def = PDEF[type]
  const group = new THREE.Group()
  const alpha = ghost ? 0.45 : 1
  function mat(col) {
    return new THREE.MeshPhongMaterial({ color:col, shininess:85, transparent:ghost||false, opacity:alpha })
  }
  if (def.isGear) {
    const r = def.gr
    group.add(new THREE.Mesh(new THREE.CylinderGeometry(r*0.7,r*0.7,def.h,32), mat(def.col)))
    for (let i=0; i<def.teeth; i++) {
      const ang = i/def.teeth*Math.PI*2
      const t = new THREE.Mesh(new THREE.BoxGeometry(0.18,def.h,0.22), mat(darkenHex(def.col,0.1)))
      t.position.set(Math.cos(ang)*r*0.88, 0, Math.sin(ang)*r*0.88); t.rotation.y=ang; group.add(t)
    }
    group.add(new THREE.Mesh(new THREE.CylinderGeometry(0.2,0.2,def.h*1.1,12), mat(0x1B1B1B)))
    return group
  }
  if (def.isWheel) {
    const torus = new THREE.Mesh(new THREE.TorusGeometry(0.75,0.38,12,24), mat(0x111111))
    torus.rotation.x=Math.PI/2; group.add(torus)
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(0.42,0.42,0.2,20), mat(0xC0C0C0))
    rim.rotation.x=Math.PI/2; group.add(rim)
    group.add(new THREE.Mesh(new THREE.CylinderGeometry(0.12,0.12,0.4,10), mat(0x888888)))
    return group
  }
  if (def.isAxle) {
    const ax = new THREE.Mesh(new THREE.CylinderGeometry(0.1,0.1,def.w,8), mat(def.col))
    ax.rotation.z=Math.PI/2; ax.position.x=def.w/2; group.add(ax); return group
  }
  const { w, h, d } = def
  const body = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), mat(def.col))
  body.position.set(w/2,h/2,d/2); body.castShadow=true; body.receiveShadow=true; group.add(body)
  if (def.studs) {
    const sr=0.28, sh=def.isPlate?0.1:0.18
    const sg = new THREE.CylinderGeometry(sr,sr,sh,16)
    const sm = mat(lightenHex(def.col, 0.12))
    for (let x=0; x<Math.round(w); x++) for (let z=0; z<Math.round(d); z++) {
      const s = new THREE.Mesh(sg, sm); s.position.set(x+0.5,h+sh/2,z+0.5); group.add(s)
    }
  }
  if (def.holes) {
    const hm = new THREE.MeshPhongMaterial({ color:0x030608, transparent:ghost||false, opacity:ghost?0.4:1 })
    for (let x=0; x<Math.round(w); x++) {
      const hole = new THREE.Mesh(new THREE.CylinderGeometry(0.2,0.2,w*1.05,16), hm)
      hole.rotation.z=Math.PI/2; hole.position.set(x+0.5,h/2,d/2); group.add(hole)
    }
  }
  if (def.special==='hub') {
    const ledM = new THREE.MeshPhongMaterial({ color:0x00FF88, emissive:0x00BB44, transparent:ghost||false, opacity:alpha })
    const led = new THREE.Mesh(new THREE.CylinderGeometry(0.42,0.42,0.22,20), ledM)
    led.name='hub-led'; led.position.set(2,h+0.11,1.5); group.add(led)
    const pm = mat(darkenHex(def.col,0.35))
    for (const px of [0.5, w-0.7]) {
      const p = new THREE.Mesh(new THREE.BoxGeometry(0.45,1.0,0.5), pm)
      p.position.set(px,h/2,-0.35); group.add(p)
    }
  }
  if (def.special==='motor') {
    const am = new THREE.MeshPhongMaterial({ color:0x999999, transparent:ghost||false, opacity:alpha })
    const axle = new THREE.Mesh(new THREE.CylinderGeometry(0.16,0.16,1.6,12), am)
    axle.name='motor-axle'; axle.rotation.z=Math.PI/2; axle.position.set(w/2,h/2,d+0.4); group.add(axle)
    const whl = new THREE.Mesh(new THREE.CylinderGeometry(0.38,0.38,0.12,16), am)
    whl.name='motor-wheel'; whl.rotation.z=Math.PI/2; whl.position.set(w/2,h/2,d+1.2); group.add(whl)
  }
  if (def.special==='motion') {
    const lm = new THREE.MeshPhongMaterial({ color:0x1122FF, shininess:200, transparent:ghost||false, opacity:alpha })
    const lens = new THREE.Mesh(new THREE.SphereGeometry(0.4,16,16), lm)
    lens.position.set(w/2,h/2,-0.3); group.add(lens)
  }
  if (def.special==='tilt') {
    const im = new THREE.MeshPhongMaterial({ color:0xFF8800, transparent:ghost||false, opacity:alpha })
    const ind = new THREE.Mesh(new THREE.BoxGeometry(0.7,0.35,0.28), im)
    ind.position.set(w/2,h+0.17,d/2); group.add(ind)
  }
  return group
}

// ── Three.js scene state ────────────────────────────────────
const threeCanvas = ref(null)
const legoRef = ref(null)
const placingType = ref(null)
const legoCount = ref(0)

let threeScene = null, threeRenderer = null, threeCamera = null
let threeLoopActive = false
let placedPieces = []
let ghostGroup = null, ghostRot = 0, selectedId = null
let orb = { theta:0.75, phi:0.52, r:22, cx:5, cy:0, cz:5 }
let camDrag = null
let threeRaycaster = null, threeGroundPlane = null, threeMouseVec = null
let motorAnimOn = false, motorAnimPow = 5

function initThree() {
  const canvas = threeCanvas.value; if (!canvas) return
  threeRenderer = new THREE.WebGLRenderer({ canvas, antialias:true, preserveDrawingBuffer:true })
  threeRenderer.setPixelRatio(Math.min(devicePixelRatio,2))
  threeRenderer.shadowMap.enabled = true
  threeRenderer.shadowMap.type = THREE.PCFSoftShadowMap

  threeScene = new THREE.Scene()
  threeScene.background = new THREE.Color(0x060A10)
  threeScene.fog = new THREE.FogExp2(0x060A10, 0.015)
  threeCamera = new THREE.PerspectiveCamera(52,1,0.1,300)

  threeScene.add(new THREE.AmbientLight(0x304060,1.2))
  const sun = new THREE.DirectionalLight(0xFFF4E8,1.8)
  sun.position.set(12,20,10); sun.castShadow=true
  sun.shadow.mapSize.width=2048; sun.shadow.mapSize.height=2048
  sun.shadow.camera.near=0.5; sun.shadow.camera.far=80
  sun.shadow.camera.left=-30; sun.shadow.camera.right=30
  sun.shadow.camera.top=30; sun.shadow.camera.bottom=-30
  threeScene.add(sun)
  threeScene.add(Object.assign(new THREE.DirectionalLight(0x4488FF,0.5), { position: new THREE.Vector3(-10,6,-10) }))

  threeScene.add(new THREE.GridHelper(32,32,0x1A2E3E,0x0E1E2E))
  const floorG = new THREE.PlaneGeometry(32,32); floorG.rotateX(-Math.PI/2)
  const floor = new THREE.Mesh(floorG, new THREE.MeshPhongMaterial({color:0x080E16,transparent:true,opacity:0.6}))
  floor.receiveShadow=true; floor.name='floor'; threeScene.add(floor)

  threeRaycaster = new THREE.Raycaster()
  threeGroundPlane = new THREE.Plane(new THREE.Vector3(0,1,0),0)
  threeMouseVec = new THREE.Vector2(-9999,-9999)

  updateCam(); bindThreeEvents(); threeLoopActive=true; threeLoop()
}

function destroyThree() {
  threeLoopActive = false
  const canvas = threeCanvas.value
  if (canvas) {
    canvas.removeEventListener('mousedown', onThreeMousedown)
    canvas.removeEventListener('contextmenu', preventCtx)
    canvas.removeEventListener('wheel', onThreeWheel)
  }
  window.removeEventListener('mousemove', onThreeMousemove)
  window.removeEventListener('mouseup', onThreeMouseup)
  if (threeRenderer) { threeRenderer.dispose(); threeRenderer=null }
  threeScene=null; threeCamera=null
}

function updateCam() {
  if (!threeCamera) return
  const { theta,phi,r,cx,cy,cz } = orb
  threeCamera.position.set(cx+r*Math.sin(phi)*Math.sin(theta), cy+r*Math.cos(phi), cz+r*Math.sin(phi)*Math.cos(theta))
  threeCamera.lookAt(cx,cy,cz)
}

function preventCtx(e) { e.preventDefault() }
function onThreeWheel(e) { orb.r=Math.max(3,Math.min(60,orb.r*(1+e.deltaY*0.001))); updateCam(); e.preventDefault() }

function bindThreeEvents() {
  const canvas = threeCanvas.value; if (!canvas) return
  canvas.addEventListener('mousedown', onThreeMousedown)
  canvas.addEventListener('contextmenu', preventCtx)
  canvas.addEventListener('wheel', onThreeWheel, { passive:false })
  window.addEventListener('mousemove', onThreeMousemove)
  window.addEventListener('mouseup', onThreeMouseup)
}

function onThreeMousedown(e) {
  if (e.button===2) { camDrag={t:'orb',x:e.clientX,y:e.clientY}; e.preventDefault() }
  else if (e.button===1) { camDrag={t:'pan',x:e.clientX,y:e.clientY}; e.preventDefault() }
  else if (e.button===0) { if (placingType.value) handlePlace(e); else handleSelect(e) }
}

function onThreeMousemove(e) {
  if (camDrag) {
    const dx=e.clientX-camDrag.x, dy=e.clientY-camDrag.y
    if (camDrag.t==='orb') {
      orb.theta-=dx*0.005; orb.phi=Math.max(0.08,Math.min(1.45,orb.phi+dy*0.005))
    } else {
      const right=new THREE.Vector3()
      threeCamera.getWorldDirection(right); right.crossVectors(right,new THREE.Vector3(0,1,0)).normalize()
      orb.cx+=right.x*(-dx)*0.02*(orb.r/20); orb.cz+=right.z*(-dx)*0.02*(orb.r/20); orb.cy+=dy*0.015*(orb.r/20)
    }
    camDrag.x=e.clientX; camDrag.y=e.clientY; updateCam()
  }
  updateThreeMousePos(e)
  if (placingType.value) updateGhost(e)
}

function onThreeMouseup() { camDrag=null }

function updateThreeMousePos(e) {
  if (!threeCanvas.value) return
  const rect=threeCanvas.value.getBoundingClientRect()
  threeMouseVec.x=((e.clientX-rect.left)/rect.width)*2-1
  threeMouseVec.y=-((e.clientY-rect.top)/rect.height)*2+1
}

function getGridHit(e) {
  updateThreeMousePos(e)
  threeRaycaster.setFromCamera(threeMouseVec,threeCamera)
  const pt=new THREE.Vector3()
  if (!threeRaycaster.ray.intersectPlane(threeGroundPlane,pt)) return null
  return { gx:Math.round(pt.x), gz:Math.round(pt.z) }
}

function getTopY(gx,gz,type) {
  const def=PDEF[type]; let maxY=0
  for (const p of placedPieces) {
    const pd=PDEF[p.type]
    if (!(gx+def.w<=p.gx||gx>=p.gx+pd.w||gz+def.d<=p.gz||gz>=p.gz+pd.d)) {
      const top=p.gy+pd.h; if(top>maxY) maxY=top
    }
  }
  return maxY
}

function updateGhost(e) {
  if (!ghostGroup||!placingType.value) return
  const hit=getGridHit(e); if(!hit) return
  const gy=getTopY(hit.gx,hit.gz,placingType.value)
  ghostGroup.position.set(hit.gx,gy,hit.gz)
  ghostGroup.rotation.y=ghostRot*Math.PI/2
}

function handlePlace(e) {
  const hit=getGridHit(e); if(!hit) return
  const gy=getTopY(hit.gx,hit.gz,placingType.value)
  const g=buildMesh(placingType.value,false)
  g.position.set(hit.gx,gy,hit.gz); g.rotation.y=ghostRot*Math.PI/2; g.castShadow=true
  const id='p'+Date.now()+Math.random().toString(36).substr(2,4)
  g.userData={id,type:placingType.value,gx:hit.gx,gy,gz:hit.gz,rot:ghostRot}
  threeScene.add(g)
  placedPieces.push({id,group:g,type:placingType.value,gx:hit.gx,gy,gz:hit.gz,rot:ghostRot})
  legoCount.value=placedPieces.length; scheduleSave()
}

function handleSelect(e) {
  updateThreeMousePos(e)
  threeRaycaster.setFromCamera(threeMouseVec,threeCamera)
  const meshes=[]
  for (const p of placedPieces) p.group.traverseVisible(o=>{ if(o.isMesh) meshes.push(o) })
  const hits=threeRaycaster.intersectObjects(meshes)
  if (!hits.length) { selectedId=null; return }
  let grp=hits[0].object
  while (grp.parent&&!grp.userData?.id) grp=grp.parent
  selectedId = grp.userData?.id||null
}

function setPlacing(type) {
  placingType.value=type
  if (ghostGroup) { threeScene?.remove(ghostGroup); ghostGroup=null }
  if (type&&threeScene) { ghostGroup=buildMesh(type,true); threeScene.add(ghostGroup) }
}

function rotateSel() {
  if (!selectedId) return
  const p=placedPieces.find(x=>x.id===selectedId); if(!p) return
  p.rot=(p.rot+1)%4; p.group.rotation.y=p.rot*Math.PI/2; scheduleSave()
}

function delSelPiece() {
  if (!selectedId) return
  const idx=placedPieces.findIndex(x=>x.id===selectedId); if(idx<0) return
  threeScene?.remove(placedPieces[idx].group); placedPieces.splice(idx,1)
  selectedId=null; legoCount.value=placedPieces.length; scheduleSave()
}

function clearBuilder() {
  if (!confirm('Очистить конструктор?')) return
  for (const p of placedPieces) threeScene?.remove(p.group)
  placedPieces=[]; legoCount.value=0; selectedId=null; scheduleSave()
}

function resizeThree() {
  if (!threeRenderer||!threeCamera||!threeCanvas.value) return
  const canvas=threeCanvas.value, w=canvas.clientWidth, h=canvas.clientHeight
  if (canvas.width!==w||canvas.height!==h) {
    threeRenderer.setSize(w,h,false); threeCamera.aspect=w/h; threeCamera.updateProjectionMatrix()
  }
}

function threeLoop() {
  if (!threeLoopActive) return
  requestAnimationFrame(threeLoop); resizeThree()
  if (motorAnimOn) {
    const spd=motorAnimPow*0.04
    for (const p of placedPieces) {
      if (p.type==='motor'||p.type==='motorB') {
        const a=p.group.getObjectByName('motor-axle'); const w=p.group.getObjectByName('motor-wheel')
        if(a) a.rotation.x+=spd; if(w) w.rotation.x+=spd
      }
      if (p.type==='gear8'||p.type==='gear24') p.group.rotation.y+=spd*0.5
    }
  }
  threeRenderer?.render(threeScene,threeCamera)
}

function serializeLegoState() {
  return { pieces: placedPieces.map(p=>({type:p.type,gx:p.gx,gy:p.gy,gz:p.gz,rot:p.rot||0})) }
}

function deserializeLegoState(state) {
  if (!state||!state.pieces||!threeScene) return
  for (const p of state.pieces) {
    const g=buildMesh(p.type,false)
    g.position.set(p.gx,p.gy,p.gz); g.rotation.y=(p.rot||0)*Math.PI/2; g.castShadow=true
    const id='p'+Math.random().toString(36).substr(2,9)
    g.userData={id,type:p.type,gx:p.gx,gy:p.gy,gz:p.gz,rot:p.rot||0}
    threeScene.add(g)
    placedPieces.push({id,group:g,type:p.type,gx:p.gx,gy:p.gy,gz:p.gz,rot:p.rot||0})
  }
  legoCount.value=placedPieces.length
}

// Watch motor → animate 3D
watch(motorOn, val => { motorAnimOn=val; motorAnimPow=motorPow.value })
watch(motorPow, val => { motorAnimPow=val })

// ── Keyboard ────────────────────────────────────────────────
function onKey(e) {
  if (e.target.tagName==='INPUT'||e.target.tagName==='SELECT') return
  if (mode.value==='build') {
    if (e.key==='r'||e.key==='R') { if(placingType.value) { ghostRot=(ghostRot+1)%4 } else rotateSel() }
    if (e.key==='Escape') setPlacing(null)
    if (e.key==='Delete'||e.key==='Backspace') delSelPiece()
  } else {
    if (e.key==='Delete'&&selectedId) delSelPiece()
  }
}
onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  destroyThree()
})

// Switch mode → init Three when entering build
watch(mode, async (val) => {
  if (val==='build') {
    await nextTick()
    if (!threeScene) initThree()
  }
})

// ── Save helper ─────────────────────────────────────────────
function scheduleSave() {
  if (!store.project) return
  store.project.code_state = JSON.stringify({ chains: chains.value })
  store.project.lego_state = JSON.stringify(serializeLegoState())
  store.markDirty()
}

// ── Load project ─────────────────────────────────────────────
onMounted(async () => {
  try {
    await store.loadProject(route.params.id)
    pname.value = store.project.name || 'Без названия'
    if (store.project.code_state) {
      try {
        const d=JSON.parse(store.project.code_state)
        if (d.chains) { chains.value=d.chains; chainIdSeq=Math.max(...d.chains.map(c=>c.id),0)+1 }
      } catch {}
    }
    // lego state will be loaded when user switches to build mode (after Three.js init)
  } catch (e) {
    router.push({ name:'projects' })
  }
})

// After Three.js inits, load saved pieces
watch(threeScene, (scene) => {
  if (!scene) return
  if (store.project?.lego_state) {
    try {
      const d=JSON.parse(store.project.lego_state)
      if (d.pieces) deserializeLegoState(d)
    } catch {}
  }
})
</script>

<style scoped>
/* ── ROOT ── */
.ws { display:flex; flex-direction:column; height:100vh; background:var(--bg); overflow:hidden; }

/* ── HEADER ── */
.ws-hdr { display:flex; align-items:center; gap:10px; padding:0 12px; height:48px; flex-shrink:0; background:var(--bg2); border-bottom:1px solid var(--border); }
.back-btn { background:var(--bg4); color:var(--text2); padding:5px 12px; font-size:12px; flex-shrink:0; }
.pname { flex:1; min-width:80px; max-width:200px; border:none; border-bottom:1px solid transparent; background:transparent; font-size:14px; font-weight:600; color:var(--text); padding:2px 4px; }
.pname:focus { border-bottom-color:var(--accent); outline:none; }
.save-pill { display:flex; align-items:center; gap:5px; font-size:11px; color:var(--text3); flex-shrink:0; }
.sdot { width:6px; height:6px; border-radius:50%; background:var(--text3); }
.save-pill.saved .sdot { background:var(--green); }
.save-pill.saving .sdot { background:var(--yellow); }
.save-pill.error .sdot { background:var(--red); }
.hbts { display:flex; align-items:center; gap:6px; margin-left:auto; flex-shrink:0; }
.btn-run { background:var(--accent); color:#fff; font-weight:600; padding:6px 16px; font-size:13px; }
.btn-run:hover:not(:disabled) { background:var(--accent2); }
.btn-stop { background:#27272a; border:1px solid #3f3f46; color:var(--text2); padding:6px 12px; }
.btn-icon { background:var(--bg4); padding:6px 10px; font-size:13px; }
.mbadge { display:flex; align-items:center; gap:6px; padding:4px 10px; border-radius:20px; background:#1c1c1f; border:1px solid var(--border); font-size:11px; color:var(--text3); flex-shrink:0; }
.mbadge.on { border-color:#ef4444; color:#ef4444; }
.mpulse { width:6px; height:6px; border-radius:50%; background:#ef4444; animation:pulse 1s infinite; flex-shrink:0; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }

/* ── MODE NAV ── */
.mode-nav { display:flex; align-items:center; gap:8px; padding:0 10px; height:38px; flex-shrink:0; background:var(--bg3); border-bottom:1px solid var(--border); }
.panel-toggle { width:28px; height:28px; padding:0; display:flex; align-items:center; justify-content:center; background:var(--bg4); color:var(--text2); font-size:11px; flex-shrink:0; }
.mode-tabs { display:flex; gap:2px; }
.mode-tab { display:flex; align-items:center; gap:5px; padding:5px 14px; font-size:12px; font-weight:600; background:transparent; color:var(--text3); border-radius:6px; transition:all 0.15s; }
.mode-tab.active { background:var(--bg4); color:var(--text); }
.mt-pip { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
.mode-extras { display:flex; align-items:center; gap:4px; margin-left:auto; }
.ct-info { font-size:11px; color:var(--text3); padding:0 6px; }
.ct-btn { padding:3px 8px; font-size:12px; background:var(--bg4); }

/* ── BODY ── */
.ws-body { display:flex; flex:1; overflow:hidden; }

/* ── LEFT PANEL ── */
.ws-panel { width:220px; flex-shrink:0; display:flex; flex-direction:column; background:var(--bg2); border-right:1px solid var(--border); overflow:hidden; }
.cats { display:flex; flex-direction:column; gap:1px; padding:8px 6px; flex-shrink:0; }
.cat-btn { display:flex; align-items:center; gap:7px; padding:7px 10px; font-size:12px; font-weight:500; background:transparent; color:var(--text2); text-align:left; border-radius:6px; transition:all 0.1s; }
.cat-btn:hover { background:var(--bg3); color:var(--text); }
.cat-btn.active { color:var(--text); }
.blocks-list { flex:1; overflow-y:auto; padding:4px 6px; display:flex; flex-direction:column; gap:3px; }
.palette-block { display:flex; align-items:center; gap:6px; padding:7px 10px; border-radius:7px; cursor:pointer; font-size:12px; font-weight:500; color:#fff; user-select:none; transition:filter 0.1s; position:relative; }
.palette-block:hover { filter:brightness(1.15); }
.pb-ico { font-size:13px; flex-shrink:0; }
.pb-add { margin-left:auto; opacity:0.7; font-size:15px; font-weight:700; }
.parts-list { flex:1; overflow-y:auto; padding:4px 6px; display:flex; flex-direction:column; gap:4px; }
.palette-part { display:flex; align-items:center; gap:8px; padding:7px 10px; border-radius:8px; cursor:pointer; background:var(--bg3); border:1px solid var(--border); font-size:11px; color:var(--text2); transition:all 0.12s; }
.palette-part:hover { border-color:var(--accent); color:var(--text); background:rgba(99,160,255,0.06); }
.palette-part.active { border-color:#60a5fa; background:rgba(96,165,250,0.14); color:#fff; box-shadow:0 0 0 1px rgba(96,165,250,0.18); }
.p-icon { font-size:18px; flex-shrink:0; width:24px; text-align:center; }
.pp-lbl { font-size:12px; font-weight:600; color:inherit; }
.pp-sub { font-size:10px; color:var(--text3); margin-top:1px; }

/* ── MAIN ── */
.ws-main { flex:1; overflow:hidden; position:relative; }

/* ── CODE CANVAS ── */
.code-canvas { width:100%; height:100%; overflow:hidden; position:relative; cursor:grab; background:#0e0e10; background-image:radial-gradient(circle,#3f3f4620 1px,transparent 1px); background-size:24px 24px; }
.code-canvas:active { cursor:grabbing; }
.cc-inner { position:absolute; top:0; left:0; transform-origin:0 0; }
.canvas-hint { position:absolute; bottom:16px; left:50%; transform:translateX(-50%); font-size:12px; color:var(--text3); pointer-events:none; border:1px dashed var(--border); padding:8px 18px; border-radius:8px; }

/* ── BLOCK CHAIN ── */
.block-chain { position:absolute; cursor:move; }
.prog-block { width:200px; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px #0007; position:relative; transition:box-shadow 0.15s; }
.prog-block.running { box-shadow:0 0 0 2px #fff4,0 4px 16px #0009; }
.prog-block+.prog-block { border-top:2px solid #fff2; }
.blk-hdr { display:flex; align-items:center; gap:6px; padding:7px 8px; font-size:12px; font-weight:600; color:#fff; }
.blk-ico { font-size:14px; flex-shrink:0; }
.blk-lbl { flex:1; }
.blk-del { width:20px; height:20px; padding:0; display:flex; align-items:center; justify-content:center; background:#fff2; color:#fff; font-size:10px; border-radius:4px; flex-shrink:0; }
.blk-del:hover { background:#fff3; }
.blk-params { padding:0 8px 8px; display:flex; flex-direction:column; gap:4px; }
.blk-param { display:flex; align-items:center; justify-content:space-between; gap:6px; }
.blk-param label { font-size:11px; color:#fffa; white-space:nowrap; flex-shrink:0; }
.blk-param input,.blk-param select { width:70px; font-size:11px; padding:3px 6px; background:#fff2; border:1px solid #fff3; border-radius:4px; color:#fff; min-width:0; }
.blk-param select { width:auto; max-width:110px; }
.chain-drop { width:200px; height:28px; display:flex; align-items:center; justify-content:center; border:1px dashed #fff3; border-top:none; border-radius:0 0 8px 8px; font-size:11px; color:#fff5; cursor:default; transition:background 0.1s; }
.chain-drop:hover { background:#fff1; color:#fff8; }

/* ── RIGHT SIM PANEL ── */
.ws-sim { width:230px; flex-shrink:0; display:flex; flex-direction:column; background:var(--bg2); border-left:1px solid var(--border); overflow-y:auto; }
.sim-section { padding:10px 10px 8px; border-bottom:1px solid var(--border); }
.sim-log-sec { flex:1; display:flex; flex-direction:column; min-height:0; }
.sim-title { font-size:10px; font-weight:700; color:var(--text3); letter-spacing:.08em; margin-bottom:7px; }
.sim-row { display:flex; align-items:center; gap:6px; margin-bottom:5px; flex-wrap:wrap; }
.sim-btn { padding:4px 10px; font-size:11px; }
.sim-btn.active { background:var(--accent); color:#fff; }
.sim-slider { flex:1; min-width:60px; accent-color:var(--accent); }
.sim-val { font-size:11px; color:var(--text2); white-space:nowrap; }
.sim-lbl { font-size:11px; color:var(--text3); flex-shrink:0; min-width:60px; }
.sim-num { width:58px; font-size:11px; padding:3px 5px; }
.sim-select { font-size:11px; padding:3px 5px; }
.sim-display { font-size:22px; font-weight:700; text-align:center; padding:8px; background:var(--bg3); border-radius:6px; min-height:42px; margin-bottom:6px; letter-spacing:2px; }
.ss-dot { width:8px; height:8px; border-radius:50%; background:var(--bg4); border:1px solid var(--border); flex-shrink:0; }
.ss-dot.active { background:#22c55e; border-color:#22c55e; box-shadow:0 0 6px #22c55e; }
.sim-log { flex:1; overflow-y:auto; font-size:10px; font-family:monospace; color:var(--text3); line-height:1.6; }
.log-line { padding:1px 2px; border-bottom:1px solid var(--bg3); word-break:break-all; }

/* ── LEGO 3D CANVAS ── */
.lego-wrap { width:100%; height:100%; position:relative; overflow:hidden; background:#060A10; }
.three-canvas { display:block; width:100%; height:100%; }
.placing-banner {
  position:absolute; top:14px; left:50%; transform:translateX(-50%);
  background:rgba(0,200,255,.15); border:1px solid rgba(0,200,255,.35);
  border-radius:20px; padding:6px 18px; font-size:12px; font-weight:800;
  color:#00c8ff; display:flex; align-items:center; gap:10px; white-space:nowrap;
  pointer-events:none;
}
.hint-esc { opacity:.5; font-size:10px; font-weight:400; }
.lego-hint {
  position:absolute; bottom:50px; left:50%; transform:translateX(-50%);
  font-size:12px; color:var(--text3); border:1px dashed var(--border);
  padding:8px 18px; border-radius:8px; pointer-events:none; background:rgba(6,10,16,.8);
  white-space:nowrap;
}
.controls-hint-3d {
  position:absolute; bottom:12px; left:50%; transform:translateX(-50%);
  background:rgba(6,10,16,.85); border:1px solid #1a2e3e; border-radius:8px;
  padding:5px 14px; font-size:10px; color:#5a7090; display:flex; gap:12px;
  white-space:nowrap; pointer-events:none;
}
.controls-hint-3d span { display:flex; align-items:center; gap:4px; }
.key3d { background:#1a2a3a; border-radius:4px; padding:1px 5px; font-family:monospace; font-size:9px; font-weight:600; color:#d8e4f0; }
</style>
