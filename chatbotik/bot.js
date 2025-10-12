import { Telegraf, Markup } from 'telegraf'
import { message } from 'telegraf/filters'
import express from 'express'
import cors from 'cors'
import path from 'path'
import { fileURLToPath } from 'url'
import { initDatabase, getProducts, createProduct, updateProduct, deleteProduct, createOrder } from './database.js'
import { saveImage, getImagePath } from './imageHandler.js'
import dotenv from 'dotenv'

// Загружаем переменные окружения
dotenv.config()

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Конфигурация
const token = process.env.BOT_TOKEN || ''
const port = process.env.PORT || 8000
const webAppUrl = process.env.WEBAPP_URL || `http://localhost:${port}`

// Инициализация
const bot = new Telegraf(token)
const app = express()

// Middleware
app.use(cors())
app.use(express.json())
app.use(express.static(path.join(__dirname, 'frontend', 'dist')))

// Создаем папки
import { mkdirSync } from 'fs'
mkdirSync('uploads', { recursive: true })
mkdirSync('frontend/dist', { recursive: true })

// Инициализируем базу данных
initDatabase()

// ==================== TELEGRAM BOT COMMANDS ====================

bot.command('start', (ctx) => {
  ctx.reply(
    '🛍️ **Добро пожаловать в наш магазин!**\n\n' +
    'Здесь вы можете:\n' +
    '• 🛒 Просматривать товары\n' +
    '• 📦 Добавлять в корзину\n' +
    '• 💳 Оформлять заказы\n' +
    '• 📞 Связываться с нами\n\n' +
    'Нажмите кнопку ниже, чтобы открыть магазин!',
    {
      parse_mode: 'Markdown',
      reply_markup: Markup.keyboard([
        [Markup.button.webApp('🛍️ Открыть магазин', `${webAppUrl}`)],
        [Markup.button.callback('📦 Каталог', 'catalog')],
        [Markup.button.callback('📞 Контакты', 'contact')]
      ]).resize()
    }
  )
})

bot.command('catalog', async (ctx) => {
  try {
    const products = await getProducts()
    
    if (products.length === 0) {
      ctx.reply('📦 Каталог пока пуст. Зайдите позже!')
      return
    }
    
    let message = '🛍️ **Каталог товаров:**\n\n'
    
    products.slice(0, 5).forEach((product, index) => {
      message += `${index + 1}. **${product.title}**\n`
      message += `   💰 ${product.price.toLocaleString()} ₽\n`
      if (product.description) {
        message += `   📝 ${product.description.substring(0, 50)}...\n`
      }
      message += '\n'
    })
    
    if (products.length > 5) {
      message += `... и еще ${products.length - 5} товаров\n\n`
    }
    
    message += 'Нажмите кнопку ниже, чтобы открыть полный каталог!'
    
    ctx.reply(message, {
      parse_mode: 'Markdown',
      reply_markup: Markup.inlineKeyboard([
        [Markup.button.webApp('🛍️ Открыть полный каталог', `${webAppUrl}`)]
      ])
    })
  } catch (error) {
    console.error('Error in catalog command:', error)
    ctx.reply('❌ Ошибка загрузки каталога. Попробуйте позже.')
  }
})

bot.command('contact', (ctx) => {
  const contactMessage = `
📞 **Связаться с нами:**

🕐 **Время работы:** 9:00 - 21:00 (МСК)

📱 **Телефон:** +7 (999) 123-45-67
📧 **Email:** support@eshoppro.ru
💬 **Telegram:** @eshoppro_support

🏢 **Адрес:**
г. Москва, ул. Примерная, д. 123

❓ **Частые вопросы:**
• Доставка по всей России
• Оплата картой или наличными
• Возврат в течение 14 дней
• Гарантия на все товары

Напишите нам, и мы обязательно поможем!
  `
  
  ctx.reply(contactMessage, {
    parse_mode: 'Markdown',
    reply_markup: Markup.inlineKeyboard([
      [Markup.button.url('💬 Написать в поддержку', 'https://t.me/eshoppro_support')],
      [Markup.button.webApp('🛍️ Вернуться в магазин', `${webAppUrl}`)]
    ])
  })
})

// Обработка нажатий на кнопки
bot.action('catalog', async (ctx) => {
  ctx.answerCbQuery()
  await ctx.reply('📦 Загружаем каталог...')
  // Вызываем команду каталога
  await bot.telegram.sendMessage(ctx.chat.id, 'catalog', { reply_markup: { remove_keyboard: true } })
})

bot.action('contact', async (ctx) => {
  ctx.answerCbQuery()
  await ctx.reply('📞 Загружаем контакты...')
  // Вызываем команду контактов
  await bot.telegram.sendMessage(ctx.chat.id, 'contact', { reply_markup: { remove_keyboard: true } })
})

