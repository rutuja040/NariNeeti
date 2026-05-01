const express = require('express')
const router  = express.Router()
const db      = require('../config/db')

router.get('/', (req, res) => {
  const sql = `
    SELECT p.scheme_name, p.state, p.risk_probability,
           p.risk_label, p.created_at
    FROM predictions_log p
    ORDER BY p.created_at DESC
    LIMIT 100
  `
  db.query(sql, (err, results) => {
    if (err) return res.status(500).json({ error: err.message })
    res.json({ records: results })
  })
})

module.exports = router