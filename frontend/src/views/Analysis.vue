<template>
  <VContainer fluid class="py-4">
    <VRow>
      <VCol cols="12" md="4">
        <VCard elevation="2" class="pa-4">
          <VTextField v-model="startDate" type="date" label="Start Date" />
          <VTextField v-model="endDate" type="date" label="End Date" />
          <VBtn color="primary" :loading="running" @click="runAnalysis">Analyze</VBtn>
          <div v-if="errorMessage" class="text-error text-caption mt-3">{{ errorMessage }}</div>
        </VCard>
      </VCol>

      <VCol cols="12" md="8">
        <VCard elevation="2" class="average-card pa-6">
          <div class="average-title">Average</div>
          <div class="average-subtitle">For the selected period</div>
          <div class="average-value">
            {{ averageLabel }} <span class="average-unit">Gal</span>
          </div>
        </VCard>
      </VCol>

      <VCol cols="12">
        <VCard elevation="2" class="pa-2">
          <highcharts :options="lineOptions" />
        </VCard>
      </VCol>

      <VCol cols="12">
        <VCard elevation="2" class="pa-2">
          <highcharts :options="scatterOptions" />
        </VCard>
      </VCol>
    </VRow>
  </VContainer>
</template>

<script setup>
import { computed, ref } from 'vue'
import axios from 'axios'

const today = new Date().toISOString().slice(0, 10)

const startDate = ref(today)
const endDate = ref(today)
const running = ref(false)
const errorMessage = ref('')
const average = ref(0)
const reserveSeries = ref([])
const correlationSeries = ref([])

const toNumberOrNull = (value) => {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

const toUtcEpochStart = (dateValue) => Math.floor(Date.parse(`${dateValue}T00:00:00Z`) / 1000)
const toUtcEpochEnd = (dateValue) => Math.floor(Date.parse(`${dateValue}T23:59:59Z`) / 1000)

const averageLabel = computed(() => Number(average.value || 0).toFixed(2))

const lineOptions = computed(() => ({
  chart: { type: 'line', height: 320, zoomType: 'x' },
  title: { text: 'Water Management Analysis', align: 'left' },
  xAxis: { type: 'datetime' },
  yAxis: { title: { text: 'Water Reserves (Gal)' } },
  legend: { enabled: false },
  credits: { enabled: false },
  series: [{ name: 'Reserve', data: reserveSeries.value }],
}))

const scatterOptions = computed(() => ({
  chart: { type: 'scatter', height: 320, zoomType: 'xy' },
  title: { text: 'Height and Water Level Correlation Analysis', align: 'left' },
  xAxis: { title: { text: 'Water Height' } },
  yAxis: { title: { text: 'Height' } },
  legend: { enabled: false },
  credits: { enabled: false },
  series: [{ name: 'Samples', data: correlationSeries.value }],
}))

const runAnalysis = async () => {
  errorMessage.value = ''

  if (!startDate.value || !endDate.value) {
    errorMessage.value = 'Start Date and End Date are required.'
    return
  }

  const startEpoch = toUtcEpochStart(startDate.value)
  const endEpoch = toUtcEpochEnd(endDate.value)

  if (!Number.isFinite(startEpoch) || !Number.isFinite(endEpoch) || startEpoch > endEpoch) {
    errorMessage.value = 'Invalid date range.'
    return
  }

  running.value = true
  try {
    const [reserveResponse, averageResponse] = await Promise.all([
      axios.get(`/api/reserve/${startEpoch}/${endEpoch}`),
      axios.get(`/api/avg/${startEpoch}/${endEpoch}`),
    ])

    const docs = Array.isArray(reserveResponse.data?.data) ? reserveResponse.data.data : []
    const avgValue = toNumberOrNull(averageResponse.data?.data)

    average.value = avgValue ?? 0
    reserveSeries.value = docs
      .map((doc) => [toNumberOrNull(doc.timestamp), toNumberOrNull(doc.reserve)])
      .filter((point) => point[0] !== null && point[1] !== null)
      .map((point) => [point[0] * 1000, point[1]])

    correlationSeries.value = docs
      .map((doc) => [toNumberOrNull(doc.waterheight), toNumberOrNull(doc.radar)])
      .filter((point) => point[0] !== null && point[1] !== null)
  } catch (error) {
    reserveSeries.value = []
    correlationSeries.value = []
    average.value = 0
    errorMessage.value = 'Unable to analyze the selected period.'
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.average-card {
  min-height: 170px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.average-title {
  font-size: 1.5rem;
  font-weight: 600;
}

.average-subtitle {
  font-size: 1rem;
  opacity: 0.8;
}

.average-value {
  margin-top: 8px;
  font-size: 2.6rem;
  font-weight: 700;
  line-height: 1;
}

.average-unit {
  font-size: 1.2rem;
  font-weight: 500;
}
</style>