// Обработка данных от WebApp
bot.on(message('web_app_data'), async (ctx) => {
  try {
    const data = JSON.parse(ctx.webAppData.data.json())
    
    if (data.type === 'order') {
      const orderResult = await createOrder(data.order)
      
      ctx.reply(
        `✅ **Заказ оформлен успешно!**\n\n` +
        `🆔 Номер заказа: #${orderResult.id}\n` +
        `💰 Сумма: ${orderResult.total_amount.toLocaleString()} ₽\n` +
        `📞 Мы свяжемся с вами в ближайшее время!`,
        { parse_mode: 'Markdown' }
      )
    } else if (data.type === 'feedback') {
      ctx.reply(
        `✅ **Спасибо за обратную связь!**\n\n` +
        `📝 Ваше сообщение: "${data.feedback}"\n\n` +
        `Мы обязательно рассмотрим ваше сообщение и ответим!`,
        { parse_mode: 'Markdown' }
      )
    }
  } catch (error) {
    console.error('Error processing web app data:', error)
    ctx.reply('❌ Произошла ошибка при обработке данных.')
  }
})

// ==================== EXPRESS API ====================

// Главная страница
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'dist', 'index.html'))
})

// API для получения товаров
app.get('/api/products', async (req, res) => {
  try {
    const products = await getProducts()
    res.json(products)
  } catch (error) {
    console.error('Error getting products:', error)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// API для создания товара (админ)
app.post('/api/products', async (req, res) => {
  try {
    const productData = req.body
    
    // Простая проверка админских прав (в реальном проекте используйте JWT)
    if (!req.headers['x-admin-password'] || req.headers['x-admin-password'] !== 'admin123') {
      return res.status(403).json({ error: 'Access denied' })
    }
    
    const product = await createProduct(productData)
    res.json(product)
  } catch (error) {
    console.error('Error creating product:', error)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// API для обновления товара (админ)
app.put('/api/products/:id', async (req, res) => {
  try {
    const { id } = req.params
    const productData = req.body
    
    if (!req.headers['x-admin-password'] || req.headers['x-admin-password'] !== 'admin123') {
      return res.status(403).json({ error: 'Access denied' })
    }
    
    const product = await updateProduct(id, productData)
    if (!product) {
      return res.status(404).json({ error: 'Product not found' })
    }
    
    res.json(product)
  } catch (error) {
    console.error('Error updating product:', error)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// API для удаления товара (админ)
app.delete('/api/products/:id', async (req, res) => {
  try {
    const { id } = req.params
    
    if (!req.headers['x-admin-password'] || req.headers['x-admin-password'] !== 'admin123') {
      return res.status(403).json({ error: 'Access denied' })
    }
    
    const success = await deleteProduct(id)
    if (!success) {
      return res.status(404).json({ error: 'Product not found' })
    }
    
    res.json({ message: 'Product deleted successfully' })
  } catch (error) {
    console.error('Error deleting product:', error)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// API для загрузки изображений
app.post('/api/upload', async (req, res) => {
  try {
    // Здесь должна быть обработка multipart/form-data
    // Для простоты пока возвращаем заглушку
    res.json({ message: 'Upload endpoint ready' })
  } catch (error) {
    console.error('Error uploading image:', error)
    res.status(500).json({ error: 'Internal server error' })
  }
})

// Статические файлы
app.get('/uploads/:filename', (req, res) => {
  const filename = req.params.filename
  const imagePath = getImagePath(filename)
  res.sendFile(imagePath)
})

// ==================== STARTUP ====================

async function start() {
  try {
    // Запускаем Express сервер
    app.listen(port, '0.0.0.0', () => {
      console.log(`🌐 Web server running on http://0.0.0.0:${port}`)
    })
    
    // Запускаем Telegram бота
    if (token) {
      await bot.launch()
      console.log('🤖 Telegram bot started successfully!')
      
      // Устанавливаем команды бота
      await bot.telegram.setMyCommands([
        { command: 'start', description: 'Запустить бота' },
        { command: 'catalog', description: 'Посмотреть каталог' },
        { command: 'contact', description: 'Связаться с нами' }
      ])
      
      // Устанавливаем WebApp URL в BotFather
      console.log(`📱 Set WebApp URL in @BotFather: ${webAppUrl}`)
    } else {
      console.log('⚠️ BOT_TOKEN not found - bot disabled')
    }
    
    console.log('🎉 Platform started successfully!')
    console.log('=' * 50)
    console.log(`🌐 Web: http://0.0.0.0:${port}`)
    console.log(`📱 WebApp URL: ${webAppUrl}`)
    console.log('🛑 Press Ctrl+C to stop')
    
  } catch (error) {
    console.error('❌ Error starting platform:', error)
    process.exit(1)
  }
}

// Graceful shutdown
process.once('SIGINT', () => {
  console.log('\n🛑 Shutting down gracefully...')
  bot.stop('SIGINT')
  process.exit(0)
})

process.once('SIGTERM', () => {
  console.log('\n🛑 Shutting down gracefully...')
  bot.stop('SIGTERM')
  process.exit(0)
})

start()
