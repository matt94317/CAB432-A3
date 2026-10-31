// 50 concurrent users reading a cached campaign dashboard, one request each ~5 s.
//
//   TOKEN=$(...)  CAMPAIGN_ID=...  k6 run scripts/load.js
//
// The token and campaign id come from the environment so no credential is saved in
// the repo. Get both with the seeded load@hookd.test account, the same way
// scripts/load_test.py signs in.
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const BASE = __ENV.BASE_URL || 'https://n12191434.cab432.com/api';
const CAMPAIGN_ID = __ENV.CAMPAIGN_ID;
const TOKEN = __ENV.TOKEN;

export const options = {
  vus: 50,
  duration: __ENV.DURATION || '15m',
};

// Cache evidence: what share of responses the API served from Redis
const cacheHits = new Rate('cache_hit_rate');

export default function () {
  const response = http.get(`${BASE}/campaigns/${CAMPAIGN_ID}/dashboard`, {
    headers: { Authorization: `Bearer ${TOKEN}` },
    tags: { name: 'campaign_dashboard' },
  });

  check(response, { 'status is 200': (r) => r.status === 200 });
  const state = response.headers['X-Cache'];
  if (state) {
    cacheHits.add(state === 'hit');
  }

  sleep(5); // each user makes one request every ~5 s
}
