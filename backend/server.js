const express = require('express')
const cors    = require('cors')
const axios   = require('axios')
require('dotenv').config()

const app  = express()
const FLASK = process.env.FLASK_URL || 'http://localhost:5001'

app.use(cors())
app.use(express.json())

// ── health ────────────────────────────────────────────
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', flask: FLASK })
})

// ── predict ───────────────────────────────────────────
app.post('/api/predict', async (req, res) => {
  try {
    const r = await axios.post(`${FLASK}/predict`, req.body, { timeout: 15000 })
    res.json(r.data)
  } catch (e) {
    console.error('Flask /predict error:', e.message)
    res.status(500).json({ error: e.message })
  }
})

// ── explain ───────────────────────────────────────────
app.post('/api/explain', async (req, res) => {
  try {
    const r = await axios.post(`${FLASK}/explain`, req.body, { timeout: 15000 })
    res.json(r.data)
  } catch (e) {
    console.error('Flask /explain error:', e.message)
    res.status(500).json({ error: e.message })
  }
})

// ── recommend ─────────────────────────────────────────
app.post('/api/recommend', async (req, res) => {
  try {
    const r = await axios.post(`${FLASK}/recommend`, req.body, { timeout: 15000 })
    res.json(r.data)
  } catch (e) {
    console.error('Flask /recommend error:', e.message)
    res.status(500).json({ error: e.message })
  }
})

// ── whatif ────────────────────────────────────────────
app.post('/api/whatif', async (req, res) => {
  try {
    const r = await axios.post(`${FLASK}/whatif`, req.body, { timeout: 15000 })
    res.json(r.data)
  } catch (e) {
    console.error('Flask /whatif error:', e.message)
    res.status(500).json({ error: e.message })
  }
})

const PORT = process.env.PORT || 5000
app.listen(PORT, () => console.log(`Express running on http://localhost:${PORT}`))