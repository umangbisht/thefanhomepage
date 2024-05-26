const express = require('express')
const bodyParser = require('body-parser')
var cors = require('cors')
const app = express()
app.use(cors())
//constants
var config = require('./config/config');
//Port
port = config.port;
require('dotenv').config({ path: '.env' })
app.listen(port)

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

var coin 		= require('./coin');
coin.configure(app);

console.log('API server started on: ' + port);
