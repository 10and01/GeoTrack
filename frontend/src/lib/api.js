const fallbackBase = '/demo_seed.json'

async function getJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
  return response.json()
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

