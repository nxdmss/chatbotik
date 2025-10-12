import sharp from 'sharp'
import path from 'path'
import { fileURLToPath } from 'url'
import { writeFile, existsSync, mkdirSync } from 'fs'
import { promisify } from 'util'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const writeFileAsync = promisify(writeFile)
const uploadsDir = path.join(__dirname, 'uploads')

// Создаем папку uploads если её нет
if (!existsSync(uploadsDir)) {
  mkdirSync(uploadsDir, { recursive: true })
}

export async function saveImage(imageData, filename) {
  try {
    // Если данные уже в base64, декодируем
    let buffer
    if (typeof imageData === 'string') {
      // Убираем data:image/jpeg;base64, если есть
      const base64Data = imageData.replace(/^data:image\/[a-z]+;base64,/, '')
      buffer = Buffer.from(base64Data, 'base64')
    } else {
      buffer = imageData
    }
    
    // Обрабатываем изображение с помощью Sharp
    const processedImage = await sharp(buffer)
      .resize(800, 600, { 
        fit: 'inside',
        withoutEnlargement: true 
      })
      .jpeg({ quality: 85 })
      .toBuffer()
    
    // Сохраняем файл
    const filePath = path.join(uploadsDir, filename)
    await writeFileAsync(filePath, processedImage)
    
    console.log(`✅ Image saved: ${filename} (${processedImage.length} bytes)`)
    return `/uploads/${filename}`
    
  } catch (error) {
    console.error('❌ Error saving image:', error)
    throw error
  }
}

export function getImagePath(filename) {
  const filePath = path.join(uploadsDir, filename)
  
  // Проверяем существование файла
  if (!existsSync(filePath)) {
    return path.join(__dirname, 'frontend', 'dist', 'assets', 'placeholder.jpg')
  }
  
  return filePath
}

export function generateFilename(originalName, prefix = 'product') {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 8)
  const extension = path.extname(originalName) || '.jpg'
  return `${prefix}_${timestamp}_${random}${extension}`
}

export async function deleteImage(filename) {
  try {
    const filePath = path.join(uploadsDir, filename)
    if (existsSync(filePath)) {
      const { unlink } = await import('fs/promises')
      await unlink(filePath)
      console.log(`✅ Image deleted: ${filename}`)
      return true
    }
    return false
  } catch (error) {
    console.error('❌ Error deleting image:', error)
    return false
  }
}
