<template>
  <VContainer fluid>
    <VRow>
      <!-- LEFT: Height(in) bar -->
      <VCol cols="12" md="3">
        <VCard class="pa-4" elevation="1">
          <div class="text-subtitle-1 font-weight-medium text-center mb-3">Height(in)</div>

          <div class="tank-wrap">
            <div class="tank">
              <div class="tank-fill" :style="{ height: heightPct + '%' }"></div>

              <!-- marker + label -->
              <div class="tank-marker" :style="{ bottom: heightPct + '%' }">
                <div class="tank-bubble"></div>
                <div class="tank-label">{{ waterheight.toFixed(1) }}</div>
              </div>
            </div>
          </div>

          <div class="text-caption text-center mt-2">Height(in)</div>
        </VCard>
      </VCol>

      <!-- RIGHT: charts -->
      <VCol cols="12" md="9">
        <VRow>
          <!-- TOP: Area chart -->
          <VCol cols="12">
            <VCard class="pa-3" elevation="1">
              <div class="d-flex align-center justify-space-between mb-2">
                <div class="text-subtitle-1 font-weight-medium">Water Reserves(10 min)</div>
                <VIcon icon="mdi:mdi-menu" size="small" class="text-medium-emphasis" />
              </div>

              <highcharts :options="areaOptions" />
            </VCard>
          </VCol>

          <!-- BOTTOM LEFT: Gauge -->
          <VCol cols="12" md="6">
            <VCard class="pa-3" elevation="1">
              <div class="d-flex align-center justify-space-between mb-2">
                <div class="text-subtitle-1 font-weight-medium">Water Reserves</div>
                <VIcon icon="mdi:mdi-menu" size="small" class="text-medium-emphasis" />
              </div>

              <highcharts :options="gaugeOptions" />

              <div class="text-center mt-2 text-subtitle-2 font-weight-medium">
                {{ reserve.toFixed(0) }} Gal
              </div>
            </VCard>
          </VCol>

          <!-- BOTTOM RIGHT: Donut -->
          <VCol cols="12" md="6">
            <VCard class="pa-3" elevation="1">
              <div class="text-subtitle-1 font-weight-medium">Water Level</div>
              <div class="text-caption text-medium-emphasis mb-2">Capacity Remaining</div>

              <highcharts :options="donutOptions" />
            </VCard>
          </VCol>
        </VRow>
      </VCol>
    </VRow>
  </VContainer>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useMqttStore } from "@/store/mqttStore";

import HC from "highcharts";
import HighchartsMore from "highcharts/highcharts-more";

// enable gauge support
HighchartsMore(HC);

// --- Lab constants ---
const MAX_WATER_HEIGHT_IN = 77.763; // lab tank max water height
const MAX_RESERVE_GAL = 1000;

// --- MQTT store ---
const mqttStore = useMqttStore();
const { payload } = storeToRefs(mqttStore);

// --- Derived live values (defaults) ---
const waterheight = computed(() => Number(payload.value?.waterheight ?? 0));
const reserve = computed(() => Number(payload.value?.reserve ?? 0));
const percentage = computed(() => Number(payload.value?.percentage ?? 0));

// clamp helper
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

const heightPct = computed(() => {
  const pct = (waterheight.value / MAX_WATER_HEIGHT_IN) * 100;
  return clamp(pct, 0, 100);
});

const pctDisplay = computed(() => clamp(percentage.value, 0, 100));

// --- Rolling 10-min reserve series ---
const seriesData = ref([]); // holds [ms, reserve]

function addPoint(tsSec, reserveVal) {
  const tms = Number(tsSec) ? Number(tsSec) * 1000 : Date.now();
  const y = Number(reserveVal);

  if (!Number.isFinite(y)) return;

  seriesData.value.push([tms, y]);

  // prune to last 10 minutes by time
  const cutoff = Date.now() - 10 * 60 * 1000;
  while (seriesData.value.length > 0 && seriesData.value[0][0] < cutoff) {
    seriesData.value.shift();
  }

  // also cap points (safety)
  if (seriesData.value.length > 700) {
    seriesData.value.splice(0, seriesData.value.length - 700);
  }
}

