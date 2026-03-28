<script setup lang="ts">
import { ElButton, ElForm, ElFormItem, ElInput, ElMessage, ElAlert } from 'element-plus'
import { ref, watch } from 'vue'
import { requestLinkExchange } from '../features/links/api'
import { getApiErrorMessage } from '../utils/api'
import BaseDialog from './BaseDialog.vue'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const visible = ref(props.modelValue)
const loading = ref(false)

const form = ref({
  name: '',
  url: '',
  description: '',
  logo_url: '',
  contact_email: '',
  contact_name: '',
  my_site_url: '',
})

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function resetForm() {
  form.value = {
    name: '',
    url: '',
    description: '',
    logo_url: '',
    contact_email: '',
    contact_name: '',
    my_site_url: '',
  }
}

async function submit() {
  if (!form.value.name.trim()) {
    ElMessage.warning('请填写网站名称')
    return
  }
  if (!form.value.url.trim()) {
    ElMessage.warning('请填写网站链接')
    return
  }
  if (!form.value.my_site_url.trim()) {
    ElMessage.warning('请填写您的网站链接')
    return
  }

  // 确保 URL 以 http:// 或 https:// 开头
  let url = form.value.url.trim()
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url
  }
  let mySiteUrl = form.value.my_site_url.trim()
  if (!mySiteUrl.startsWith('http://') && !mySiteUrl.startsWith('https://')) {
    mySiteUrl = 'https://' + mySiteUrl
  }

  loading.value = true
  try {
    const data = await requestLinkExchange({
      ...form.value,
      url,
      my_site_url: mySiteUrl,
    })
    ElMessage.success(data.message)
    resetForm()
    visible.value = false
    emit('success')
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error, '申请失败'))
  } finally {
    loading.value = false
  }
}

function close() {
  visible.value = false
}
</script>

<template>
  <BaseDialog
    v-model="visible"
    title="申请友情链接"
    width="500px"
    :close-on-click-modal="false"
    @closed="resetForm"
  >
    <ElAlert
      type="info"
      :closable="false"
      style="margin-bottom: 16px"
    >
      <template #title>
        <div style="line-height: 1.6">
          <strong>自动交换规则：</strong><br>
          如果您的网站已添加本站链接，系统将自动添加。<br>
          否则需要等待手动添加（不知道能否成功，还没测试）。
        </div>
      </template>
    </ElAlert>

    <ElForm label-position="top">
      <ElFormItem label="网站名称 *">
        <ElInput
          v-model="form.name"
          placeholder="您的网站名称"
          maxlength="100"
          show-word-limit
        />
      </ElFormItem>

      <ElFormItem label="网站链接 *">
        <ElInput
          v-model="form.url"
          placeholder="https://example.com"
          maxlength="500"
        />
      </ElFormItem>

      <ElFormItem label="网站描述">
        <ElInput
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="简单描述您的网站"
          maxlength="200"
          show-word-limit
        />
      </ElFormItem>

      <ElFormItem label="Logo 链接">
        <ElInput
          v-model="form.logo_url"
          placeholder="https://example.com/logo.png（可选）"
          maxlength="500"
        />
      </ElFormItem>

      <ElFormItem label="您的网站链接 *（用于自动检测）">
        <ElInput
          v-model="form.my_site_url"
          placeholder="https://yoursite.com"
          maxlength="500"
        />
        <template #description>
          请填写包含本站链接的页面地址，系统将自动检测
        </template>
      </ElFormItem>

      <ElFormItem label="联系人名称">
        <ElInput
          v-model="form.contact_name"
          placeholder="您的称呼（可选）"
          maxlength="100"
        />
      </ElFormItem>

      <ElFormItem label="联系邮箱">
        <ElInput
          v-model="form.contact_email"
          placeholder="your@email.com（可选）"
          maxlength="255"
        />
      </ElFormItem>
    </ElForm>

    <template #footer>
      <ElButton @click="close">取消</ElButton>
      <ElButton type="primary" :loading="loading" @click="submit">
        提交申请
      </ElButton>
    </template>
  </BaseDialog>
</template>
