<template>
  <div class="ai-chat-container">
    <el-button type="primary" circle size="large" class="chat-trigger" @click="toggleChat">
      <el-icon><ChatDotRound /></el-icon>
    </el-button>

    <el-card v-if="visible" class="chat-window">
      <template #header>
        <div class="card-header">
          <span>AI 助手</span>
          <el-button link @click="visible = false"><el-icon><Close /></el-icon></el-button>
        </div>
      </template>
      <div class="chat-content" ref="chatContentRef">
        <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
          <div class="bubble">{{ msg.content }}</div>
          <div v-if="msg.references && msg.references.length" class="references">
             <p>参考来源:</p>
             <ul>
               <li v-for="(ref, rIndex) in msg.references" :key="rIndex">
                 <a :href="ref" target="_blank">{{ ref }}</a>
               </li>
             </ul>
          </div>
        </div>
      </div>
      <div class="chat-input">
        <el-input v-model="input" placeholder="请输入问题..." @keyup.enter="send">
          <template #append>
            <el-button @click="send" :loading="loading">发送</el-button>
          </template>
        </el-input>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ChatDotRound, Close } from '@element-plus/icons-vue'
import { chatWithAI } from '../api/ai'

const visible = ref(false)
const input = ref('')
const loading = ref(false)
const messages = ref([
  { role: 'assistant', content: '您好！我是知公AI助手，有什么可以帮您？' }
])
const chatContentRef = ref(null)

const toggleChat = () => {
  visible.value = !visible.value
  if (visible.value) {
    scrollToBottom()
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContentRef.value) {
      chatContentRef.value.scrollTop = chatContentRef.value.scrollHeight
    }
  })
}

const send = async () => {
  if (!input.value.trim()) return
  
  const question = input.value
  messages.value.push({ role: 'user', content: question })
  input.value = ''
  scrollToBottom()
  
  loading.value = true
  try {
    const res = await chatWithAI(question)
    messages.value.push({ 
      role: 'assistant', 
      content: res.answer || '暂无回答',
      references: res.references || []
    })
  } catch (error) {
    messages.value.push({ role: 'assistant', content: '抱歉，遇到了一些问题，请稍后再试。' })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.ai-chat-container {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 1000;
}
.chat-trigger {
  width: 60px;
  height: 60px;
  font-size: 24px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}
.chat-window {
  position: absolute;
  bottom: 80px;
  right: 0;
  width: 350px;
  height: 500px;
  display: flex;
  flex-direction: column;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.message {
  display: flex;
  flex-direction: column;
  max-width: 85%;
}
.message.user {
  align-self: flex-end;
  align-items: flex-end;
}
.message.assistant {
  align-self: flex-start;
  align-items: flex-start;
}
.bubble {
  padding: 8px 12px;
  border-radius: 8px;
  background-color: #f4f4f5;
  word-wrap: break-word;
}
.message.user .bubble {
  background-color: #409EFF;
  color: white;
}
.references {
  font-size: 0.8em;
  margin-top: 5px;
  color: #666;
  width: 100%;
}
.references ul {
  padding-left: 20px;
  margin: 5px 0;
}
.chat-input {
  margin-top: 10px;
}
</style>
