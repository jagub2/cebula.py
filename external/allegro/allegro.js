const fs = require('fs')
const md5 = require('md5')
const redis = require('redis')

let settingsFile = process.env.SETTINGS_FILE || "settings.json"
let rawdata = fs.readFileSync(`${__dirname}/${settingsFile}`)
const settings = JSON.parse(rawdata)
const scrapeUrl = settings['scrapeUrl']
const xpath = settings['xpath']
const delay = settings['delay']
const delayRand = settings['delayRand']
const redisSettings = settings['redis']

const puppeteer = require('puppeteer-extra')
const StealthPlugin = require('puppeteer-extra-plugin-stealth')
puppeteer.use(StealthPlugin())

const redisClient = redis.createClient({
  url: `redis://${redisSettings['host']}`
})

redisClient.on('error', (err) => console.log('Redis Client Error', err))
redisClient.connect()

let doScan = async function(browser) {
  console.log('Scanning..')
  const page = await browser.newPage()
  await page.goto(scrapeUrl, {waitUntil: 'networkidle2'})
  await page.waitForTimeout(5000)

  await page.waitForXPath(xpath)
  const links = await page.$x(xpath)
  const linkUrls = await page.evaluate((...links) => {
    return links.map(e => e.href)
  }, ...links)
  const linkTitles = await page.evaluate((...links) => {
    return links.map(e => e.textContent)
  }, ...links)
  let zipped = linkTitles.map((x, i) => [x, linkUrls[i]])

  let addedEntries = 0
  zipped.forEach(async element => {
    let hash = md5(element[0] + "-" + element[1])
    let hashPresent = await redisClient.sIsMember(redisSettings['cache_key'], hash)
    if(!hashPresent) {
        redisClient.sAdd(redisSettings['cache_key'], hash)
        redisClient.lPush(redisSettings['data_key'], JSON.stringify(element))
        addedEntries += 1
    }
  })
  await page.close()

  console.log(`Scan done! Added entries: ${addedEntries}`)
}

let random = function (min, max) {
  return Math.floor(Math.random() * (max - min) + min)
}

puppeteer.launch(settings['chromeSettings']).then(async browser => {
  while(true) {
    await doScan(browser)
    let currentDelay = (delay + random(-delayRand, delayRand))
    console.log(`Sleeping ${currentDelay} s...`)
    await new Promise(r => setTimeout(r, currentDelay * 1000))
  }
  await browser.close()
  await redisClient.disconnect()
})

