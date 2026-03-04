<template>
  <VContainer fluid class="control-page py-10">
    <VRow justify="center" class="mt-6">
      <VCol cols="12" sm="10" md="6" lg="4">
        <VCard elevation="2" class="pa-8 text-center">
          <VCardTitle class="justify-center text-h5">Combination</VCardTitle>
          <VCardSubtitle class="pb-6">Enter your four digit passcode</VCardSubtitle>

          <div class="otp-row">
            <VTextField
              v-for="(_, index) in digits"
              :key="index"
              :ref="(el) => setInputRef(el, index)"
              :model-value="digits[index]"
              type="text"
              inputmode="numeric"
              maxlength="1"
              variant="outlined"
              density="comfortable"
              hide-details
              class="otp-input"
              @update:model-value="onDigitInput(index, $event)"
              @keydown="onDigitKeydown(index, $event)"
              @paste="onPaste(index, $event)"
            />
          </div>

          <VBtn
            class="mt-6"
            color="primary"
            size="small"
            :loading="submitting"
            :disabled="!canSubmit"
            @click="submitPasscode"
          >
            SUBMIT
          </VBtn>
        </VCard>
      </VCol>
    </VRow>

    <VSnackbar v-model="snackbar.show" :color="snackbar.color" timeout="3200">
      {{ snackbar.message }}
    </VSnackbar>
  </VContainer>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import axios from 'axios'

const digits = ref(['', '', '', ''])
const inputRefs = ref([])
const submitting = ref(false)
const snackbar = ref({ show: false, color: 'success', message: '' })

const showMessage = (message, color = 'success') => {
  snackbar.value = { show: true, color, message }
}

const setInputRef = (el, index) => {
  if (el) inputRefs.value[index] = el
}

const focusInput = (index) => {
  const field = inputRefs.value[index]
  if (field && typeof field.focus === 'function') {
    field.focus()
  }
}

const normalizeDigit = (value) => String(value ?? '').replace(/\D/g, '').slice(-1)

const onDigitInput = (index, value) => {
  const digit = normalizeDigit(value)
  digits.value[index] = digit
  if (digit && index < digits.value.length - 1) {
    nextTick(() => focusInput(index + 1))
  }
}

const onPaste = (index, event) => {
  event.preventDefault()
  const text = (event.clipboardData?.getData('text') ?? '').replace(/\D/g, '')
  if (!text) return

  const chars = text.slice(0, digits.value.length - index).split('')
  chars.forEach((char, offset) => {
    digits.value[index + offset] = char
  })

  const last = Math.min(index + chars.length - 1, digits.value.length - 1)
  nextTick(() => focusInput(last))
}

const onDigitKeydown = (index, event) => {
  if (event.key === 'Backspace') {
    if (digits.value[index]) {
      digits.value[index] = ''
      event.preventDefault()
      return
    }
    if (index > 0) {
      event.preventDefault()
      nextTick(() => focusInput(index - 1))
    }
    return
  }

  if (event.key === 'ArrowLeft' && index > 0) {
    event.preventDefault()
    nextTick(() => focusInput(index - 1))
    return
  }

  if (event.key === 'ArrowRight' && index < digits.value.length - 1) {
    event.preventDefault()
    nextTick(() => focusInput(index + 1))
  }
}

const passcode = computed(() => digits.value.join(''))
const canSubmit = computed(() => digits.value.every((digit) => /^\d$/.test(digit)))

const clearInputs = () => {
  digits.value = ['', '', '', '']
  nextTick(() => focusInput(0))
}

onMounted(() => {
  nextTick(() => focusInput(0))
})

const submitPasscode = async () => {
  if (!canSubmit.value) return

  const code = passcode.value
  submitting.value = true
  try {
    const form = new URLSearchParams()
    form.append('passcode', code)
    const response = await axios.post('/api/set/combination', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    showMessage(response.data?.message ?? `Passcode submitted: ${code}`, 'success')
    clearInputs()
  } catch (error) {
    const message = error?.response?.data?.message ?? error?.message ?? 'Request failed'
    showMessage(message, 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.control-page {
  min-height: calc(100vh - 130px);
  background: #f7f8fa;
}

.otp-row {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.otp-input {
  max-width: 64px;
}

:deep(.otp-input .v-field) {
  border-radius: 10px;
}

:deep(.otp-input .v-field__input) {
  min-height: 56px;
  text-align: center;
  justify-content: center;
  font-size: 1.35rem;
  font-weight: 600;
  padding-inline: 0;
}
</style>
