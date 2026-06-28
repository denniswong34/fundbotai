<template>
  <div>
    <v-row>
      <v-col cols="12" class="d-flex align-center justify-space-between">
        <h2 class="text-h4 font-weight-bold">{{ $t('nav.brokers') }}</h2>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="showAddDialog = true">
          {{ $t('common.add_broker') }}
        </v-btn>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col v-if="loading" cols="12" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" />
      </v-col>
      <v-col v-else-if="connections.length === 0" cols="12" class="text-center py-8">
        <v-icon size="64" color="text-disabled" class="mb-4">mdi-link-variant-off</v-icon>
        <div class="text-h6 text-medium-emphasis">{{ $t('common.no_data') }}</div>
      </v-col>
      <v-col v-for="conn in connections" :key="conn.id" cols="12" md="6" lg="4">
        <v-card class="glass-card" elevation="0">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" :color="conn.is_connected ? 'success' : 'error'">
              mdi-circle
            </v-icon>
            <span class="font-weight-bold">{{ conn.name }}</span>
            <v-spacer />
            <v-chip size="x-small" variant="flat" :color="conn.is_connected ? 'success' : 'error'">
              {{ conn.is_connected ? $t('common.connected') : $t('common.disconnected') }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">{{ $t('common.type') }}</div>
                <div>{{ conn.broker_type }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis">{{ $t('common.market') }}</div>
                <div>{{ conn.market_type }}</div>
              </v-col>
            </v-row>
            <v-row class="mt-2">
              <v-col cols="12" v-if="conn.last_connected_at">
                <div class="text-caption text-medium-emphasis">{{ $t('common.last_connected') }}</div>
                <div class="text-body-2">{{ formatDate(conn.last_connected_at) }}</div>
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions>
            <v-btn size="small" variant="outlined" color="primary" @click="testConnection(conn)" :loading="testingId === conn.id">
              <v-icon left>mdi-flash</v-icon>
              {{ $t('common.test_connection') }}
            </v-btn>
            <v-spacer />
            <v-btn icon size="small" variant="text" color="error" @click="confirmDelete(conn)">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <AddBrokerDialog v-model="showAddDialog" @created="loadConnections" />

    <!-- Delete Confirm -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card class="glass-card">
        <v-card-title>{{ $t('common.delete') }}</v-card-title>
        <v-card-text>
          {{ $t('common.confirm_delete') }} "{{ deleting?.name }}"?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="error" @click="doDelete">{{ $t('common.delete') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import brokerApi from '@/services/brokerApi'
import AddBrokerDialog from '@/components/broker/AddBrokerDialog.vue'

const connections = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const testingId = ref(null)
const deleteDialog = ref(false)
const deleting = ref(null)

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

async function loadConnections() {
  loading.value = true
  try {
    const res = await brokerApi.list()
    connections.value = res.data
  } finally {
    loading.value = false
  }
}

async function testConnection(conn) {
  testingId.value = conn.id
  try {
    await brokerApi.test(conn.id)
    await loadConnections()
  } finally {
    testingId.value = null
  }
}

function confirmDelete(conn) {
  deleting.value = conn
  deleteDialog.value = true
}

async function doDelete() {
  if (!deleting.value) return
  try {
    await brokerApi.delete(deleting.value.id)
    connections.value = connections.value.filter((c) => c.id !== deleting.value.id)
  } finally {
    deleteDialog.value = false
    deleting.value = null
  }
}

onMounted(() => {
  loadConnections()
})
</script>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.03) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  transition: transform 0.2s;
}
.glass-card:hover {
  transform: translateY(-2px);
}
</style>
