<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, type RouteLocationRaw } from 'vue-router'

// Section tabs under a page title. Each tab is a real route, so it survives a reload
// and the phone's back button moves between tabs. On a narrow screen the row scrolls;
// a fade at the edge shows there is more, and the active tab is scrolled into view.
defineProps<{ tabs: { label: string; to: RouteLocationRaw }[]; label: string }>()

const route = useRoute()
const nav = ref<HTMLElement | null>(null)
const moreLeft = ref(false)
const moreRight = ref(false)

function updateFades() {
  const el = nav.value
  if (!el) return
  moreLeft.value = el.scrollLeft > 2
  moreRight.value = el.scrollLeft + el.clientWidth < el.scrollWidth - 2
}

async function revealActive() {
  await nextTick()
  const active = nav.value?.querySelector<HTMLElement>('.is-active')
  active?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
  updateFades()
}

onMounted(() => {
  revealActive()
  window.addEventListener('resize', updateFades)
})
onBeforeUnmount(() => window.removeEventListener('resize', updateFades))
watch(() => route.fullPath, revealActive)
</script>

<template>
  <nav
    ref="nav"
    class="tabs"
    :class="{ 'more-left': moreLeft, 'more-right': moreRight }"
    :aria-label="label"
    @scroll.passive="updateFades"
  >
    <RouterLink v-for="tab in tabs" :key="tab.label" :to="tab.to" class="tab" exact-active-class="is-active">
      {{ tab.label }}
    </RouterLink>
  </nav>
</template>

<style scoped>
.tabs {
  --fade: 2.5rem;
  display: flex;
  gap: 0.25rem;
  overflow-x: auto;
  scrollbar-width: none;
  padding: 0.25rem;
  margin: 0 -0.25rem;
  border-bottom: 1px solid var(--line);
}

.tabs::-webkit-scrollbar {
  display: none;
}

.more-right {
  mask-image: linear-gradient(to right, #000 calc(100% - var(--fade)), transparent);
}

.more-left {
  mask-image: linear-gradient(to left, #000 calc(100% - var(--fade)), transparent);
}

.more-left.more-right {
  mask-image: linear-gradient(
    to right,
    transparent,
    #000 var(--fade),
    #000 calc(100% - var(--fade)),
    transparent
  );
}

.tab {
  flex: none;
  padding: 0.55rem 0.9rem;
  border-radius: var(--radius-control) var(--radius-control) 0 0;
  color: var(--muted);
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  margin-bottom: -0.3rem;
  transition: color 0.15s, border-color 0.15s;
}

.tab:hover {
  color: var(--ink);
}

.tab.is-active {
  color: var(--ink);
  border-bottom-color: var(--ink);
}
</style>
