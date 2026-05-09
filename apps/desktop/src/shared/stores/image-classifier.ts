import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDesktopImageClassifierStore = defineStore('desktop-image-classifier', () => {
  const 分类进行中 = ref(false)

  function 设置分类进行中(value: boolean) {
    分类进行中.value = value
  }

  return {
    分类进行中,
    设置分类进行中,
  }
})
