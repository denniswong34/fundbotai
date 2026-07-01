<template>
  <div>
    <h2 class="text-h4 font-weight-bold mb-6">{{ $t('org.title') }}</h2>

    <v-row>
      <v-col cols="12" md="6">
        <v-card class="glass-card mb-6" elevation="0">
          <v-card-title>{{ $t('org.org_info') }}</v-card-title>
          <v-card-text v-if="auth.organization">
            <v-row>
              <v-col cols="4" class="text-medium-emphasis">{{ $t('common.name') }}:</v-col>
              <v-col cols="8" class="font-weight-bold">{{ auth.organization.name }}</v-col>
            </v-row>
            <v-row>
              <v-col cols="4" class="text-medium-emphasis">{{ $t('common.slug') }}:</v-col>
              <v-col cols="8">{{ auth.organization.slug }}</v-col>
            </v-row>
            <v-row>
              <v-col cols="4" class="text-medium-emphasis">{{ $t('org.role') }}:</v-col>
              <v-col cols="8">
                <v-chip size="x-small" variant="flat" color="primary">
                  {{ auth.organization.role }}
                </v-chip>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center">
            {{ $t('org.members') }}
            <v-spacer />
            <v-btn
              v-if="isAdmin"
              size="small"
              color="primary"
              prepend-icon="mdi-account-plus"
              @click="showInvite = true"
            >
              {{ $t('org.invite') }}
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-list v-if="members.length > 0" density="compact">
              <v-list-item
                v-for="m in members"
                :key="m.id"
                class="rounded-lg mb-1"
              >
                <template v-slot:prepend>
                  <v-avatar color="primary" size="32">
                    <span class="text-body-2">{{ (m.username || '?')[0].toUpperCase() }}</span>
                  </v-avatar>
                </template>
                <v-list-item-title>{{ m.username || 'Unknown' }}</v-list-item-title>
                <v-list-item-subtitle>{{ m.email || '' }}</v-list-item-subtitle>
                <template v-slot:append>
                  <v-chip size="x-small" variant="flat" :color="roleColor(m.role)">
                    {{ $t('org.' + m.role) }}
                  </v-chip>
                  <v-btn
                    v-if="isAdmin && m.role !== 'owner'"
                    icon
                    size="x-small"
                    variant="text"
                    color="error"
                    @click="removeMember(m)"
                    class="ml-2"
                  >
                    <v-icon small>mdi-close</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-medium-emphasis text-center py-4">
              {{ $t('common.loading') }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Invite Dialog -->
    <v-dialog v-model="showInvite" max-width="400">
      <v-card class="glass-card">
        <v-card-title>{{ $t('org.invite') }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="inviteUsername"
            :label="$t('auth.username')"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
          <v-select
            v-model="inviteRole"
            :label="$t('org.role')"
            :items="['member', 'admin']"
            variant="outlined"
            density="compact"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showInvite = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" :loading="inviting" @click="doInvite">{{ $t('org.invite') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import axios from 'axios'

const auth = useAuthStore()

const members = ref([])
const showInvite = ref(false)
const inviteUsername = ref('')
const inviteRole = ref('member')
const inviting = ref(false)

const isAdmin = computed(() => {
  return auth.organization?.role === 'owner' || auth.organization?.role === 'admin'
})

function roleColor(role) {
  const colors = { owner: 'warning', admin: 'primary', member: 'success' }
  return colors[role] || 'grey'
}

async function loadMembers() {
  if (!auth.organization?.id) return
  try {
    const token = localStorage.getItem('access_token')
    const res = await axios.get(`/api/orgs/${auth.organization.id}/members`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    members.value = res.data
  } catch {
    members.value = []
  }
}

async function doInvite() {
  inviting.value = true
  try {
    const token = localStorage.getItem('access_token')
    await axios.post(
      `/api/orgs/${auth.organization.id}/members`,
      { username: inviteUsername.value, role: inviteRole.value },
      { headers: { Authorization: `Bearer ${token}` } },
    )
    showInvite.value = false
    inviteUsername.value = ''
    await loadMembers()
  } finally {
    inviting.value = false
  }
}

async function removeMember(m) {
  try {
    const token = localStorage.getItem('access_token')
    await axios.delete(`/api/orgs/${auth.organization.id}/members/${m.user_id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    await loadMembers()
  } catch {
    // handle error
  }
}

onMounted(() => {
  loadMembers()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}
</style>
