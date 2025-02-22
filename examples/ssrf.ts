import express from 'express';
import axios from 'axios';

const app = express();

/**
 * This endpoint accepts a URL as a query parameter and fetches its content.
 * Vulnerability: The URL is taken directly from the user input without proper validation,
 * allowing an attacker to make the server request internal or restricted resources.
 */
app.get('/fetch', async (req, res) => {
  const url = req.query.url;
  if (!url || typeof url !== 'string') {
    return res.status(400).send('Invalid URL parameter.');
  }

  try {
    // SSRF Vulnerability: No validation is performed on the provided URL.
    const response = await axios.get(url);
    res.send(response.data);
  } catch (error) {
    res.status(500).send('Error fetching the URL.');
  }
});

app.listen(3000, () => {
  console.log('Server is running on port 3000');
});
