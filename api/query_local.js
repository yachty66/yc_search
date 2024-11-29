import { GoogleGenerativeAI } from "@google/generative-ai";
import fs from "fs";
import path from "path";

// Initialize the model
const genAI = new GoogleGenerativeAI(process.env.GOOGLE_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

function get_prompt(query, data) {
  return `
        You get as input all the rows of a database with all companies which ever took part of YC. You are given a query from a user and you must return the IDs of the companies that match the query. Here is the query:

        ---
        ${query}
        ---

        Return the exact names of the companies that match the query. The names of the companies must be taken from the value of the key "company_name" in the database.

        Here is the database:

        ---
        ${data}
        ---

        It is possible that the query has no results; in this case, return an empty array. You must return your result in JSON format like this:

        {"response": ["Company A", "Company B", "Company C"]}

        Return the names of the companies that match the query in JSON format:
    `;
}

function get_clean_json(rawResponse) {
  const cleanJson = rawResponse
    .replace(/```json\n/, "")
    .replace(/\n```/, "")
    .trim();
  return JSON.parse(cleanJson);
}

async function get_company_data(companyNames, allCompanies) {
  return allCompanies.filter((company) =>
    companyNames.includes(company.company_name)
  );
}

export default async function handler(req, res) {
  console.log("Query received:", req.body);

  const { query } = req.body;
  console.log("Getting companies for query:", query);

  // Read the local JSON file
  const filePath = path.join(process.cwd(), "data/all.json");
  const jsonData = fs.readFileSync(filePath, "utf8");
  const allCompanies = JSON.parse(jsonData);

  const prompt = get_prompt(query, JSON.stringify(allCompanies, null, 2));
  const result = await model.generateContent(prompt);
  const companyNames = get_clean_json(await result.response.text()).response;

  const matchedCompanies = await get_company_data(companyNames, allCompanies);
  console.log("Matched Companies:", matchedCompanies);

  return res.status(200).json(matchedCompanies);
}
