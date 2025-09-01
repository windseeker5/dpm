const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  
  // Test Desktop
  console.log('=== Testing Desktop Layout ===');
  const desktopContext = await browser.newContext({ viewport: { width: 1200, height: 800 } });
  const desktopPage = await desktopContext.newPage();
  
  try {
    // Navigate and login
    await desktopPage.goto('http://localhost:5000');
    await desktopPage.fill('input[name="email"]', 'kdresdell@gmail.com');
    await desktopPage.fill('input[name="password"]', 'admin123');
    await desktopPage.click('button[type="submit"]');
    
    // Wait for dashboard
    await desktopPage.waitForSelector('.kpi-cards-wrapper', { timeout: 10000 });
    
    // Check desktop layout
    const kpiWrapper = await desktopPage.locator('.kpi-cards-wrapper');
    const displayStyle = await kpiWrapper.evaluate(el => getComputedStyle(el).display);
    const gridColumns = await kpiWrapper.evaluate(el => getComputedStyle(el).gridTemplateColumns);
    
    console.log(`Desktop Display: ${displayStyle}`);
    console.log(`Desktop Grid Columns: ${gridColumns}`);
    
    // Check card positions
    const cards = await desktopPage.locator('.kpi-card-mobile').all();
    console.log(`Desktop Card Count: ${cards.length}`);
    
    if (cards.length >= 2) {
      const card1Box = await cards[0].boundingBox();
      const card2Box = await cards[1].boundingBox();
      
      if (card1Box && card2Box) {
        const sameRow = Math.abs(card1Box.y - card2Box.y) < 10;
        console.log(`Desktop Cards in Same Row: ${sameRow}`);
        console.log(`Card 1 Y: ${card1Box.y}, Card 2 Y: ${card2Box.y}`);
      }
    }
    
    // Take a screenshot
    await desktopPage.screenshot({ path: 'desktop-kpi.png' });
    
  } catch (error) {
    console.log(`Desktop test error: ${error.message}`);
  }
  
  await desktopContext.close();
  
  // Test Mobile
  console.log('\n=== Testing Mobile Layout ===');
  const mobileContext = await browser.newContext({ viewport: { width: 375, height: 667 } });
  const mobilePage = await mobileContext.newPage();
  
  try {
    // Navigate and login
    await mobilePage.goto('http://localhost:5000');
    await mobilePage.fill('input[name="email"]', 'kdresdell@gmail.com');
    await mobilePage.fill('input[name="password"]', 'admin123');
    await mobilePage.click('button[type="submit"]');
    
    // Wait for dashboard
    await mobilePage.waitForSelector('.kpi-cards-wrapper', { timeout: 10000 });
    
    // Check mobile layout
    const kpiWrapper = await mobilePage.locator('.kpi-cards-wrapper');
    const displayStyle = await kpiWrapper.evaluate(el => getComputedStyle(el).display);
    const overflowX = await kpiWrapper.evaluate(el => getComputedStyle(el).overflowX);
    const flexDirection = await kpiWrapper.evaluate(el => getComputedStyle(el).flexDirection);
    
    console.log(`Mobile Display: ${displayStyle}`);
    console.log(`Mobile Overflow X: ${overflowX}`);
    console.log(`Mobile Flex Direction: ${flexDirection}`);
    
    // Check scrollable behavior
    const scrollWidth = await kpiWrapper.evaluate(el => el.scrollWidth);
    const clientWidth = await kpiWrapper.evaluate(el => el.clientWidth);
    
    console.log(`Mobile Scroll Width: ${scrollWidth}`);
    console.log(`Mobile Client Width: ${clientWidth}`);
    console.log(`Mobile Horizontally Scrollable: ${scrollWidth > clientWidth}`);
    
    // Take a screenshot
    await mobilePage.screenshot({ path: 'mobile-kpi.png' });
    
  } catch (error) {
    console.log(`Mobile test error: ${error.message}`);
  }
  
  await mobileContext.close();
  await browser.close();
})();