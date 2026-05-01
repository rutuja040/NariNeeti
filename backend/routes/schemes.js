const express    = require('express')
const router     = express.Router()
const controller = require('../controllers/schemeController')

router.get('/',       controller.getSchemes)
router.get('/history', controller.getHistory)

module.exports = router