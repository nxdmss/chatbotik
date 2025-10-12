import sqlite3 from 'sqlite3'
import { promisify } from 'util'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const dbPath = path.join(__dirname, 'shop.db')

// Создаем подключение к базе данных
const db = new sqlite3.Database(dbPath)

// Промисфицируем методы
const dbRun = promisify(db.run.bind(db))
const dbGet = promisify(db.get.bind(db))
const dbAll = promisify(db.all.bind(db))

export function initDatabase() {
  console.log('🗄️ Initializing database...')
  
  // Создаем таблицы
  const createProductsTable = `
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      price INTEGER NOT NULL,
      description TEXT,
      category TEXT DEFAULT 'general',
      image_url TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `
  
  const createOrdersTable = `
    CREATE TABLE IF NOT EXISTS orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      customer_name TEXT NOT NULL,
      customer_phone TEXT NOT NULL,
      customer_address TEXT,
      total_amount INTEGER NOT NULL,
      status TEXT DEFAULT 'pending',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `
  
  const createOrderItemsTable = `
    CREATE TABLE IF NOT EXISTS order_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      order_id INTEGER,
      product_id INTEGER,
      quantity INTEGER NOT NULL,
      price INTEGER NOT NULL,
      FOREIGN KEY (order_id) REFERENCES orders (id),
      FOREIGN KEY (product_id) REFERENCES products (id)
    )
  `
  
  db.run(createProductsTable)
  db.run(createOrdersTable)
  db.run(createOrderItemsTable)
  
  // Добавляем тестовые данные
  addTestData()
  
  console.log('✅ Database initialized successfully')
}

async function addTestData() {
  try {
    // Проверяем, есть ли уже товары
    const existingProducts = await dbAll('SELECT COUNT(*) as count FROM products')
    
    if (existingProducts[0].count === 0) {
      console.log('📦 Adding test products...')
      
      const testProducts = [
        {
          title: 'iPhone 15 Pro',
          price: 99999,
          description: 'Новейший смартфон Apple с титановым корпусом',
          category: 'electronics'
        },
        {
          title: 'MacBook Air M3',
          price: 129999,
          description: 'Мощный ноутбук для работы и творчества',
          category: 'electronics'
        },
        {
          title: 'Nike Air Max 270',
          price: 8999,
          description: 'Спортивные кроссовки для активного образа жизни',
          category: 'clothing'
        },
        {
          title: 'Кофе Starbucks Premium',
          price: 299,
          description: 'Премиальный кофе в зернах для истинных ценителей',
          category: 'food'
        },
        {
          title: 'Книга "Python для начинающих"',
          price: 1999,
          description: 'Полное руководство по изучению Python',
          category: 'books'
        },
        {
          title: 'Samsung Galaxy S24',
          price: 89999,
          description: 'Флагманский смартфон с ИИ-функциями',
          category: 'electronics'
        },
        {
          title: 'Adidas Ultraboost 22',
          price: 12999,
          description: 'Беговые кроссовки с технологией Boost',
          category: 'clothing'
        },
        {
          title: 'Чай Earl Grey Premium',
          price: 599,
          description: 'Элитный чай с бергамотом',
          category: 'food'
        }
      ]
      
      for (const product of testProducts) {
        await dbRun(
          'INSERT INTO products (title, price, description, category) VALUES (?, ?, ?, ?)',
          [product.title, product.price, product.description, product.category]
        )
      }
      
      console.log(`✅ Added ${testProducts.length} test products`)
    }
  } catch (error) {
    console.error('❌ Error adding test data:', error)
  }
}

export async function getProducts(category = null) {
  try {
    let query = 'SELECT * FROM products ORDER BY created_at DESC'
    let params = []
    
    if (category) {
      query = 'SELECT * FROM products WHERE category = ? ORDER BY created_at DESC'
      params = [category]
    }
    
    const products = await dbAll(query, params)
    return products
  } catch (error) {
    console.error('Error getting products:', error)
    throw error
  }
}

export async function getProductById(id) {
  try {
    const product = await dbGet('SELECT * FROM products WHERE id = ?', [id])
    return product
  } catch (error) {
    console.error('Error getting product by id:', error)
    throw error
  }
}

export async function createProduct(productData) {
  try {
    const { title, price, description, category, image_url } = productData
    
    const result = await dbRun(
      'INSERT INTO products (title, price, description, category, image_url) VALUES (?, ?, ?, ?, ?)',
      [title, price, description || '', category || 'general', image_url || '']
    )
    
    const newProduct = await getProductById(result.lastID)
    return newProduct
  } catch (error) {
    console.error('Error creating product:', error)
    throw error
  }
}

export async function updateProduct(id, productData) {
  try {
    const { title, price, description, category, image_url } = productData
    
    await dbRun(
      'UPDATE products SET title = ?, price = ?, description = ?, category = ?, image_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [title, price, description, category, image_url, id]
    )
    
    const updatedProduct = await getProductById(id)
    return updatedProduct
  } catch (error) {
    console.error('Error updating product:', error)
    throw error
  }
}

export async function deleteProduct(id) {
  try {
    const result = await dbRun('DELETE FROM products WHERE id = ?', [id])
    return result.changes > 0
  } catch (error) {
    console.error('Error deleting product:', error)
    throw error
  }
}

export async function createOrder(orderData) {
  try {
    const { customer_name, customer_phone, customer_address, items } = orderData
    
    // Вычисляем общую сумму
    let totalAmount = 0
    for (const item of items) {
      const product = await getProductById(item.product_id)
      if (product) {
        totalAmount += product.price * item.quantity
      }
    }
    
    // Создаем заказ
    const orderResult = await dbRun(
      'INSERT INTO orders (customer_name, customer_phone, customer_address, total_amount) VALUES (?, ?, ?, ?)',
      [customer_name, customer_phone, customer_address || '', totalAmount]
    )
    
    const orderId = orderResult.lastID
    
    // Создаем элементы заказа
    for (const item of items) {
      const product = await getProductById(item.product_id)
      if (product) {
        await dbRun(
          'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
          [orderId, item.product_id, item.quantity, product.price]
        )
      }
    }
    
    return {
      id: orderId,
      total_amount: totalAmount
    }
  } catch (error) {
    console.error('Error creating order:', error)
    throw error
  }
}

export async function getOrders() {
  try {
    const orders = await dbAll(`
      SELECT 
        o.*,
        COUNT(oi.id) as items_count
      FROM orders o
      LEFT JOIN order_items oi ON o.id = oi.order_id
      GROUP BY o.id
      ORDER BY o.created_at DESC
    `)
    
    return orders
  } catch (error) {
    console.error('Error getting orders:', error)
    throw error
  }
}

export async function getOrderById(id) {
  try {
    const order = await dbGet('SELECT * FROM orders WHERE id = ?', [id])
    if (!order) return null
    
    const items = await dbAll(`
      SELECT 
        oi.*,
        p.title,
        p.description
      FROM order_items oi
      JOIN products p ON oi.product_id = p.id
      WHERE oi.order_id = ?
    `, [id])
    
    order.items = items
    return order
  } catch (error) {
    console.error('Error getting order by id:', error)
    throw error
  }
}

// Закрываем соединение с базой данных при завершении процесса
process.on('exit', () => {
  db.close()
})
