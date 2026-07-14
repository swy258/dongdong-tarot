import { defineStore } from 'pinia'
import { ref } from 'vue'
import { readingsAPI } from '../api'

export const useReadingsStore = defineStore('readings', () => {
  const currentReading = ref(null)
  const history = ref([])
  const total = ref(0)
  const interpretStream = ref('')

  const createReading = async (data) => {
    const { data: result } = await readingsAPI.create(data)
    currentReading.value = result
    return result
  }

  const streamInterpret = async (readingId, onChunk, onDone, onError) => {
    try {
      const response = await readingsAPI.interpret(readingId)
      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        fullText += chunk
        interpretStream.value = fullText
        if (onChunk) onChunk(chunk, fullText)
      }
      if (onDone) onDone(fullText)
      return fullText
    } catch (err) {
      if (onError) onError(err)
      throw err
    }
  }

  const fetchReading = async (id) => {
    const { data } = await readingsAPI.getOne(id)
    currentReading.value = data
    return data
  }

  const fetchSharedReading = async (shareCode) => {
    const { data } = await readingsAPI.getShared(shareCode)
    return data
  }

  const fetchHistory = async (page = 0, limit = 20) => {
    const { data } = await readingsAPI.getHistory({ skip: page * limit, limit })
    history.value = data.readings
    total.value = data.total
    return data
  }

  return {
    currentReading,
    history,
    total,
    interpretStream,
    createReading,
    streamInterpret,
    fetchReading,
    fetchSharedReading,
    fetchHistory,
  }
})
