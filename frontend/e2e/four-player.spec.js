import { expect, test } from '@playwright/test';

const API_URL = 'http://127.0.0.1:8001';

async function register(page, email) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Need an account?' }).click();
  await page.getByPlaceholder('Email').fill(email);
  await page.getByPlaceholder('Password (8+ characters)').fill('phase-two-password');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByRole('heading', { name: new RegExp(`Welcome, ${email}`) })).toBeVisible();
}

test('four isolated players complete one authoritative round and receive identical results', async ({ browser }) => {
  const instructorContext = await browser.newContext();
  const instructor = await instructorContext.newPage();
  await register(instructor, 'instructor@e2e.test');
  await instructor.getByRole('button', { name: 'Create instructor game' }).click();
  await expect(instructor.getByRole('heading', { name: 'Game lobby' })).toBeVisible({ timeout: 30000 });
  await expect(instructor.getByTestId('lobby-connection')).toHaveText('Live');
  const joinCode = await instructor.locator('strong').first().innerText();
  const sessionId = await instructor.evaluate(() => window.localStorage.getItem('pangeaworld.sessionId'));

  const playerEmails = ['president-one@e2e.test', 'president-two@e2e.test', 'executive-one@e2e.test', 'executive-two@e2e.test'];
  const playerContexts = [];
  const players = [];
  for (const email of playerEmails) {
    const context = await browser.newContext();
    const page = await context.newPage();
    await register(page, email);
    await page.getByPlaceholder('Lobby join code').fill(joinCode);
    await page.getByRole('button', { name: 'Join game' }).click();
    await expect(page.getByRole('heading', { name: 'Game lobby' })).toBeVisible();
    await expect(page.getByTestId('lobby-connection')).toHaveText('Live');
    playerContexts.push(context);
    players.push(page);
  }

  await instructor.reload();
  const response = await instructorContext.request.get(`${API_URL}/api/sessions/${sessionId}/lobby`);
  expect(response.ok()).toBeTruthy();
  const lobby = await response.json();
  const [firstNation, secondNation] = lobby.seats.nations;
  const seats = [
    `president:${firstNation.id}`,
    `president:${secondNation.id}`,
    `executive:${lobby.seats.companies.find((company) => company.nation_id === firstNation.id).id}`,
    `executive:${lobby.seats.companies.find((company) => company.nation_id === secondNation.id).id}`,
  ];

  for (let index = 0; index < playerEmails.length; index += 1) {
    const memberRow = instructor.locator(`[data-member-email="${playerEmails[index]}"]`);
    await memberRow.locator('select').selectOption(seats[index]);
    await expect(memberRow).toContainText(seats[index].startsWith('president') ? 'president' : 'executive');
  }

  await instructor.getByRole('button', { name: 'Start game' }).click();
  await expect(instructor.getByRole('heading', { name: 'Instructor readiness board' })).toBeVisible();
  await expect(instructor.getByText(/Round 1.*planning/)).toBeVisible();

  for (let index = 0; index < players.length; index += 1) {
    const roleLabel = index < 2 ? 'President' : 'Company Executive';
    await expect(players[index].getByText(roleLabel, { exact: true }).first()).toBeVisible();
    await expect(players[index].getByTestId('game-status')).toContainText(/Decision:.*Live/);
  }

  await instructor.getByRole('button', { name: 'Advance phase' }).click();
  for (const player of players) {
    // The REST safety poll runs every two seconds, so this remains bounded
    // even during a short WebSocket reconnect window.
    await expect(player.getByTestId('game-status')).toContainText(/Round 1.*presidential/, { timeout: 5000 });
  }

  for (let index = 2; index < 4; index += 1) {
    await players[index].locator('button.nav-item').filter({ hasText: 'Decisions' }).click({ force: true, timeout: 10000 });
    await expect(players[index].getByRole('button', { name: 'Save Decisions' })).toBeDisabled();
    const early = await playerContexts[index].request.post(
      `${API_URL}/api/sessions/${sessionId}/companies/${seats[index].split(':')[1]}/decisions`,
      { data: { decision_data: {} } },
    );
    expect(early.status()).toBe(409);
  }

  for (let index = 0; index < 2; index += 1) {
    await players[index].locator('button.nav-item').filter({ hasText: 'Indexes' }).click({ force: true, timeout: 10000 });
    await players[index].getByRole('button', { name: 'Apply Policies' }).click();
    await expect(players[index].getByText(/Presidential decision submitted to the server/)).toBeVisible();
    await expect(players[index].getByTestId('game-status')).toContainText(/Decision: submitted/, { timeout: 5000 });
  }

  await instructor.getByRole('button', { name: 'Advance phase' }).click();
  for (const player of players) {
    await expect(player.getByTestId('game-status')).toContainText(/Round 1.*company/, { timeout: 5000 });
  }

  for (let index = 2; index < 4; index += 1) {
    const page = players[index];
    await page.getByLabel('Product price').fill(String(180 + index));
    await page.getByLabel('Production volume').fill('1.2');
    await page.getByLabel('R&D investment').fill('100');
    const supplier = page.locator('.input-group select').nth(1);
    await expect(supplier.locator('option')).not.toHaveCount(0);
    await page.getByLabel('Sourcing quantity').fill('1');
    await page.getByRole('button', { name: 'Save Decisions' }).click();
    await expect(page.getByText('Draft saved on the server. It is not submitted yet.')).toBeVisible();
    await page.getByRole('button', { name: 'Submit Decisions' }).click();
    await expect(page.getByText(/Submitted to the server for Round 1/)).toBeVisible();
    await expect(page.getByTestId('game-status')).toContainText(/Decision: submitted/, { timeout: 5000 });
  }

  await instructor.getByRole('button', { name: 'Advance phase' }).click();
  await expect(instructor.getByText(/Round 1.*processing/)).toBeVisible({ timeout: 5000 });
  await instructor.getByRole('button', { name: 'Advance phase' }).click();
  await expect(instructor.getByText(/Round 2.*planning/)).toBeVisible({ timeout: 15000 });

  for (const player of players) {
    await expect(player.getByTestId('game-status')).toContainText(/Round 2.*planning/, { timeout: 5000 });
    await expect(player.getByTestId('round-results')).toContainText('Round 1 results published');
    await expect(player.getByTestId('round-results')).toContainText('Pangea Times:');
  }

  const sessionViews = await Promise.all(playerContexts.map(async (context) => {
    const sessionResponse = await context.request.get(`${API_URL}/api/sessions/${sessionId}`);
    expect(sessionResponse.ok()).toBeTruthy();
    return sessionResponse.json();
  }));
  const canonicalRound = sessionViews[0].rounds.find((round) => round.number === 1);
  expect(canonicalRound.status).toBe('complete');
  expect(canonicalRound.results.nations.length).toBeGreaterThan(0);
  for (const view of sessionViews.slice(1)) {
    expect(view.current_round).toBe(2);
    expect(view.phase).toBe('planning');
    expect(view.map_snapshot).toEqual(sessionViews[0].map_snapshot);
    expect(view.rounds.find((round) => round.number === 1).results).toEqual(canonicalRound.results);
  }

  const newsFeeds = await Promise.all(playerContexts.map(async (context) => {
    const newsResponse = await context.request.get(`${API_URL}/api/sessions/${sessionId}/news`);
    expect(newsResponse.ok()).toBeTruthy();
    return newsResponse.json();
  }));
  expect(newsFeeds[0].articles.length).toBeGreaterThan(0);
  for (const feed of newsFeeds.slice(1)) expect(feed).toEqual(newsFeeds[0]);

  await players[0].getByRole('button', { name: 'Sign out' }).click();
  await players[0].getByPlaceholder('Email').fill(playerEmails[0]);
  await players[0].getByPlaceholder('Password (8+ characters)').fill('phase-two-password');
  await players[0].getByRole('button', { name: 'Sign in' }).click();
  await expect(players[0].getByText('President', { exact: true }).first()).toBeVisible();
  await expect(players[0].getByTestId('game-status')).toContainText(/Round 2.*planning/);
  await expect(players[0].getByTestId('round-results')).toContainText('Round 1 results published');
  await players[0].getByRole('button', { name: 'Map View' }).click();
  await expect(players[0].getByRole('alert')).toHaveCount(0);
  await expect(players[0].locator('canvas').first()).toBeVisible();
  await players[0].reload();
  await expect(players[0].getByText('President', { exact: true }).first()).toBeVisible();
  await expect(players[0].getByTestId('game-status')).toContainText(/Round 2.*planning/);
  await players[0].getByRole('button', { name: 'Map View' }).click();
  await expect(players[0].locator('canvas').first()).toBeVisible();

  await Promise.all(playerContexts.map((context) => context.close()));
  await instructorContext.close();
});
