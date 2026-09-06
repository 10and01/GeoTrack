const fallbackBase = '/demo_seed.json'

async function getJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
  return response.json()
}

function withQuery(path, params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '' && value !== 'all') {
      search.set(key, String(value))
    }
  })
  const query = search.toString()
  return query ? `${path}?${query}` : path
}

export function queryTrajectories(params = {}) {
  return getJson(withQuery('/api/query/trajectories', params))
}

export function queryHotspots(params = {}) {
  return getJson(withQuery('/api/query/hotspots', params))
}

export function getTrajectory(trajectoryId) {
  return getJson(`/api/trajectories/${encodeURIComponent(trajectoryId)}`)
}

export function getJob(jobId) {
  return getJson(`/api/jobs/${encodeURIComponent(jobId)}`)
}
export async function loadDashboardData() {
  try {
    const [summary, users, trajectories, hotspots, patterns, quality] = await Promise.all([
      getJson('/api/summary'),
      getJson('/api/users?limit=100'),
      getJson('/api/trajectories?limit=100'),
      getJson('/api/hotspots?limit=30'),
      getJson('/api/patterns/clusters'),
      getJson('/api/data-quality'),
    ])
    return { summary, users, trajectories, hotspots, patterns, quality, mode: 'api' }
  } catch (error) {
    const seed = await getJson(fallbackBase)
    return { ...seed, mode: 'demo', error: error.message }
  }
}

export async function runJob(job_type = 'mine') {
  const response = await fetch('/api/jobs/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_type }),
  })
  if (!response.ok) throw new Error('任务提交失败')
  return response.json()
}
