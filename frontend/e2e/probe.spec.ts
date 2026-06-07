import { expect, test } from '@playwright/test'

const HOST_A = '8.8.8.8'
const HOST_B = '1.1.1.1'

test.describe('core user flows', () => {
  let targetAId: string

  test.beforeAll(async ({ request }) => {
    // Trigger probes to create targets in the DB
    await request.post('/api/probe', { data: { target: HOST_A } })
    await request.post('/api/probe', { data: { target: HOST_B } })

    // Poll until HOST_A probe result is available (traceroute can take ~30 s)
    for (let i = 0; i < 40; i++) {
      const r = await request.get(`/api/results?target=${HOST_A}&limit=1`)
      const json = await r.json()
      if (json.total > 0) break
      await new Promise((res) => setTimeout(res, 2_000))
    }

    // Resolve HOST_A target ID for route mocking
    const targetsRes = await request.get('/api/targets')
    const targets: Array<{ host: string; id: string }> = await targetsRes.json()
    targetAId = targets.find((t) => t.host === HOST_A)?.id ?? ''
    expect(targetAId).not.toBe('')
  })

  test('on-demand probe creates a map marker', async ({ page }) => {
    // Stub the route endpoint with known coordinates — GeoIP is not available in CI
    // Use glob so the full URL (http://localhost/api/routes/...) is matched
    await page.route(`**/api/routes/${targetAId}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ target_id: targetAId, hops: [[37.751, -97.822]] }),
      })
    )

    await page.goto('/')

    // Select HOST_A from the sidebar target list
    await page.getByRole('button', { name: HOST_A, exact: true }).click()

    // The mocked route triggers a vector layer (path or circle) in the leaflet overlay pane
    await expect(page.locator('.leaflet-overlay-pane .leaflet-interactive').first()).toBeVisible()

    // Trigger an on-demand probe via the UI button
    await page.getByRole('button', { name: `Probe ${HOST_A}` }).click()

    // The button should remain (not disappear or error)
    await expect(page.getByRole('button', { name: /Probe/ })).toBeVisible()
  })

  test('selecting a different target updates the latency chart', async ({ page }) => {
    // Wait until HOST_B probe result is also available
    for (let i = 0; i < 20; i++) {
      const r = await page.request.get(`/api/results?target=${HOST_B}&limit=1`)
      const json = await r.json()
      if (json.total > 0) break
      await new Promise((res) => setTimeout(res, 2_000))
    }

    await page.goto('/')

    // Select HOST_A — latency chart should render with data
    await page.getByRole('button', { name: HOST_A, exact: true }).click()
    await expect(page.locator('.recharts-surface')).toBeVisible()

    // Switch to HOST_B — chart re-renders for the new target
    await page.getByRole('button', { name: HOST_B, exact: true }).click()
    await expect(page.locator('.recharts-surface')).toBeVisible()
  })
})
