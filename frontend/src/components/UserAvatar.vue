<script setup lang="ts">
import { computed } from 'vue'
import { avatarUrl } from '../api/users'
import type { User } from '../types/models'

// A person's mark: their photo, or the first letter of their name written by hand
// inside a pen-drawn ring. Each of the two people writes in their own pen colour.
const props = withDefaults(defineProps<{ user: User | null | undefined; size?: 'sm' | 'md' | 'lg' }>(), {
  size: 'md',
})

const url = computed(() => (props.user ? avatarUrl(props.user) : null))
const initial = computed(() => props.user?.display_name.trim().charAt(0).toUpperCase() || '?')
// Lower id writes in ink, the other in the lilac pencil; stable whatever page lists them.
const pen = computed(() => (props.user && props.user.id % 2 === 0 ? 'var(--cat-5)' : 'var(--ink)'))
</script>

<template>
  <span
    class="avatar"
    :class="`is-${size}`"
    :style="{ '--pen': pen }"
    :title="user?.display_name"
    role="img"
    :aria-label="user?.display_name ?? 'Неизвестно'"
  >
    <img v-if="url" :src="url" alt="" loading="lazy" decoding="async" />
    <template v-else>
      <svg class="ring" viewBox="0 0 40 40" aria-hidden="true">
        <!-- Not quite closed and not quite round, like a circle drawn by hand. -->
        <path d="M31.5 8.5C27.8 4.9 21.6 3.3 15.9 5.2 8.6 7.6 4.3 14.8 5.4 22.3c1.1 7.7 8 13.1 15.9 12.7 7.4-.4 13.5-6.1 14.1-13.3.4-4.7-1.2-8.6-4.1-11.7-1.4-1.5-3.3-2.7-5.1-3.5" />
      </svg>
      <span class="letter" aria-hidden="true">{{ initial }}</span>
    </template>
  </span>
</template>

<style scoped>
.avatar {
  position: relative;
  display: inline-grid;
  place-items: center;
  flex: none;
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
  color: var(--pen);
  vertical-align: middle;
}

.is-sm {
  --size: 1.6rem;
}

.is-md {
  --size: 2.25rem;
}

.is-lg {
  --size: 5.5rem;
}

img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 0 0 1.5px var(--pen);
}

.ring {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  fill: color-mix(in srgb, var(--pen) 10%, transparent);
  stroke: currentColor;
  stroke-width: 2.2;
  stroke-linecap: round;
}

.is-lg .ring {
  stroke-width: 1.6;
}

.letter {
  position: relative;
  font-family: var(--font-hand);
  font-weight: 600;
  font-size: calc(var(--size) * 0.62);
  line-height: 1;
  transform: translateY(0.02em);
}
</style>