// Watch MQTT payload and update series
watch(
  payload,
  (p) => {
    if (!p) return;
    addPoint(p.timestamp, p.reserve);
  },
  { deep: true }
);

// --- Connect MQTT on mount ---
onMounted(() => {
  try {
    mqttStore.connect();
    setTimeout(() => {
      mqttStore.subscribe("elet2415/radar");
    }, 500);
  } catch (e) {
    // keep silent; dashboard should still render
    console.log("MQTT connect/subscribe failed:", e);
  }
});

onBeforeUnmount(() => {
  try {
    mqttStore.unsubcribe("elet2415/radar");
  } catch (e) {
    // no-op
  }
});

// --- Highcharts options ---
const areaOptions = computed(() => ({
  chart: {
    type: "area",
    height: 300,
    animation: false,
  },
  title: { text: null },
  credits: { enabled: true },
  legend: { enabled: true },
  xAxis: {
    type: "datetime",
    title: { text: "Time" },
  },
  yAxis: {
    min: 0,
    max: MAX_RESERVE_GAL,
    title: { text: "Water level (Gal)" },
  },
  tooltip: {
    xDateFormat: "%H:%M:%S",
    pointFormat: "<b>{point.y:.0f} Gal</b>",
  },
  plotOptions: {
    area: {
      marker: { enabled: false },
    },
    series: { animation: false },
  },
  series: [
    {
      name: "Water",
      data: seriesData.value,
    },
  ],
}));

const gaugeOptions = computed(() => ({
  chart: {
    type: "gauge",
    height: 240,
    animation: false,
  },
  title: { text: null },
  credits: { enabled: true },
  pane: {
    startAngle: -90,
    endAngle: 90,
    background: null,
    center: ["50%", "75%"],
    size: "110%",
  },
  yAxis: {
    min: 0,
    max: MAX_RESERVE_GAL,
    tickInterval: 100,
    tickPosition: "inside",
    tickLength: 10,
    tickWidth: 1,
    minorTickInterval: null,
    labels: { distance: 15 },
    plotBands: [
      { from: 0, to: 200, color: "#d9534f" },   // red
      { from: 200, to: 600, color: "#f0ad4e" }, // yellow
      { from: 600, to: 1000, color: "#5cb85c" } // green
    ],
    title: { text: null },
  },
  series: [
    {
      name: "Reserve",
      data: [clamp(reserve.value, 0, MAX_RESERVE_GAL)],
      tooltip: { valueSuffix: " Gal" },
      dataLabels: {
        enabled: false,
      },
    },
  ],
}));

const donutOptions = computed(() => ({
  chart: {
    type: "pie",
    height: 240,
    animation: false,
  },
  title: {
    text: `${pctDisplay.value.toFixed(0)}%`,
    align: "center",
    verticalAlign: "middle",
    y: 10,
    style: { fontSize: "34px", fontWeight: "700" },
  },
  credits: { enabled: true },
  tooltip: { pointFormat: "<b>{point.y:.0f}%</b>" },
  plotOptions: {
    pie: {
      innerSize: "70%",
      dataLabels: { enabled: false },
      borderWidth: 0,
    },
    series: { animation: false },
  },
  series: [
    {
      name: "Capacity",
      data: [
        { name: "Remaining", y: pctDisplay.value },
        { name: "Used", y: 100 - pctDisplay.value },
      ],
    },
  ],
}));
</script>

<style scoped>
/* Simple tank look to match lab */
.tank-wrap {
  display: flex;
  justify-content: center;
  padding: 8px 0 4px;
}

.tank {
  position: relative;
  width: 90px;
  height: 520px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 50px;
  background: rgba(0, 0, 0, 0.02);
  overflow: hidden;
}

.tank-fill {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  background: #54b948; /* green */
  transition: height 250ms ease;
}

.tank-marker {
  position: absolute;
  left: 8px;
  transform: translateY(50%);
  display: flex;
  align-items: center;
  gap: 8px;
}

.tank-bubble {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #3c8d2f;
}

.tank-label {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.65);
  color: white;
}
</style>
