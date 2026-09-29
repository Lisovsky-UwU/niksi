<script setup lang="ts">
import { ref, watch } from 'vue'
import { changeMyPassword, removeMyAvatar, updateMyProfile, uploadMyAvatar } from '../api/users'
import UserAvatar from '../components/UserAvatar.vue'
import { useAuthStore } from '../stores/auth'
import { useBudgetStore } from '../stores/budget'
import type { User } from '../types/models'

const auth = useAuthStore()
const budget = useBudgetStore()

function applyUser(user: User) {
  auth.setUser(user)
  budget.replaceUser(user)
}

// --- name ---
const name = ref(auth.user?.display_name ?? '')
const nameStatus = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')
watch(name, () => {
  if (nameStatus.value !== 'saving') nameStatus.value = 'idle'
})

async function saveName() {
  if (!name.value.trim()) return
  nameStatus.value = 'saving'
  try {
    applyUser(await updateMyProfile(name.value.trim()))
    nameStatus.value = 'saved'
  } catch {
    nameStatus.value = 'error'
  }
}

// --- avatar ---
const fileInput = ref<HTMLInputElement | null>(null)
const avatarBusy = ref(false)
const avatarError = ref('')

// Crops the middle square of the picture and shrinks it to 256×256, so the upload is tiny.
async function toAvatarBlob(file: File): Promise<Blob> {
  const bitmap = await createImageBitmap(file)
  const side = Math.min(bitmap.width, bitmap.height)
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = 256
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('no canvas')
  ctx.drawImage(bitmap, (bitmap.width - side) / 2, (bitmap.height - side) / 2, side, side, 0, 0, 256, 256)
  bitmap.close()
  const encode = (type: string) =>
    new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, type, 0.86))
  // Some browsers cannot encode WebP and quietly return PNG; JPEG is the fallback then.
  const webp = await encode('image/webp')
  if (webp && webp.type === 'image/webp') return webp
  const jpeg = await encode('image/jpeg')
  if (!jpeg) throw new Error('encode failed')
  return jpeg
}

async function handleFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  avatarError.value = ''
  avatarBusy.value = true
  try {
    applyUser(await uploadMyAvatar(await toAvatarBlob(file)))
  } catch {
    avatarError.value = 'Не получилось загрузить фото. Попробуйте другую картинку: JPEG, PNG или WebP.'
  } finally {
    avatarBusy.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

async function removeAvatar() {
  avatarBusy.value = true
  try {
    applyUser(await removeMyAvatar())
  } finally {
    avatarBusy.value = false
  }
}

// --- password ---
const currentPassword = ref('')
const newPassword = ref('')
const repeatPassword = ref('')
const passwordError = ref('')
const passwordSaved = ref(false)
const passwordBusy = ref(false)

async function savePassword() {
  passwordError.value = ''
  passwordSaved.value = false
  if (newPassword.value.length < 8) {
    passwordError.value = 'Новый пароль должен быть не короче 8 символов.'
    return
  }
  if (newPassword.value !== repeatPassword.value) {
    passwordError.value = 'Новый пароль и повтор не совпадают.'
    return
  }
  passwordBusy.value = true
  try {
    await changeMyPassword(currentPassword.value, newPassword.value)
    passwordSaved.value = true
    currentPassword.value = newPassword.value = repeatPassword.value = ''
  } catch {
    passwordError.value = 'Текущий пароль указан неверно.'
  } finally {
    passwordBusy.value = false
  }
}
</script>

<template>
  <div class="settings">
    <h1>Настройки</h1>

    <section class="section" aria-labelledby="profile-title">
      <div class="section-head">
        <h2 id="profile-title">Профиль</h2>
      </div>

      <div class="photo">
        <UserAvatar :user="auth.user" size="lg" />
        <div class="photo-actions">
          <p class="muted hint">
            Фото видно рядом с вашими тратами, доходом и серой зоной. Без фото стоит первая буква имени.
          </p>
          <div class="buttons">
            <button class="btn" type="button" :disabled="avatarBusy" @click="fileInput?.click()">
              {{ auth.user?.avatar_version ? 'Заменить фото' : 'Загрузить фото' }}
            </button>
            <button
              v-if="auth.user?.avatar_version"
              class="btn btn-quiet"
              type="button"
              :disabled="avatarBusy"
              @click="removeAvatar"
            >
              Убрать фото
            </button>
          </div>
          <input
            ref="fileInput"
            class="visually-hidden"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/heic"
            tabindex="-1"
            @change="handleFile"
          />
          <p v-if="avatarError" class="error-text" role="alert">{{ avatarError }}</p>
        </div>
      </div>

      <form class="name-form" @submit.prevent="saveName">
        <label class="field">
          Имя
          <input v-model="name" type="text" maxlength="100" required autocomplete="nickname" />
        </label>
        <button class="btn btn-primary" type="submit" :disabled="nameStatus === 'saving' || !name.trim()">
          Сохранить имя
        </button>
        <p v-if="nameStatus === 'saved'" class="ok" role="status">Имя сохранено.</p>
        <p v-else-if="nameStatus === 'error'" class="error-text" role="alert">Имя не сохранилось. Попробуйте ещё раз.</p>
      </form>

      <p class="muted email">Вход по почте {{ auth.user?.email }}</p>
    </section>

    <section class="section" aria-labelledby="password-title">
      <div class="section-head">
        <h2 id="password-title">Пароль</h2>
      </div>
      <form class="password-form" @submit.prevent="savePassword">
        <label class="field">
          Текущий пароль
          <input v-model="currentPassword" type="password" required autocomplete="current-password" />
        </label>
        <div class="form-grid">
          <label class="field">
            Новый пароль
            <input v-model="newPassword" type="password" required minlength="8" autocomplete="new-password" />
          </label>
          <label class="field">
            Повторите новый
            <input v-model="repeatPassword" type="password" required autocomplete="new-password" />
          </label>
        </div>
        <p class="muted hint">Не короче 8 символов.</p>
        <button class="btn btn-primary submit" type="submit" :disabled="passwordBusy">Сменить пароль</button>
        <p v-if="passwordError" class="error-text" role="alert">{{ passwordError }}</p>
        <p v-else-if="passwordSaved" class="ok" role="status">Пароль изменён. Он понадобится при следующем входе.</p>
      </form>
    </section>
  </div>
</template>

<style scoped>
.settings {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 40rem;
}

h1 {
  padding-top: 0.5rem;
}

.photo {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.photo-actions {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  flex: 1 1 14rem;
  min-width: 0;
}

.buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.hint {
  font-size: 0.875rem;
}

.name-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 0.5rem 0.75rem;
}

.name-form .ok,
.name-form .error-text {
  grid-column: 1 / -1;
}

.email {
  font-size: 0.875rem;
}

.password-form {
  display: grid;
  gap: 0.75rem;
}

.submit {
  justify-self: start;
}

.ok {
  color: var(--green);
  font-size: 0.9rem;
}

@media (max-width: 480px) {
  .name-form {
    grid-template-columns: 1fr;
  }

  .name-form .btn {
    justify-self: start;
  }
}
</style>
