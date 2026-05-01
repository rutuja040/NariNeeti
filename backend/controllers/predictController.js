const axios = require('axios')
const db    = require('../config/db')
require('dotenv').config()

const FLASK = process.env.FLASK_URL

// ── 1. Risk prediction ────────────────────────────────
exports.predict = async (req, res) => {
  try {
    const response = await axios.post(`${FLASK}/predict`, req.body)
    const result   = response.data

    // save to DB
    const sql = `
      INSERT INTO predictions_log
      (scheme_name, state, district, year, quarter,
       risk_probability, risk_label, risk_category, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW())
    `
    const vals = [
      req.body.Scheme_Name  || '',
      req.body.State        || '',
      req.body.District     || '',
      req.body.Year         || 0,
      req.body.Quarter      || '',
      result.risk_probability,
      result.risk_label,
      result.risk_category
    ]

    db.query(sql, vals, (err) => {
      if (err) console.error('DB log error:', err.message)
    })

    res.json(result)

  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}

// ── 2. SHAP explanation ───────────────────────────────
exports.explain = async (req, res) => {
  try {
    const response = await axios.post(`${FLASK}/explain`, req.body)
    res.json(response.data)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}

// ── 3. What-if simulation ─────────────────────────────
exports.whatif = async (req, res) => {
  try {
    const response = await axios.post(`${FLASK}/whatif`, req.body)
    res.json(response.data)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}

// ── 4. Recommendations ────────────────────────────────
exports.recommend = async (req, res) => {
  try {
    const response = await axios.post(`${FLASK}/recommend`, req.body)
    res.json(response.data)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}

// ── 5. Prediction log ─────────────────────────────────
exports.getLog = (req, res) => {
  const sql = `
    SELECT * FROM predictions_log
    ORDER BY created_at DESC
    LIMIT 50
  `
  db.query(sql, (err, results) => {
    if (err) return res.status(500).json({ error: err.message })
    res.json({ logs: results, total: results.length })
  })
}