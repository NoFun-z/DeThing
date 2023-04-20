const express = require('express');
const bodyParser = require('body-parser');

const app = express();
const port = 4000;

// Set the "Final Project" folder as the views directory
app.set('views', __dirname);
// Set EJS as the view engine
app.set('view engine', 'ejs');

// Use body-parser middleware to parse request body
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Define route handler for /Login.html endpoint
app.get('/Login.html', (req, res) => {

    // Pass the stdout data to the Login.ejs file and render it with camera element ID as needed
    res.render('Login');
});

app.get('/Home.html', (req, res) => {
  // Access the username query parameter
  const username = req.query.username;

  // Render the Home.ejs file and send it as the response, passing the welcome message and content
  res.render('Home', { welcomeMessage: 'Welcome to my web page ' + username, Content: 'Please add a voice chat' });
});



// Start the server
app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
