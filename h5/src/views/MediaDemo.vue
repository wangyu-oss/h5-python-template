<template>
  <div class="page">
    <div class="card">
      <img v-lazy="'https://dummyimage.com/600x320/1989fa/ffffff&text=lazy'" alt="" class="shot" />
    </div>
    <div class="card">
      <video ref="videoRef" class="player" controls playsinline>
        <source src="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4" type="video/mp4" />
      </video>
      <div class="row rates">
        <span>倍速</span>
        <van-button size="small" @click="setRate(1)">1x</van-button>
        <van-button size="small" @click="setRate(1.5)">1.5x</van-button>
        <van-button size="small" @click="videoRef?.requestFullscreen()">全屏</van-button>
      </div>
    </div>
    <div class="card">
      <audio class="sound" controls src="https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3"></audio>
      <div class="row" style="margin-top: 8px">
        <van-button size="small" type="primary" @click="record">录音</van-button>
        <span class="muted">{{ recordText }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { showToast } from 'vant'

const videoRef = ref<HTMLVideoElement>()
const recordText = ref('')

function setRate(rate: number) {
  if (videoRef.value) videoRef.value.playbackRate = rate
}

async function record() {
  if (!navigator.mediaDevices?.getUserMedia) {
    showToast('当前环境不能录音')
    return
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const recorder = new MediaRecorder(stream)
    recorder.start()
    recordText.value = '录音中，3 秒后停止'
    window.setTimeout(() => {
      recorder.stop()
      stream.getTracks().forEach((track) => track.stop())
      recordText.value = '录音已结束'
    }, 3000)
  } catch {
    showToast('没有获得麦克风权限')
  }
}
</script>

<style scoped>
.shot,
.player,
.sound {
  display: block;
  width: 100%;
  border-radius: 12px;
}

.shot {
  height: 180px;
  object-fit: cover;
}

.player {
  max-height: 220px;
  background: #0f172a;
}

.rates { margin-top: 12px; }

.row { margin-top: 12px; }
</style>
