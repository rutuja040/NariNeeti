const express    = require('express')
const router     = express.Router()
const controller = require('../controllers/predictController')

router.post('/',          controller.predict)
router.post('/explain',   controller.explain)
router.post('/whatif',    controller.whatif)
router.post('/recommend', controller.recommend)
router.get('/log',        controller.getLog)

module.exports = router