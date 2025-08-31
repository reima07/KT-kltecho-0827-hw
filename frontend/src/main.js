import Vue from 'vue'
import App from './App.vue'
import { initTelemetry } from './telemetry.js'

Vue.config.productionTip = false

// OpenTelemetry 초기화
initTelemetry()

new Vue({
  render: h => h(App)
}).$mount('#app') 