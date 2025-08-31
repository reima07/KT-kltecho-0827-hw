<template>
  <div id="app">
    <h1>K8s 마이크로서비스 데모</h1>
    
    <!-- 로그인/회원가입 섹션 -->
    <div class="section" v-if="!isLoggedIn">
      <div v-if="!showRegister">
        <h2>로그인</h2>
        <input v-model="username" placeholder="사용자명">
        <input v-model="password" type="password" placeholder="비밀번호">
        <button @click="login" @click.native="trackUserAction('login_button_click')">로그인</button>
        <button @click="showRegister = true" @click.native="trackUserAction('register_button_click')" class="register-btn">회원가입</button>
      </div>
      <div v-else>
        <h2>회원가입</h2>
        <input v-model="registerUsername" placeholder="사용자명">
        <input v-model="registerPassword" type="password" placeholder="비밀번호">
        <input v-model="confirmPassword" type="password" placeholder="비밀번호 확인">
        <button @click="register" @click.native="trackUserAction('register_submit')">가입하기</button>
        <button @click="showRegister = false" @click.native="trackUserAction('back_to_login')">로그인으로 돌아가기</button>
      </div>
    </div>

    <div v-else>
      <div class="user-info">
        <span>안녕하세요, {{ username }}님</span>
        <button @click="logout" @click.native="trackUserAction('logout_button_click')">로그아웃</button>
      </div>

      <div class="container">
        <div class="section">
          <h2>MariaDB 메시지 관리</h2>
          <input v-model="dbMessage" placeholder="저장할 메시지 입력">
          <button @click="saveToDb" @click.native="trackUserAction('save_to_db_button_click')">DB에 저장</button>
          <button @click="getFromDb" @click.native="trackUserAction('get_from_db_button_click')">DB에서 조회</button>
          <button @click="insertSampleData" @click.native="trackUserAction('insert_sample_data_button_click')" class="sample-btn">샘플 데이터 저장</button>
          <div v-if="loading" class="loading-spinner">
            <p>데이터를 불러오는 중...</p>
          </div>
          <div v-if="dbData.length && !loading">
            <h3>저장된 메시지 (최근 10개):</h3>
            <ul>
              <li v-for="item in dbData.slice(0, 10)" :key="item.id">{{ item.message }} ({{ formatDate(item.created_at) }})</li>
            </ul>
            <p v-if="dbData.length > 10" class="log-note">
              * 최근 10개 메시지만 표시됩니다. (총 {{ dbData.length }}개)
            </p>
          </div>
        </div>

        <div class="section">
          <h2>Redis 로그</h2>
          <button @click="getRedisLogs" @click.native="trackUserAction('get_redis_logs_button_click')">Redis 로그 조회 (최근 10개)</button>
          <div v-if="redisLogs.length">
            <h3>API 호출 로그 (최근 10개):</h3>
            <ul>
              <li v-for="(log, index) in redisLogs.slice(0, 10)" :key="index">
                [{{ formatDate(log.timestamp) }}] {{ log.action }}: {{ log.details }}
              </li>
            </ul>
            <p v-if="redisLogs.length > 10" class="log-note">
              * 최근 10개 로그만 표시됩니다. (총 {{ redisLogs.length }}개)
            </p>
          </div>
        </div>

        <div class="section">
          <h2>Kafka 로그</h2>
          <button @click="getKafkaLogs" @click.native="trackUserAction('get_kafka_logs_button_click')">Kafka 로그 조회 (최근 10개)</button>
          <div v-if="kafkaLogs.length">
            <h3>API 통계 로그 (최근 10개):</h3>
            <ul>
              <li v-for="(log, index) in kafkaLogs.slice(0, 10)" :key="index">
                [{{ formatDate(log.timestamp) }}] {{ log.method }} {{ log.endpoint }}: {{ log.message }}
              </li>
            </ul>
            <p v-if="kafkaLogs.length > 10" class="log-note">
              * 최근 10개 로그만 표시됩니다. (총 {{ kafkaLogs.length }}개)
            </p>
          </div>
        </div>



        <div class="section">
          <h2>메시지 검색</h2>
          <div class="search-section">
            <input v-model="searchQuery" placeholder="메시지 검색">
            <button @click="searchMessages" @click.native="trackUserAction('search_messages_button_click')">검색</button>
            <button @click="getAllMessages" @click.native="trackUserAction('get_all_messages_button_click')" class="view-all-btn">전체 메시지 보기</button>
          </div>
          <div v-if="searchResults.length > 0" class="search-results">
            <h3>검색 결과:</h3>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>메시지</th>
                  <th>생성 시간</th>
                  <th>사용자</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="result in searchResults" :key="result.id">
                  <td>{{ result.id }}</td>
                  <td>{{ result.message }}</td>
                  <td>{{ formatDate(result.created_at) }}</td>
                  <td>{{ result.user_id || '없음' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

// nginx 프록시를 통해 요청하도록 수정
const API_BASE_URL = '/api';

export default {
  name: 'App',
  data() {
    return {
      username: '',
      password: '',
      isLoggedIn: false,
      searchQuery: '',
      dbMessage: '',
      dbData: [],
      redisLogs: [],
      kafkaLogs: [],
      sampleMessages: [
        '안녕하세요! 테스트 메시지입니다.',
        'K8s 데모 샘플 데이터입니다.',
        '마이크로서비스 테스트 중입니다.',
        '샘플 메시지 입니다.'
      ],
      offset: 0,
      limit: 20,
      loading: false,
      hasMore: true,
      showRegister: false,
      registerUsername: '',
      registerPassword: '',
      confirmPassword: '',
      currentUser: null,
      searchResults: []
    }
  },
  mounted() {
    // 페이지 뷰 추적
    if (window.telemetry) {
      window.telemetry.tracePageView('K8s Demo App', window.location.href);
    }
  },
  methods: {
    // 사용자 행동 추적 메서드
    trackUserAction(action, details = {}) {
      if (window.telemetry) {
        window.telemetry.traceUserAction(action, {
          ...details,
          timestamp: new Date().toISOString(),
          user: this.currentUser || 'anonymous'
        });
      }
      
      // 구조화된 로그 출력 (Loki용)
      const logEntry = {
        timestamp: new Date().toISOString(),
        level: 'INFO',
        message: `User action: ${action}`,
        service_name: 'jiwoo-frontend',
        action: action,
        user: this.currentUser || 'anonymous',
        ...details
      };
      console.log(JSON.stringify(logEntry));
    },

    // API 호출 추적 메서드
    trackApiCall(url, method, responseTime, statusCode, error = null) {
      if (window.telemetry) {
        window.telemetry.traceApiCall(url, method, responseTime, statusCode, error);
      }
    },

    // 날짜를 사용자 친화적인 형식으로 변환
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleString();
    },
    
    // MariaDB에 메시지 저장
    async saveToDb() {
      const startTime = Date.now();
      try {
        const response = await axios.post(`${API_BASE_URL}/db/message`, {
          message: this.dbMessage
        });
        this.dbMessage = '';
        this.getFromDb();
        
        // API 호출 추적
        this.trackApiCall(`${API_BASE_URL}/db/message`, 'POST', Date.now() - startTime, response.status);
      } catch (error) {
        console.error('DB 저장 실패:', error);
        const status = (error && error.response && error.response.status) ? error.response.status : 0;
        this.trackApiCall(`${API_BASE_URL}/db/message`, 'POST', Date.now() - startTime, status, error);
      }
    },

    // MariaDB에서 메시지 조회 (페이지네이션 적용)
    async getFromDb() {
      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/db/messages?offset=${this.offset}&limit=${this.limit}`);
        this.dbData = response.data;
        this.hasMore = response.data.length === this.limit;
      } catch (error) {
        console.error('DB 조회 실패:', error);
      } finally {
        this.loading = false;
      }
    },

    // 샘플 데이터를 DB에 저장
    async insertSampleData() {
      const randomMessage = this.sampleMessages[Math.floor(Math.random() * this.sampleMessages.length)];
      try {
        await axios.post(`${API_BASE_URL}/db/message`, {
          message: randomMessage
        });
        this.getFromDb();
      } catch (error) {
        console.error('샘플 데이터 저장 실패:', error);
      }
    },

    // Redis에 저장된 API 호출 로그 조회
    async getRedisLogs() {
      try {
        const response = await axios.get(`${API_BASE_URL}/logs/redis`);
        this.redisLogs = response.data;
      } catch (error) {
        console.error('Redis 로그 조회 실패:', error);
      }
    },

    // Kafka에 저장된 API 통계 로그 조회
    async getKafkaLogs() {
      try {
        const response = await axios.get(`${API_BASE_URL}/logs/kafka`);
        this.kafkaLogs = response.data;
      } catch (error) {
        console.error('Kafka 로그 조회 실패:', error);
      }
    },

    // 사용자 로그인 처리
    async login() {
      const startTime = Date.now();
      try {
        const response = await axios.post(`${API_BASE_URL}/login`, {
          username: this.username,
          password: this.password
        });
        
        if (response.data.status === 'success') {
          this.isLoggedIn = true;
          this.currentUser = this.username;
          this.username = '';
          this.password = '';
          
          // API 호출 추적
          this.trackApiCall(`${API_BASE_URL}/login`, 'POST', Date.now() - startTime, response.status);
        } else {
          alert(response.data.message || '로그인에 실패했습니다.');
          this.trackApiCall(`${API_BASE_URL}/login`, 'POST', Date.now() - startTime, 400, new Error(response.data.message));
        }
      } catch (error) {
        console.error('로그인 실패:', error);
        const status = (error && error.response && error.response.status) ? error.response.status : 0;
        this.trackApiCall(`${API_BASE_URL}/login`, 'POST', Date.now() - startTime, status, error);
        alert(error.response && error.response.data 
          ? error.response.data.message 
          : '로그인에 실패했습니다.');
      }
    },
    
    // 로그아웃 처리
    async logout() {
      try {
        await axios.post(`${API_BASE_URL}/logout`);
        this.isLoggedIn = false;
        this.username = '';
        this.password = '';
      } catch (error) {
        console.error('로그아웃 실패:', error);
      }
    },

    // 메시지 검색 기능
    async searchMessages() {
      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/db/messages/search`, {
          params: { q: this.searchQuery }
        });
        this.searchResults = response.data;
      } catch (error) {
        console.error('검색 실패:', error);
        alert('검색에 실패했습니다.');
      } finally {
        this.loading = false;
      }
    },

    // 전체 메시지 조회
    async getAllMessages() {
      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/db/messages`);
        this.searchResults = response.data;
      } catch (error) {
        console.error('전체 메시지 로드 실패:', error);
      } finally {
        this.loading = false;
      }
    },

    // 페이지네이션을 위한 추가 데이터 로드
    async loadMore() {
      this.offset += this.limit;
      await this.getFromDb();
    },

    // 회원가입 처리
    async register() {
      if (this.registerPassword !== this.confirmPassword) {
        alert('비밀번호가 일치하지 않습니다');
        return;
      }
      
      try {
        const response = await axios.post(`${API_BASE_URL}/register`, {
          username: this.registerUsername,
          password: this.registerPassword
        });
        
        if (response.data.status === 'success') {
          alert('회원가입이 완료되었습니다. 로그인해주세요.');
          this.showRegister = false;
          this.registerUsername = '';
          this.registerPassword = '';
          this.confirmPassword = '';
        }
      } catch (error) {
        console.error('회원가입 실패:', error);
        alert(error.response && error.response.data && error.response.data.message 
          ? error.response.data.message 
          : '회원가입에 실패했습니다.');
      }
    }
  }
}
</script>

<style>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

input {
  margin-right: 10px;
  padding: 5px;
  width: 300px;
}

button {
  margin-right: 10px;
  padding: 5px 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

.sample-btn {
  background-color: #28a745;
}

.sample-btn:hover {
  background-color: #218838;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  margin: 5px 0;
  padding: 5px;
  border-bottom: 1px solid #eee;
}

.pagination {
  text-align: center;
  margin-top: 10px;
}

.pagination button {
  padding: 5px 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.pagination button:hover {
  background-color: #0056b3;
}

.pagination button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading-spinner {
  text-align: center;
  margin-top: 20px;
  font-size: 16px;
  color: #555;
}

.user-info {
  text-align: right;
  padding: 10px;
  margin-bottom: 20px;
}

.search-section {
  margin: 10px 0;
}

.search-section input {
  width: 200px;
  margin-right: 10px;
}

.register-btn {
  background-color: #6c757d;
}

.register-btn:hover {
  background-color: #5a6268;
}

.search-results {
  margin-top: 20px;
}

.search-results table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.search-results th,
.search-results td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.search-results th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.search-results tr:hover {
  background-color: #f5f5f5;
}

.view-all-btn {
  background-color: #6c757d;
}

.view-all-btn:hover {
  background-color: #5a6268;
}

.log-note {
  font-size: 12px;
  color: #666;
  font-style: italic;
  margin-top: 10px;
  text-align: center;
}


</style> 