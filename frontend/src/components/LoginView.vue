<template>
  <main class="login-page">
    <form class="login-panel" @submit.prevent="submit">
      <div class="login-brand"><i class="pi pi-map"></i><span>Ortomapas</span></div>
      <h1>Entrar</h1>
      <label for="email">E-mail</label>
      <InputText id="email" v-model="email" type="email" autocomplete="username" required />
      <label for="senha">Senha</label>
      <Password id="senha" v-model="senha" :feedback="false" toggleMask autocomplete="current-password" required />
      <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
      <Button type="submit" label="Entrar" icon="pi pi-sign-in" :loading="loading" />
    </form>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Message from 'primevue/message'
import { login } from '../api/client'

const emit = defineEmits(['authenticated'])
const email = ref('')
const senha = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  loading.value = true; error.value = ''
  try {
    const { data } = await login({ email: email.value, senha: senha.value })
    localStorage.setItem('ortomapas_token', data.access_token)
    localStorage.setItem('ortomapas_user', JSON.stringify(data.usuario))
    emit('authenticated', data.usuario)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Nao foi possivel entrar'
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: grid; place-items: center; background: #11111b; color: #cdd6f4; }
.login-panel { width: min(360px, calc(100vw - 32px)); display: grid; gap: 10px; padding: 28px; border: 1px solid #45475a; background: #1e1e2e; border-radius: 8px; }
.login-brand { display: flex; gap: 8px; align-items: center; color: #4ade80; font-weight: 700; font-size: 1.1rem; }
h1 { font-size: 1.4rem; margin: 4px 0 10px; } label { font-size: .82rem; color: #a6adc8; }
</style>
