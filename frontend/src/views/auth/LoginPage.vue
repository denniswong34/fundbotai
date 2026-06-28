<template>
  <v-row justify="center" align="center" class="fill-height">
    <v-col cols="12" sm="8" md="5" lg="4">
      <v-card class="glass-card pa-6" elevation="0">
        <v-card-title class="text-center pa-0 mb-6">
          <v-icon size="48" color="primary" class="mb-2">mdi-finance</v-icon>
          <div class="text-h4 font-weight-bold">{{ $t('common.app_name') }}</div>
          <div class="text-body-2 text-medium-emphasis">{{ $t('auth.login_subtitle') }}</div>
        </v-card-title>

        <v-card-text class="pa-0">
          <!-- Tab Toggle -->
          <v-tabs v-model="tab" color="primary" align-tabs="center" class="mb-4">
            <v-tab value="login">{{ $t('common.login') }}</v-tab>
            <v-tab value="register">{{ $t('auth.register_title') }}</v-tab>
          </v-tabs>

          <!-- Login Form -->
          <v-window v-model="tab">
            <v-window-item value="login">
              <v-form ref="loginForm" @submit.prevent="handleLogin">
                <v-text-field
                  v-model="loginData.username"
                  :label="$t('auth.username')"
                  :rules="[v => !!v || 'Username is required']"
                  variant="outlined"
                  density="compact"
                  class="mb-3"
                />
                <v-text-field
                  v-model="loginData.password"
                  :label="$t('auth.password')"
                  type="password"
                  :rules="[v => !!v || 'Password is required']"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-btn
                  color="primary"
                  size="large"
                  block
                  type="submit"
                  :loading="auth.loading"
                >
                  {{ $t('common.login') }}
                </v-btn>
              </v-form>
            </v-window-item>

            <!-- Register Form -->
            <v-window-item value="register">
              <v-form ref="registerForm" @submit.prevent="handleRegister">
                <v-text-field
                  v-model="registerData.username"
                  :label="$t('auth.username')"
                  :rules="[v => !!v || 'Username is required']"
                  variant="outlined"
                  density="compact"
                  class="mb-3"
                />
                <v-text-field
                  v-model="registerData.email"
                  :label="$t('auth.email')"
                  type="email"
                  :rules="[v => !!v || 'Email is required']"
                  variant="outlined"
                  density="compact"
                  class="mb-3"
                />
                <v-text-field
                  v-model="registerData.password"
                  :label="$t('auth.password')"
                  type="password"
                  :rules="[v => !!v || 'Password is required', v => v.length >= 6 || 'Min 6 characters']"
                  variant="outlined"
                  density="compact"
                  class="mb-3"
                />
                <v-text-field
                  v-model="registerData.confirm"
                  :label="$t('common.confirm_password')"
                  type="password"
                  :rules="[v => v === registerData.password || 'Passwords must match']"
                  variant="outlined"
                  density="compact"
                  class="mb-4"
                />
                <v-btn
                  color="primary"
                  size="large"
                  block
                  type="submit"
                  :loading="auth.loading"
                >
                  {{ $t('auth.register_title') }}
                </v-btn>
              </v-form>
            </v-window-item>
          </v-window>

          <v-alert
            v-if="errorMsg"
            :text="errorMsg"
            type="error"
            variant="tonal"
            closable
            class="mt-4"
            @click:close="errorMsg = ''"
          />
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'

const auth = useAuthStore()
const router = useRouter()

const tab = ref('login')
const errorMsg = ref('')

const loginData = ref({ username: '', password: '' })
const registerData = ref({ username: '', email: '', password: '', confirm: '' })

async function handleLogin() {
  errorMsg.value = ''
  try {
    await auth.login(loginData.value.username, loginData.value.password)
    router.push('/')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Login failed'
  }
}

async function handleRegister() {
  errorMsg.value = ''
  try {
    await auth.register(
      registerData.value.username,
      registerData.value.email,
      registerData.value.password,
    )
    router.push('/')
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || 'Registration failed'
  }
}
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}
.fill-height {
  min-height: calc(100vh - 64px);
}
</style>
