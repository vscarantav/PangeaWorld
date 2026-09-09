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

test('four isolated browser sessions receive their assigned dashboards and persisted map', async ({ browser }) => {
  const instructorContext = await browser.newContext();
  const instructor = await instructorContext.newPage();
  await register(instructor, 'instructor@e2e.test');
  await instructor.getByRole('button', { name: 'Create instructor game' }).click();
  await expect(instructor.getByRole('heading', { name: 'Game lobby' })).toBeVisible({ timeout: 30000 });
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

  for (let index = 0; index < players.length; index += 1) {
    await players[index].reload();
    const roleLabel = index < 2 ? 'President' : 'Company Executive';
    await expect(players[index].getByText(roleLabel, { exact: true }).first()).toBeVisible();
    await expect(players[index].getByText(/Decision:.*Live/)).toBeVisible();
  }

  await instructor.getByRole('button', { name: 'Advance phase' }).click();
  for (const player of players) {
    // The REST safety poll runs every 15 seconds, so a five-second assertion
    // proves the session WebSocket delivered the phase notification.
    await expect(player.getByText(/Round 1.*presidential/)).toBeVisible({ timeout: 5000 });
  }

  await players[0].getByRole('button', { name: 'Map View' }).click();
  await expect(players[0].getByRole('alert')).toHaveCount(0);
  await expect(players[0].locator('canvas')).toBeVisible();
  await players[0].reload();
  await players[0].getByRole('button', { name: 'Map View' }).click();
  await expect(players[0].getByRole('alert')).toHaveCount(0);
  await expect(players[0].locator('canvas')).toBeVisible();

  await players[0].getByRole('button', { name: 'Sign out' }).click();
  await players[0].getByPlaceholder('Email').fill(playerEmails[0]);
  await players[0].getByPlaceholder('Password (8+ characters)').fill('phase-two-password');
  await players[0].getByRole('button', { name: 'Sign in' }).click();
  await expect(players[0].getByText('President', { exact: true }).first()).toBeVisible();

  await Promise.all(playerContexts.map((context) => context.close()));
  await instructorContext.close();
});
