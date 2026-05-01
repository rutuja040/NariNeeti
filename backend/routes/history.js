const express = require('express')
const router  = express.Router()
const db      = require('../config/db')

router.get('/', (req, res) => {
  const { state, year } = req.query
  let sql    = 'SELECT * FROM schemes WHERE 1=1'
  const vals = []

  if (state) { sql += ' AND State = ?';  vals.push(state) }
  if (year)  { sql += ' AND Year = ?';   vals.push(year)  }

  sql += ' ORDER BY Year, Quarter LIMIT 200'

  db.query(sql, vals, (err, results) => {
    if (err) return res.status(500).json({ error: err.message })
    res.json({ records: results })
  })
})

module.exports = router