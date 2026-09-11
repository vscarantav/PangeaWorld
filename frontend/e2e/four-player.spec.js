import { expect, test } from '@playwright/test';

const API_URL = `http://127.0.0.1:${process.env.E2E_BACKEND_PORT || 8001}`;

async function register(page, email) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Need an account?' }).click();
  await page.getByPlaceholder('Email').fill(email);
  await page.getByPlaceholder('Password (8+ characters)').fill('phase-two-password');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(page.getByRole('heading', { name: new RegExp(`Welcome, ${email}`) })).toBeVisible();
}

async function login(page, email) {
  await page.goto('/');
  await page.getByPlaceholder('Email').fill(email);
  await page.getByPlaceholder('Password (8+ characters)').fill('phase-two-password');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: new RegExp(`Welcome, ${email}`) })).toBeVisible();
}

async function confirmReview(page) {
  await expect(page.getByRole('dialog', { name: 'Compare your decision' })).toBeVisible();
  await page.getByLabel('Foregone alternative').selectOption('reserve');
  await page.getByLabel('Decision rationale').fill('I prefer the current investment to reserves because its near-term benefit outweighs the flexibility lost; further spending should wait.');
  await page.getByRole('button', { name: 'Confirm reviewed decision' }).click();
}

async function advancePhase(request, sessionId, expectedPhase) {
  const response = await request.post(`${API_URL}/api/sessions/${sessionId}/advance`, {
    data: { expected_phase: expectedPhase },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
}

async function expectPlayerShell(page, roleLabel) {
  let lastError;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await expect(page.getByText(roleLabel, { exact: true }).first()).toBeVisible({ timeout: 12000 });
      await expect(page.getByTestId('game-status')).toBeVisible({ timeout: 5000 });
      return;
    } catch (error) {
      lastError = error;
      if (attempt < 2) await page.reload({ waitUntil: 'domcontentloaded' });
    }
  }
  throw lastError;
}

async function clickPlayerNav(page, name, roleLabel) {
  const navigationItem = () => page.locator('button.nav-item').filter({ hasText: name });
  try {
    await navigationItem().click({ timeout: 10000 });
  } catch {
    // Reloading is also the supported recovery path for a real player whose
    // initial state request was interrupted during a lobby/phase transition.
    await page.reload({ waitUntil: 'domcontentloaded' });
    await expectPlayerShell(page, roleLabel);
    await navigationItem().click({ timeout: 10000 });
  }
}

