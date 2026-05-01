const db = require('../config/db')

// get all unique schemes and states
exports.getSchemes = (req, res) => {
  const sql = `
    SELECT DISTINCT Scheme_Name, State, District
    FROM schemes
    ORDER BY Scheme_Name
  `
  db.query(sql, (err, results) => {
    if (err) return res.status(500).json({ error: err.message })

    const schemes  = [...new Set(results.map(r => r.Scheme_Name))]
    const states   = [...new Set(results.map(r => r.State))]

    // districts grouped by state
    const districtsByState = {}
    results.forEach(r => {
      if (!districtsByState[r.State]) districtsByState[r.State] = []
      if (!districtsByState[r.State].includes(r.District)) {
        districtsByState[r.State].push(r.District)
      }
    })

    res.json({ schemes, states, districtsByState })
  })
}

// get historical data for trends page
exports.getHistory = (req, res) => {
  const { state, scheme_name, year_from, year_to } = req.query

  let sql    = 'SELECT * FROM schemes WHERE 1=1'
  const vals = []

  if (state) {
    sql += ' AND State = ?'
    vals.push(state)
  }
  if (scheme_name) {
    sql += ' AND Scheme_Name = ?'
    vals.push(scheme_name)
  }
  if (year_from) {
    sql += ' AND Year >= ?'
    vals.push(parseInt(year_from))
  }
  if (year_to) {
    sql += ' AND Year <= ?'
    vals.push(parseInt(year_to))
  }

  sql += ' ORDER BY Year, Quarter LIMIT 500'

  db.query(sql, vals, (err, results) => {
    if (err) return res.status(500).json({ error: err.message })
    res.json({ records: results, total: results.length })
  })
}