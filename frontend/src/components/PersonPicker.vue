<script setup lang="ts">
import type { User } from '../types/models'
import UserAvatar from './UserAvatar.vue'

// Choose one of the two people: their avatar and name as a pair of radio buttons.
const model = defineModel<number | null>({ required: true })
defineProps<{ users: User[]; label: string; name: string; meId?: number | null }>()
</script>

<template>
  <fieldset class="people">
    <legend class="legend">{{ label }}</legend>
    <label v-for="user in users" :key="user.id" class="person">
      <input v-model="model" type="radio" :name="name" :value="user.id" />
      <span class="face">
        <UserAvatar :user="user" size="sm" />
        {{ user.id === meId ? 'Я' : user.display_name }}
      </span>
    </label>
  </fieldset>
</template>

<style scoped>
.people {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
  padding: 0;
  border: none;
  min-width: 0;
}

.legend {
  float: left;
  margin-right: 0.35rem;
  padding: 0;
  font-size: 0.875rem;
  color: var(--muted);
}

.person input {
  position: absolute;
  opacity: 0;
  width: 1px;
  height: 1px;
}

.face {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.2rem 0.75rem 0.2rem 0.25rem;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--sheet);
  font-size: 0.9rem;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.15s, border-color 0.15s, box-shadow 0.15s;
}

.face:hover {
  opacity: 1;
}

.person input:checked + .face {
  opacity: 1;
  border-color: var(--ink);
  box-shadow: 0 0 0 1px var(--ink);
  font-weight: 600;
}

.person input:focus-visible + .face {
  outline: 2px solid var(--ink);
  outline-offset: 2px;
}
</style>