test('four isolated players exercise the Phase 4 live classroom path', async ({ browser }, testInfo) => {
  const runSuffix = testInfo.repeatEachIndex ? `-${testInfo.repeatEachIndex}` : '';
  const instructorContext = await browser.newContext();
  const instructor = await instructorContext.newPage();
  const instructorEmail = 'instructor@e2e.test';
  if (testInfo.repeatEachIndex === 0) await register(instructor, instructorEmail);
  else await login(instructor, instructorEmail);
  await instructor.getByRole('button', { name: 'Create instructor game' }).click();
  await expect(instructor.getByRole('heading', { name: 'Game lobby' })).toBeVisible({ timeout: 30000 });
  await expect(instructor.getByTestId('lobby-connection')).toHaveText('Live');
  const joinCode = await instructor.locator('strong').first().innerText();
  const sessionId = await instructor.evaluate(() => window.localStorage.getItem('pangeaworld.sessionId'));

  const playerEmails = [
    `president-one${runSuffix}@e2e.test`,
    `president-two${runSuffix}@e2e.test`,
    `executive-one${runSuffix}@e2e.test`,
    `executive-two${runSuffix}@e2e.test`,
  ];
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
  const initialReadiness = await instructorContext.request.get(`${API_URL}/api/sessions/${sessionId}/readiness`);
  expect(initialReadiness.ok(), await initialReadiness.text()).toBeTruthy();
  expect((await initialReadiness.json()).phase).toBe('planning');

  for (let index = 0; index < players.length; index += 1) {
    const roleLabel = index < 2 ? 'President' : 'Company Executive';
    await expectPlayerShell(players[index], roleLabel);
    await expect(players[index].getByTestId('game-status')).toContainText(/Decision:.*Live/);
  }

  await players[0].getByTitle('Open AI Advisor').click();
  await expect(players[0].getByText('Gemini Advisor')).toBeVisible();
  const tariffPrompt = players[0].getByRole('button', { name: 'What are the trade-offs of raising tariffs this round?' });
  await expect(tariffPrompt).toBeEnabled();
  await tariffPrompt.click();
  await expect(players[0].getByText(/What impact do you think raising tariffs/)).toBeVisible({ timeout: 10000 });
  await players[0].getByTitle('Close').click();

  await expect(instructor.getByText('Phase 4 instructor analytics')).toBeVisible();
  await instructor.getByRole('button', { name: 'Refresh analytics' }).click();
  await expect(instructor.getByRole('cell', { name: playerEmails[0] }).first()).toBeVisible();
  await expect(instructor.getByText('AI seat backfill')).toBeVisible();

  await advancePhase(instructorContext.request, sessionId, 'planning');
  for (const player of players) {
    // The REST safety poll runs every two seconds, so this remains bounded
    // even during a short WebSocket reconnect window.
    await expect(player.getByTestId('game-status')).toContainText(/Round 1.*presidential/, { timeout: 5000 });
  }

  const eventResponse = await instructorContext.request.post(`${API_URL}/api/sessions/${sessionId}/phase3/events`, {
    data: { catalog_key: 'coastal_storm', target_nation_id: firstNation.id },
  });
  expect(eventResponse.ok()).toBeTruthy();
  const scheduledEvent = await eventResponse.json();

  for (let index = 2; index < 4; index += 1) {
    await clickPlayerNav(players[index], 'Decisions', 'Company Executive');
    await expect(players[index].getByRole('button', { name: 'Save Decisions' })).toBeDisabled();
    const early = await playerContexts[index].request.post(
      `${API_URL}/api/sessions/${sessionId}/companies/${seats[index].split(':')[1]}/decisions`,
      { data: { decision_data: {} } },
    );
    expect(early.status()).toBe(409);
  }

  for (let index = 0; index < 2; index += 1) {
    await clickPlayerNav(players[index], 'Intel', 'President');
    if (index === 0) {
      await players[index].getByLabel('Emergency preparedness fund').fill('500');
    }
    await players[index].getByLabel('Submit a direct attack order').check();
    await players[index].getByLabel('Attack target').selectOption(String(index === 0 ? secondNation.id : firstNation.id));
    await players[index].getByLabel('Deploy infantry').fill('1');
    await players[index].getByRole('button', { name: 'Save readiness plan' }).click();
    await confirmReview(players[index]);
    await expect(players[index].getByText(/Readiness plan saved for Round/)).toBeVisible();
    await clickPlayerNav(players[index], 'Indexes', 'President');
    await players[index].getByRole('button', { name: 'Apply Policies' }).click();
    await confirmReview(players[index]);
    await expect(players[index].getByText(/Presidential decision submitted to the server/)).toBeVisible();
    await expect(players[index].getByTestId('game-status')).toContainText(/Decision: submitted/, { timeout: 5000 });
  }

  await advancePhase(instructorContext.request, sessionId, 'presidential');
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
    await expect(page.getByText('Saved locally', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Submit Decisions' }).click();
    await confirmReview(page);
    await expect(page.getByText('Server confirmed', { exact: true })).toBeVisible();
    await expect(page.getByTestId('game-status')).toContainText(/Decision: submitted/, { timeout: 5000 });
  }

  await advancePhase(instructorContext.request, sessionId, 'company');
  await advancePhase(instructorContext.request, sessionId, 'processing');
  const roundTwoResponse = await instructorContext.request.get(`${API_URL}/api/sessions/${sessionId}`);
  expect(roundTwoResponse.ok()).toBeTruthy();
  expect(await roundTwoResponse.json()).toMatchObject({ current_round: 2, phase: 'planning' });

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

  const eventResults = await Promise.all(playerContexts.map(async (context) => {
    const resultResponse = await context.request.get(`${API_URL}/api/sessions/${sessionId}/phase3/results`);
    expect(resultResponse.ok()).toBeTruthy();
    return resultResponse.json();
  }));
  expect(eventResults[0].results.length).toBeGreaterThanOrEqual(3);
  const disasterResult = eventResults[0].results.find((result) => result.event_id === scheduledEvent.id);
  expect(disasterResult.effects.public_fund_used).toBeGreaterThan(0);
  const combatResults = eventResults[0].results.filter((result) => result.event_type === 'military_attack');
  expect(combatResults).toHaveLength(2);
  expect(new Set(combatResults.map((result) => result.target_nation_id))).toEqual(new Set([firstNation.id, secondNation.id]));
  expect(JSON.stringify(eventResults[0])).not.toContain('private_financing_cost');
  expect(JSON.stringify(combatResults)).not.toContain('deployment');
  expect(JSON.stringify(combatResults)).not.toContain('rolls');
  for (const results of eventResults.slice(1)) expect(results).toEqual(eventResults[0]);

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
