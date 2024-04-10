// Example 1: ChatGPT generated code example with Unnecessary Block Violation (Commit 9)
const axios = require('axios');
const express = require('express');
require('dotenv').config();

const router = express.Router();

router.post('/', async (req, res) => {
    const { prompt, max_tokens } = req.body;

    try {
        const response = await axios({
            method: 'post',
            url: 'https://api.openai.com/v1/engines/davinci-codex/completions',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.OPENAI_KEY}`
            },
            data: {
                prompt,
                max_tokens
            }
        });

        res.json(response.data);
    } catch (err) {
        console.error(err);
        res.status(500).json({ message: 'Server error' });
    }
});

module.exports = router;



//  Example 2: ChatGPT generated code example with Unnecessary Block Violation (Commit 24)

// Dependencies and Libraries
const fs = require("fs");
const path = require('path');
const contentful = require("contentful");
const moment = require('moment');
const xmlFormatter = require('xml-formatter');
const { paramsApplier } = require("react-router-sitemap");

// Configuration Constants
const CONTENTFUL_CONFIG = {
  space: process.env.REACT_APP_SPACE_ID || "f6zwhql64w01",
  accessToken: process.env.REACT_APP_ACCESS_TOKEN || "00b696c26342aa70ce936b551fe48e6548745fa637b6cd0c62fa72886af5bd78",
  environment: process.env.REACT_APP_ENVIRONMENT || "master"
};
const client = contentful.createClient(CONTENTFUL_CONFIG);

// Utility Functions
async function fetchContentfulEntries(contentType) {
  try {
    const entries = await client.getEntries({ content_type: contentType });
    return entries.items.length > 0 ? entries.items : [];
  } catch (error) {
    console.error(`Error fetching ${contentType} entries:`, error);
    return [];
  }
}

// Sitemap Generation Functions
function generatePathsBasedOnRoute(route) {
  const config = { [route.path]: [{ ...route.params }] };
  return paramsApplier([route.path], config);
}

function generateSitemap(routes) {
  const date = moment().format('YYYY-MM-DD');
  const host = 'https://jobsforit.de';

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
      <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      ${routes.map(route => `<url><loc>${host + route}</loc><lastmod>${date}</lastmod></url>`).join("")}
      </urlset>`;

  return xmlFormatter(xml);
}

// Main Execution
async function sitemapGenerator() {
  try {
    console.log('Starting sitemap generation...');

    const technologies = (await fetchContentfulEntries("technology")).map(tech => tech.fields.name.toLowerCase());
    const cities = (await fetchContentfulEntries("city")).map(city => city.fields.name.toLowerCase());
    const jobs = (await fetchContentfulEntries('job')).map(job => encodeURIComponent(job.fields.slug));

    // ... (rest of the routes declaration remains unchanged)

    const newRoutes = routes.flatMap(generatePathsBasedOnRoute);

    console.log('Saving sitemap to public/sitemap.xml');
    fs.writeFileSync(path.join(process.cwd(), 'public', 'sitemap.xml'), generateSitemap(newRoutes));
    console.log('Sitemap generation completed.');

  } catch (error) {
    console.error('Error generating sitemap:', error);
  }
}

sitemapGenerator();


// Example 3:
import fs from 'fs';
import { promisify } from 'util';
import { sanitizeAndResolvePath } from '../../fileutils/sanitizeAndResolvePath.js';

const readFileAsync = promisify(fs.readFile);

export async function fileReadHandler(req, res) {
  const { filepath } = req.params;

  if (!filepath) {
    return res.status(400).send({ error: 'File path is required' });
  }

  try {
    const resolvedPath = sanitizeAndResolvePath(filepath);
    if (!fs.existsSync(resolvedPath)) {  // Check if file exists
      return res.status(404).send({ error: 'File not found' });
    }
    const fileContent = await readFileAsync(resolvedPath, 'utf8');
    res.send(fileContent);
  } catch (error) {
    res.status(500).send({ error: 'Unable to read file' });
  }
}

